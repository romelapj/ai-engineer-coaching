"""
Explicación 4. Few-shot: los ejemplos mandan más que las instrucciones

Del deck: puedes escribir tres párrafos explicando qué es un reclamo
"duplicated" y el modelo seguirá dudando. Le muestras dos ejemplos y acierta.
Los ejemplos son instrucciones ejecutables: no describen el criterio, lo
demuestran.

Regla práctica: 3-5 ejemplos, cubriendo los casos que de verdad te confunden
a ti. Un ejemplo por clase "fácil" no aporta nada; el que vale es el del caso
límite.

Este archivo corre el MISMO reclamo con y sin ejemplos, para que veas la
diferencia en la misma corrida.

Cómo correrlo:
    python 03_few_shot.py
"""

import anthropic

client = anthropic.Anthropic()

# --- Versión A: solo instrucciones -----------------------------------------
SIN_EJEMPLOS = """Clasifica el reclamo en una de estas clases:
fraud, duplicated, not_received, other.
Responde solo con el nombre de la clase."""

# --- Versión B: las mismas instrucciones + ejemplos -------------------------
# Los <example> van dentro de etiquetas XML porque le marcan al modelo dónde
# empieza y termina cada uno. Sin delimitadores, un ejemplo largo se confunde
# con la instrucción que va antes.
CON_EJEMPLOS = """Clasifica el reclamo en una de estas clases:
fraud, duplicated, not_received, other.
Responde solo con el nombre de la clase.

<examples>
<example>
texto: Me sacaron el pago dos veces el mismo día
clase: duplicated
</example>
<example>
texto: El pago salió pero nunca recibí el pedido
clase: not_received
</example>
<example>
texto: Yo no hice esa compra
clase: fraud
</example>
<example>
texto: ¿A qué hora abren?
clase: other
</example>
</examples>"""


def clasificar(system_prompt, reclamo):
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        temperature=0,  # Determinista: queremos comparar prompts, no suerte.
        max_tokens=100,  # La respuesta es una palabra; no hace falta más.
        system=system_prompt,
        messages=[{"role": "user", "content": f"Clasifica: '{reclamo}'"}],
    )
    return resp.content[0].text.strip()


def main():
    # Un caso deliberadamente ambiguo: menciona un cobro repetido, pero la
    # palabra "duplicated" no aparece por ningún lado.
    reclamo = "Vi que me habían cobrado dos veces por el mismo producto"
    print(f"Reclamo: {reclamo!r}\n")

    print("A) Solo instrucciones")
    print("   →", clasificar(SIN_EJEMPLOS, reclamo))

    print("\nB) Instrucciones + 4 ejemplos")
    print("   →", clasificar(CON_EJEMPLOS, reclamo))

    print(
        "\nEn un caso fácil las dos aciertan y parece que los ejemplos sobran.\n"
        "El día 6 vas a medir las dos versiones contra 10 casos reales, y ahí\n"
        "es donde la diferencia deja de ser una opinión."
    )


if __name__ == "__main__":
    main()
