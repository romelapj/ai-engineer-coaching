"""
Explicación 4/4 (Acto 2, Pilar de robustez): Logging exhaustivo

Del deck: mínimo por llamada: request_id (lo que soporte de Anthropic pide
para investigar), tokens de entrada/salida (ahí vive la factura),
stop_reason (si es "max_tokens", la respuesta quedó truncada en silencio),
latencia y número de intentos. En DEBUG puedes guardar el payload
completo (sin PII); en INFO solo las métricas. Eso es lo que va a prod.

Este archivo hace UNA llamada real al modelo (barata, max_tokens chico),
envuelta en el with_backoff del pilar 1, y registra en el log exactamente
los datos que el deck pide.

Cómo correrlo:
    python 08_logging.py
"""

import logging
import random
import time

import anthropic

client = anthropic.Anthropic()

# Configuramos el sistema de logs para que muestre, como mínimo, mensajes
# de nivel INFO (información general, no solo errores).
logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")
log = logging.getLogger("tool_loop")
# Creamos un "registrador" con nombre propio, para identificar de dónde
# vienen estos mensajes si el programa tiene más partes.


def with_backoff(fn, max_retries=5):
    # El mismo wrapper de reintentos del Pilar 1 (backoff exponencial + jitter).
    for attempt in range(max_retries):
        try:
            return fn()
        except (
            anthropic.RateLimitError,
            anthropic.InternalServerError,
            anthropic.APITimeoutError,
        ):
            if attempt == max_retries - 1:
                raise
            time.sleep(min(60, 2**attempt) * random.random())


def main():
    t0 = time.monotonic()
    # Guardamos el instante exacto (un reloj que solo avanza) justo
    # antes de hacer la llamada, para poder medir la latencia real después.

    resp = with_backoff(
        lambda: client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=100,
            messages=[{"role": "user", "content": "Responde en una sola frase: ¿qué es tool use?"}],
        )
    )

    latencia = time.monotonic() - t0

    # Registramos en el log todo lo que necesitaríamos para investigar un
    # problema a las 3 a.m., SIN el contenido completo de la respuesta
    # (eso iría solo en DEBUG, no en INFO).
    log.info(
        "llm_call request_id=%s model=%s stop_reason=%s in_tok=%d out_tok=%d latency_s=%.2f",
        resp._request_id,
        resp.model,
        resp.stop_reason,
        resp.usage.input_tokens,
        resp.usage.output_tokens,
        latencia,
    )

    if resp.stop_reason == "max_tokens":
        # Si esto pasa, la respuesta quedó truncada en silencio: el
        # deck insiste en vigilar este caso porque es fácil de pasar por alto.
        log.warning("¡la respuesta se truncó por max_tokens! considera subir el límite")

    print("\nTexto de la respuesta (esto sí iría en DEBUG, no en INFO):")
    print("".join(b.text for b in resp.content if b.type == "text"))


if __name__ == "__main__":
    main()
