"""
Explicación 3/4 (Acto 1): Tool calls en paralelo

Del deck: "Compara mis órdenes ORD-8841 y ORD-9200" trae dos bloques
tool_use en un solo turno. Regla de oro: responde TODOS en un solo mensaje
user. Ejecuta las tools de forma concurrente (ThreadPoolExecutor o
asyncio.gather): 3 tools de 2s -> ~2s total, no 6s. Si una falla, no
rompas el lote: devuélvela marcada con is_error.

Este archivo llama al modelo real y pide algo que dispara DOS tool_use al
mismo tiempo. Cada tool simulada tarda 2 segundos (time.sleep) para que se
note la diferencia entre ejecutar en serie vs en paralelo.

Cómo correrlo:
    python 03_paralelo.py
"""

import json
import time
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor

import anthropic

client = anthropic.Anthropic()

ORDERS = {
    "ORD-8841": {"status": "shipped", "eta": "2026-07-04"},
    "ORD-9200": {"status": "processing", "eta": "2026-07-12"},
}


def get_order_status(order_id: str) -> dict:
    time.sleep(2)  # Simulamos una consulta lenta (ej. una base de datos real).
    return ORDERS.get(order_id, {"error": "orden no existe"})


TOOLS = {"get_order_status": get_order_status}

tools = [
    {
        "name": "get_order_status",
        "description": (
            "Consulta el estado de una orden y su fecha estimada de "
            "entrega. Úsala siempre que el usuario pregunte por una "
            "orden. ID formato ORD-NNNN, p. ej. ORD-8841."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
    }
]

# Empaquetamos el resultado de una tool junto con si falló o no,
# para poder marcar "is_error" sin romper el resto del lote.
ToolOut = namedtuple("ToolOut", ["content", "failed"])


def run_tool_safe(block) -> ToolOut:
    # Versión segura: si la tool lanza cualquier error inesperado, lo
    # atrapamos en vez de tumbar el programa entero.
    try:
        fn = TOOLS[block.name]
        resultado = fn(**block.input)
        return ToolOut(json.dumps(resultado, ensure_ascii=False), False)
    except Exception as e:
        return ToolOut(json.dumps({"error": str(e)}), True)


def main():
    messages = [
        {
            "role": "user",
            "content": "Compara mis órdenes ORD-8841 y ORD-9200, ¿cuál llega primero?",
        }
    ]

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        tools=tools,
        messages=messages,
    )

    # De la respuesta del modelo, nos quedamos solo con los pedazos que
    # son peticiones de tool. Puede haber más de una en la misma respuesta.
    calls = [b for b in resp.content if b.type == "tool_use"]
    print(f"El modelo pidió {len(calls)} tool(s) en un solo turno:")
    for b in calls:
        print(f"  -> {b.name}({b.input})  [id={b.id}]")

    print("\nEjecutando en PARALELO con ThreadPoolExecutor...")
    t0 = time.monotonic()
    with ThreadPoolExecutor() as ex:
        # Le pedimos al grupo de hilos que ejecute run_tool_safe sobre
        # cada petición, todas a la vez en paralelo.
        outs = list(ex.map(run_tool_safe, calls))
    elapsed_parallel = time.monotonic() - t0
    print(f"Tiempo en paralelo: {elapsed_parallel:.1f}s "
          f"(en serie habría tardado ~{2 * len(calls)}s)")

    # zip empareja cada petición original con su resultado, uno a uno,
    # en el mismo orden.
    results = [
        {
            "type": "tool_result",
            "tool_use_id": b.id,
            "content": out.content,
            "is_error": out.failed,
        }
        for b, out in zip(calls, outs)
    ]

    messages.append({"role": "assistant", "content": resp.content})
    # TODOS los tool_use del turno se responden en UN solo mensaje user
    # (regla de oro del deck). Si falta uno, el siguiente turno da 400.
    messages.append({"role": "user", "content": results})

    resp_final = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        tools=tools,
        messages=messages,
    )
    print("\n=== RESPUESTA FINAL DEL MODELO ===")
    print("".join(b.text for b in resp_final.content if b.type == "text"))


if __name__ == "__main__":
    main()
