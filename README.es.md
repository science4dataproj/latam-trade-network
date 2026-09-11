🇪🇸 Español | [🇬🇧 English](README.md)

# Riesgo de Concentración Comercial en América Latina: Detección y Forecasting de Cambios Estructurales

## Estado del proyecto
**Versión vigente: v2 (completa)** — universo de partners ampliado a socios
globales (no solo LatAm) y datos extendidos a 2025. La versión anterior
(`v1-regional-only`, ver tag en GitHub) medía diversificación solo dentro de
la región, lo cual resultó ciego a dependencias extra-regionales masivas
(ej. México-EE.UU.). Ver `CHANGELOG.es.md` para el detalle de cada versión
y por qué cambió.

**Documentos completos:**
- `reports/informe_completo.pdf` — metodología base (v1), en español.
- `reports/informe_v2_continuacion.pdf` — qué se agregó en v2 y por qué.
- `reports/articulo_sintesis_final.pdf` / `reports/article_summary_en.pdf` — versión corta tipo artículo, en español e inglés.

> Con datos a 2025, 7 de 10 países muestran quiebre estructural estadísticamente robusto. Perú es el caso más crítico: riesgo crónico alto (51% de sus exportaciones a China) y probabilidad de alerta de cambio reciente de 99.7%.

## El problema de negocio

¿Qué países de América Latina están entrando a una zona de riesgo elevado
de concentración de socios comerciales en los próximos 12-24 meses, y
dónde debería un exportador o inversionista regional priorizar monitoreo
o diversificación?

Esto importa ahora por dos razones concretas: (1) fricción comercial real
y verificable entre países de la región coincidiendo con realineamientos
políticos recientes (ver `reports/articulo_sintesis_final.pdf`), y (2)
varios países de la región eligieron nuevos gobiernos en 2025-2026, lo que
hace especialmente relevante monitorear si la estructura de comercio
también está cambiando.

## La respuesta corta

| País | Riesgo crónico | P(alerta) |
|---|---|---|
| 🔴 Perú | Alto (51% a China) | 99.7% |
| 🟠 Chile | Moderado | 95.9% |
| 🟠 Brasil | Moderado | 92.5% |
| 🟡 Honduras | Alto | 39.1% |
| 🟡 Guatemala | Alto | 29.0% |
| 🟢 México | Alto (92.6% a EE.UU.) | 0.03% — estructural, no una crisis nueva |
| 🟢 Colombia, Argentina, Ecuador, Bolivia | Bajo-Moderado | <2% |

Ver `data/processed/risk_dashboard_final.csv` para el detalle completo, y
la Figura 3 de `reports/informe_v2_continuacion.pdf` para la versión
visual.

## Datos

- **Fuente:** UN Comtrade, exportaciones reportadas por el país exportador
  (mirror statistics resuelto: se usa consistentemente el lado exportador).
- **Cobertura:** anual, 2000-2025 (2025 incompleto para Honduras y Perú por
  rezago de publicación).
- **Países (reporters):** México, Brasil, Argentina, Colombia, Perú,
  Ecuador, Bolivia, Honduras, Guatemala, Chile (Cuba y Venezuela excluidos
  por cobertura de reporte insuficiente).
- **Universo de partners:** los 10 países de la lista + Estados Unidos,
  China, Alemania, Japón, Corea del Sur (ver `CHANGELOG.es.md`, v2).
- **Nivel de agregación:** TOTAL (todos los productos, sin desagregar por
  código HS).

## Metodología (resumen)

1. **Construcción de la red** — grafo pesado y dirigido por año, nodo =
   país, edge = valor de exportación bilateral.
2. **Entropía de Shannon** — diversificación de destinos de exportación
   por país-año, normalizada [0,1].
3. **Detección de quiebres estructurales** — sup-F (Quandt-Andrews) con
   p-value por bootstrap (2,000 simulaciones) + corrección de Bonferroni
   por comparaciones múltiples, más CUSUM como confirmación secundaria.
4. **Forecasting probabilístico** — naive, ETS, ARIMA, regresión
   bayesiana, XGBoost, comparados bajo walk-forward validation (ventana
   expansiva). Métrica: MAE + cobertura del intervalo de predicción al 80%.
5. **Traducción a alerta de riesgo** — probabilidad vía la distribución
   predictiva del mejor forecast (análogo a un cálculo de
   Value-at-Risk), complementada con un indicador de nivel de
   concentración absoluto.

