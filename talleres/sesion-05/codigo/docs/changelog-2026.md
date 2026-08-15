# Changelog 2026

Cambios publicados en la plataforma PagosYa durante 2026.

## Cambios de seguridad 2026

Desde enero de 2026 la versión mínima de TLS es 1.3; las conexiones TLS 1.2
entran en periodo de deprecación y serán rechazadas a partir de julio.
Además, las llaves de sandbox (`sk_test_`) ahora expiran automáticamente a
los 90 días de su creación para reducir el riesgo de llaves olvidadas.

## Nuevos endpoints 2026

En 2026 se lanzó el endpoint v3 de Checkout Lite, una versión reducida del
checkout pensada para integraciones móviles: menos campos, respuesta más
liviana y soporte nativo para Apple Pay y Google Pay. El endpoint v2
completo sigue siendo la opción recomendada para web.
