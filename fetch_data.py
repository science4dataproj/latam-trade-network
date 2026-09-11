"""
Extraction of bilateral export data from UN Comtrade for the Latin
American trade network.

REQUIRES:
    pip install comtradeapicall pandas

REQUIRES A FREE API KEY:
    1. Register at https://comtradeplus.un.org (free)
    2. Generate a subscription key in the developer portal
    3. Export it as an environment variable:
       export UN_COMTRADE_KEY="your_key_here"

EXTRACTION DESIGN:
    - For each REPORTER country in the list, we request its EXPORTS
      (flowCode='X') to ALL partners (partnerCode is left unrestricted here;
      filtering down to the 10 countries of interest happens in the
      processing step). This resolves the mirror-statistics problem: we
      only use the "exporter" side as the source of truth, never mixing it
      with what the partner reported as an import.
    - freqCode='A' (annual) is requested first, because monthly coverage
      varies a lot by country and may not exist for several of these 10.
      If validation shows several countries do have complete monthly data,
      a second pass with freqCode='M' can be run.
    - cmdCode='TOTAL' (all products, undisaggregated) for the general
      network.
    - Each call is saved raw to data/raw/ without transformation — any
      cleaning or filtering happens in a separate processing script, not
      here.
"""

import os
import time
import pandas as pd
import comtradeapicall

SUBSCRIPTION_KEY = os.environ.get("UN_COMTRADE_KEY")
if not SUBSCRIPTION_KEY:
    raise RuntimeError(
        "Missing UN_COMTRADE_KEY environment variable. "
        "See instructions in this file's docstring."
    )

# M49 codes for the 10 countries (Cuba and Venezuela excluded due to coverage)
REPORTERS = {
    "Mexico": 484,
    "Brazil": 76,
    "Argentina": 32,
    "Colombia": 170,
    "Peru": 604,
    "Ecuador": 218,
    "Bolivia": 68,
    "Honduras": 340,
    "Guatemala": 320,
    "Chile": 152,
}

START_YEAR = 2000
END_YEAR = 2024

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)


def fetch_reporter_year(reporter_name: str, reporter_code: int, year: int) -> pd.DataFrame:
    """Fetch TOTAL exports from one reporter to all partners, for one year."""
    df = comtradeapicall.getFinalData(
        SUBSCRIPTION_KEY,
        typeCode="C",          # goods trade
        freqCode="A",          # annual
        clCode="HS",
        period=str(year),
        reporterCode=str(reporter_code),
        cmdCode="TOTAL",
        flowCode="X",          # exports
        partnerCode=None,      # all partners; filtered later
        partner2Code=None,
        customsCode=None,
        motCode=None,
        maxRecords=2500,
        format_output="JSON",
        countOnly=None,
        includeDesc=True,
    )
    return df


def main():
    for name, code in REPORTERS.items():
        frames = []
        for year in range(START_YEAR, END_YEAR + 1):
            try:
                df = fetch_reporter_year(name, code, year)
                if df is not None and len(df) > 0:
                    frames.append(df)
                    print(f"{name} {year}: {len(df)} rows")
                else:
                    print(f"{name} {year}: no data")
            except Exception as e:
                print(f"{name} {year}: ERROR - {e}")
            time.sleep(1)  # respect rate limit

        if frames:
            full = pd.concat(frames, ignore_index=True)
            out_path = os.path.join(RAW_DIR, f"{name.lower()}_exports_raw.csv")
            full.to_csv(out_path, index=False)
            print(f"Saved: {out_path} ({len(full)} total rows)")
        else:
            print(f"WARNING: {name} had no data in the {START_YEAR}-{END_YEAR} range")


if __name__ == "__main__":
    main()
