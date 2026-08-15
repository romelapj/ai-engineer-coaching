"""
Explicación 2 · El Token-ó-metro: ¿cuánto me va a costar esto?

Del deck: el ejercicio de la sesión. Un CLI que responde una pregunta que
vas a hacerte en cada proyecto: "¿cuánto cuesta esto, en cada modelo?".

La idea de fondo: elegir modelo no es elegir "el mejor". Es elegir el más
barato que resuelve TU tarea con la calidad que necesitas. Y eso no se
decide leyendo un blog: se decide midiendo tu propio prompt.

Este archivo mide un prompt real contra tres modelos y proyecta el gasto a
100.000 peticiones al mes.

Cómo correrlo:
    python 01_tokenometro.py
    python 01_tokenometro.py "tu propio texto aquí"
"""

import sys

import anthropic

client = anthropic.Anthropic()

# Precios en dólares por MILLÓN de tokens, a agosto de 2026.
# OJO: esta tabla caduca. Los precios cambian y salen modelos nuevos, así
# que la lección no es memorizarla, es tenerla en UN solo sitio del código
# y saber dónde verificarla: platform.claude.com/docs/en/about-claude/models
PRECIOS = {
    # modelo                 entrada  salida   contexto
    "claude-haiku-4-5":     (  1.00,   5.00,  "200K"),
    "claude-sonnet-4-6":    (  3.00,  15.00,  "1M"),
    "claude-opus-4-8":      (  5.00,  25.00,  "1M"),
}

# Cuántas peticiones al mes esperas. Cambia este número por el tuyo: es la
# diferencia entre "da igual el modelo" y "esto no cabe en el presupuesto".
PETICIONES_MES = 100_000

# Cuántos tokens esperas que responda el modelo. La salida cuesta 5x la
# entrada, así que estimarla mal es el error más caro de la tabla.
TOKENS_SALIDA_ESTIMADOS = 300


def contar_entrada(texto, modelo):
    # El conteo es específico del modelo: el mismo texto puede dar números
    # distintos en modelos distintos, así que se cuenta con cada uno.
    resp = client.messages.count_tokens(
        model=modelo,
        messages=[{"role": "user", "content": texto}],
    )
    return resp.input_tokens


def costo(tokens_entrada, tokens_salida, precio_entrada, precio_salida):
    # Los precios vienen por millón de tokens: dividimos entre 1.000.000
    # para obtener el costo de UNA petición.
    return (
        tokens_entrada * precio_entrada / 1_000_000
        + tokens_salida * precio_salida / 1_000_000
    )


def main():
    # Si pasas un texto por la terminal se usa ese; si no, uno de ejemplo.
    texto = (
        sys.argv[1]
        if len(sys.argv) > 1
        else (
            "Clasifica este reclamo de un cliente en una de estas categorías: "
            "fraude, cobro duplicado, pedido no recibido, otro. "
            "Reclamo: 'Vi que me habían cobrado dos veces por el mismo producto'."
        )
    )

    print(f"Prompt de {len(texto)} caracteres")
    print(f"Proyección: {PETICIONES_MES:,} peticiones/mes, "
          f"{TOKENS_SALIDA_ESTIMADOS} tokens de salida estimados\n")

    print(f"{'modelo':22} {'ctx':>5} {'tok_in':>7} {'$/petición':>12} {'$/mes':>10}")
    print("-" * 60)

    for modelo, (precio_in, precio_out, contexto) in PRECIOS.items():
        tokens_in = contar_entrada(texto, modelo)
        por_peticion = costo(tokens_in, TOKENS_SALIDA_ESTIMADOS, precio_in, precio_out)
        al_mes = por_peticion * PETICIONES_MES
        print(
            f"{modelo:22} {contexto:>5} {tokens_in:>7} "
            f"{por_peticion:>12.6f} {al_mes:>10,.0f}"
        )

    print(
        "\nMira la columna de la derecha, no la del medio. Un decimal de\n"
        "diferencia por petición son miles de dólares al mes. Y al revés:\n"
        "para una tarea simple, pagar el modelo más caro es tirar dinero."
    )
    print(
        "\nLa pregunta correcta no es '¿cuál es el mejor modelo?' sino\n"
        "'¿cuál es el más barato que resuelve MI tarea?'. Eso se responde\n"
        "midiendo, que es justo lo que vas a hacer en la sesión 02."
    )


if __name__ == "__main__":
    main()
