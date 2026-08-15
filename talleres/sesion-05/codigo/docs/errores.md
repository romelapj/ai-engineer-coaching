# Catálogo de errores de PagosYa

Cada error de negocio tiene un código propio con formato `E-XXXX`. Este
catálogo existe a propósito en esta sesión: ocho secciones que hablan casi
de lo mismo (errores de pago) son el terreno donde el vector search puro se
confunde y la búsqueda léxica (BM25) brilla.

## Error E-1001: petición malformada

El error `E-1001` indica que el cuerpo de la petición no cumple el esquema:
falta un campo obligatorio o un tipo de dato es incorrecto. El detalle
exacto viene en el campo `error.message`. No tiene sentido reintentar la
misma petición sin corregirla primero.

## Error E-2004: moneda no soportada

El error `E-2004` aparece cuando la moneda del pago no está habilitada para
tu cuenta. Las monedas activas se consultan en el dashboard, en la sección
Configuración > Monedas. Para habilitar una moneda nueva debes abrir un
ticket con el equipo de operaciones.

## Error E-3010: monto excede el límite

El error `E-3010` significa que el monto del pago supera el límite máximo
configurado para tu cuenta. El límite default es de 10.000 USD por
transacción y puede ampliarse con una verificación adicional de identidad
del comercio.

## Error E-4012: fondos insuficientes

El error `E-4012` es un rechazo del banco emisor por fondos insuficientes
en la cuenta del pagador. No es un error de tu integración. La práctica
recomendada es mostrarle al usuario un mensaje claro y ofrecerle pagar con
otro método; reintentar de inmediato casi siempre vuelve a fallar.

## Error E-4019: tarjeta vencida

El error `E-4019` indica que la tarjeta usada está vencida. Pide al usuario
una tarjeta vigente u otro método de pago. Este rechazo lo emite el banco
emisor, así que reintentar con la misma tarjeta siempre devuelve el mismo
error.

## Error E-4020: CVV inválido

El error `E-4020` significa que el código de seguridad (CVV) no coincide.
Permite al usuario reintentar escribiéndolo de nuevo, pero bloquea el
formulario después de 3 intentos fallidos: más intentos disparan las reglas
antifraude del emisor.

## Error E-5001: timeout del emisor

El error `E-5001` ocurre cuando el banco emisor no respondió a tiempo. Es
un error transitorio: es seguro reintentar la operación usando la misma
`Idempotency-Key` para no duplicar el cobro. Recomendamos máximo 2
reintentos con espera de 5 segundos.

## Error E-7777: rechazo por riesgo

El error `E-7777` es un bloqueo del motor antifraude de PagosYa. Por
seguridad no se informa el motivo específico. NO debes reintentar la
operación: reintentos repetidos de un pago bloqueado por riesgo pueden
llevar a la suspensión temporal de la cuenta del comercio.
