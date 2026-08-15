# Changelog 2025

Cambios publicados en la plataforma PagosYa durante 2025. Este documento y
su gemelo de 2026 existen para la demo de metadata filtering: la misma
pregunta ("¿qué TLS exige la API?") tiene respuestas DISTINTAS según el
año, y solo el filtro de metadata garantiza recuperar la correcta.

## Cambios de seguridad 2025

Desde marzo de 2025 la API exige TLS 1.2 como versión mínima; las
conexiones con TLS 1.1 o inferior son rechazadas con un error de handshake.
Además, las API keys de producción comprometidas ahora se pueden revocar de
inmediato desde el dashboard sin esperar el periodo de gracia.

## Nuevos endpoints 2025

En 2025 se lanzó la versión v2 del endpoint de Checkout, que unifica la
creación del pago y la sesión de checkout en una sola llamada. La versión
v1 quedó marcada como obsoleta y dejará de recibir mejoras, aunque seguirá
funcionando hasta nuevo aviso.
