🇬🇧 English | [🇪🇸 Español](README.es.md)

# Trade Concentration Risk in Latin America: Structural Change Detection and Forecasting

## Project Status
**Current version: v2 (complete)** — partner universe expanded to global
partners (not just LatAm), data extended through 2025. The previous
version (`v1-regional-only`, see the GitHub tag) measured diversification
only within the region, which turned out to be blind to massive
extra-regional dependencies (e.g., Mexico-US). See `CHANGELOG.md` for
details on each version and why it changed.

**Full documents:**
- `reports/informe_completo.pdf` — base methodology (v1), in Spanish.
- `reports/informe_v2_continuacion.pdf` — what was added in v2 and why, in Spanish.
- `reports/articulo_sintesis_final.pdf` / `reports/article_summary_en.pdf` — short article-style summary, in Spanish and English.

> With data through 2025, 7 of 10 countries show a statistically robust structural break. Peru is the most critical case: high chronic risk (51% of its exports go to China) and a 99.7% probability of a recent-change alert.

## The Business Problem

Which Latin American countries are entering a zone of elevated
trade-concentration risk over the next 12-24 months, and where should a
regional exporter or investor prioritize monitoring or diversification?

This matters now for two concrete reasons: (1) real, verifiable trade
friction between countries in the region coinciding with recent political
realignments (see `reports/article_summary_en.pdf`), and (2) several
countries in the region elected new governments in 2025-2026, making it
especially relevant to monitor whether trade structure is changing too.

## The Short Answer

| Country | Chronic Risk | P(alert) |
|---|---|---|
| 🔴 Peru | High (51% to China) | 99.7% |
| 🟠 Chile | Moderate | 95.9% |
| 🟠 Brazil | Moderate | 92.5% |
| 🟡 Honduras | High | 39.1% |
| 🟡 Guatemala | High | 29.0% |
| 🟢 Mexico | High (92.6% to US) | 0.03% — structural, not a new crisis |
| 🟢 Colombia, Argentina, Ecuador, Bolivia | Low-Moderate | <2% |

See `data/processed/risk_dashboard_final.csv` for full detail, and Figure
3 in `reports/informe_v2_continuacion.pdf` for the visual version.

## Data

- **Source:** UN Comtrade, exports as reported by the exporting country
  (mirror-statistics issue resolved by consistently using the exporter
  side).
- **Coverage:** annual, 2000-2025 (2025 incomplete for Honduras and Peru
  due to publication lag).
- **Countries (reporters):** Mexico, Brazil, Argentina, Colombia, Peru,
  Ecuador, Bolivia, Honduras, Guatemala, Chile (Cuba and Venezuela
  excluded due to insufficient reporting coverage).
- **Partner universe:** the 10 countries on the list + United States,
  China, Germany, Japan, South Korea (see `CHANGELOG.md`, v2).
- **Aggregation level:** TOTAL (all products, not disaggregated by HS
  code).

## Methodology (summary)

1. **Network construction** — weighted, directed graph by year, node =
   country, edge = bilateral export value.
2. **Shannon entropy** — export-destination diversification by
   country-year, normalized to [0,1].
3. **Structural break detection** — sup-F (Quandt-Andrews) with
   bootstrap-estimated p-values (2,000 simulations) + Bonferroni
   correction for multiple comparisons, plus CUSUM as a secondary check.
4. **Probabilistic forecasting** — naive, ETS, ARIMA, Bayesian
   regression, XGBoost, compared under expanding-window walk-forward
   validation. Metric: MAE + 80% prediction-interval coverage.
5. **Translation to a risk alert** — probability via the best forecast's
   predictive distribution (analogous to a Value-at-Risk calculation),
   complemented by an absolute concentration-level indicator.

Full detail on every step (including discarded methods and why) is in
`reports/informe_completo.pdf` and `reports/informe_v2_continuacion.pdf`
(Spanish) and `reports/article_summary_en.pdf` (English summary).

**Methodological note — DFA discarded:** Detrended Fluctuation Analysis
was considered as a second line of evidence for regime change, but was
discarded. DFA requires series of hundreds/thousands of points for the
scaling exponent to be stable; with ~22-26 annual observations per
country, the log-log fit does not have enough window scales to be
reliable.

## Key Results

- **The regional blind spot:** Mexico appeared as the most diversified
  country under a region-only metric (0.86) and turns out to be the most
  concentrated under the global metric (0.16, 92.6% to the US).
- **7 of 10 countries** show a robust structural break under Bonferroni
  correction. A cluster in 2007-2009 (global financial crisis) + one
  recent case (Colombia, 2022) worth watching, not confirmed as causal.
- **Naive wins the forecasting comparison** in most countries — trade
  entropy is near-persistent, and no sophisticated method should beat
  persistence when there is no strong trend.
- **XGBoost has only ~29.5% interval coverage** (target: 80%) — not
  recommended for quantifying uncertainty in this project despite a
  competitive MAE.

## Data Cleaning: Findings and Decisions

UN Comtrade returns trade broken down simultaneously along three
additional dimensions, each with its own "total" row plus breakdown rows
that sum to that total. Without filtering all three, the trade value gets
double-counted:
1. Mode of transport (`motCode`): total vs. air/sea/land/etc.
2. Partner2 (`partner2Code`): total vs. breakdown by consignee/final
   destination.
3. Customs regime (`customsCode`): total (`C00`) vs. breakdown by regime
   type.

The total row was consistently filtered for all three dimensions across
the 10 countries. Validated: zero residual duplicates by (exporter, year,
partner) in the final dataset.

## Limitations

- Small N in annual series (~22-26 points per country) — limits the
  power of ML-based forecasting; validation rigor is prioritized over
  model complexity.
- Mirror statistics: only one reporting direction (exporter) is used, no
  full bilateral reconciliation.
- Honduras: no data in 2008, 2013, 2022, 2025 — genuine absence, not
  imputed. Peru also has no 2025 data published yet.
- Cuba/Venezuela excluded due to insufficient reporting coverage, not
  "zero risk."
- Statistically significant structural breaks do not imply causality
  about their origin (see the confounders discussion in
  `reports/informe_v2_continuacion.pdf`).

## References

- Alves, L.G.A., Mangioni, G., Rodrigues, F.A., Panzarasa, P., & Moreno,
  Y. (2018). Unfolding the Complexity of the Global Value Chain: Strength
  and Entropy in the Single-Layer, Multiplex, and Multi-Layer
  International Trade Networks. *Entropy*, 20(12), 909.
- Andrews, D.W.K. (1993). Tests for Parameter Instability and Structural
  Change with Unknown Change Point. *Econometrica*, 61(4), 821-856.
- UN Comtrade Database, comtradeplus.un.org.

## How to Reproduce

```bash
pip install -r requirements.txt
export UN_COMTRADE_KEY="your_key_here"   # free at comtradeplus.un.org

python src/fetch_data.py               # initial extraction, 2000-2024
python src/fetch_data_update.py        # incremental, new years
python src/process_data.py             # regional edge list
python src/build_network.py            # regional entropy
python src/build_network_global.py     # entropy + global partner universe
python src/structural_breaks.py network_metrics_global.csv _global
python src/forecasting.py network_metrics_global.csv _global
python src/risk_alert.py network_metrics_global.csv forecast_walkforward_results_global.csv _global
python src/risk_dashboard_final.py
python src/make_report_figures_v2.py   # v2 report figures
```
