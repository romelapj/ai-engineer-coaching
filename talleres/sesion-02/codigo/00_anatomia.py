"""
Explicación 1. La anatomía de un request

Del deck: toda llamada a la API tiene las mismas piezas, y cada una decide
algo distinto del resultado. No son parámetros que se copian de un tutorial:
system define QUIÉN es el modelo, messages QUÉ se le pide, temperature
CUÁNTA libertad tiene y max_tokens DÓNDE se corta.

Este archivo hace una sola llamada y muestra, además del texto, los datos de
uso que casi nadie mira la primera vez (tokens y stop_reason).

Cómo correrlo:
    python 00_anatomia.py
"""

import anthropic  # El SDK oficial: pip install anthropic

# Anthropic() sin argumentos lee la variable de entorno ANTHROPIC_API_KEY.
# La llave nunca se escribe dentro del código: termina en git y de ahí no sale.
client = anthropic.Anthropic()

response = client.messages.create(
    # QUÉ modelo. Cambiarlo cambia precio, velocidad y calidad, en ese orden
    # de impacto sobre tu factura.
    model="claude-sonnet-4-6",
    # CUÁNTA libertad tiene para elegir la siguiente palabra. 0 = siempre la
    # más probable (reproducible); 1 = más variedad. Para clasificar o
    # extraer datos quieres números bajos; para redactar, altos.
    temperature=0.2,
    # DÓNDE se corta la respuesta. Es un tope de seguridad, no un objetivo:
    # el modelo no intenta llenarlo. Pero si lo alcanza, la respuesta queda
    # truncada a media frase; por eso más abajo miramos stop_reason.
    max_tokens=1024,
    # QUIÉN es el modelo: rol, reglas y tono. Va en su propio parámetro, no
    # dentro de messages, y pesa más que una instrucción suelta del usuario.
    system=(
        "Eres un analista de soporte de una pasarela de pagos. "
        "Clasificas reclamos de clientes. "
        "Responde solo en JSON válido, sin explicaciones ni comentarios."
    ),
    # QUÉ se le pide. Es una lista de turnos que se alternan user/assistant
    # y SIEMPRE termina en un turno "user".
    messages=[
        {"role": "user", "content": "Clasifica este reclamo: 'Me cobraron doble'"},
    ],
)

# La respuesta llega como una lista de bloques; el texto está en el primero.
print("--- lo que respondió el modelo ---")
print(response.content[0].text)

# Estos tres datos son los que vas a querer en tus logs desde el primer día.
print("\n--- los datos que casi nadie mira ---")
print("stop_reason  :", response.stop_reason)
# "end_turn" = terminó porque quiso. "max_tokens" = lo cortaste tú, y la
# respuesta está incompleta aunque parezca entera.
print("input_tokens :", response.usage.input_tokens)
print("output_tokens:", response.usage.output_tokens)
# Ahí vive la factura. Los tokens de entrada se pagan en CADA llamada, y en
# una conversación larga son casi todo el costo.
