"""
Explicación 1/4 (Acto 1). La tool: "la descripción ES el prompt"

Del deck: el modelo solo ve tres cosas de cada tool: name, description e
input_schema. La calidad de sus decisiones depende más de qué tan buena es
la descripción que del código detrás. input_schema es JSON Schema: la firma
de la función traducida a un formato que el modelo entiende.

Este archivo NO llama a ningún modelo: solo arma la "ficha" que se le
enviaría, y prueba que la función real funciona. La llamada real ocurre en
02_el_loop.py.

Cómo correrlo:
    python 01_la_tool.py
"""

import json

# Creamos un diccionario: una tabla de dos columnas en memoria.
# La llave es el código de orden, el valor es su información.
ORDERS = {
    "ORD-8841": {"status": "shipped", "eta": "2026-07-04"},
    "ORD-9200": {"status": "processing", "eta": "2026-07-12"},
}


def get_order_status(order_id: str) -> dict:
    # Definimos una función normal de Python.
    # "order_id: str" avisa que espera texto; "-> dict" avisa que devuelve un diccionario.
    return ORDERS.get(order_id, {"error": "orden no existe"})
    # .get busca la llave en el diccionario. Si existe, la devuelve;
    # si no, devuelve un mensaje de error en su lugar.


# Creamos una lista con una "ficha" que describe la tool para el modelo.
# Esto no ejecuta nada por sí solo: es solo texto descriptivo (metadata).
tools = [
    {
        "name": "get_order_status",
        # El nombre exacto que el modelo usará para pedir esta tool.
        # Debe coincidir con el nombre real de la función de arriba.
        "description": (
            "Consulta el estado de una orden y su "
            "fecha estimada de entrega. Úsala siempre "
            "que el usuario pregunte por una orden. "
            "ID formato ORD-NNNN, p. ej. ORD-8841."
        ),
        # Este texto es EL PROMPT que realmente lee el modelo: explica
        # qué hace, cuándo usarla y da un ejemplo concreto del formato.
        "input_schema": {
            # Describimos, en formato estándar JSON Schema, qué datos debe
            # mandar el modelo si decide usar esta tool.
            "type": "object",
            # Los datos de entrada vienen agrupados como un "objeto"
            # (parecido a un diccionario de Python).
            "properties": {
                "order_id": {"type": "string"},
                # Existe un campo llamado "order_id" y su valor debe ser texto.
            },
            "required": ["order_id"],
            # Marcamos "order_id" como obligatorio: el modelo no puede
            # omitirlo al usar la tool.
        },
    }
]


def main():
    print("Esto es exactamente lo que el modelo 've' de la tool:\n")
    print(json.dumps(tools, indent=2, ensure_ascii=False))

    print("\nProbemos que la función real funciona, sin ningún modelo de por medio:")
    print("get_order_status('ORD-8841') ->", get_order_status("ORD-8841"))
    print("get_order_status('ORD-0000') ->", get_order_status("ORD-0000"))


if __name__ == "__main__":
    main()
