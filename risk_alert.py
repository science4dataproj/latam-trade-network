"""
Translation of the probabilistic forecast (step 4b) into an alert probability.

Design history (documented, not deleted): the initial approach trained a
supervised classifier (Logistic Regression) on lagged entropy features to
predict whether the following year would cross the country's own 20th
historical percentile. Result: ROC-AUC ~ 0.49, PR-AUC barely above the base
rate -- no real predictive signal, even with an added 3-year momentum
feature. Conclusion: short entropy lags do not predict a one-year-ahead
threshold crossing well, consistent with the structural breaks detected in
(4a) operating on multi-year scales, not year-to-year.

Approach adopted instead: rather than a new classifier, the predictive
distribution ALREADY produced by each country-year's best forecasting model
(mean + prediction-interval standard deviation) is used. The alert
probability is the area of that normal distribution below the risk
threshold (expanding historical 20th percentile) -- the same calculation
underlying a Value-at-Risk: P(risk) = P(forecast_entropy < threshold).

This directly reuses the uncertainty already validated in 4b instead of
introducing a new model with no signal.
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy.stats import norm

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
METRICS_FILENAME = sys.argv[1] if len(sys.argv) > 1 else "network_metrics_by_country_year.csv"
FORECAST_FILENAME = sys.argv[2] if len(sys.argv) > 2 else "forecast_walkforward_results.csv"
OUTPUT_SUFFIX = sys.argv[3] if len(sys.argv) > 3 else ""
METRICS_PATH = os.path.join(PROCESSED_DIR, METRICS_FILENAME)
FORECAST_PATH = os.path.join(PROCESSED_DIR, FORECAST_FILENAME)

MIN_HISTORY = 5
Z_80 = 1.2816


def historical_threshold(entropy_series: np.ndarray, upto_idx: int) -> float:
    """20th percentile using only observations prior to upto_idx."""
    past = entropy_series[:upto_idx]
    past_valid = past[~np.isnan(past)]
    if len(past_valid) < MIN_HISTORY:
        return np.nan
    return np.percentile(past_valid, 20)


def forecast_to_alert_probability(forecast_results: pd.DataFrame, metrics: pd.DataFrame) -> pd.DataFrame:
    # Reconstruct each prediction's implied sigma from the 80% interval
    # already computed in the forecast (pi_hi - pi_lo = 2 * Z_80 * sigma)
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

            # Use the method with the lowest global MAE from 4b as the
            # probability source (naive) -- consistent with the finding
            # that it was the best forecast point for most countries
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
    print(f"Saved: {out_path} ({len(alerts)} rows)\n")

    # Simple evaluation: did years with high p_alert have more real alerts?
    alerts_valid = alerts.dropna(subset=["actual_alert"])
    from sklearn.metrics import roc_auc_score, average_precision_score
    print("ROC-AUC (p_alert vs. actual alert):", roc_auc_score(alerts_valid.actual_alert, alerts_valid.p_alert))
    print("PR-AUC:", average_precision_score(alerts_valid.actual_alert, alerts_valid.p_alert))
    print("Base rate:", alerts_valid.actual_alert.mean())

    print("\nMost recent year available by country (current situation):")
    latest = alerts.sort_values("year").groupby("country").tail(1)
    print(latest[["country", "year", "forecast_mu", "p_alert"]].sort_values("p_alert", ascending=False).to_string(index=False))
