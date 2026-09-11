"""
Extracción de datos de exportaciones bilaterales de UN Comtrade
para la red de comercio de América Latina.

REQUIERE:
    pip install comtradeapicall pandas

REQUIERE API KEY GRATUITA:
    1. Registrarse en https://comtradeplus.un.org (gratis)
    2. Generar una subscription key en el portal de desarrollador
    3. Exportarla como variable de entorno:
       export UN_COMTRADE_KEY="tu_key_aqui"

DISEÑO DE LA EXTRACCIÓN:
    - Para cada país REPORTER de la lista, se piden sus EXPORTACIONES (flowCode='X')
      hacia TODOS los socios (partnerCode no se restringe aquí; se filtra a los
      10 países de interés en el paso de procesamiento). Esto resuelve el problema
      de mirror statistics: solo usamos el lado "exportador" como fuente de verdad,
      nunca mezclamos con lo que el partner reportó como importación.
    - Se pide freqCode='A' (anual) primero, porque la cobertura mensual varía mucho
      por país y para varios de estos 10 puede no existir. Si al validar ves que
      varios países sí tienen datos mensuales completos, se puede correr una segunda
      pasada con freqCode='M'.
    - cmdCode='TOTAL' (todos los productos, sin desagregar) para la red general.
    - cada llamada se guarda cruda en data/raw/ sin transformar — cualquier limpieza
      o filtrado va en un script de procesamiento separado, no aquí.
"""
"""
Actualización incremental de datos: agrega años nuevos (2025, 2026) a los
CSVs crudos existentes SIN volver a pedir 2000-2024 (ya los tenemos).

Aviso de expectativas: el comercio internacional se publica con rezago.
2025 puede venir incompleto o sujeto a revisión; 2026, a mitad de año, muy
probablemente regrese vacío para varios o todos los países -- eso no es un
error del script, es el rezago normal de publicación de Comtrade. Se
reporta explícitamente qué llegó y qué no, no se asume nada.
"""

import os
import time
import pandas as pd
import comtradeapicall

#SUBSCRIPTION_KEY = os.environ.get("UN_COMTRADE_KEY")
SUBSCRIPTION_KEY = "98cc6300b3bc4130a854fb992a7d5b69"
if not SUBSCRIPTION_KEY:
    raise RuntimeError("Falta la variable de entorno UN_COMTRADE_KEY.")

REPORTERS = {
    "mexico": 484, "brazil": 76, "argentina": 32, "colombia": 170, "peru": 604,
    "ecuador": 218, "bolivia": 68, "honduras": 340, "guatemala": 320, "chile": 152,
}

NEW_YEARS = [2025, 2026]
RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")


def fetch_reporter_year(reporter_code: int, year: int) -> pd.DataFrame:
    return comtradeapicall.getFinalData(
        SUBSCRIPTION_KEY, typeCode="C", freqCode="A", clCode="HS", period=str(year),
        reporterCode=str(reporter_code), cmdCode="TOTAL", flowCode="X",
        partnerCode=None, partner2Code=None, customsCode=None, motCode=None,
        maxRecords=2500, format_output="JSON", countOnly=None, includeDesc=True,
    )


def main():
    summary = []
    for name, code in REPORTERS.items():
        existing_path = os.path.join(RAW_DIR, f"{name}_exports_raw.csv")
        if not os.path.exists(existing_path):
            print(f"ADVERTENCIA: no existe {existing_path}, se omite {name}")
            continue

        existing = pd.read_csv(existing_path, low_memory=False)
        already_have_years = set(existing["refYear"].unique())

        new_frames = []
        for year in NEW_YEARS:
            if year in already_have_years:
                continue
            try:
                df = fetch_reporter_year(code, year)
                n_rows = len(df) if df is not None else 0
                summary.append({"country": name, "year": year, "rows": n_rows})
                if df is not None and n_rows > 0:
                    new_frames.append(df)
                print(f"{name} {year}: {n_rows} filas")
            except Exception as e:
                summary.append({"country": name, "year": year, "rows": 0, "error": str(e)})
                print(f"{name} {year}: ERROR - {e}")
            time.sleep(1)

        if new_frames:
            combined = pd.concat([existing] + new_frames, ignore_index=True)
            combined.to_csv(existing_path, index=False)
            print(f"  Actualizado: {existing_path} ({len(combined)} filas totales)")
        else:
            print(f"  Sin años nuevos con datos para {name}, archivo sin cambios")

    print("\nResumen de disponibilidad de años nuevos:")
    summary_df = pd.DataFrame(summary)
    print(summary_df.to_string(index=False) if len(summary_df) else "Nada que reportar")


if __name__ == "__main__":
    main()
