---
title: "Riesgo de Concentración Comercial en América Latina — Informe de Continuación (v2)"
subtitle: "Ampliación a socios globales y segundo indicador de riesgo"
date: "Septiembre 2026"
geometry: margin=2.5cm
fontsize: 11pt
toc: true
---

# 1. Qué es este documento

Este es un informe de continuación, no una repetición del informe v1. Documenta específicamente qué se agregó en esta etapa, por qué se agregó, qué cambió en los resultados como consecuencia, y qué preguntas quedan abiertas para investigación futura. Para la metodología base (construcción de la red, cálculo de entropía, diseño del forecasting) ver `informe_completo_v1.md` (v1) — aquí no se repite.

---

# 2. Qué se agregó y por qué

## 2.1 Universo de partners ampliado a socios globales

**El problema detectado:** la versión v1 calculaba la entropía de cada país usando solo a los otros 9 países de LatAm como universo posible de destinos de exportación. Eso responde la pregunta "¿qué tan diversificado está este país *dentro de la región*?" — una pregunta distinta, y más limitada, de "¿qué tan concentrado está el riesgo comercial de este país?".

**Qué se hizo:** se mantuvieron los mismos 10 países como *reporters* (no se volvió a pedir su comercio, ya lo teníamos), pero se dejó de filtrar los *partners* solo a la región — se incluyeron también Estados Unidos, China, Alemania (como ancla de la UE, no existe un código agregado limpio de "Unión Europea" en Comtrade), Japón y Corea del Sur.

**Limitación de alcance reconocida:** estos 5 países nunca fueron consultados como reporters, así que la corrección aplica al lado de exportación (`export_entropy`) de los 10 países LatAm, no a su lado de importación.

## 2.2 Segundo indicador: riesgo crónico vs. riesgo de cambio

**El hallazgo que lo motivó:** al correr la alerta de riesgo (que mide desviación respecto a la propia historia del país) sobre la métrica global, México salió con ~0% de probabilidad de alerta pese a tener, por mucho, la concentración más alta del grupo (92.6% de sus exportaciones a un solo país). No es un error — es que esa dependencia es estructural y estable, no un cambio reciente, y el indicador de alerta está diseñado para detectar cambios, no niveles.

**Qué se agregó:** un segundo indicador, independiente del primero, que mide nivel absoluto de concentración (% de exportaciones al socio dominante), clasificado en Alto/Moderado/Bajo con umbrales fijos (no relativos a la historia de cada país). El dashboard final cruza los dos ejes.

---

# 3. Resultados (con datos actualizados a 2025)

## 3.1 El punto ciego de México, cuantificado

| País | Año más reciente | Entropía regional | Entropía global | Diferencia | Socio dominante |
|---|---|---|---|---|---|
| México | 2025 | 0.861 | 0.158 | −0.703 | EE.UU. (92.8%) |
| Colombia | 2025 | 0.802 | 0.587 | −0.216 | EE.UU. (59.3%) |
| Ecuador | 2025 | 0.831 | 0.644 | −0.187 | EE.UU. (38.4%) |
| Chile | 2025 | 0.802 | 0.639 | −0.163 | China (47.0%) |
| Brasil | 2025 | 0.750 | 0.629 | −0.122 | China (50.4%) |
| Honduras | 2024* | 0.521 | 0.414 | −0.107 | EE.UU. (71.2%) |
| Perú | 2024* | 0.863 | 0.625 | −0.237 | China (51.3%) |
| Guatemala | 2025 | 0.539 | 0.501 | −0.038 | EE.UU. (59.3%) |
| Bolivia | 2025 | 0.735 | 0.793 | +0.059 | China (28.6%) |
| Argentina | 2025 | 0.637 | 0.730 | +0.093 | Brasil (28.5%) |

*Honduras y Perú aún no tienen dato de 2025 publicado — su fila usa 2024, el último año disponible. No es un error, es rezago real de reporte.

México se sostiene como el hallazgo central incluso con el año nuevo: el país "más diversificado" bajo la lente regional sigue siendo, por un margen enorme, el más concentrado bajo la lente global. Ver **Figura A**.

