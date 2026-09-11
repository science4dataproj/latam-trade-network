"""
Structural break detection in each country's export_entropy series.

Primary method: Quandt-Andrews sup-F.
    - A linear trend model (entropy ~ constant + year) is fit to the whole
      series.
    - For each candidate break year (trimming 15% at each end, Andrews'
      1993 standard rule to avoid breaks at the edges where the test loses
      power), that single model is compared against two separate trend
      models (before/after the break) via an F-test.
    - The year with the highest F-stat is the candidate structural break.
    - The asymptotic critical values of sup-F are NOT a standard F (it is a
      multiple-comparisons problem over an unknown break point). Instead of
      using Andrews' tables (which assume longer series), the p-value is
      estimated by BOOTSTRAP: simulate under the null hypothesis of "no
      break" (single trend + residuals resampled with replacement),
      recompute sup-F on each simulation, and compare the observed
      statistic against that empirical distribution.

Secondary method: CUSUM of OLS residuals (Brown-Durbin-Evans), via
statsmodels, as an independent confirmation of parameter instability.

Important methodological note (see limitations in the README): with series
of ~22-25 annual observations, the statistical power of these tests is
limited. Results are reported with that honesty, not as definitive
findings.
"""

import os
import sys
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import breaks_cusumolsresid

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
METRICS_FILENAME = sys.argv[1] if len(sys.argv) > 1 else "network_metrics_by_country_year.csv"
OUTPUT_SUFFIX = sys.argv[2] if len(sys.argv) > 2 else ""
METRICS_PATH = os.path.join(PROCESSED_DIR, METRICS_FILENAME)

TRIM = 0.15       # Andrews' (1993) standard trim at each end
N_BOOTSTRAP = 2000
MIN_OBS = 15       # minimum non-null observations required to run the test
RANDOM_SEED = 42


def sup_f_stat(y: np.ndarray, t: np.ndarray, trim: float = TRIM):
    """Compute the Quandt-Andrews sup-F and the year (index) at which it occurs."""
    n = len(y)
    lo = int(np.floor(n * trim))
    hi = int(np.ceil(n * (1 - trim)))

    X_full = sm.add_constant(t)
    model_full = sm.OLS(y, X_full).fit()
    ssr_full = model_full.ssr

    best_f, best_idx = -np.inf, None
    for i in range(lo, hi):
        # Segment 1 and 2, each with its own constant + trend
        t1, y1 = t[:i], y[:i]
        t2, y2 = t[i:], y[i:]
        if len(t1) < 3 or len(t2) < 3:
            continue
        ssr1 = sm.OLS(y1, sm.add_constant(t1)).fit().ssr
        ssr2 = sm.OLS(y2, sm.add_constant(t2)).fit().ssr
        ssr_restricted = ssr1 + ssr2

        # F-test: 2 extra parameters (constant and slope of the second segment)
        k = 2
        f_stat = ((ssr_full - ssr_restricted) / k) / (ssr_restricted / (n - 2 * k))
        if f_stat > best_f:
            best_f, best_idx = f_stat, i

    return best_f, best_idx


def bootstrap_pvalue(y: np.ndarray, t: np.ndarray, observed_f: float,
                      n_boot: int = N_BOOTSTRAP, seed: int = RANDOM_SEED) -> float:
    """Empirical p-value: under H0 (no break), how often does the simulated
    sup-F equal or exceed the observed one?"""
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
        return {"n_obs": len(df_country), "status": "insufficient observations"}

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

    out_path = os.path.join(PROCESSED_DIR, f"structural_breaks_by_country{OUTPUT_SUFFIX}.csv")
    out.to_csv(out_path)
    print(out.to_string())
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
