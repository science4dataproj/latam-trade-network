"""
Versión ampliada del universo de partners: en vez de restringir los destinos
de exportación de cada país LatAm a los otros 9 de la región, se incluyen
también los socios comerciales globales más relevantes (EE.UU., China,
Alemania como ancla de la UE, Japón, Corea del Sur).

Por qué: la versión regional-only medía "qué tan diversificado está un país
DENTRO de LatAm", lo cual es ciego a dependencias masivas fuera de la región
(ej. México y EE.UU.). Esta versión corrige ese punto ciego para
export_entropy.

Limitación de alcance, documentada explícitamente: los 5 socios globales
NUNCA fueron consultados como reporters (no se pidió su propio comercio),
solo aparecen como partners en los reportes de exportación de los 10 países
LatAm. Por lo tanto, esta corrección aplica a export_entropy (diversificación
de DESTINOS), no a import_entropy (que seguiría limitado al universo
regional, ya que no tenemos el reporte de exportación de EE.UU./China/etc.
hacia LatAm).
"""

import glob
import os
import numpy as np
import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "data", "processed")

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
    print(f"Edge list ampliado guardado: {out_edges_path} ({len(edges_global)} filas)")

    # export_entropy con universo ampliado, por país-año
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

    # Comparar contra la versión regional-only ya calculada
    regional = pd.read_csv(os.path.join(PROCESSED_DIR, "network_metrics_by_country_year.csv"))
    comparison = entropy_global.merge(
        regional[["country", "year", "export_entropy"]].rename(columns={"export_entropy": "export_entropy_regional"}),
        on=["country", "year"], how="left"
    )
    comparison["gap"] = comparison["export_entropy_regional"] - comparison["export_entropy_global"]

    out_comp_path = os.path.join(PROCESSED_DIR, "entropy_regional_vs_global.csv")
    comparison.to_csv(out_comp_path, index=False)
    print(f"Comparación guardada: {out_comp_path}")

    # network_metrics_global.csv: mismo formato que network_metrics_by_country_year.csv
    # (country, year, export_entropy, n_export_partners) para que structural_breaks.py,
    # forecasting.py y risk_alert.py lo puedan leer sin cambios adicionales
    metrics_global = entropy_global.rename(
        columns={"export_entropy_global": "export_entropy", "n_export_partners_global": "n_export_partners"}
    )[["country", "year", "export_entropy", "n_export_partners"]]
    out_metrics_path = os.path.join(PROCESSED_DIR, "network_metrics_global.csv")
    metrics_global.to_csv(out_metrics_path, index=False)
    print(f"Métricas guardadas: {out_metrics_path}\n")

    print("Promedio 2000-2024, regional vs. global, y el socio dominante más reciente:")
    latest = comparison.sort_values("year").groupby("country").tail(1)
    avg = comparison.groupby("country")[["export_entropy_regional", "export_entropy_global", "gap"]].mean().round(3)
    avg["top_partner_2024"] = latest.set_index("country")["top_partner"]
    avg["top_partner_share_2024"] = latest.set_index("country")["top_partner_share"].round(3)
    print(avg.sort_values("gap", ascending=False))


if __name__ == "__main__":
    main()
