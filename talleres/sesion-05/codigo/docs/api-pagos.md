# Guía de la API de Pagos

Documentación interna de la API de pagos de la empresa ficticia "PagosYa".
Misma base de conocimiento de la sesión 04, ampliada para esta sesión.

## Autenticación

Todas las peticiones a la API de PagosYa requieren una API key en el header
`X-Api-Key`. Las API keys se generan desde el dashboard, en la sección
Configuración > Credenciales. Existen dos tipos de llaves: las de sandbox
(prefijo `sk_test_`) y las de producción (prefijo `sk_live_`). Nunca uses
llaves de producción en ambientes de prueba. Si una llave se filtra, puedes
rotarla desde el dashboard sin downtime: la llave anterior sigue siendo
válida durante 24 horas después de la rotación.

## Timeouts y reintentos

El timeout default de la API es de 30 segundos por petición. Si tu cliente
necesita un límite más corto, puedes enviar el header `X-Timeout-Ms` con un
valor entre 1000 y 30000 milisegundos. Para operaciones de creación de pago
recomendamos configurar reintentos con backoff exponencial: máximo 3
reintentos, empezando con una espera de 2 segundos. Todas las operaciones
de escritura aceptan el header `Idempotency-Key` para evitar cobros
duplicados cuando reintentas una petición.

## Límites de tasa

El rate limit es de 100 peticiones por minuto por API key. Si lo superas,
la API responde con un código HTTP 429 y el header `Retry-After` indica
cuántos segundos debes esperar antes del siguiente intento. Los límites se
calculan por ventana deslizante de 60 segundos, no por minuto de reloj.
