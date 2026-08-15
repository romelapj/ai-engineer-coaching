# Guía de Webhooks

Cómo funcionan las notificaciones asíncronas (webhooks) que PagosYa envía
a tu servidor.

## Configuración de webhooks

Los webhooks se configuran en el dashboard, en la sección Desarrolladores >
Webhooks. Debes registrar una URL HTTPS pública; las URLs HTTP sin
certificado son rechazadas. Puedes registrar hasta 5 endpoints distintos
por cuenta, y elegir para cada uno qué eventos quieres recibir (por ejemplo
`payment.approved`, `payment.declined` o `refund.completed`).

## Verificación de firma

Cada webhook incluye el header `X-Signature` con un HMAC-SHA256 del cuerpo
de la petición, firmado con tu webhook secret. Siempre verifica esta firma
antes de procesar el evento: es la única forma de garantizar que la
notificación realmente viene de PagosYa y no de un atacante. El webhook
secret es distinto de tu API key y se muestra una sola vez al crear el
endpoint.

## Reintentos de entrega

Si tu servidor no responde con un código 2xx en menos de 10 segundos,
PagosYa reintenta la entrega del webhook hasta 8 veces durante las
siguientes 24 horas, con esperas crecientes entre intentos. Después del
octavo intento fallido el evento se marca como no entregado y puedes
recuperarlo manualmente desde el dashboard durante los siguientes 30 días.
