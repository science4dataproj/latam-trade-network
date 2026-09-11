"""
Incremental data update: adds new years (2025, 2026) to the existing raw
CSVs WITHOUT re-requesting 2000-2024 (already have those).

Expectation notice: international trade data is published with a lag.
2025 may arrive incomplete or subject to revision; 2026, mid-year, will
very likely come back empty for several or all countries -- that is not a
script error, it is Comtrade's normal publication lag. What did and did
not arrive is reported explicitly, nothing is assumed.
"""

import os
import time
import pandas as pd
import comtradeapicall

SUBSCRIPTION_KEY = os.environ.get("UN_COMTRADE_KEY")
if not SUBSCRIPTION_KEY:
    raise RuntimeError("Missing UN_COMTRADE_KEY environment variable.")

REPORTERS = {
    "mexico": 484, "brazil": 76, "argentina": 32, "colombia": 170, "peru": 604,
    "ecuador": 218, "bolivia": 68, "honduras": 340, "guatemala": 320, "chile": 152,
}

NEW_YEARS = [2025, 2026]
RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")


def fetch_reporter_year(reporter_code: int, year: int) -> pd.DataFrame:
    return comtradeapicall.getFinalData(
        SUBSCRIPTION_KEY, typeCode="C", freqCode="A", clCode="HS", period=str(year),
        reporterCode=str(reporter_code), cmdCode="TOTAL", flowCode="X",
        partnerCode=None, partner2Code=None, customsCode=None, motCode=None,
        maxRecords=2500, format_output="JSON", countOnly=None, includeDesc=True,
    )


def main():
    summary = []
    for name, code in REPORTERS.items():
        existing_path = os.path.join(RAW_DIR, f"{name}_exports_raw.csv")
        if not os.path.exists(existing_path):
            print(f"WARNING: {existing_path} does not exist, skipping {name}")
            continue

        existing = pd.read_csv(existing_path, low_memory=False)
        already_have_years = set(existing["refYear"].unique())

        new_frames = []
        for year in NEW_YEARS:
            if year in already_have_years:
                continue
            try:
                df = fetch_reporter_year(code, year)
                n_rows = len(df) if df is not None else 0
                summary.append({"country": name, "year": year, "rows": n_rows})
                if df is not None and n_rows > 0:
                    new_frames.append(df)
                print(f"{name} {year}: {n_rows} rows")
            except Exception as e:
                summary.append({"country": name, "year": year, "rows": 0, "error": str(e)})
                print(f"{name} {year}: ERROR - {e}")
            time.sleep(1)

        if new_frames:
            combined = pd.concat([existing] + new_frames, ignore_index=True)
            combined.to_csv(existing_path, index=False)
            print(f"  Updated: {existing_path} ({len(combined)} total rows)")
        else:
            print(f"  No new years with data for {name}, file unchanged")

    print("\nSummary of new-year availability:")
    summary_df = pd.DataFrame(summary)
    print(summary_df.to_string(index=False) if len(summary_df) else "Nothing to report")


if __name__ == "__main__":
    main()
