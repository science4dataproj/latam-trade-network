"""
Processing of raw UN Comtrade data -> clean bilateral edge list for the
Latin American trade network.

Corrections applied to the raw data (documented, not silent):
    1. motCode == 0 filter ("TOTAL MOT"): several countries report trade
       broken down by mode of transport (air, sea, land, etc.) IN ADDITION
       to a row with the already-aggregated total. Summing everything
       without filtering doubles the value. We keep only the already
       aggregated row.
    2. partner2Code == 0 filter ("World"): similarly to the point above,
       several countries also break down by "partner2" (consignee/final
       destination) in addition to reporting the total. Same double-count
       problem if not filtered, same solution: keep only the total.
    3. customsCode == 'C00' filter ("TOTAL CPC"): a third level of
       breakdown, this time by customs regime (direct export vs. other
       regimes such as re-export or free trade zones). Same pattern, same
       solution.
    4. partnerCode != 0 filter: excludes the "World" row (global
       aggregate), we only want the bilateral breakdown.
    5. Partner filter to the 10 countries on the list: each reporter
       exported to ~100-400 partners worldwide; we keep only the other 9
       LatAm countries on our list.
    6. Value source: ALWAYS the exporter side (reporter's flowCode='X').
       Not reconciled against what the partner reported as an import —
       this is a documented design decision, not an oversight
       (see README, limitations section).

Known coverage gaps (not imputed, left as genuine absence):
    - Honduras: no data in 2008, 2013, 2022.
"""

import glob
import os
import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

# The 10 countries in the study (Cuba and Venezuela excluded for coverage)
LATAM_ISO = {"MEX", "BRA", "ARG", "COL", "PER", "ECU", "BOL", "HND", "GTM", "CHL"}


def load_and_clean(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath, low_memory=False)

    before = len(df)

    # 1. Only the aggregated total by mode of transport
    df = df[df["motCode"] == 0]

    # 2. Only the aggregated total by partner2 (avoids double counting from
    #    the "consignee / final destination" breakdown)
    df = df[df["partner2Code"] == 0]

    # 3. Only the aggregated total by customs regime
    df = df[df["customsCode"] == "C00"]

    # 4. Exclude the "World" row
    df = df[df["partnerCode"] != 0]

    # 5. Only partners within our list of 10 countries
    df = df[df["partnerISO"].isin(LATAM_ISO)]

    after = len(df)
    reporter = df["reporterISO"].iloc[0] if len(df) > 0 else "UNKNOWN"
    print(f"{filepath}: {before} raw rows -> {after} clean rows (reporter={reporter})")

    # Check for residual duplicates: there should be no more than one row
    # per (reporterISO, refYear, partnerISO) after the filters above
    dup_check = df.groupby(["reporterISO", "refYear", "partnerISO"]).size()
    n_dups = (dup_check > 1).sum()
    if n_dups > 0:
        print(f"  WARNING: {n_dups} reporter-year-partner combinations with residual duplicates")

    return df[["reporterISO", "partnerISO", "refYear", "primaryValue"]].rename(
        columns={
            "reporterISO": "exporter",
            "partnerISO": "importer",
            "refYear": "year",
            "primaryValue": "value_usd",
        }
    )


def main():
    raw_files = sorted(glob.glob(os.path.join(RAW_DIR, "*_exports_raw.csv")))
    if not raw_files:
        raise RuntimeError(f"No CSVs found in {RAW_DIR}")

    all_edges = [load_and_clean(f) for f in raw_files]
    edges = pd.concat(all_edges, ignore_index=True)

    # Report final coverage: how many years each country has as an exporter
    # within our network of 10
    coverage = edges.groupby("exporter")["year"].nunique().sort_values()
    print("\nFinal coverage (years with at least one reported edge):")
    print(coverage)

    out_path = os.path.join(PROCESSED_DIR, "trade_edges_latam.csv")
    edges.to_csv(out_path, index=False)
    print(f"\nSaved: {out_path} ({len(edges)} total edges)")


if __name__ == "__main__":
    main()