**Patrón norte-sur, confirmado con datos frescos:** México, Colombia, Ecuador, Guatemala dominados por EE.UU.; Chile, Brasil, Perú dominados por China. Novedad de esta actualización: **Bolivia cambió su socio dominante de Brasil a China** respecto al corte anterior — vale la pena vigilar si es ruido de un año o el inicio de un patrón.

## 3.2 Quiebres estructurales, con un año adicional de evidencia

**7 de 10 países mantienen quiebre estructural robusto bajo Bonferroni** — mismo conteo que con datos a 2024, pero con un cambio notable: **Colombia ahora marca su año de quiebre en 2022** (antes en un año distinto), el mismo año de la elección de Gustavo Petro. Con solo 3 años de dato posterior a ese punto, es prematuro afirmar una relación causal — pero es exactamente la señal que vale la pena seguir monitoreando, tal como se planteó en la sección de líneas futuras del corte anterior. Ver **Figura B**.

Guatemala, Bolivia y Chile no muestran quiebre robusto bajo la corrección estricta.

## 3.3 Forecasting, re-corrido con 105 folds (antes 97)

| Método | MAE | Cobertura del intervalo 80% |
|---|---|---|
| naive | 0.0185 | 81.9% |
| arima | 0.0203 | 72.4% |
| ets | 0.0222 | 71.4% |
| xgboost | 0.0222 | 29.5% |
| bayesian | 0.0326 | 62.9% |

El patrón se sostiene sin cambios de fondo: naive sigue ganando, XGBoost sigue con cobertura de intervalo muy por debajo del objetivo (29.5%, prácticamente igual que antes) — confirma con más datos que ese método no debería usarse para dar incertidumbre confiable en este proyecto, no fue una casualidad del corte anterior.

## 3.4 Dashboard final de dos ejes

Ver **Figura C**. Con el año nuevo, el mapa de riesgo se reordena parcialmente:

- **Perú se mantiene como el caso más crítico** (riesgo crónico Alto + P(alerta) 99.7%).
- **Chile sube a riesgo crónico Moderado con P(alerta) 95.2%** — sigue en el cuadrante de vigilancia activa.
- **Colombia y Guatemala entran a riesgo crónico Alto** (antes en el límite o en Moderado) — su concentración en el socio dominante cruzó el umbral de 50%.
- **Argentina baja a riesgo crónico Bajo** (antes Moderado) — su dependencia de Brasil se diluyó ligeramente.
- **México se mantiene en riesgo crónico Alto sin cambio reciente** (P(alerta) 0.7%) — la lectura no cambió: dependencia estructural estable, no una crisis nueva.

---

# 4. Discusión: ¿el efecto es real, o hay algo más detrás?

Esta pregunta se trabajó explícitamente durante esta etapa y vale la pena dejarla documentada.

**Lo que el bootstrap confirma:** que el patrón de 7/10 quiebres (con corrección de comparaciones múltiples) no es producto de ruido bajo el modelo nulo.

**Lo que el bootstrap NO puede descartar, y por qué importa:**

- **Confounder identificado: el superciclo de commodities.** El clúster de quiebres en 2007-2009 (Brasil, Honduras, Perú, Ecuador) coincide tanto con la crisis financiera global como con el pico y colapso de precios de materias primas — dos fenómenos entrelazados en el mismo periodo para economías exportadoras de commodities. El test no puede separar cuál de las dos causas (o ambas) es la responsable del quiebre detectado.
- **Caso nuevo a vigilar, mismo principio de cautela: Colombia, quiebre en 2022.** Coincide con la elección de Gustavo Petro, pero con solo 3 años de datos posteriores el test tiene poder estadístico limitado para confirmar nada con solidez — se documenta como candidato a seguir, no como hallazgo cerrado.
- **Dirección de causalidad, relevante para investigación futura:** para la pregunta de si los gobiernos recién electos con agenda afín a EE.UU. (Chile, Argentina, Ecuador, y próximamente posibles cambios en Colombia/Perú/Brasil) producen cambios en la estructura comercial, la dirección de causalidad no es obvia a priori — es igualmente plausible que un choque económico previo (deterioro comercial, crisis) haya influido en el resultado electoral, no al revés. Separar estas direcciones requiere diseño causal, no solo coincidencia temporal.
- **Distinción importante señalada en esta etapa:** el comercio exterior (lo que mide este proyecto) y la salud macroeconómica de un país (inflación, deuda, tipo de cambio) son ejes distintos — el caso de Argentina, con comercio relativamente diversificado pero una crisis macroeconómica severa y bien documentada, es el ejemplo más claro de esa distinción dentro de los propios datos del proyecto.

