"""
Explicación 7. Prompts versionados: v1 contra v2, con números

Del deck: los prompts son código. Viven en el repo, tienen versión, y cuando
cambias uno demuestras que mejoró en vez de afirmarlo. La v2 de aquí junta
todo lo del taller: ejemplos (día 4), etiquetas XML (día 5) y salida JSON.

Este archivo corre LAS DOS versiones sobre el mismo golden set y las compara.
Ese es el entregable de la semana: no un prompt mejor, sino la evidencia de
que lo es.

Cuesta 2 llamadas por caso (una por versión). Con 10 casos son 20 llamadas
baratas.

Cómo correrlo:
    python 06_eval_v2.py
"""

import json
from pathlib import Path

import anthropic

client = anthropic.Anthropic()

# --- v1: la del archivo anterior, tal cual ----------------------------------
PROMPT_V1 = (
    "Clasifica el reclamo en una de las siguientes clases: "
    "fraud, duplicated, not_received, other. "
    "Responde solo el valor de la clase, sin nada adicional."
)

# --- v2: ejemplos + estructura + salida JSON --------------------------------
PROMPT_V2 = """Clasificas reclamos de una pasarela de pagos.
Responde SOLO con JSON válido: sin markdown, sin backticks, sin texto extra.

<classes>
- "fraud": cargo no autorizado o engaño del comercio
- "duplicated": cobrado dos veces por lo mismo
- "not_received": pagó pero el producto nunca llegó
- "other": consultas y gestiones que no son un cobro mal hecho
</classes>

<examples>
<example>
reclamo: Me sacaron el pago dos veces el mismo día
respuesta: {"class": "duplicated"}
</example>
<example>
reclamo: El pago salió pero nunca recibí el pedido
respuesta: {"class": "not_received"}
</example>
<example>
reclamo: Yo no hice esa compra
respuesta: {"class": "fraud"}
</example>
<example>
reclamo: ¿Cómo cambio mi dirección de envío?
respuesta: {"class": "other"}
</example>
</examples>

<format>
{"class": "fraud|duplicated|not_received|other"}
</format>"""


def cargar_casos():
    ruta = Path(__file__).parent / "golden.json"
    return json.loads(ruta.read_text(encoding="utf-8"))["test_cases"]


def clasificar_v1(reclamo):
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        temperature=0,
        max_tokens=100,
        system=PROMPT_V1,
        messages=[{"role": "user", "content": f"Clasifica el reclamo: '{reclamo}'"}],
    )
    # Salida sin estructura: hay que limpiarla a mano y cruzar los dedos.
    return resp.content[0].text.strip().lower()


def clasificar_v2(reclamo):
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        temperature=0,
        max_tokens=100,
        system=PROMPT_V2,
        messages=[{"role": "user", "content": f"<claim>{reclamo}</claim>"}],
    )
    crudo = resp.content[0].text.strip()
    try:
        # Salida con estructura: se lee un campo, no se adivina.
        return json.loads(crudo)["class"].strip().lower()
    except (json.JSONDecodeError, KeyError):
        # Si aun así no vino JSON, lo registramos como fallo explícito en vez
        # de rescatarlo con parsing tolerante: queremos que se note.
        return f"<no-json: {crudo[:30]}>"


def evaluar(nombre, funcion, casos):
    # Corre una versión del prompt sobre todos los casos y devuelve cuántos
    # acertó y cuáles falló.
    aciertos, fallos = 0, []
    for caso in casos:
        prediccion = funcion(caso["claim"])
        ok = prediccion == caso["expected_class"]
        aciertos += ok
        if not ok:
            fallos.append((caso, prediccion))
    print(f"{nombre}: {aciertos}/{len(casos)} = {aciertos / len(casos):.0%}")
    return aciertos, fallos


def main():
    casos = cargar_casos()
    print(f"Comparando dos versiones del prompt sobre {len(casos)} casos.\n")

    aciertos_v1, fallos_v1 = evaluar("v1 (solo instrucciones)     ", clasificar_v1, casos)
    aciertos_v2, fallos_v2 = evaluar("v2 (ejemplos + XML + JSON)  ", clasificar_v2, casos)

    delta = aciertos_v2 - aciertos_v1
    print(f"\nDiferencia: {delta:+d} casos")
    if delta > 0:
        print("La v2 gana. Ese '+' es lo que justifica el cambio en el PR.")
    elif delta == 0:
        print(
            "Empate. Y eso también es un resultado: significa que el golden set\n"
            "es demasiado fácil y no distingue las dos versiones. Agrega casos\n"
            "límite hasta que las separe."
        )
    else:
        print("La v2 empeoró. Revierte y quédate con la v1: para eso se mide.")

    for nombre, fallos in (("v1", fallos_v1), ("v2", fallos_v2)):
        if fallos:
            print(f"\nFallos de {nombre}:")
            for caso, prediccion in fallos:
                print(f"  [{caso['id']}] esperaba {caso['expected_class']} → {prediccion!r}")
                print(f"       {caso['claim']}")


if __name__ == "__main__":
    main()
