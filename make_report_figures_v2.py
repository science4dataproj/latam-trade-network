import os
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams.update({"font.size": 10, "figure.dpi": 150})

PROCESSED = os.path.join(os.path.dirname(__file__), "data", "processed")
FIGDIR = os.path.join(os.path.dirname(__file__), "reports", "v2", "figures")
os.makedirs(FIGDIR, exist_ok=True)

COUNTRY_NAMES = {"MEX":"México","BRA":"Brasil","ARG":"Argentina","COL":"Colombia","PER":"Perú",
                 "ECU":"Ecuador","BOL":"Bolivia","HND":"Honduras","GTM":"Guatemala","CHL":"Chile"}

comp = pd.read_csv(os.path.join(PROCESSED, "entropy_regional_vs_global.csv"))
breaks_g = pd.read_csv(os.path.join(PROCESSED, "structural_breaks_by_country_global.csv"))
dash = pd.read_csv(os.path.join(PROCESSED, "risk_dashboard_final.csv"))

# --- Figura A: entropía regional vs. global, 2024 ---
latest = comp.sort_values("year").groupby("country").tail(1).sort_values("export_entropy_global")
fig, ax = plt.subplots(figsize=(8.5, 5))
y = range(len(latest))
ax.barh([i - 0.2 for i in y], latest["export_entropy_regional"], height=0.4, label="Regional (solo LatAm)", color="#7fb3d5")
ax.barh([i + 0.2 for i in y], latest["export_entropy_global"], height=0.4, label="Global (+ socios extra-regionales)", color="#d35400")
ax.set_yticks(list(y))
ax.set_yticklabels([COUNTRY_NAMES[c] for c in latest["country"]])
ax.set_xlabel("Entropía de diversificación de exportaciones (2024)")
ax.set_title("Entropía regional vs. global: el punto ciego de México")
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(FIGDIR, "figA_regional_vs_global.png"))
plt.close(fig)

# --- Figura B: sup-F global con significancia ---
alpha_bonferroni = 0.05 / len(breaks_g)  # corrección por 10 tests independientes
breaks_g["significant_bonferroni_p005"] = breaks_g["bootstrap_pvalue"] < alpha_bonferroni

bs = breaks_g.sort_values("sup_f_stat")
colors = ["#2ca02c" if sig else "#999999" for sig in bs["significant_bonferroni_p005"]]
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.barh([COUNTRY_NAMES[c] for c in bs["country"]], bs["sup_f_stat"], color=colors)
ax.set_xlabel("Estadístico sup-F (Quandt-Andrews)")
ax.set_title("Quiebres estructurales, entropía global\n(verde = significativo bajo Bonferroni, p<0.005)")
for i, (f, yr) in enumerate(zip(bs["sup_f_stat"], bs["candidate_break_year"])):
    ax.text(f + 1, i, f"año: {int(yr)}", va="center", fontsize=7, color="dimgray")
fig.tight_layout()
fig.savefig(os.path.join(FIGDIR, "figB_structural_breaks_global.png"))
plt.close(fig)

# --- Figura C: dashboard de dos ejes, con etiquetas de país ---
fig, ax = plt.subplots(figsize=(7.5, 6))
colors_tier = {"Alto": "#c0392b", "Moderado": "#e67e22", "Bajo": "#27ae60"}
for _, row in dash.iterrows():
    ax.scatter(row["top_partner_share"] * 100, row["p_alert"] * 100,
               color=colors_tier[row["riesgo_cronico"]], s=90, zorder=3)
    ax.annotate(row["nombre"], (row["top_partner_share"] * 100, row["p_alert"] * 100),
                textcoords="offset points", xytext=(6, 4), fontsize=8)
ax.axhline(30, color="gray", linestyle="--", linewidth=0.8)
ax.axvline(50, color="gray", linestyle="--", linewidth=0.8)
ax.set_xlabel("Riesgo crónico: % export. al socio dominante")
ax.set_ylabel("P(alerta) por cambio reciente (%)")
ax.set_title("Dashboard de riesgo combinado (2024)\nrojo=crónico alto, naranja=moderado, verde=bajo")
fig.tight_layout()
fig.savefig(os.path.join(FIGDIR, "figC_dashboard_final.png"))
plt.close(fig)

print("Figuras v2 generadas:", os.listdir(FIGDIR))
