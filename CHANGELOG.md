# Changelog

## v2 — Universo de partners global + datos extendidos (en curso)
Se detectó que la entropía calculada solo con los 9 socios LatAm subestimaba
gravemente la concentración real de México (0.879 regional vs. 0.171 con
socios globales — 92.6% de sus exportaciones van a EE.UU., invisible en v1).
Se amplió el universo de partners a EE.UU., China, Alemania, Japón y Corea
del Sur, manteniendo los mismos 10 países como reporters. Todo el pipeline
(quiebres estructurales, forecasting, alerta) se re-corrió con la métrica
corregida, y se agregó un segundo indicador (riesgo crónico vs. riesgo de
cambio reciente) tras encontrar que México mostraba 0% de alerta pese a
tener el riesgo más alto — hallazgo que expuso la diferencia entre "nivel
absoluto de concentración" y "cambio respecto a la propia historia".
Datos extendidos de 2000-2024 a 2000-2026 (sujeto a disponibilidad real de
publicación de Comtrade para los años más recientes).
Ver `reports/informe_completo.pdf` para el detalle metodológico completo de v1.

## v1 — Red regional LatAm (2026-09)
Versión inicial: 10 países de LatAm, entropía de diversificación calculada
solo entre ellos, quiebres estructurales (sup-F + bootstrap + Bonferroni),
forecasting comparado (naive/ETS/ARIMA/bayesiano/XGBoost) con walk-forward
validation, y traducción a probabilidad de alerta vía la distribución
predictiva del forecast. Tag: `v1-regional-only`.
