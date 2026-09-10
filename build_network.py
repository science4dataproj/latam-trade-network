"""
Construcción de la red de comercio LatAm (pesada, dirigida, por año) y
cálculo de métricas de diversificación (entropía de Shannon) por país.

Definiciones:
    - Para cada año, se construye un grafo dirigido con los 10 países como
      nodos y el valor de exportación bilateral (USD) como peso del edge.
    - Como los 10 países son simultáneamente reporters, el edge list cubre
      AMBAS direcciones entre cada par (A exporta a B y B exporta a A quedan
      cada uno registrado por su propio reporte de exportación) — no hay que
      inferir importaciones, ya están ahí como exportaciones del otro país.

    - export_entropy(país, año): entropía de Shannon de la distribución de
      DESTINOS de las exportaciones de ese país dentro de los otros 9.
      Baja entropía = las exportaciones del país se concentran en pocos
      destinos (mayor riesgo de concentración). Se normaliza dividiendo
      entre log(9) para que el rango sea [0, 1] independiente del número
      de socios activos ese año.

    - import_entropy(país, año): mismo cálculo pero sobre el ORIGEN de lo
      que ese país importa desde los otros 9 (es decir, tomando los edges
      donde ese país es el importer).

    - weighted_out_strength / weighted_in_strength: suma total de USD
      exportados/importados hacia/desde los otros 9, por año.
"""

import os
import numpy as np
import pandas as pd
import networkx as nx

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "data", "processed")
EDGES_PATH = os.path.join(PROCESSED_DIR, "trade_edges_latam.csv")

COUNTRIES = {"MEX", "BRA", "ARG", "COL", "PER", "ECU", "BOL", "HND", "GTM", "CHL"}
MAX_ENTROPY = np.log(len(COUNTRIES) - 1)  # log(9), máxima diversificación posible


def shannon_entropy(weights: np.ndarray) -> float:
    """Entropía de Shannon normalizada [0,1] de un vector de pesos no negativos."""
    weights = weights[weights > 0]
    if len(weights) == 0:
        return np.nan
    p = weights / weights.sum()
    h = -np.sum(p * np.log(p))
    return h / MAX_ENTROPY


def build_year_graph(df_year: pd.DataFrame) -> nx.DiGraph:
    G = nx.DiGraph()
    G.add_nodes_from(COUNTRIES)
    for _, row in df_year.iterrows():
        G.add_edge(row["exporter"], row["importer"], weight=row["value_usd"])
    return G


def compute_metrics(edges: pd.DataFrame) -> pd.DataFrame:
    records = []
    for year, df_year in edges.groupby("year"):
        G = build_year_graph(df_year)

        for country in COUNTRIES:
            # Exportaciones: edges saliendo de este país
            out_weights = df_year.loc[df_year["exporter"] == country, "value_usd"].values
            # Importaciones: edges llegando a este país
            in_weights = df_year.loc[df_year["importer"] == country, "value_usd"].values

            records.append({
                "country": country,
                "year": year,
                "export_entropy": shannon_entropy(out_weights),
                "import_entropy": shannon_entropy(in_weights),
                "n_export_partners": (out_weights > 0).sum(),
                "n_import_partners": (in_weights > 0).sum(),
                "total_exports_usd": out_weights.sum(),
                "total_imports_usd": in_weights.sum(),
                "weighted_out_degree": G.out_degree(country, weight="weight"),
                "weighted_in_degree": G.in_degree(country, weight="weight"),
            })

    return pd.DataFrame(records).sort_values(["country", "year"]).reset_index(drop=True)


def main():
    edges = pd.read_csv(EDGES_PATH)
    metrics = compute_metrics(edges)

    out_path = os.path.join(PROCESSED_DIR, "network_metrics_by_country_year.csv")
    metrics.to_csv(out_path, index=False)
    print(f"Guardado: {out_path} ({len(metrics)} filas)")

    print("\nResumen de export_entropy (diversificación de destinos) por país, promedio 2000-2024:")
    print(metrics.groupby("country")["export_entropy"].mean().sort_values())

    print("\nCobertura de filas por país (debería ser 25, o 22 para Honduras):")
    print(metrics.groupby("country").size())


if __name__ == "__main__":
    main()
