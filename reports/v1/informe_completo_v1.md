---
title: "Riesgo de Concentración Comercial en América Latina: Detección y Forecasting de Cambios Estructurales en Redes de Comercio"
author: "Alberto Rosales"
date: "Septiembre 2026"
geometry: margin=2.5cm
fontsize: 11pt
toc: true
---

# Resumen ejecutivo

Este proyecto exploratorio construye una red de comercio ponderada y dirigida entre 10 países de América Latina (2000-2024), mide su evolución con entropía de Shannon, detecta formalmente cuándo ocurrieron quiebres estructurales, compara cinco métodos de forecasting probabilístico bajo validación walk-forward, y traduce todo eso en una probabilidad de alerta de riesgo de concentración comercial por país.

---

# 1. Motivación y pregunta de negocio

**Por qué este proyecto y no otro:** El mundo está viviendo un proceso histórico importante, moverse de un sistema unipolar dirigido sólo por EUA y su coalición occidental quienes resultaron vencedores de la segunda guerra mundial y la guerra fría, a estar ante un escenario con dos grandes nuevos polos en el oriente del mundo: Rusia y China. Con la llegada de Trump al poder en su segundo mandato, esta separación se ha hecho más evidente, y según los analistas, el acuerdo es que cada quien se quede con su zona de influencia, en este caso EUA con toda américa, recordando el manifiesto Monroe "América para los americanos". 

Además de esta ruptura tripolar, hay otra más de la que no se está hablando mucho como tal: una aparente ruptura de occidente entre lo que los medios llaman ultra-derecha y el progresismo (wokismo). En los últimos años, esta facción considerada de derecha/ultraderecha con tintes nacionalistas, anti inmigrantes y profundamente arraigados en la religión cristina, está ganando las elecciones en diferentes países. América latina no es la excepción. En los últimos años la ultraderecha ha tomado Argentina, Ecuador, Chile, Peru, Colombia y en las próximas elecciones viene la pelea por Brasil, quedando México como el último bastión latinoamericano que esta ultraderecha no ha podido tomar y al menos en el mediano plazo se ve difícil.

La pregunta de trabajo es ¿podemos ver y/o cuantificar los efectos de estas rupturas geopolíticas? Recientemente, se han reportado roces entre México y países de derecha como Argentina, Ecuador (ruptura de relaciones por invasión de la embajada) y Peru, que han repercutido en el comercio de estas zonas, por ejemplo México ya no importa tanta carne y otros productos de Argentina, con Ecuador ya no hay relaciones diplomáticas y al parecer ya no hay relaciones comerciales tampoco, Perú por su parte se ha puesto de acuerdo con EUA para comerciar la Palta/Aguacate y dejar fuera a México. Estos movimientos han sido motivados por la diferencia en ideologías de los presidentes en turno, un aparente golpeteo del bloque de ultra-derecha contra México se está fraguando. Analizando todo esto generlo la siguiente hipótesis, ¿se puede ver el efecto de la ruputra de latinoamérica en los patrones de comercio?

Para ello vamos a comenzar con algo más básico, construir un detector de cambios de ŕegimen en series de tiempo usando como variable la concentración de socios comerciales cuantificados como la entropía de Shanon y el HHI. Esperamos que haya cambios en las crisis económicas de cada país así como en la crisis global de 2007 y en el COVID. Para ello la pregunta de este análisis es

**Pregunta de decisión concreta:** ¿qué países de América Latina están entrando a una zona de riesgo elevado de concentración de socios comerciales en los próximos 12-24 meses, y dónde debería un exportador o inversionista regional priorizar monitoreo o diversificación?

---

# 2. Fundamento teórico: qué se usó, de dónde viene, y qué conecta con tu doctorado

La tabla siguiente es el mapa central de este documento. 

