"""
Explicación 4/4 (Acto 1): JSON garantizado con tool_choice + Pydantic

Del deck: antes se extraía JSON con prompts, parsing tolerante y "rezos".
Ahora tool_choice OBLIGA al modelo a llamar una tool específica: el input
de esa tool ES tu JSON. Pydantic valida además reglas de negocio (tipos,
campos). Con 2-3 reintentos reinyectando el error, se corrige la mayoría
de outputs inválidos.

Este archivo llama al modelo real, lo obliga a usar la tool
"save_case_summary" y valida su respuesta con Pydantic.

Cómo correrlo:
    python 04_json_garantizado.py
"""

import anthropic
from pydantic import BaseModel, ValidationError

client = anthropic.Anthropic()


class CaseSummary(BaseModel):
    # Definimos la forma exacta del resumen final, heredando de BaseModel
    # (la clase base de Pydantic que sabe validar tipos y campos).
    order_id: str  # Debe existir y debe ser texto.
    status: str  # Debe existir y debe ser texto.
    next_action: str  # Debe existir y debe ser texto.


# Armamos una tool cuyo único propósito es "guardar" datos con esa forma.
# input_schema se genera automáticamente a partir de la clase de arriba:
# no hace falta escribir el JSON Schema a mano.
summary_tool = {
    "name": "save_case_summary",
    "description": "Guarda el resumen final del caso de soporte.",
    "input_schema": CaseSummary.model_json_schema(),
}


def main():
    messages = [
        {
            "role": "user",
            "content": (
                "Resume este caso de soporte: la orden ORD-8841 ya fue "
                "enviada y llega el 2026-07-04. El cliente pregunta si "
                "necesita hacer algo más. Guarda el resumen del caso."
            ),
        }
    ]

    summary = None
    for attempt in range(3):
        # Intentamos hasta 3 veces conseguir un resumen válido, por si
        # el modelo se equivoca en el formato la primera vez.
        print(f"intento {attempt}: llamando al modelo (tool_choice forzado)...")

        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            tools=[summary_tool],
            # Con esto OBLIGAMOS al modelo a usar exactamente esta tool:
            # no puede responder con texto libre.
            tool_choice={"type": "tool", "name": "save_case_summary"},
            messages=messages,
        )

        # Buscamos el primer pedazo de la respuesta que sea una petición
        # de tool (sabemos que va a existir, por el tool_choice forzado).
        block = next(b for b in resp.content if b.type == "tool_use")
        print("  el modelo mandó este input:", block.input)

        try:
            # Le pedimos a Pydantic que revise los datos del modelo y
            # confirme que cumplen la forma esperada de CaseSummary.
            summary = CaseSummary.model_validate(block.input)
            print("  ✓ validación OK")
            break
        except ValidationError as err:
            print("  ✗ validación falló:", err)
            # Guardamos en el historial el intento fallido del modelo,
            # tal como vino.
            messages.append({"role": "assistant", "content": resp.content})
            # Le devolvemos al modelo el error exacto, marcado como
            # is_error, para que lo corrija en el siguiente intento.
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Corrige y reintenta: {err}",
                            "is_error": True,
                        }
                    ],
                }
            )

    print("\n=== RESUMEN VALIDADO (objeto Python real, no texto suelto) ===")
    print(summary)
    print("order_id  :", summary.order_id)
    print("status    :", summary.status)
    print("next_action:", summary.next_action)


if __name__ == "__main__":
    main()
