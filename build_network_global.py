"""
Expanded partner-universe version: instead of restricting each LatAm
country's export destinations to the other 9 in the region, the most
relevant global trading partners are also included (USA, China, Germany as
an EU anchor, Japan, South Korea).

Why: the regional-only version measured "how diversified is a country
WITHIN LatAm," which is blind to massive dependencies outside the region
(e.g., Mexico and the US). This version corrects that blind spot for
export_entropy.

Explicitly documented scope limitation: the 5 global partners were NEVER
queried as reporters (their own trade was not requested), they only appear
as partners in the 10 LatAm countries' export reports. Therefore, this
correction applies to export_entropy (DESTINATION diversification), not to
import_entropy (which remains limited to the regional universe, since we
do not have the US/China/etc. export reports toward LatAm).
"""

import glob
import os
import numpy as np
import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

LATAM_ISO = {"MEX", "BRA", "ARG", "COL", "PER", "ECU", "BOL", "HND", "GTM", "CHL"}
GLOBAL_PARTNERS_ISO = {"USA", "CHN", "DEU", "JPN", "KOR"}
FULL_PARTNER_SET = LATAM_ISO | GLOBAL_PARTNERS_ISO
MAX_ENTROPY_GLOBAL = np.log(len(FULL_PARTNER_SET) - 1)  # log(13)


def load_and_clean(filepath: str, partner_set: set) -> pd.DataFrame:
    df = pd.read_csv(filepath, low_memory=False)
    df = df[df["motCode"] == 0]
    df = df[df["partner2Code"] == 0]
    df = df[df["customsCode"] == "C00"]
    df = df[df["partnerCode"] != 0]
    df = df[df["partnerISO"].isin(partner_set)]
    return df[["reporterISO", "partnerISO", "refYear", "primaryValue"]].rename(
        columns={"reporterISO": "exporter", "partnerISO": "importer",
                 "refYear": "year", "primaryValue": "value_usd"}
    )


def shannon_entropy(weights: np.ndarray, max_entropy: float) -> float:
    weights = weights[weights > 0]
    if len(weights) == 0:
        return np.nan
    p = weights / weights.sum()
    h = -np.sum(p * np.log(p))
    return h / max_entropy


def main():
    raw_files = sorted(glob.glob(os.path.join(RAW_DIR, "*_exports_raw.csv")))
    edges_global = pd.concat(
        [load_and_clean(f, FULL_PARTNER_SET) for f in raw_files], ignore_index=True
    )
    out_edges_path = os.path.join(PROCESSED_DIR, "trade_edges_global_partners.csv")
    edges_global.to_csv(out_edges_path, index=False)
    print(f"Expanded edge list saved: {out_edges_path} ({len(edges_global)} rows)")

    # export_entropy with expanded universe, by country-year
    records = []
    for (country, year), df_cy in edges_global.groupby(["exporter", "year"]):
        weights = df_cy["value_usd"].values
        records.append({
            "country": country,
            "year": year,
            "export_entropy_global": shannon_entropy(weights, MAX_ENTROPY_GLOBAL),
            "n_export_partners_global": (weights > 0).sum(),
            "top_partner_share": weights.max() / weights.sum() if weights.sum() > 0 else np.nan,
            "top_partner": df_cy.loc[df_cy["value_usd"].idxmax(), "importer"],
        })
    entropy_global = pd.DataFrame(records).sort_values(["country", "year"])

    # Compare against the already-computed regional-only version
    regional = pd.read_csv(os.path.join(PROCESSED_DIR, "network_metrics_by_country_year.csv"))
    comparison = entropy_global.merge(
        regional[["country", "year", "export_entropy"]].rename(columns={"export_entropy": "export_entropy_regional"}),
        on=["country", "year"], how="left"
    )
    comparison["gap"] = comparison["export_entropy_regional"] - comparison["export_entropy_global"]

    out_comp_path = os.path.join(PROCESSED_DIR, "entropy_regional_vs_global.csv")
    comparison.to_csv(out_comp_path, index=False)
    print(f"Comparison saved: {out_comp_path}")

    # network_metrics_global.csv: same format as network_metrics_by_country_year.csv
    # (country, year, export_entropy, n_export_partners) so structural_breaks.py,
    # forecasting.py and risk_alert.py can read it without further changes
    metrics_global = entropy_global.rename(
        columns={"export_entropy_global": "export_entropy", "n_export_partners_global": "n_export_partners"}
    )[["country", "year", "export_entropy", "n_export_partners"]]
    out_metrics_path = os.path.join(PROCESSED_DIR, "network_metrics_global.csv")
    metrics_global.to_csv(out_metrics_path, index=False)
    print(f"Metrics saved: {out_metrics_path}\n")

    print("2000-2024 average, regional vs. global, and most recent dominant partner:")
    latest = comparison.sort_values("year").groupby("country").tail(1)
    avg = comparison.groupby("country")[["export_entropy_regional", "export_entropy_global", "gap"]].mean().round(3)
    avg["top_partner_2024"] = latest.set_index("country")["top_partner"]
    avg["top_partner_share_2024"] = latest.set_index("country")["top_partner_share"].round(3)
    print(avg.sort_values("gap", ascending=False))


if __name__ == "__main__":
    main()