| Técnica usada | Qué hace en el proyecto | Área de origen |
|---|---|---|---|---|
| **Entropía de Shannon en redes** | Mide diversificación de socios comerciales | Teoría de la información / econofísica |
| **Grafos dirigidos ponderados (NetworkX)** | Representa el comercio bilateral | Teoría de grafos |
| **Test sup-F de Quandt-Andrews** | Detecta el año de quiebre estructural más probable | Econometría de series de tiempo |
| **Bootstrap para p-value** | Calcula significancia del sup-F sin tablas de valores críticos | Estadística computacional (Efron, 1979) |
| **Corrección de Bonferroni** | Ajusta el umbral de significancia por correr 10 tests | Estadística (comparaciones múltiples) | 
| **CUSUM (Brown-Durbin-Evans / Ploberger-Krämer)** | Segunda confirmación de inestabilidad de parámetros | Econometría |
| **DFA (considerado, descartado)** | Se evaluó como tercera línea de evidencia | Sistemas complejos|
| **Exponential Smoothing (Holt, tendencia amortiguada)** | Baseline clásico de forecasting | Series de tiempo clásicas |
| **ARIMA / SARIMAX** | Segundo baseline clásico, orden elegido por AIC | Series de tiempo (Box-Jenkins) |
| **Bayesian Ridge Regression** | Modelo con salida probabilística genuina (posterior) | Estadística bayesiana |
| **XGBoost (gradient boosting)** | ML no lineal para comparación | Machine learning | 
| **Walk-forward validation (ventana expansiva)** | Evita leakage temporal en forecasting | Buenas prácticas de ML en series de tiempo |
| **ROC-AUC / PR-AUC** | Mide si una probabilidad tiene señal real, más allá de un umbral fijo | Clasificación Machine Learning |
| **Traducción forecast → probabilidad de riesgo (estilo VaR)** | Convierte el intervalo de predicción en P(riesgo) | Gestión de riesgo cuantitativo |


---

# 3. Datos: fuente, limpieza, y lo que salió mal en el camino (a propósito lo dejo aquí)

**Fuente:** UN Comtrade, exportaciones bilaterales reportadas por el país exportador (`flowCode='X'`), 2000-2024, 10 países (México, Brasil, Argentina, Colombia, Perú, Ecuador, Bolivia, Honduras, Guatemala, Chile — Cuba y Venezuela excluidos por cobertura de reporte insuficiente).

**Tres capas de desglose que la API regresa sin pedirlas, y que si no se filtran duplican el valor de comercio:**

```python
# Cada una de estas dimensiones tiene una fila de TOTAL + filas desglosadas
# que suman a ese total. Sin filtrar las tres, el valor se cuenta 2-3 veces.
df = df[df["motCode"] == 0]        # total por modo de transporte
df = df[df["partner2Code"] == 0]   # total por "partner2" (destino final)
df = df[df["customsCode"] == "C00"]  # total por régimen aduanero
```

Este hallazgo no estaba en el diseño original — se descubrió al validar los datos de México y Honduras antes de escalar a los 10 países, exactamente el tipo de sorpresa que uno espera encontrar validando en pequeño antes de automatizar.

**Hueco de cobertura real:** Honduras no tiene reporte en 2008, 2013 y 2022. Se dejó como `NaN` explícito, nunca interpolado.

**Decisión de diseño sobre asimetría (mirror statistics):** se usa siempre el lado exportador como fuente de verdad, nunca se reconcilia con lo que el país importador reportó. Es una simplificación documentada, no un descuido.

---

# 4. Metodología, paso a paso: qué se hizo y por qué

## 4.1 Construcción de la red

**Por qué:** para poder aplicar métricas de red (no solo comparar series aisladas por país), se necesita una estructura de grafo donde el comercio bilateral sea explícito.

Cada año se construye un grafo dirigido con los 10 países como nodos y el valor de exportación bilateral (USD) como peso del edge — ambas direcciones quedan cubiertas porque cada país es simultáneamente reporter de sus propias exportaciones.

## 4.2 Entropía de diversificación

**Por qué:** queríamos una sola métrica por país-año que capturara "qué tan concentrados están sus socios comerciales", análoga al índice de riesgo que construiste en Peñoles a partir de múltiples indicadores.

**Validación cualitativa, no solo el número:** antes de confiar en la métrica, se investigaron dos movimientos bruscos para confirmar que reflejaban eventos reales y no ruido de datos:

- Brasil, 2001→2002: la entropía sube porque la participación de Argentina en las exportaciones de Brasil cae de 51% a 29% — coincide exactamente con la crisis argentina de 2001-2002 (corralito, default, devaluación).
- El clúster de quiebres estructurales en 2007-2009 (ver sección 4.3) coincide con el inicio de la crisis financiera global — el mismo patrón que reporta la literatura académica citada.

Ver **Figura 1** para las 10 series completas, con ambos eventos marcados.

## 4.3 Detección de quiebres estructurales

