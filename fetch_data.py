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

import os
import time
import pandas as pd
import comtradeapicall
import urllib3

SUBSCRIPTION_KEY = os.environ.get("UN_COMTRADE_KEY")
if not SUBSCRIPTION_KEY:
    raise RuntimeError(
        "Falta la variable de entorno UN_COMTRADE_KEY. "
        "Ver instrucciones en el docstring de este archivo."
    )

# Códigos M49 de los 10 países (Cuba y Venezuela excluidos por cobertura)
REPORTERS = {
    "Mexico": 484,
    "Brazil": 76,
    "Argentina": 32,
    "Colombia": 170,
    "Peru": 604,
    "Ecuador": 218,
    "Bolivia": 68,
    "Honduras": 340,
    "Guatemala": 320,
    "Chile": 152,
}

START_YEAR = 2000
END_YEAR = 2024

RAW_DIR = os.path.join(os.path.dirname(__file__),"data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)


def fetch_reporter_year(reporter_name: str, reporter_code: int, year: int) -> pd.DataFrame:
    """Trae exportaciones TOTAL de un reporter hacia todos los partners, para un año."""
    df = comtradeapicall.getFinalData(
        SUBSCRIPTION_KEY,
        typeCode="C",          # comercio de bienes (goods)
        freqCode="A",          # anual
        clCode="HS",
        period=str(year),
        reporterCode=str(reporter_code),
        cmdCode="TOTAL",
        flowCode="X",          # exportaciones
        partnerCode=None,      # todos los partners; se filtra después
        partner2Code=None,
        customsCode=None,
        motCode=None,
        maxRecords=2500,
        format_output="JSON",
        countOnly=None,
        includeDesc=True,
    )
    return df


def main():
    for name, code in REPORTERS.items():
        frames = []
        for year in range(START_YEAR, END_YEAR + 1):
            try:
                df = fetch_reporter_year(name, code, year)
                if df is not None and len(df) > 0:
                    frames.append(df)
                    print(f"{name} {year}: {len(df)} filas")
                else:
                    print(f"{name} {year}: sin datos")
            except Exception as e:
                print(f"{name} {year}: ERROR - {e}")
            time.sleep(1)  # respetar rate limit

        if frames:
            full = pd.concat(frames, ignore_index=True)
            out_path = os.path.join(RAW_DIR, f"{name.lower()}_exports_raw.csv")
            full.to_csv(out_path, index=False)
            print(f"Guardado: {out_path} ({len(full)} filas totales)")
        else:
            print(f"ADVERTENCIA: {name} no tuvo ningún dato en el rango {START_YEAR}-{END_YEAR}")


if __name__ == "__main__":
    main()
