"""
Explicación 6. Un prompt sin medir es una opinión

Del deck: "mejoré el prompt" no significa nada si no puedes decir cuánto.
Antes de tocar una palabra, necesitas un conjunto de casos con la respuesta
correcta escrita a mano (el golden set) y un número.

Diez casos ya sirven. No hace falta un dataset: hacen falta los diez casos
que de verdad te confunden.

Este archivo mide la versión 1 del prompt: la que escribirías sin pensarlo
mucho. Guarda el número que salga, porque el archivo siguiente lo va a usar.

Cómo correrlo:
    python 05_eval_v1.py
"""

import json
from pathlib import Path

import anthropic

client = anthropic.Anthropic()

# Versión 1 del prompt: instrucciones y ya. Nada de ejemplos, nada de
# estructura. Es el punto de partida honesto.
PROMPT_V1 = (
    "Clasifica el reclamo en una de las siguientes clases: "
    "fraud, duplicated, not_received, other. "
    "Responde solo el valor de la clase, sin nada adicional."
)


def cargar_casos():
    # El golden set vive en un archivo aparte, no dentro del código: así se
    # le pueden agregar casos sin tocar la lógica de evaluación.
    ruta = Path(__file__).parent / "golden.json"
    return json.loads(ruta.read_text(encoding="utf-8"))["test_cases"]


def clasificar(reclamo):
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        temperature=0,  # Sin esto, dos corridas dan números distintos y no
        # sabrías si mejoró el prompt o si tuviste suerte.
        max_tokens=100,
        system=PROMPT_V1,
        messages=[{"role": "user", "content": f"Clasifica el reclamo: '{reclamo}'"}],
    )
    # .strip().lower() para que "Duplicated\n" cuente igual que "duplicated".
    # Esa limpieza a mano es el síntoma de una salida sin estructura.
    return resp.content[0].text.strip().lower()


def main():
    casos = cargar_casos()
    aciertos = 0
    fallos = []

    print(f"Evaluando el prompt v1 contra {len(casos)} casos...\n")

    for caso in casos:
        prediccion = clasificar(caso["claim"])
        ok = prediccion == caso["expected_class"]
        aciertos += ok

        marca = "✓" if ok else "✗"
        print(f"{marca} [{caso['id']:2}] esperaba {caso['expected_class']:13} → {prediccion!r}")
        if not ok:
            fallos.append(caso)

    print(f"\nExactitud v1: {aciertos}/{len(casos)} = {aciertos / len(casos):.0%}")

    if fallos:
        print("\nLos que falló (aquí es donde se decide el próximo cambio):")
        for c in fallos:
            print(f"  [{c['id']}] {c['claim']}")


if __name__ == "__main__":
    main()
