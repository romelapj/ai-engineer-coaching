"""
Explicación 3. Streaming: latencia percibida vs latencia real

Del deck: el streaming NO hace la respuesta más rápida. La respuesta completa
tarda exactamente lo mismo. Lo que cambia es CUÁNDO ve algo el usuario: en vez
de mirar un spinner 8 segundos, lee la primera palabra a los 0.4.

Las dos métricas que importan tienen nombre:
  TTFT (time to first token) : cuánto tarda en aparecer la primera palabra.
  Total                      : cuánto tarda la respuesta entera.

Este archivo mide las dos en la misma llamada, para que veas la diferencia
con tus propios números.

Cómo correrlo:
    python 02_streaming.py
"""

import time

import anthropic

client = anthropic.Anthropic()

SYSTEM = "Responde en al menos 3 párrafos, en español."


def main():
    print("Pidiendo una respuesta larga en streaming...\n")

    t0 = time.monotonic()  # Reloj que solo avanza: el correcto para medir.
    ttft = None
    trozos = 0

    # stream() abre la conexión y va entregando la respuesta por pedazos.
    # El "with" garantiza que la conexión se cierra aunque algo falle.
    with client.messages.stream(
        model="claude-sonnet-4-6",
        temperature=1,
        max_tokens=1024,
        system=SYSTEM,
        messages=[
            {"role": "user", "content": "Resume por qué el streaming mejora la UX."},
        ],
    ) as stream:
        for texto in stream.text_stream:
            # Este bucle se ejecuta una vez por cada pedazo que llega.
            if ttft is None:
                # La primera vuelta es el momento exacto en que el usuario
                # dejaría de mirar un spinner. Se mide una sola vez.
                ttft = time.monotonic() - t0
            trozos += 1
            print(texto, end="", flush=True)
            # flush=True fuerza a que se pinte YA. Sin él, Python guarda el
            # texto en un buffer y lo suelta todo junto al final, que es
            # justamente lo que estamos intentando evitar.

        # Al terminar, el SDK te arma el mensaje completo con sus metadatos.
        final = stream.get_final_message()

    total = time.monotonic() - t0

    print("\n\n--- las dos latencias ---")
    print(f"TTFT (primera palabra) : {ttft:.2f}s")
    print(f"Total (respuesta entera): {total:.2f}s")
    print(f"Trozos recibidos        : {trozos}")
    print(f"Tokens de salida        : {final.usage.output_tokens}")
    print(
        f"\nEl usuario esperó {ttft:.2f}s para ver algo, no {total:.2f}s. "
        f"La respuesta tardó lo mismo: solo cambió la espera percibida."
    )


if __name__ == "__main__":
    main()