**Por qué:** una entropía que sube o baja no dice si el cambio es ruido normal o una reconfiguración real. Se necesita un test formal con significancia estadística, no solo inspección visual. Un quiebre estructural significa que el proceso que genera los datos cambió, no solo que los datos cambiaron de valor. Toda serie de tiempo se puede pensar como generada por un proceso con ciertos parámetros (una tendencia, una media, una varianza). Mientras esos parámetros sean estables, cualquier movimiento año a año es solo ruido alrededor de ese proceso constante. Un quiebre estructural es el momento en que los parámetros mismos cambian — la serie "antes" y la serie "después" no son la misma cosa fluctuando, son dos procesos distintos empalmados.

Interpretación correcta de lo que el test dice cuándo cambió el comportamiento y con qué confianza estadística ese cambio no es ruido. No te dice por qué cambió. La causa es algo que tú tienes que argumentar aparte, con evidencia histórica o económica — el test es ciego a narrativa, que es justamente su fortaleza y su límite al mismo tiempo.

**Método:** sup-F de Quandt-Andrews (recorte de 15% en cada extremo), con p-value estimado por bootstrap de residuales (2000 simulaciones bajo la hipótesis nula de "sin quiebre"), más CUSUM como confirmación secundaria. Corrección de Bonferroni aplicada por correr 10 tests independientes. Sup-F de Quandt-Andrews: para cada año candidato (recortando 15% en cada extremo), comparamos dos modelos:

Modelo A: una sola tendencia lineal para toda la serie.
Modelo B: dos tendencias separadas, una antes y otra después de ese año candidato.

Si el año candidato es un verdadero quiebre, el Modelo B va a reducir mucho el error respecto al Modelo A (porque ahora cada tramo tiene su propia pendiente/nivel). Calculamos un F-stat que mide esa mejora, para cada año candidato, y nos quedamos con el año que da el F-stat más alto — ese es "el mejor candidato a quiebre" que la serie ofrece.

Por qué necesita bootstrap y no una tabla de F estándar: aquí está el detalle técnico importante. No estamos haciendo un solo test — estamos probando ~18 años candidatos por país y quedándonos con el máximo. Eso es, en esencia, hacer 18 comparaciones múltiples y reportar solo la más favorable. Un F-stat normal asume que probaste un solo punto de quiebre conocido de antemano; el máximo de 18 pruebas tiene una distribución distinta (más generosa hacia falsos positivos) que una F individual. El bootstrap resuelve esto simulando bajo la hipótesis nula ("no hay quiebre en ningún año") miles de veces, calculando el sup-F simulado cada vez, y viendo qué tan seguido ese máximo simulado iguala o supera al que observamos en los datos reales. Así el p-value ya incorpora el costo de haber buscado en 18 lugares, no solo en uno.

CUSUM como segunda opinión: en vez de buscar un quiebre puntual, mide si los residuales acumulados del modelo se desvían sistemáticamente de cero a lo largo del tiempo — es sensible a inestabilidad gradual, no a un salto específico. Por eso, como vimos, a veces no coincide con el sup-F: son preguntas ligeramente distintas ("¿hay un salto en un punto?" vs. "¿el modelo se volvió inestable de forma difusa?").

**Resultado:** 5 de 10 países muestran quiebre robusto incluso bajo la corrección estricta (Bolivia, Guatemala, Perú, Honduras, Colombia), y 4 de esos 5 caen entre 2007-2009 — el mismo patrón de la crisis financiera global documentado en la literatura de redes de comercio (Alves et al., 2018). Ver **Figura 2**.

**Nota metodológica — DFA descartado:** se consideró como segunda línea de evidencia, pero con ~22-25 observaciones anuales el exponente de escalamiento de DFA no es estadísticamente confiable (la técnica típicamente requiere cientos/miles de puntos). Se documenta la decisión en vez de forzar la técnica.


## 4.4 Forecasting probabilístico con walk-forward validation

**Por qué comparar 5 métodos y no solo el "mejor":** el objetivo no es solo pronosticar, es demostrar criterio sobre cuándo cada método gana o pierde 


**Resultado global (97 folds, 10 países):**

| Método | MAE | Cobertura del intervalo 80% |
|---|---|---|
| naive | 0.0196 | 90.7% |
| arima | 0.0221 | 80.4% |
| xgboost | 0.0221 | 24.7% |
| ets | 0.0237 | 79.4% |
| bayesian | 0.0321 | 80.4% |

**Diagnóstico, no solo el ranking:**