---

# 5. Conclusiones de esta etapa

1. La corrección del universo de partners no fue cosmética — cambió la conclusión central del proyecto para al menos un país (México), de "diversificado" a "el más concentrado del grupo", y se sostiene con el año adicional de datos (2025).
2. El patrón norte-EE.UU. / sur-China es ahora visible y cuantificado, algo que la versión v1 no podía mostrar por construcción. Con el dato nuevo, Bolivia mostró un cambio de socio dominante (de Brasil a China) que vale la pena confirmar en el próximo corte.
3. Un solo indicador de riesgo (la alerta relativa) esconde la mitad de la historia — el caso de México lo demuestra directamente, con o sin el año nuevo. El dashboard de dos ejes es una mejora estructural, no un agregado cosmético.
4. Con datos a 2025, apareció un primer candidato concreto para la pregunta política pendiente: el quiebre estructural de Colombia en 2022 coincide con un cambio de gobierno. Sigue sin haber suficientes observaciones posteriores para tratarlo como algo más que una señal a vigilar.
5. La pregunta más amplia de si el realineamiento político reciente en la región se traduce en cambios de estructura comercial **sigue sin poderse responder con rigor** — la mayoría de los gobiernos relevantes (Chile, próximamente Brasil) aún no tienen o apenas están generando datos posteriores a su transición. Forzar una conclusión ahora sería el mismo error que se ha evitado durante todo el proyecto.

---

# 6. Líneas de investigación futura

- **Monitoreo recurrente:** correr este pipeline trimestralmente conforme se publiquen datos nuevos, para acumular observaciones post-cambio de gobierno de forma orgánica. En 12-18 meses habría base real para un Chow test dirigido al año específico de cada transición política (más potente que el sup-F genérico, al no pagar el costo de búsqueda entre múltiples candidatos).
- **Diseño causal (synthetic control):** para separar el efecto específico de un cambio de gobierno del efecto de shocks globales comunes, construyendo un contrafactual con países similares sin el cambio político, con placebo tests para descartar falsos positivos. Esto es, en esencia, el diseño ya planeado como Proyecto 2.
- **Capa de datos de alta frecuencia como señal adelantada:** los mercados financieros (índices bursátiles, tipo de cambio, spreads de deuda soberana) reaccionan casi en tiempo real a percepción geopolítica, mientras que el comercio real es una señal lenta y rezagada. Un diseño de dos velocidades (mercados como anticipación, comercio real como confirmación) permitiría contrastar si la narrativa geopolítica dominante se está traduciendo en cambios reales de estructura económica, o si se queda solo en percepción de mercado sin permear al comercio físico.
- **Extensión a valor agregado real (TiVA):** el comercio bruto (lo que mide este proyecto) no equivale a captura doméstica de valor — una extensión futura podría incorporar datos de Trade in Value Added (OCDE/OMC) para distinguir entre "exporta mucho" y "retiene beneficio económico real", una distinción especialmente relevante para economías con alto componente de maquila como México.

---

# Apéndice: Figuras

![Figura A: Entropía regional vs. global, 2024 — el punto ciego de México](figures_v2/figA_regional_vs_global.png)

![Figura B: Quiebres estructurales con la métrica global](figures_v2/figB_structural_breaks_global.png)

![Figura C: Dashboard de riesgo combinado, dos ejes](figures_v2/figC_dashboard_final.png)
