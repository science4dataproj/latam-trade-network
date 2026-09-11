"""
Construction of the LatAm trade network (weighted, directed, by year) and
calculation of diversification metrics (Shannon entropy) by country.

Definitions:
    - For each year, a directed graph is built with the 10 countries as
      nodes and bilateral export value (USD) as edge weight.
    - Since all 10 countries are simultaneously reporters, the edge list
      covers BOTH directions for each pair (A exports to B and B exports to
      A are each recorded from their own export report) — imports do not
      need to be inferred, they are already there as the other country's
      exports.

    - export_entropy(country, year): Shannon entropy of the DESTINATION
      distribution of that country's exports among the other 9. Low
      entropy = the country's exports are concentrated in few destinations
      (higher concentration risk). Normalized by dividing by log(9) so the
      range is [0, 1] regardless of how many partners were active that
      year.

    - import_entropy(country, year): same calculation but over the ORIGIN
      of what that country imports from the other 9 (i.e., taking the
      edges where that country is the importer).

    - weighted_out_strength / weighted_in_strength: total USD
      exported/imported to/from the other 9, per year.
"""

import os
import numpy as np
import pandas as pd
import networkx as nx

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
EDGES_PATH = os.path.join(PROCESSED_DIR, "trade_edges_latam.csv")

COUNTRIES = {"MEX", "BRA", "ARG", "COL", "PER", "ECU", "BOL", "HND", "GTM", "CHL"}
MAX_ENTROPY = np.log(len(COUNTRIES) - 1)  # log(9), maximum possible diversification


def shannon_entropy(weights: np.ndarray) -> float:
    """Normalized [0,1] Shannon entropy of a vector of non-negative weights."""
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
            # Exports: edges leaving this country
            out_weights = df_year.loc[df_year["exporter"] == country, "value_usd"].values
            # Imports: edges arriving at this country
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
    print(f"Saved: {out_path} ({len(metrics)} rows)")

    print("\nSummary of export_entropy (destination diversification) by country, 2000-2024 average:")
    print(metrics.groupby("country")["export_entropy"].mean().sort_values())

    print("\nRow coverage by country (should be 25, or 22 for Honduras):")
    print(metrics.groupby("country").size())


if __name__ == "__main__":
    main()