- **El naive gana** porque la entropía se mueve poco año a año (proceso casi-persistente); ningún método sofisticado debería ganarle a la persistencia cuando la serie no tiene tendencia fuerte, y efectivamente no le gana.
- **El bayesiano pierde de forma explicable:** se le ajustó una tendencia cuadrática sobre TODO el histórico, así que sobre-extrapola en series con meseta reciente (ver Figura 3, Colombia). No es un modelo roto — es un modelo cuyo diseño no encaja con el patrón de la serie.
- **XGBoost tiene cobertura de intervalo de solo 24.7%** (el objetivo es 80%) — el método de intervalo (bootstrap de residuales de entrenamiento) subestima sistemáticamente el error real fuera de muestra. Esto es un hallazgo de "qué no usaríamos para dar incertidumbre confiable", útil aunque XGBoost compita bien en MAE puro.

## 4.5 Del forecast a la probabilidad de alerta

**Intento inicial (descartado, documentado):** se entrenó un clasificador supervisado (Logistic Regression code in risk_classifier_attempt_lagfeatures.txt) sobre features rezagadas de entropía para predecir si el año siguiente cruzaría el percentil 20 histórico. Resultado: ROC-AUC ~ 0.49 — esencialmente azar, incluso agregando una feature de momentum de 3 años. Conclusión: los lags cortos de entropía no predicen bien un cruce de umbral a un año, consistente con que los quiebres detectados en 4.3 son fenómenos multi-año, no año-a-año.

**Enfoque adoptado en su lugar:** en vez de un modelo nuevo, se reutiliza la distribución predictiva que ya generó el mejor forecast de cada país-año (media + desviación estándar del intervalo). La probabilidad de alerta es el área de esa distribución normal por debajo del umbral de riesgo — el mismo cálculo que sustenta un Value-at-Risk paramétrico:

**Resultado: ROC-AUC = 0.939, PR-AUC = 0.422** (vs. tasa base de 5.2%) — una mejora sustancial sobre el intento inicial, y evidencia de que la incertidumbre ya validada en el forecast contenía la señal que el clasificador nuevo no pudo encontrar por sí solo.

---

# 5. Resultados finales

**Ranking de riesgo, 2024** (ver Figura 4 para la versión gráfica):

| País | P(alerta) |
|---|---|
| Chile | 44.5% |
| Perú | 13.9% |
| México | 12.4% |
| Brasil | 0.7% |
| Honduras | 0.7% |
| Colombia | 0.3% |
| Guatemala | 0.1% |
| Argentina | 0.05% |
| Ecuador | 0.002% |
| Bolivia | 0.002% |

Chile como el más alto es contraintuitivo a primera vista (es de los países más diversificados en promedio), pero es coherente con el diseño: Chile tiene una banda histórica muy estrecha, así que un desvío moderado respecto a su propio patrón pesa proporcionalmente más que el mismo desvío en un país con más volatilidad histórica. Queda pendiente de tu revisión manual antes de presentarlo como hallazgo firme, con la misma disciplina que se aplicó a Brasil y Honduras en este documento.

---

# 6. Limitaciones
- Sólo se tomaron ciertos países de Latinoamérica y sus relaciones comerciales entre sí, lo que limita el análisis, por ejemplo no está EUA ni China.
- N pequeño en series anuales (~22-25 puntos por país) — limita el poder estadístico de todos los tests, documentado explícitamente en cada sección en vez de ignorado.
- Mirror statistics: se usa una sola dirección de reporte (exportador), sin reconciliación bilateral.
- Honduras: 3 años sin dato, tratados como ausencia real. Probablemente lo descartaremos en el siguiente análisis
- Cuba y Venezuela excluidos por cobertura, no por "riesgo cero".
- Un quiebre estructural estadísticamente significativo no implica causalidad sobre su origen. Sólo es un cambio de régimen
- El panel de clasificación de alerta (intento descartado) tenía solo 191 observaciones pooled — insuficiente para un clasificador con features débiles, aunque suficiente para el enfoque final basado en el forecast.

---

# 7. Preguntas que surgieron a partir de este primer análisis

