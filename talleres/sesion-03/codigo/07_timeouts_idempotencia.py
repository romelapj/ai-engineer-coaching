"""
Explicación 3/4 (Acto 2, Pilar de robustez): Timeouts e idempotencia

Del deck: el default del SDK es 10 minutos de espera, una eternidad para
un chat interactivo. Pero un timeout NO garantiza que la petición falló:
pudo completarse igual en segundo plano. Reintentar una tool que cobra
dinero o envía un correo puede duplicar el efecto. Diseña primero: tools
de solo lectura cuando se pueda, y separa "proponer" de "confirmar".

Este archivo (1) construye un cliente real de Anthropic con timeout y
max_retries configurados (sin llamar a la red, solo para mostrar la
configuración), y (2) simula, sin necesitar internet, cómo una guarda de
idempotencia evita cobrar dos veces por un reintento.

Cómo correrlo:
    python 07_timeouts_idempotencia.py
"""

import anthropic

# --- Parte 1: el cliente bien configurado ---

client = anthropic.Anthropic(timeout=30.0, max_retries=4)
# timeout=30.0  -> si una llamada no responde en 30 segundos, se cancela
#                  sola (el default son 10 minutos, demasiado para un chat).
# max_retries=4 -> el propio SDK reintentará hasta 4 veces solo, además
#                  de cualquier with_backoff propio que le pongamos encima.

print("Cliente configurado:")
print("  timeout     =", client.timeout)
print("  max_retries =", client.max_retries)

# --- Parte 2: guarda de idempotencia contra el "efecto doble" ---

procesados = set()
# Un conjunto (una lista que no permite duplicados) donde anotamos qué
# operaciones ya se ejecutaron.


def cobrar_una_vez(operacion_id: str, monto: float) -> dict:
    # Función segura para cobrar dinero: recibe un identificador único de
    # la operación y el monto a cobrar.
    if operacion_id in procesados:
        # Antes de cobrar, preguntamos: ¿esta operación ya se procesó
        # antes (por ejemplo, en un intento anterior tras un timeout)?
        return {"status": "ya procesado, no se repite el cobro", "monto": 0}
    procesados.add(operacion_id)
    # Si es la primera vez, anotamos que esta operación ya se está
    # procesando, ANTES de devolver el resultado.
    return {"status": "cobro realizado", "monto": monto}


def main():
    print("\nSimulando: la llamada al modelo tardó y tu código reintentó,")
    print("pero la tool 'cobrar' ya se había ejecutado en el intento anterior.\n")

    op_id = "orden-ORD-8841-cobro-1"

    print("intento 1 (llamada original):")
    print(" ", cobrar_una_vez(op_id, 49.90))

    print("intento 2 (reintento por timeout, MISMO operacion_id):")
    print(" ", cobrar_una_vez(op_id, 49.90))

    print("\nSin esta guarda, el segundo intento habría cobrado 49.90 de nuevo.")


if __name__ == "__main__":
    main()
