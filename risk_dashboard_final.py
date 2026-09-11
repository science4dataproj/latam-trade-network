"""
Dashboard final: combina dos indicadores complementarios, no uno solo.

    - riesgo_cronico: nivel ABSOLUTO de concentración, basado en el % de
      exportaciones que va al socio dominante (top_partner_share). No depende
      de la historia propia del país -- es comparable entre países.
      Umbrales: >50% Alto, 30-50% Moderado, <30% Bajo.

    - p_alert: probabilidad de que la entropía haya caído por debajo del
      percentil 20 de la propia historia del país (paso 4c) -- detecta
      CAMBIO reciente, no nivel absoluto.

Por qué los dos y no uno: ya vimos que México tiene el riesgo crónico más
alto del grupo (92.6% de sus exportaciones a un solo país) pero casi cero
probabilidad de alerta (porque esa dependencia es estructural, no un cambio
reciente). Un solo indicador oculta la mitad de la historia en cualquier
dirección -- un país puede estar sano en uno y en foco rojo en el otro, y
esa combinación es información real, no ruido.
"""

import os
import pandas as pd

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "data", "processed")

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
    alerts = pd.read_csv(os.path.join(PROCESSED_DIR, "risk_alert_from_forecast.csv"))

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
    print(f"\nGuardado: {out_path}")

    print("\nCuadrantes:")
    for _, row in dash.iterrows():
        cambio = "alerta reciente" if row["p_alert"] > 0.3 else "sin cambio reciente"
        print(f"  {row['nombre']:12s}: riesgo crónico {row['riesgo_cronico']:9s} | {cambio} (p={row['p_alert']:.3f})")


if __name__ == "__main__":
    main()
