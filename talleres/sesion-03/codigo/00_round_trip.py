"""
Explicación 0: La anatomía del round-trip (4 fases)

Del deck: sin herramientas, el modelo solo puede rendirse ("no tengo acceso
a tus órdenes") o alucinar ("tu orden llega mañana"). Tool use es el arreglo:
el modelo DECIDE qué hacer, tu código LO HACE. El intercambio siempre tiene
4 fases: pide -> ejecutas -> devuelves -> respondes.

Este archivo NO llama a ningún modelo real ni necesita internet: es una
simulación para entender la FORMA del proceso antes de ver la API de verdad
en 02_el_loop.py.

Cómo correrlo:
    python 00_round_trip.py
"""


class Peticion:
    # "class" crea una plantilla reutilizable. Aquí definimos cómo se ve
    # "lo que el modelo pide hacer": el nombre de la tool + los datos que quiere pasarle.
    def __init__(self, nombre_tool, argumentos):
        # Esta receta se ejecuta cada vez que creamos una Peticion nueva.
        self.nombre_tool = nombre_tool  # Guardamos el nombre de la tool pedida, ej: "get_order_status".
        self.argumentos = argumentos    # Guardamos los datos que el modelo quiere entregarle a esa tool.


def modelo_decide(pregunta_usuario):
    # Función que simula lo que haría el modelo de IA: decidir qué tool necesita, SIN ejecutar nada.
    if "orden" in pregunta_usuario:
        # Si el usuario menciona la palabra "orden" en su pregunta...
        return Peticion("get_order_status", {"order_id": "ORD-8841"})
        # ...el modelo "pide" usar la tool de órdenes con ese identificador.
    return None
    # Si no aplica ninguna tool, el modelo no pide nada especial.


def ejecutar_tool(peticion):
    # Esta función representa a "tu código": la única parte que de verdad ejecuta acciones.
    if peticion.nombre_tool == "get_order_status":
        # Miramos qué tool pidió el modelo.
        return {"status": "shipped", "eta": "2026-07-04"}
        # Simulamos lo que traería una base de datos real: estado y fecha de entrega.
    return {"error": "tool no reconocida"}


def main():
    pregunta = "¿Dónde va mi orden ORD-8841?"
    # Este texto representa lo que escribió la persona usuaria.
    print(f"Usuario pregunta: {pregunta}\n")

    # FASE 1 (PIDE): el modelo decide qué tool necesita (no la ejecuta).
    paso_1 = modelo_decide(pregunta)
    print("FASE 1 (pide)     ->", paso_1.nombre_tool, paso_1.argumentos)

    # FASE 2 (EJECUTAS): tu código corre la función de verdad.
    # El modelo NUNCA ejecuta nada, solo emitió la intención en la fase anterior.
    paso_2 = ejecutar_tool(paso_1)
    print("FASE 2 (ejecutas) ->", paso_2)

    # FASE 3 (DEVUELVES): empaquetamos el resultado con un id para que el
    # modelo sepa a qué petición corresponde (tool_use_id en la API real).
    paso_3 = {"tool_use_id": "abc123", "content": paso_2}
    print("FASE 3 (devuelves) ->", paso_3)

    # FASE 4 (RESPONDE): con el resultado ya disponible, el modelo arma la
    # respuesta final para la persona usuaria.
    paso_4 = f"Tu orden está '{paso_2['status']}' y llega el {paso_2['eta']}."
    print("FASE 4 (responde) ->", paso_4)


if __name__ == "__main__":
    # Esto significa: "si este archivo se ejecuta directamente (no si otro
    # archivo lo importa), corre la función main()".
    main()
