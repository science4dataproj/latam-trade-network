"""
Final dashboard: combines two complementary indicators, not just one.

    - riesgo_cronico ("chronic risk"): ABSOLUTE concentration level, based
      on the % of exports going to the dominant partner (top_partner_share).
      Does not depend on the country's own history -- comparable across
      countries. Thresholds: >50% High, 30-50% Moderate, <30% Low.

    - p_alert: probability that entropy has fallen below the country's own
      20th historical percentile (step 4c) -- detects RECENT CHANGE, not
      absolute level.

Why both and not just one: we already saw that Mexico has the highest
chronic risk in the group (92.6% of its exports to a single country) but
near-zero alert probability (because that dependence is structural, not a
recent change). A single indicator hides half the story in either
direction -- a country can look healthy on one and be a red flag on the
other, and that combination is real information, not noise.

Note: DataFrame column names and category values (e.g. "riesgo_cronico",
"Alto"/"Moderado"/"Bajo") are kept in Spanish to stay consistent with the
already-generated processed CSVs and the figure-generation scripts that
consume them (make_report_figures_v2.py). Only comments, docstrings, and
console messages were translated to English.
"""

import os
import pandas as pd

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

COUNTRY_NAMES = {"MEX": "México", "BRA": "Brasil", "ARG": "Argentina", "COL": "Colombia",
                  "PER": "Perú", "ECU": "Ecuador", "BOL": "Bolivia", "HND": "Honduras",
                  "GTM": "Guatemala", "CHL": "Chile"}


def chronic_tier(share: float) -> str:
    if share > 0.50:
        return "Alto"
    elif share > 0.30:
        return "Moderado"
    return "Bajo"


def main():
    comp = pd.read_csv(os.path.join(PROCESSED_DIR, "entropy_regional_vs_global.csv"))
    alerts = pd.read_csv(os.path.join(PROCESSED_DIR, "risk_alert_from_forecast_global.csv"))

    latest_comp = comp.sort_values("year").groupby("country").tail(1)
    latest_alert = alerts.sort_values("year").groupby("country").tail(1)

    dash = latest_comp.merge(latest_alert[["country", "p_alert"]], on="country", how="left")
    dash["riesgo_cronico"] = dash["top_partner_share"].apply(chronic_tier)
    dash["nombre"] = dash["country"].map(COUNTRY_NAMES)

    dash = dash[["nombre", "country", "top_partner", "top_partner_share",
                 "riesgo_cronico", "p_alert"]].sort_values("top_partner_share", ascending=False)

    out_path = os.path.join(PROCESSED_DIR, "risk_dashboard_final.csv")
    dash.to_csv(out_path, index=False)

    print(dash.to_string(index=False))
    print(f"\nSaved: {out_path}")

    print("\nQuadrants:")
    for _, row in dash.iterrows():
        change = "recent alert" if row["p_alert"] > 0.3 else "no recent change"
        print(f"  {row['nombre']:12s}: chronic risk {row['riesgo_cronico']:9s} | {change} (p={row['p_alert']:.3f})")


if __name__ == "__main__":
    main()
