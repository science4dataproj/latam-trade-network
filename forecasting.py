"""
Probabilistic forecasting of export_entropy with walk-forward validation.

Methods compared:
    - naive: last observed value (mandatory baseline)
    - ets: Holt linear trend (statsmodels ExponentialSmoothing)
    - arima: SARIMAX with order selected by AIC over a small grid
    - bayesian: Bayesian Ridge regression (sklearn) on [year, year^2] —
      genuinely Bayesian (Gaussian prior on coefficients, not just the
      name): gives a posterior mean + predictive standard deviation, hence
      the interval.
    - xgboost: XGBoost on lag features (lag1, lag2) + year. With initial
      folds of only 12-15 training points, it is expected to compete
      poorly against the simple baselines — that is reported as-is, not
      hidden or forced to "win."

Validation: expanding-window walk-forward. min_train initial training
years, then forecast 1 year ahead, add the real year, repeat. Metric: MAE
and 80% prediction-interval coverage (how often the real value fell inside
the interval — the calibration check that separates a real interval from
decoration).
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.linear_model import BayesianRidge
import xgboost as xgb

warnings.filterwarnings("ignore")

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
METRICS_FILENAME = sys.argv[1] if len(sys.argv) > 1 else "network_metrics_by_country_year.csv"
OUTPUT_SUFFIX = sys.argv[2] if len(sys.argv) > 2 else ""
METRICS_PATH = os.path.join(PROCESSED_DIR, METRICS_FILENAME)

MIN_TRAIN = 15
Z_80 = 1.2816  # z-score for an 80% interval


def fit_predict_naive(y_train, t_train, t_pred):
    point = y_train[-1]
    # PI based on the historical deviation of year-over-year changes (naive walk)
    diffs = np.diff(y_train)
    sigma = np.std(diffs) if len(diffs) > 1 else 0.05
    return point, point - Z_80 * sigma, point + Z_80 * sigma


def fit_predict_ets(y_train, t_train, t_pred):
    model = ExponentialSmoothing(y_train, trend="add", damped_trend=True).fit()
    point = model.forecast(1)[0]
    resid_sigma = np.std(model.resid)
    return point, point - Z_80 * resid_sigma, point + Z_80 * resid_sigma


def fit_predict_arima(y_train, t_train, t_pred):
    best_aic, best_order, best_fit = np.inf, None, None
    for p in range(3):
        for d in range(2):
            for q in range(3):
                try:
                    fit = sm.tsa.SARIMAX(y_train, order=(p, d, q),
                                          enforce_stationarity=False,
                                          enforce_invertibility=False).fit(disp=False)
                    if fit.aic < best_aic:
                        best_aic, best_order, best_fit = fit.aic, (p, d, q), fit
                except Exception:
                    continue
    fc = best_fit.get_forecast(1)
    point = fc.predicted_mean[0]
    ci = fc.conf_int(alpha=0.20)
    return point, ci[0][0], ci[0][1]


def fit_predict_bayesian(y_train, t_train, t_pred):
    # Standardize year (center and scale) before building features — without
    # this, [t, t^2] with raw years (~2015, ~4,060,225) badly conditions
    # BayesianRidge's precision matrix and produces absurd intervals.
    t_mean, t_std = t_train.mean(), t_train.std()
    t_train_std = (t_train - t_mean) / t_std
    t_pred_std = (t_pred - t_mean) / t_std

    X_train = np.column_stack([t_train_std, t_train_std ** 2])
    model = BayesianRidge()
    model.fit(X_train, y_train)
    X_pred = np.array([[t_pred_std, t_pred_std ** 2]])
    point, std = model.predict(X_pred, return_std=True)
    return point[0], point[0] - Z_80 * std[0], point[0] + Z_80 * std[0]


def fit_predict_xgboost(y_train, t_train, t_pred):
    if len(y_train) < 5:
        return np.nan, np.nan, np.nan
    lag1 = y_train[:-1]
    lag2_padded = np.concatenate([[y_train[0]], y_train[:-2]]) if len(y_train) > 2 else np.zeros(len(lag1))
    X_train = np.column_stack([t_train[1:], lag1, lag2_padded[:len(lag1)]])
    y_target = y_train[1:]

    model = xgb.XGBRegressor(n_estimators=50, max_depth=2, learning_rate=0.1)
    model.fit(X_train, y_target)

    X_pred = np.array([[t_pred, y_train[-1], y_train[-2] if len(y_train) > 1 else y_train[-1]]])
    point = model.predict(X_pred)[0]

    # Approximate PI via bootstrap of in-sample residuals (XGBoost gives no native uncertainty)
    resid = y_target - model.predict(X_train)
    sigma = np.std(resid) if len(resid) > 1 else 0.05
    return point, point - Z_80 * sigma, point + Z_80 * sigma


METHODS = {
    "naive": fit_predict_naive,
    "ets": fit_predict_ets,
    "arima": fit_predict_arima,
    "bayesian": fit_predict_bayesian,
    "xgboost": fit_predict_xgboost,
}


def walk_forward(country_df: pd.DataFrame, min_train: int = MIN_TRAIN) -> pd.DataFrame:
    df = country_df.dropna(subset=["export_entropy"]).sort_values("year").reset_index(drop=True)
    y_all = df["export_entropy"].values
    t_all = df["year"].values.astype(float)

    results = []
    for i in range(min_train, len(df)):
        y_train, t_train = y_all[:i], t_all[:i]
        y_true, t_pred = y_all[i], t_all[i]

        for method_name, fn in METHODS.items():
            try:
                point, lo, hi = fn(y_train, t_train, t_pred)
            except Exception as e:
                point, lo, hi = np.nan, np.nan, np.nan

            results.append({
                "year": int(t_pred),
                "method": method_name,
                "y_true": y_true,
                "y_pred": point,
                "pi_lo": lo,
                "pi_hi": hi,
                "abs_error": abs(y_true - point) if not np.isnan(point) else np.nan,
                "in_interval": (lo <= y_true <= hi) if not np.isnan(lo) else np.nan,
            })

    return pd.DataFrame(results)


def summarize(wf_results: pd.DataFrame) -> pd.DataFrame:
    summary = wf_results.groupby("method").agg(
        n_folds=("abs_error", "count"),
        mae=("abs_error", "mean"),
        pi_coverage_80=("in_interval", "mean"),
    ).round(4)
    return summary.sort_values("mae")


def run_all_countries(metrics: pd.DataFrame, min_train: int = MIN_TRAIN) -> pd.DataFrame:
    all_results = []
    for country, df_c in metrics.groupby("country"):
        n_valid = df_c["export_entropy"].notna().sum()
        if n_valid < min_train + 3:
            print(f"{country}: only {n_valid} valid observations, skipping (minimum {min_train + 3})")
            continue
        wf = walk_forward(df_c, min_train=min_train)
        wf["country"] = country
        all_results.append(wf)
    return pd.concat(all_results, ignore_index=True)


if __name__ == "__main__":
    metrics = pd.read_csv(METRICS_PATH)

    print("Running walk-forward for the 10 countries...\n")
    wf_all = run_all_countries(metrics)

    out_path = os.path.join(PROCESSED_DIR, f"forecast_walkforward_results{OUTPUT_SUFFIX}.csv")
    wf_all.to_csv(out_path, index=False)
    print(f"\nSaved: {out_path} ({len(wf_all)} rows)")

    print("\nGlobal summary by method (all countries pooled):")
    global_summary = wf_all.groupby("method").agg(
        n_folds=("abs_error", "count"),
        mae=("abs_error", "mean"),
        pi_coverage_80=("in_interval", "mean"),
    ).round(4).sort_values("mae")
    print(global_summary)

    print("\nLowest-MAE method by country:")
    best_by_country = wf_all.groupby(["country", "method"])["abs_error"].mean().reset_index()
    winner = best_by_country.loc[best_by_country.groupby("country")["abs_error"].idxmin()]
    print(winner[["country", "method", "abs_error"]].sort_values("country").to_string(index=False))
