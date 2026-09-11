"""
Traducción del forecast probabilístico (paso 4b) a probabilidad de alerta.

Historial de diseño (documentado, no borrado): el enfoque inicial entrenaba
un clasificador supervisado (Logistic Regression) sobre features rezagadas
de entropía para predecir si el año siguiente cruzaría el percentil 20
histórico del propio país. Resultado: ROC-AUC ≈ 0.49, PR-AUC apenas por
encima de la tasa base — sin señal predictiva real, ni con features
adicionales de momentum de 3 años. Conclusión: los lags cortos de entropía
no predicen bien un cruce de umbral a un año, consistente con que los
quiebres estructurales detectados (4a) operan en escalas multi-año, no
año-a-año.

Enfoque adoptado en su lugar: en vez de un clasificador nuevo, se usa la
distribución predictiva que YA generó el mejor modelo de forecasting de cada
país-año (media + desviación estándar del intervalo de predicción). La
probabilidad de alerta es el área de esa distribución normal por debajo del
umbral de riesgo (percentil 20 histórico expandido) -- el mismo cálculo que
sustenta un Value-at-Risk: P(riesgo) = P(entropía_forecast < umbral).

Esto reutiliza directamente la incertidumbre ya validada en 4b en vez de
introducir un modelo nuevo sin señal.
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy.stats import norm

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "data", "processed")
METRICS_FILENAME = sys.argv[1] if len(sys.argv) > 1 else "network_metrics_by_country_year.csv"
FORECAST_FILENAME = sys.argv[2] if len(sys.argv) > 2 else "forecast_walkforward_results.csv"
OUTPUT_SUFFIX = sys.argv[3] if len(sys.argv) > 3 else ""
METRICS_PATH = os.path.join(PROCESSED_DIR, METRICS_FILENAME)
FORECAST_PATH = os.path.join(PROCESSED_DIR, FORECAST_FILENAME)

MIN_HISTORY = 5
Z_80 = 1.2816


def historical_threshold(entropy_series: np.ndarray, upto_idx: int) -> float:
    """Percentil 20 usando solo observaciones anteriores a upto_idx."""
    past = entropy_series[:upto_idx]
    past_valid = past[~np.isnan(past)]
    if len(past_valid) < MIN_HISTORY:
        return np.nan
    return np.percentile(past_valid, 20)


def forecast_to_alert_probability(forecast_results: pd.DataFrame, metrics: pd.DataFrame) -> pd.DataFrame:
    # Reconstruir sigma implícito de cada predicción a partir del intervalo
    # de 80% ya calculado en el forecast (pi_hi - pi_lo = 2 * Z_80 * sigma)
    fr = forecast_results.copy()
    fr["sigma_implied"] = (fr["pi_hi"] - fr["pi_lo"]) / (2 * Z_80)

    records = []
    for country, df_c in metrics.groupby("country"):
        df_c = df_c.sort_values("year").reset_index(drop=True)
        entropy = df_c["export_entropy"].values
        years = df_c["year"].values

        for idx, year in enumerate(years):
            threshold = historical_threshold(entropy, idx)
            if np.isnan(threshold):
                continue

            fc_rows = fr[(fr.country == country) & (fr.year == year)]
            if fc_rows.empty:
                continue

            # Usar el método con menor MAE global de 4b como fuente de la
            # probabilidad (naive) -- consistente con el hallazgo de que fue
            # el mejor punto de forecast en la mayoría de los países
            best_row = fc_rows[fc_rows.method == "naive"]
            if best_row.empty:
                continue
            best_row = best_row.iloc[0]

            mu, sigma = best_row["y_pred"], best_row["sigma_implied"]
            if sigma <= 0 or np.isnan(sigma):
                continue

            p_alert = norm.cdf(threshold, loc=mu, scale=sigma)
            actual_alert = int(entropy[idx] < threshold) if not np.isnan(entropy[idx]) else np.nan

            records.append({
                "country": country,
                "year": year,
                "forecast_mu": mu,
                "forecast_sigma": sigma,
                "threshold_p20": threshold,
                "p_alert": p_alert,
                "actual_alert": actual_alert,
                "actual_entropy": entropy[idx],
            })

    return pd.DataFrame(records)


if __name__ == "__main__":
    metrics = pd.read_csv(METRICS_PATH)
    forecast_results = pd.read_csv(FORECAST_PATH)

    alerts = forecast_to_alert_probability(forecast_results, metrics)
    out_path = os.path.join(PROCESSED_DIR, f"risk_alert_from_forecast{OUTPUT_SUFFIX}.csv")
    alerts.to_csv(out_path, index=False)
    print(f"Guardado: {out_path} ({len(alerts)} filas)\n")

    # Evaluación simple: ¿los años con p_alert alto tuvieron más alertas reales?
    alerts_valid = alerts.dropna(subset=["actual_alert"])
    from sklearn.metrics import roc_auc_score, average_precision_score
    print("ROC-AUC (p_alert vs. alerta real):", roc_auc_score(alerts_valid.actual_alert, alerts_valid.p_alert))
    print("PR-AUC:", average_precision_score(alerts_valid.actual_alert, alerts_valid.p_alert))
    print("Tasa base:", alerts_valid.actual_alert.mean())

    print("\nÚltimo año disponible por país (situación actual):")
    latest = alerts.sort_values("year").groupby("country").tail(1)
    print(latest[["country", "year", "forecast_mu", "p_alert"]].sort_values("p_alert", ascending=False).to_string(index=False))
