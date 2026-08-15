"""
Explicación 3 · Muestreo: temperature, max_tokens y stop_reason

Del deck: el modelo no elige "la" siguiente palabra. Calcula una
probabilidad para cada token posible y luego MUESTREA de esa distribución.
Los parámetros de muestreo controlan ese sorteo:

  temperature  escala la distribución antes de sortear. 0 = siempre el token
               más probable (reproducible); 1 = más variedad.
  max_tokens   es un tope DURO de salida. No es un objetivo: el modelo no
               intenta llenarlo. Pero si lo toca, corta a media frase.

Y stop_reason es el campo que te dice cuál de las dos cosas pasó.

Este archivo corre el mismo prompt tres veces con temperature 0 y tres con
temperature 1, para que veas la diferencia con tus ojos. Después provoca un
corte por max_tokens a propósito.

Cómo correrlo:
    python 02_muestreo.py
"""

import anthropic

client = anthropic.Anthropic()

MODELO = "claude-sonnet-4-6"
PROMPT = "Dame 3 nombres para una fintech de pagos en Latinoamérica. Solo los nombres."


def generar(temperature, max_tokens=200):
    resp = client.messages.create(
        model=MODELO,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[{"role": "user", "content": PROMPT}],
    )
    texto = "".join(b.text for b in resp.content if b.type == "text")
    return texto.strip(), resp.stop_reason, resp.usage.output_tokens


def main():
    # --- temperature 0: la misma entrada tiende a la misma salida ---------
    print("=== temperature = 0 (conservador) ===")
    for i in range(3):
        texto, _, _ = generar(temperature=0)
        print(f"  corrida {i + 1}: {texto.splitlines()[0][:60]}")

    # --- temperature 1: más variedad --------------------------------------
    print("\n=== temperature = 1 (creativo) ===")
    for i in range(3):
        texto, _, _ = generar(temperature=1)
        print(f"  corrida {i + 1}: {texto.splitlines()[0][:60]}")

    print(
        "\nCon temperature 0 las tres corridas se parecen mucho; con 1 se\n"
        "separan. Para clasificar o extraer datos quieres 0: si cada corrida\n"
        "diera algo distinto no podrías medir si tu prompt mejoró.\n"
        "OJO: ni temperature=0 garantiza salidas idénticas. El cálculo en\n"
        "GPU por lotes no es determinista. Diseña tests tolerantes."
    )

    # --- max_tokens: el corte silencioso ----------------------------------
    print("\n=== max_tokens = 10 (a propósito, demasiado bajo) ===")
    texto, motivo, salida = generar(temperature=0, max_tokens=10)
    print(f"  respuesta   : {texto!r}")
    print(f"  stop_reason : {motivo}")
    print(f"  output_tokens: {salida}")

    if motivo == "max_tokens":
        print(
            "\n  ↑ Ahí está el bug silencioso. La respuesta se cortó a media\n"
            "  frase y NADA falló: no hay excepción, no hay error HTTP.\n"
            "  Si no miras stop_reason, procesas una respuesta incompleta\n"
            "  como si estuviera entera. Por eso va en tus logs desde el día 1."
        )


if __name__ == "__main__":
    main()
