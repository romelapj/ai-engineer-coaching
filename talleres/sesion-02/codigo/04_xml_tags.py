"""
Explicación 5. Estructura con etiquetas XML

Del deck: cuando un prompt mezcla instrucciones, datos del usuario y formato
de salida en un solo bloque de texto, el modelo tiene que adivinar dónde
termina una cosa y empieza la otra. Las etiquetas XML se lo dicen.

Y hay una razón de seguridad además de la de claridad: si el texto del
usuario va dentro de <claim>, una frase como "ignora las instrucciones
anteriores" queda claramente marcada como DATO, no como instrucción. No es
blindaje, pero sube mucho el listón.

Este archivo extrae varios campos de un reclamo y valida que la respuesta sea
JSON de verdad.

Cómo correrlo:
    python 04_xml_tags.py
    python 04_xml_tags.py "El domiciliario nunca llegó y me cobraron 50000"
"""

import json
import sys

import anthropic

client = anthropic.Anthropic()

# Si pasas un texto por la terminal se usa ese; si no, uno de ejemplo.
# sys.argv es la lista de lo que escribiste: [nombre_del_script, primer_argumento, ...]
texto_usuario = (
    sys.argv[1]
    if len(sys.argv) > 1
    else "Vi que me habían cobrado dos veces por el mismo producto"
)

# Cada sección del prompt va en su propia etiqueta. El modelo no tiene que
# deducir la estructura: se la damos hecha.
PROMPT = f"""<instructions>
Extrae los campos del reclamo. Responde SOLO con JSON válido:
sin markdown, sin backticks, sin texto adicional.
Si un campo no aparece en el reclamo, usa null.
</instructions>

<claim>
{texto_usuario}
</claim>

<classes>
- "fraud": cargo no autorizado o engaño del comercio
- "duplicated": cobrado dos veces por lo mismo
- "not_received": pagó pero el producto nunca llegó
- "other": cualquier otra cosa
</classes>

<format>
{{
  "type": "fraud|duplicated|not_received|other",
  "amount": null,
  "currency": null,
  "urgency": false
}}
</format>"""


def main():
    print(f"Reclamo: {texto_usuario!r}\n")

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        temperature=0.2,
        max_tokens=1024,
        messages=[{"role": "user", "content": PROMPT}],
    )
    crudo = resp.content[0].text

    # NUNCA confíes en que el texto es JSON solo porque lo pediste. Este
    # try/except es la diferencia entre un error claro y un crash raro tres
    # capas más arriba.
    try:
        datos = json.loads(crudo)
    except json.JSONDecodeError:
        print("El modelo NO devolvió JSON válido. Esto fue lo que mandó:")
        print(crudo)
        return

    print("JSON válido, ya como diccionario de Python:")
    print(json.dumps(datos, indent=2, ensure_ascii=False))
    print("\nAcceso por campo:")
    print("  type    :", datos["type"])
    print("  amount  :", datos["amount"])
    print("  currency:", datos["currency"])

    print(
        "\nEsto funciona casi siempre, y 'casi' es el problema. En la sesión 03\n"
        "vas a ver cómo tool_choice convierte este 'casi' en una garantía."
    )


if __name__ == "__main__":
    main()
