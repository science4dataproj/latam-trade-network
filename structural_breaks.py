"""
Detección de quiebres estructurales en las series de export_entropy por país.

Método principal: sup-F de Quandt-Andrews.
    - Se ajusta un modelo de tendencia lineal (entropía ~ constante + año) a
      toda la serie.
    - Para cada posible año de quiebre (recortando 15% en cada extremo, regla
      estándar de Andrews 1993 para evitar quiebres en los bordes donde el
      test pierde poder), se compara ese modelo único contra dos modelos de
      tendencia separados (antes/después del quiebre), vía F-test.
    - El año con el F-stat más alto es el candidato a quiebre estructural.
    - Los valores críticos asintóticos del sup-F NO son una F estándar (es
      un problema de comparaciones múltiples sobre el punto de quiebre
      desconocido). En vez de usar tablas de Andrews (que asumen series más
      largas), el p-value se estima por BOOTSTRAP: se simula bajo la
      hipótesis nula de "no hay quiebre" (tendencia única + residuales
      re-muestreados con reemplazo), se recalcula el sup-F en cada
      simulación, y se compara el estadístico observado contra esa
      distribución empírica.

Método secundario: CUSUM de residuales OLS (Brown-Durbin-Evans), vía
statsmodels, como confirmación independiente de inestabilidad de parámetros.

Nota metodológica importante (ver limitaciones en el README): con series de
~22-25 observaciones anuales, el poder estadístico de estos tests es
limitado. Se reportan los resultados con esa honestidad, no como hallazgos
definitivos.
"""

import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import breaks_cusumolsresid

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "data", "processed")
METRICS_PATH = os.path.join(PROCESSED_DIR, "network_metrics_by_country_year.csv")

TRIM = 0.15       # recorte estándar de Andrews (1993) en cada extremo
N_BOOTSTRAP = 2000
MIN_OBS = 15       # mínimo de observaciones no-nulas para correr el test
RANDOM_SEED = 42


def sup_f_stat(y: np.ndarray, t: np.ndarray, trim: float = TRIM):
    """Calcula el sup-F de Quandt-Andrews y el año (índice) donde ocurre."""
    n = len(y)
    lo = int(np.floor(n * trim))
    hi = int(np.ceil(n * (1 - trim)))

    X_full = sm.add_constant(t)
    model_full = sm.OLS(y, X_full).fit()
    ssr_full = model_full.ssr

    best_f, best_idx = -np.inf, None
    for i in range(lo, hi):
        # Segmento 1 y 2, cada uno con su propia constante + tendencia
        t1, y1 = t[:i], y[:i]
        t2, y2 = t[i:], y[i:]
        if len(t1) < 3 or len(t2) < 3:
            continue
        ssr1 = sm.OLS(y1, sm.add_constant(t1)).fit().ssr
        ssr2 = sm.OLS(y2, sm.add_constant(t2)).fit().ssr
        ssr_restricted = ssr1 + ssr2

        # F-test: 2 parámetros extra (constante y pendiente del segundo segmento)
        k = 2
        f_stat = ((ssr_full - ssr_restricted) / k) / (ssr_restricted / (n - 2 * k))
        if f_stat > best_f:
            best_f, best_idx = f_stat, i

    return best_f, best_idx


def bootstrap_pvalue(y: np.ndarray, t: np.ndarray, observed_f: float,
                      n_boot: int = N_BOOTSTRAP, seed: int = RANDOM_SEED) -> float:
    """P-value empírico: bajo H0 (sin quiebre), ¿qué tan seguido el sup-F
    simulado iguala o supera al observado?"""
    rng = np.random.default_rng(seed)
    X_full = sm.add_constant(t)
    model_full = sm.OLS(y, X_full).fit()
    resid = np.asarray(model_full.resid)
    fitted = np.asarray(model_full.fittedvalues)

    count_exceed = 0
    for _ in range(n_boot):
        sim_resid = rng.choice(resid, size=len(resid), replace=True)
        y_sim = fitted + sim_resid
        f_sim, _ = sup_f_stat(y_sim, t)
        if f_sim >= observed_f:
            count_exceed += 1

    return count_exceed / n_boot


def run_cusum(y: np.ndarray, t: np.ndarray):
    X = sm.add_constant(t)
    resid = sm.OLS(y, X).fit().resid
    try:
        stat, pval, _ = breaks_cusumolsresid(resid, ddof=2)
        return stat, pval
    except Exception as e:
        return np.nan, np.nan


def analyze_country(df_country: pd.DataFrame):
    df_country = df_country.dropna(subset=["export_entropy"]).sort_values("year")
    if len(df_country) < MIN_OBS:
        return {"n_obs": len(df_country), "status": "insuficientes observaciones"}

    y = df_country["export_entropy"].values
    t = df_country["year"].values.astype(float)

    f_obs, break_idx = sup_f_stat(y, t)
    break_year = int(t[break_idx]) if break_idx is not None else None
    p_boot = bootstrap_pvalue(y, t, f_obs)
    cusum_stat, cusum_p = run_cusum(y, t)

    return {
        "n_obs": len(df_country),
        "sup_f_stat": round(f_obs, 3),
        "candidate_break_year": break_year,
        "bootstrap_pvalue": round(p_boot, 4),
        "significant_break_p05": p_boot < 0.05,
        "cusum_stat": round(cusum_stat, 3) if not np.isnan(cusum_stat) else np.nan,
        "cusum_pvalue": round(cusum_p, 4) if not np.isnan(cusum_p) else np.nan,
    }


def main():
    metrics = pd.read_csv(METRICS_PATH)
    results = []
    for country, df_c in metrics.groupby("country"):
        res = analyze_country(df_c)
        res["country"] = country
        results.append(res)

    out = pd.DataFrame(results).set_index("country")
    cols = ["n_obs", "sup_f_stat", "candidate_break_year", "bootstrap_pvalue",
            "significant_break_p05", "cusum_stat", "cusum_pvalue"]
    out = out[[c for c in cols if c in out.columns]]

    out_path = os.path.join(PROCESSED_DIR, "structural_breaks_by_country.csv")
    out.to_csv(out_path)
    print(out.to_string())
    print(f"\nGuardado: {out_path}")


if __name__ == "__main__":
    main()
