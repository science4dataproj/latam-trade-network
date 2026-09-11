🇬🇧 English | [🇪🇸 Español](CHANGELOG.es.md)

# Changelog

## v2 — Global partner universe + extended data (2026-09, complete)
It was found that entropy calculated using only the 9 LatAm partners
severely understated Mexico's real concentration (0.879 regional vs. 0.171
with global partners — 92.6% of its exports go to the US, invisible in
v1). The partner universe was expanded to the US, China, Germany, Japan,
and South Korea, keeping the same 10 countries as reporters. The entire
pipeline (structural breaks, forecasting, alerts) was re-run with the
corrected metric, and a second indicator was added (chronic risk vs.
recent-change risk) after finding that Mexico showed 0% alert probability
despite having the highest risk level — a finding that exposed the
difference between "absolute concentration level" and "change relative to
one's own history."
Data extended from 2000-2024 to 2000-2025 (Honduras and Peru still without
2025 published). New finding from this update: Colombia shows a
structural break in 2022, coinciding with the change in government —
documented as a signal to monitor, not as a causal conclusion.
See `reports/informe_v2_continuacion.pdf` for the full detail of this
stage, and `reports/informe_completo.pdf` for v1's base methodology.
Tag: `v2-global-partners`.

## v1 — Regional LatAm network (2026-09)
Initial version: 10 LatAm countries, diversification entropy calculated
only among them, structural breaks (sup-F + bootstrap + Bonferroni),
compared forecasting (naive/ETS/ARIMA/bayesian/XGBoost) under
walk-forward validation, and translation to alert probability via the
forecast's predictive distribution. Tag: `v1-regional-only`.
