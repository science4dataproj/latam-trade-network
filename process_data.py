"""
Procesamiento de datos crudos de UN Comtrade -> edge list bilateral limpio
para la red de comercio de América Latina.

Correcciones aplicadas sobre el dato crudo (documentadas, no silenciosas):
    1. Filtro motCode == 0 ("TOTAL MOT"): varios países reportan el comercio
       desglosado por modo de transporte (aéreo, marítimo, terrestre, etc.)
       ADEMÁS de una fila con el total ya agregado. Sumar todo sin filtrar
       duplica el valor. Nos quedamos solo con la fila ya agregada.
    2. Filtro partner2Code == 0 ("World"): de forma análoga al punto anterior,
       varios países también desglosan por "partner2" (socio consignatario /
       destino final) además de reportar el total. Mismo problema de doble
       conteo si no se filtra, misma solución: quedarnos solo con el total.
    3. Filtro customsCode == 'C00' ("TOTAL CPC"): tercer nivel de desglose,
       esta vez por régimen aduanero (exportación directa vs. otros regímenes
       como reexportación o zonas francas). Mismo patrón, misma solución.
    4. Filtro partnerCode != 0: se excluye la fila "World" (agregado global),
       nos interesa solo el desglose bilateral.
    5. Filtro de partner a los 10 países de la lista: cada reporter exportó
       a ~100-400 socios en el mundo; nos quedamos solo con los otros 9
       países de LatAm de nuestra lista.
    6. Fuente de valor: SIEMPRE el lado exportador (flowCode='X' del reporter).
       No se reconcilia con lo que el partner reportó como importación —
       esto es una decisión de diseño documentada, no un descuido
       (ver README, sección de limitaciones).

Huecos de cobertura conocidos (no se imputan, quedan como ausencia real):
    - Honduras: sin datos en 2008, 2013, 2022.
"""

import glob
import os
import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__),"data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Los 10 países del estudio (Cuba y Venezuela excluidos por cobertura)
LATAM_ISO = {"MEX", "BRA", "ARG", "COL", "PER", "ECU", "BOL", "HND", "GTM", "CHL"}


def load_and_clean(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath, low_memory=False)

    before = len(df)

    # 1. Solo el total agregado por modo de transporte
    df = df[df["motCode"] == 0]

    # 2. Solo el total agregado por partner2 (evita doble conteo por
    #    desglose de "socio consignatario / destino final")
    df = df[df["partner2Code"] == 0]

    # 3. Solo el total agregado por régimen aduanero
    df = df[df["customsCode"] == "C00"]

    # 4. Excluir la fila "World"
    df = df[df["partnerCode"] != 0]

    # 4. Solo partners dentro de nuestra lista de 10 países
    df = df[df["partnerISO"].isin(LATAM_ISO)]

    after = len(df)
    reporter = df["reporterISO"].iloc[0] if len(df) > 0 else "UNKNOWN"
    print(f"{filepath}: {before} filas crudas -> {after} filas limpias (reporter={reporter})")

    # Verificación de duplicados residuales: no debería haber más de una fila
    # por (reporterISO, refYear, partnerISO) después de los filtros anteriores
    dup_check = df.groupby(["reporterISO", "refYear", "partnerISO"]).size()
    n_dups = (dup_check > 1).sum()
    if n_dups > 0:
        print(f"  ADVERTENCIA: {n_dups} combinaciones reporter-año-partner con duplicados residuales")

    return df[["reporterISO", "partnerISO", "refYear", "primaryValue"]].rename(
        columns={
            "reporterISO": "exporter",
            "partnerISO": "importer",
            "refYear": "year",
            "primaryValue": "value_usd",
        }
    )


def main():
    raw_files = sorted(glob.glob(os.path.join(RAW_DIR, "*_exports_raw.csv")))
    if not raw_files:
        raise RuntimeError(f"No se encontraron CSVs en {RAW_DIR}")

    all_edges = [load_and_clean(f) for f in raw_files]
    edges = pd.concat(all_edges, ignore_index=True)

    # Reportar cobertura final: cuántos años tiene cada país reportando
    # como exportador dentro de nuestra red de 10
    coverage = edges.groupby("exporter")["year"].nunique().sort_values()
    print("\nCobertura final (años con al menos un edge reportado):")
    print(coverage)

    out_path = os.path.join(PROCESSED_DIR, "trade_edges_latam.csv")
    edges.to_csv(out_path, index=False)
    print(f"\nGuardado: {out_path} ({len(edges)} edges totales)")


if __name__ == "__main__":
    main()
