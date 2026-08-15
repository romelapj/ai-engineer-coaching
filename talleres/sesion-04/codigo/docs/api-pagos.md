# Guía de la API de Pagos

Documentación interna de la API de pagos de la empresa ficticia "PagosYa".
Este archivo es la "base de conocimiento" que el pipeline RAG va a ingestar.

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

## Códigos de error

La API usa códigos HTTP estándar. Un `400` indica que la petición está mal
formada (revisa el campo `error.message` para el detalle). Un `401` indica
API key inválida o expirada. Un `429` significa que superaste el rate limit:
el límite es de 100 peticiones por minuto por API key, y la respuesta
incluye el header `Retry-After` con los segundos a esperar. Los errores
`5xx` son fallas del lado de PagosYa y es seguro reintentarlos con la misma
`Idempotency-Key`.
