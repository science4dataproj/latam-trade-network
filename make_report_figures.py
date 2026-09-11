import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams.update({"font.size": 10, "figure.dpi": 150})

PROCESSED = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
FIGDIR = os.path.join(os.path.dirname(__file__), "..", "reports", "figures")
os.makedirs(FIGDIR, exist_ok=True)

metrics = pd.read_csv(os.path.join(PROCESSED, "network_metrics_by_country_year.csv"))
breaks = pd.read_csv(os.path.join(PROCESSED, "structural_breaks_by_country.csv"))
forecast = pd.read_csv(os.path.join(PROCESSED, "forecast_walkforward_results.csv"))
alerts = pd.read_csv(os.path.join(PROCESSED, "risk_alert_from_forecast.csv"))

COUNTRY_NAMES = {"MEX":"México","BRA":"Brasil","ARG":"Argentina","COL":"Colombia","PER":"Perú",
                 "ECU":"Ecuador","BOL":"Bolivia","HND":"Honduras","GTM":"Guatemala","CHL":"Chile"}

# --- Figure 1: entropy by country, 2000-2024, with real-event annotations (plotted text stays in Spanish for the Spanish PDF) ---
fig, ax = plt.subplots(figsize=(9, 5.5))
for country, df_c in metrics.groupby("country"):
    df_c = df_c.sort_values("year")
    ax.plot(df_c["year"], df_c["export_entropy"], marker="o", markersize=2.5,
            linewidth=1.3, label=COUNTRY_NAMES[country])

ax.axvspan(2001, 2002, color="gray", alpha=0.15)
ax.annotate("Crisis Argentina\n(2001-2002)", xy=(2001.5, 0.15), fontsize=8, ha="center", color="dimgray")
ax.axvspan(2007.5, 2009.5, color="gray", alpha=0.15)
ax.annotate("Crisis financiera\nglobal (2008)", xy=(2008.5, 0.15), fontsize=8, ha="center", color="dimgray")

ax.set_xlabel("Año")
ax.set_ylabel("Entropía normalizada de exportaciones\n(0 = concentrado, 1 = diversificado)")
ax.set_title("Diversificación de destinos de exportación por país, 2000-2024")
ax.legend(loc="lower left", fontsize=7, ncol=2)
ax.set_ylim(0, 1)
fig.tight_layout()
fig.savefig(os.path.join(FIGDIR, "fig1_entropy_timeseries.png"))
plt.close(fig)

# --- Figure 2: sup-F stat by country with significance threshold (plotted text stays in Spanish for the Spanish PDF) ---
breaks_sorted = breaks.sort_values("sup_f_stat", ascending=True)
colors = ["#2ca02c" if sig else "#999999" for sig in breaks_sorted["significant_bonferroni_p005"]]
fig, ax = plt.subplots(figsize=(8, 4.5))
bars = ax.barh(breaks_sorted["country"].map(COUNTRY_NAMES), breaks_sorted["sup_f_stat"], color=colors)
ax.set_xlabel("Estadístico sup-F (Quandt-Andrews)")
ax.set_title("Evidencia de quiebre estructural por país\n(verde = significativo bajo Bonferroni, p<0.005)")
for i, (f, yr) in enumerate(zip(breaks_sorted["sup_f_stat"], breaks_sorted["candidate_break_year"])):
    ax.text(f + 1, i, f"año candidato: {int(yr)}", va="center", fontsize=7, color="dimgray")
fig.tight_layout()
fig.savefig(os.path.join(FIGDIR, "fig2_structural_breaks.png"))
plt.close(fig)

# --- Figure 3: walk-forward forecast, Colombia, naive vs. bayesian (best and worst method) (plotted text stays in Spanish for the Spanish PDF) ---
col = forecast[(forecast.country == "COL") & (forecast.method.isin(["naive", "bayesian"]))]
actual = metrics[(metrics.country == "COL")].sort_values("year")
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(actual["year"], actual["export_entropy"], color="black", linewidth=1.5, label="Valor real")
for method, style in [("naive", "-o"), ("bayesian", "-s")]:
    sub = col[col.method == method].sort_values("year")
    ax.plot(sub["year"], sub["y_pred"], style, markersize=4, label=f"Forecast ({method})")
    ax.fill_between(sub["year"], sub["pi_lo"], sub["pi_hi"], alpha=0.15)
ax.set_xlabel("Año")
ax.set_ylabel("Entropía de exportaciones")
ax.set_title("Walk-forward validation, Colombia: mejor método (naive) vs. peor (bayesiano)")
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(FIGDIR, "fig3_forecast_colombia.png"))
plt.close(fig)

# --- Figure 4: current risk ranking (2024) (plotted text stays in Spanish for the Spanish PDF) ---
latest = alerts.sort_values("year").groupby("country").tail(1).sort_values("p_alert", ascending=True)
colors4 = ["#d62728" if p > 0.3 else ("#ff7f0e" if p > 0.1 else "#2ca02c") for p in latest["p_alert"]]
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.barh(latest["country"].map(COUNTRY_NAMES), latest["p_alert"] * 100, color=colors4)
ax.set_xlabel("Probabilidad de alerta, 2024 (%)")
ax.set_title("Ranking de riesgo de concentración comercial, 2024\n(rojo >30%, naranja >10%, verde <10%)")
fig.tight_layout()
fig.savefig(os.path.join(FIGDIR, "fig4_risk_ranking_2024.png"))
plt.close(fig)

print("Figures generated in", FIGDIR)  # note: chart text itself stays in Spanish, feeds the Spanish PDF
print(os.listdir(FIGDIR))