El detalle completo de cada paso (incluyendo métodos descartados y por
qué) está en `reports/informe_completo.pdf` y
`reports/informe_v2_continuacion.pdf`.

**Nota metodológica — DFA descartado:** se consideró Detrended Fluctuation
Analysis como segunda línea de evidencia de cambio de régimen, pero se
descartó. DFA requiere series de cientos/miles de puntos para que el
exponente de escalamiento sea estable; con ~22-26 observaciones anuales
por país, el ajuste log-log no tiene suficientes escalas de ventana para
ser confiable.

## Resultados principales

- **El punto ciego regional:** México aparecía como el país más
  diversificado bajo una métrica solo-regional (0.86) y resulta el más
  concentrado bajo la métrica global (0.16, 92.6% a EE.UU.).
- **7 de 10 países** muestran quiebre estructural robusto bajo Bonferroni.
  Clúster en 2007-2009 (crisis financiera global) + un caso reciente
  (Colombia, 2022) a vigilar, no confirmado como causal.
- **El naive gana el forecasting** en la mayoría de los países — la
  entropía de comercio es casi-persistente, y ningún método sofisticado
  debería ganarle a la persistencia cuando no hay tendencia fuerte.
- **XGBoost tiene cobertura de intervalo de solo ~29.5%** (objetivo 80%) —
  no se recomienda para cuantificar incertidumbre en este proyecto pese a
  tener un MAE competitivo.

## Limpieza de datos: hallazgos y decisiones

UN Comtrade regresa el comercio desglosado simultáneamente en tres
dimensiones adicionales, cada una con su propia fila de "total" más filas
de desglose que suman a ese total. Sin filtrar las tres, el valor de
comercio se duplica:
1. Modo de transporte (`motCode`): total vs. aéreo/marítimo/terrestre/etc.
2. Partner2 (`partner2Code`): total vs. desglose por socio
   consignatario/destino final.
3. Régimen aduanero (`customsCode`): total (`C00`) vs. desglose por tipo
   de régimen.

Se filtró consistentemente a la fila de total en las tres dimensiones
para los 10 países. Validado: cero duplicados residuales por (exportador,
año, socio) en el dataset final.

## Limitaciones

- N pequeño en series anuales (~22-26 puntos por país) — limita el poder
  de forecasting con ML; se prioriza rigor de validación sobre
  complejidad de modelo.
- Mirror statistics: se usa una sola dirección de reporte (exportador), no
  reconciliación bilateral completa.
- Honduras: sin datos en 2008, 2013, 2022, 2025 — ausencia real, no se
  imputa. Perú tampoco tiene 2025 publicado aún.
- Cuba/Venezuela excluidos por cobertura de reporte insuficiente, no
  "riesgo cero".
- Los quiebres estructurales estadísticamente significativos no implican
  causalidad sobre su origen (ver discusión de confounders en
  `reports/informe_v2_continuacion.pdf`).

## Referencias

- Alves, L.G.A., Mangioni, G., Rodrigues, F.A., Panzarasa, P., & Moreno,
  Y. (2018). Unfolding the Complexity of the Global Value Chain: Strength
  and Entropy in the Single-Layer, Multiplex, and Multi-Layer
  International Trade Networks. *Entropy*, 20(12), 909.
- Andrews, D.W.K. (1993). Tests for Parameter Instability and Structural
  Change with Unknown Change Point. *Econometrica*, 61(4), 821-856.
- UN Comtrade Database, comtradeplus.un.org.

## Cómo reproducir

```bash
pip install -r requirements.txt
export UN_COMTRADE_KEY="tu_key_aqui"   # gratis en comtradeplus.un.org

python src/fetch_data.py               # extracción inicial 2000-2024
python src/fetch_data_update.py        # incremental, años nuevos
python src/process_data.py             # edge list regional
python src/build_network.py            # entropía regional
python src/build_network_global.py     # entropía + universo global de partners
python src/structural_breaks.py network_metrics_global.csv _global
python src/forecasting.py network_metrics_global.csv _global
python src/risk_alert.py network_metrics_global.csv forecast_walkforward_results_global.csv _global
python src/risk_dashboard_final.py
python src/make_report_figures_v2.py   # figuras del informe v2
```
