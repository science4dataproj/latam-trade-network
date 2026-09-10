# Riesgo de Concentración Comercial en América Latina: Detección y Forecasting de Cambios Estructurales

> [1 línea, se escribe al final cuando ya sepamos el resultado real — ej. "3 de 10 países muestran señales tempranas de riesgo de concentración comercial creciente hacia 2026-2027"]

## El problema de negocio
<!--
NO empezar con "este proyecto analiza redes de comercio". Empezar con la pregunta
que le importa a alguien que toma decisiones: un exportador, un analista de riesgo
soberano, un inversionista regional.

Placeholder de la pregunta ya definida:
"¿Qué países de América Latina están entrando a una zona de riesgo elevado de
concentración de socios comerciales en los próximos 12-24 meses, y dónde debería
un exportador/inversionista regional priorizar monitoreo o diversificación?"

Aquí también va, en 2-3 líneas, el POR QUÉ importa esto ahora (contexto de
guerra comercial/reconfiguración de bloques — sin etiquetar ideología de gobiernos).
-->

## La respuesta corta
<!-- Se llena al final: ranking semáforo (verde/amarillo/rojo) de los 10 países,
la gráfica principal, y 2-3 líneas de conclusión. Esto es lo único que el 80%
de los lectores va a ver. -->

## Datos
<!--
- Fuente: UN Comtrade, exportaciones reportadas por el país exportador (mirror
  statistics resuelto: se usa consistentemente el lado exportador)
- Cobertura: [mensual o anual, según lo que confirme el pull] , 20XX-2025
- Países: México, Brasil, Argentina, Colombia, Perú, Ecuador, Bolivia, Honduras,
  Guatemala, Chile (Cuba y Venezuela excluidos por cobertura de reporte insuficiente
  — documentar con evidencia del pull)
- Nivel de agregación: TOTAL (todos los productos)
-->

## Metodología
### 1. Construcción de la red
<!-- Red pesada y dirigida, nodo = país, edge = valor de exportación bilateral -->

### 2. Métricas de red y su evolución temporal
<!-- Entropía de distribución de pesos, grado ponderado, densidad -->

### 3. Detección de cambios estructurales
<!-- Chow test / CUSUM sobre la serie de entropía + DFA como segunda línea de evidencia
     (persistencia/antipersistencia) -->

### 4. Forecasting probabilístico
<!-- ARIMA/ETS vs modelo bayesiano estructural vs XGBoost, walk-forward validation,
     intervalos de predicción. Baseline naive obligatorio. -->

### 5. Traducción a alerta de riesgo
<!-- Clasificador entrenado (logística/random forest) con salida P(riesgo),
     features = métricas de red rezagadas. Evaluado con precision/recall vs
     backtesting histórico. -->

## Validación de robustez de la métrica central
<!-- Prueba de bondad de ajuste (KS) sobre la distribución de pesos de la red
     (power-law vs lognormal) — justifica por qué la entropía es interpretable -->

## Resultados
<!-- Por país: serie de entropía + quiebres detectados + forecast con intervalos
     + probabilidad de alerta. Se llena al final. -->

## Limpieza de datos: hallazgos y decisiones
<!--
UN Comtrade regresa el comercio desglosado simultáneamente en tres dimensiones
adicionales, cada una con su propia fila de "total" más filas de desglose que
suman a ese total. Sin filtrar las tres, el valor de comercio se duplica:
    1. Modo de transporte (motCode): total vs. aéreo/marítimo/terrestre/etc.
    2. Partner2 (partner2Code): total vs. desglose por socio consignatario/destino final.
    3. Régimen aduanero (customsCode): total ('C00') vs. desglose por tipo de régimen.
Se filtró consistentemente a la fila de total en las tres dimensiones para los
10 países. Validado: cero duplicados residuales por (exportador, año, socio)
en el dataset final.
-->

## Limitaciones (sección obligatoria, no opcional)
<!--
- N pequeño en series anuales (~25 puntos por país) — limita el poder de
  forecasting con ML, documentar por qué se prioriza rigor de validación
  sobre complejidad de modelo
- Mirror statistics: se usa una sola dirección de reporte (exportador), no
  reconciliación bilateral completa
- Honduras: sin datos en 2008, 2013, 2022 — ausencia real, no se imputa
- Cuba/Venezuela excluidos por cobertura de reporte insuficiente, no "riesgo cero"
- Structural breaks estadísticamente significativos no implican causalidad
-->

## Referencias
<!--
- Alves et al. (2018), "Unfolding the Complexity of the Global Value Chain:
  Strength and Entropy in the Single-Layer, Multiplex, and Multi-Layer
  International Trade Networks", Entropy 20(12), 909.
- [agregar los otros 2-3 papers relevantes conforme se citen en el cuerpo]
-->

## Cómo reproducir
<!-- Instrucciones de setup, se llena al final -->
