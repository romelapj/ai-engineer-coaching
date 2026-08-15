"""
Explicación 2. Multi-turn: la API no tiene memoria

Del deck: la API es SIN ESTADO. No recuerda nada de la llamada anterior. Si
quieres que el modelo "recuerde" algo, tienes que volver a mandárselo entero
en cada petición. Eso tiene dos consecuencias que sorprenden:

  1. La conversación es una lista que TÚ mantienes y haces crecer.
  2. Los tokens de entrada crecen en cada turno, y se pagan cada vez.

Y trae un regalo: si tú escribes los turnos del "assistant", puedes ponerle
en la boca la respuesta que quieres que imite. Eso es few-shot barato.

Cómo correrlo:
    python 01_multi_turn.py
"""

import anthropic

client = anthropic.Anthropic()

SYSTEM = (
    "Eres un experto en identificar montos y monedas dentro de texto libre. "
    "Responde solo en JSON válido, sin explicaciones ni comentarios."
)


def extraer(messages):
    # Una sola función que manda la lista de turnos tal cual se la pasen y
    # devuelve el texto de la respuesta.
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        temperature=0,  # Extraer datos es tarea determinista: temperature 0.
        max_tokens=1024,
        system=SYSTEM,
        messages=messages,
    )
    return resp.content[0].text, resp.usage.input_tokens


def main():
    # --- Turno 1: la conversación empieza con un solo mensaje --------------
    messages = [
        {"role": "user", "content": "Extrae el monto: 'pagué 45.000 COP'"},
    ]
    texto, tokens = extraer(messages)
    print("Turno 1")
    print("  respuesta     :", texto)
    print("  input_tokens  :", tokens)

    # --- Turno 2: aquí está el punto de la sesión -------------------------
    # Para que el modelo "recuerde" el turno anterior, se lo volvemos a
    # mandar ENTERO: su propia respuesta incluida, como turno "assistant".
    messages.append({"role": "assistant", "content": texto})
    messages.append({"role": "user", "content": "Ahora: 'me cobraron veinte dólares'"})

    texto_2, tokens_2 = extraer(messages)
    print("\nTurno 2 (mandando los 3 mensajes anteriores otra vez)")
    print("  respuesta     :", texto_2)
    print("  input_tokens  :", tokens_2)
    print(f"  → la entrada creció {tokens_2 - tokens} tokens respecto al turno 1")

    # El modelo acertó el formato del turno 2 sin que se lo explicáramos:
    # copió la forma de su propia respuesta anterior. Eso es few-shot
    # implícito, y es la razón por la que a veces un bug de formato se
    # "contagia" a todos los turnos siguientes de una conversación.


if __name__ == "__main__":
    main()
