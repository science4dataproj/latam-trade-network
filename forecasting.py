"""
Forecasting probabilístico de export_entropy con walk-forward validation.

Métodos comparados:
    - naive: último valor observado (baseline obligatorio)
    - ets: Holt linear trend (statsmodels ExponentialSmoothing)
    - arima: SARIMAX con orden seleccionado por AIC sobre una grilla chica
    - bayesian: Bayesian Ridge regression (sklearn) sobre [año, año^2] —
      Bayesiano genuino (prior gaussiano sobre coeficientes, no solo el
      nombre): da media posterior + desviación estándar predictiva, de ahí
      el intervalo.
    - xgboost: XGBoost sobre features de lags (lag1, lag2) + año. Con folds
      iniciales de solo 12-15 puntos de entrenamiento, se espera que compita
      mal contra los baselines simples — eso se reporta tal cual, no se
      esconde ni se fuerza a que "gane".

Validación: walk-forward de ventana expansiva. min_train años de
entrenamiento inicial, luego se pronostica 1 año adelante, se agrega el año
real, se repite. Métrica: MAE y cobertura del intervalo de predicción al 80%
(qué % de las veces el valor real cayó dentro del intervalo — el chequeo de
calibración que separa un intervalo real de un adorno).
"""

import os
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.linear_model import BayesianRidge
import xgboost as xgb

warnings.filterwarnings("ignore")

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
METRICS_PATH = os.path.join(PROCESSED_DIR, "network_metrics_by_country_year.csv")

MIN_TRAIN = 15
Z_80 = 1.2816  # z-score para intervalo de 80%


def fit_predict_naive(y_train, t_train, t_pred):
    point = y_train[-1]
    # PI basado en la desviación histórica de cambios año-a-año (naive walk)
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
    # Estandarizar año (centrar y escalar) antes de construir features —
    # sin esto, [t, t^2] con años crudos (~2015, ~4,060,225) mal condiciona
    # la matriz de precisión de BayesianRidge y produce intervalos absurdos.
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

    # PI aproximado por bootstrap de residuales in-sample (XGBoost no da incertidumbre nativa)
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
            print(f"{country}: solo {n_valid} observaciones válidas, se omite (mínimo {min_train + 3})")
            continue
        wf = walk_forward(df_c, min_train=min_train)
        wf["country"] = country
        all_results.append(wf)
    return pd.concat(all_results, ignore_index=True)


if __name__ == "__main__":
    metrics = pd.read_csv(METRICS_PATH)

    print("Corriendo walk-forward para los 10 países...\n")
    wf_all = run_all_countries(metrics)

    out_path = os.path.join(PROCESSED_DIR, "forecast_walkforward_results.csv")
    wf_all.to_csv(out_path, index=False)
    print(f"\nGuardado: {out_path} ({len(wf_all)} filas)")

    print("\nResumen global por método (todos los países juntos):")
    global_summary = wf_all.groupby("method").agg(
        n_folds=("abs_error", "count"),
        mae=("abs_error", "mean"),
        pi_coverage_80=("in_interval", "mean"),
    ).round(4).sort_values("mae")
    print(global_summary)

    print("\nMétodo con menor MAE por país:")
    best_by_country = wf_all.groupby(["country", "method"])["abs_error"].mean().reset_index()
    winner = best_by_country.loc[best_by_country.groupby("country")["abs_error"].idxmin()]
    print(winner[["country", "method", "abs_error"]].sort_values("country").to_string(index=False))