1.- Es interesante ver cómo es que comercialmente Argentina tiene bajo riesgo (dentro de nuestras definiciones) pero es el pais con una grave crisis económica en la región. Me sonaría contra intuitivo, pero parece que son dos cosas distintas.  
2.- Importaciones y exportaciones de un país, sin embargo las empresas que comercian son las que se llevan las ganancias, al final cierta parte se queda en la gente (por sus salarios), otra más en impuestos (aunque por acuerdos puedan estar extentos de aranceles) y finalmente las ganancias se las llevan esas empresas, normalmente de EUA y Chinas. Cuál es el verdadero beneficio para el país?
3.- Sobre la dependencia del cono sur con China, suena muy interesante ya que actualmente, Países como Chile, Argentina, Ecuador, Colombia, tuvieron elecciones recientemente y todos los candidatos electos tienen una agenda muy parecida a la de EUA, combina mucho con lo que algunos analistas llaman la "nueva doctrina Monroe de Trump" y los manifiestos que salieron después de su elección. Será interesante ver si hay un cambio. Hay que seguir monitoreando este espacioque Colombia, Perú apenas está arrancando su mandato los presidentes con agenda común a EUA, y en Brasil habrá elecciones próximamente y es el caso mas interesante porque es miembro de los Brics. Si gana la facción de Bolsonaro, pro EUA, seguro cambian las cosas de forma mas profunda por el volumen que maneja Brasil
4.- Sigo con mi idea de ver si se puede detectar el punto donde hay un cambio en los patrones de comercio producto de los cambios geopolíticos, seguro necesito mas datos para poder establecer algo (años) pero qué mas ajustes podríamos ir haciendo? Quisiera ir analizando en tiempo real como pasamos del viejo orden mundial (Paises del Norte comerciando con EUA, Paises de suramérica con China) a este supuesto cambio geopolítico tripolar donde cada polo estaría dominando su área de influencia, por ende se esperaría una estructura diferente. Y si no la hay, seria tmb interesante verlo ya que ese cambio geopolítico solo se queda ahí, pero no permea en la parte comercial. Es como la parte de las bolsas de valores. A pesar de como está el mundo viviendo (según) transicioes de polos geopolíticos, guerras, las boslas siguen subiendo, claro con sus bajones por noticias puntuales como lo de Ormuz y la guerra con Irán, pero las bolsas siguen subiendo. Muchos analistas geopolíticos ven que es el fin del mundo y una gran crisis viene, pero los datos don distintos, creo que solo venden temor para tener mas likes en sus páginas y podcasts, eso me ha parecido y por eso me interesa tanto ese tema



---

# 9. Trabajo Futuro

La entropía original solo medía diversificación dentro de los 9 países LatAm, lo cual es ciego a dependencias masivas fuera de la región (el caso más claro: México y su ~93% de dependencia de EE.UU., invisible en el diseño original). 

Integrar los siguientes cambios:
- Universo de partners ampliado — mismos 10 países como reporters, pero ahora comparados contra EE.UU., China, Alemania, Japón y Corea del Sur además de los 9 de LatAm (build_network_global.py).
- Comparación explícita regional vs. global — no se reemplazó la v1, se conservó como punto de comparación (entropy_regional_vs_global.csv), lo cual generó el hallazgo más fuerte del proyecto hasta ahora (México debería de pasar de "más diversificado" a "más concentrado" del grupo dada la dependencia tan fuerte con EUA por el T-MEC).

-Integrar un segundo indicador nuevo: riesgo crónico vs. riesgo de cambio — no estaba en el diseño original. Salió de un hallazgo inesperado (México con 0% de alerta puede y debe de tener el riesgo más alto por depender de EUA) que forzó a reconocer que "alerta" (cambio reciente) y "nivel absoluto de concentración" son preguntas distintas, y el dashboard final ahora reporta ambas.
---

# 9. Referencias

- Alves, L.G.A., Mangioni, G., Rodrigues, F.A., Panzarasa, P., & Moreno, Y. (2018). Unfolding the Complexity of the Global Value Chain: Strength and Entropy in the Single-Layer, Multiplex, and Multi-Layer International Trade Networks. *Entropy*, 20(12), 909.
- Andrews, D.W.K. (1993). Tests for Parameter Instability and Structural Change with Unknown Change Point. *Econometrica*, 61(4), 821-856.
- Efron, B. (1979). Bootstrap Methods: Another Look at the Jackknife. *The Annals of Statistics*, 7(1), 1-26.
- Jorion, P. (2006). *Value at Risk: The New Benchmark for Managing Financial Risk*. McGraw-Hill.
- UN Comtrade Database, https://comtradeplus.un.org

---

# Apéndice: Figuras

![Figura 1: Entropía de diversificación por país, 2000-2024, con eventos macroeconómicos anotados](reports/v1/figures/fig1_entropy_timeseries.png)

![Figura 2: Evidencia de quiebre estructural por país (sup-F, corrección de Bonferroni)](reports/v1/figures/fig2_structural_breaks.png)

![Figura 3: Walk-forward validation en Colombia, mejor método (naive) vs. peor (bayesiano)](reports/v1/figures/fig3_forecast_colombia.png)

![Figura 4: Ranking de riesgo de concentración comercial, 2024](reports/v1/figures/fig4_risk_ranking_2024.png)
