"""
Explicación 2/4 (Acto 1). El loop: tool_use -> tool_result

Del deck: el modelo responde con un bloque tool_use cuando quiere ejecutar
algo (stop_reason == "tool_use"). Tu código corre la función real y
devuelve el resultado como tool_result, enlazado por tool_use_id. El ciclo
se repite hasta que el modelo responde con texto normal.

Este archivo SÍ llama al modelo de verdad (usa tu ANTHROPIC_API_KEY del
entorno). Vas a ver impreso, paso a paso, cada fase del round-trip real.

Cómo correrlo:
    python 02_el_loop.py
"""

import json

import anthropic

# Creamos un "cliente": el objeto que sabe enviar y recibir mensajes
# del servicio de Anthropic. Lee la API key de la variable de entorno
# ANTHROPIC_API_KEY automáticamente.
client = anthropic.Anthropic()

# Nuestra "base de datos" falsa en memoria.
ORDERS = {"ORD-8841": {"status": "shipped", "eta": "2026-07-04"}}


def get_order_status(order_id: str) -> dict:
    return ORDERS.get(order_id, {"error": "orden no existe"})


# Diccionario que conecta el NOMBRE de la tool (texto) con la FUNCIÓN
# real de Python que hay que correr cuando el modelo la pida.
TOOLS = {"get_order_status": get_order_status}

tools = [
    {
        "name": "get_order_status",
        "description": (
            "Consulta el estado de una orden y su "
            "fecha estimada de entrega. Úsala siempre "
            "que el usuario pregunte por una orden. "
            "ID formato ORD-NNNN, p. ej. ORD-8841."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
    }
]


def run_tool(name: str, args: dict) -> str:
    # Recibe el nombre de una tool pedida y sus argumentos, y decide
    # qué función de Python ejecutar de verdad.
    fn = TOOLS.get(name)
    if fn is None:
        # Si el modelo se inventó una tool que no existe, no tumbamos
        # el programa: devolvemos un error en texto JSON.
        return json.dumps({"error": f"tool desconocida: {name}"})
    return json.dumps(fn(**args), ensure_ascii=False)
    # Ejecutamos la función real con sus argumentos y convertimos el
    # resultado a texto JSON para poder enviarlo de vuelta al modelo.


def main():
    # El historial de la conversación arranca con un solo mensaje:
    # la pregunta de la persona usuaria.
    messages = [{"role": "user", "content": "¿Dónde va mi orden ORD-8841?"}]

    for turno in range(10):
        # Repetimos hasta 10 veces como máximo, para no quedar atrapados
        # en un ciclo infinito si algo sale mal. "El presupuesto va en
        # el código, no en un TODO" (regla del deck).
        print(f"\n--- turno {turno}: llamando al modelo real ---")

        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            tools=tools,
            messages=messages,
        )
        print("stop_reason:", resp.stop_reason)

        if resp.stop_reason != "tool_use":
            # El modelo terminó con una respuesta normal, sin pedir tool.
            break

        # Si SÍ pidió una tool, guardamos ese turno completo del modelo
        # en el historial, tal cual vino (error clásico #1: olvidar esto).
        messages.append({"role": "assistant", "content": resp.content})

        results = []
        for b in resp.content:
            if b.type == "tool_use":
                print(f"  el modelo PIDE -> {b.name}({b.input})")
                salida = run_tool(b.name, b.input)
                print(f"  tu código EJECUTA y responde -> {salida}")
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": b.id,
                        # content va serializado con json.dumps, nunca
                        # un dict crudo (error clásico #2 del deck).
                        "content": salida,
                    }
                )

        # Agregamos los resultados al historial como mensaje "user",
        # así lo exige la API.
        messages.append({"role": "user", "content": results})

    texto_final = "".join(b.text for b in resp.content if b.type == "text")
    print("\n=== RESPUESTA FINAL DEL MODELO ===")
    print(texto_final)


if __name__ == "__main__":
    main()
