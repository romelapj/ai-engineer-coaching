"""
Explicación 1/4 (Acto 2, Pilar de robustez). Retries: backoff exponencial + jitter

Del deck: trata al LLM como cualquier servicio externo: toda llamada de
red va a fallar tarde o temprano. Cien clientes fallando juntos y
reintentando exactamente a los 2 segundos crean una "retry storm"; el
jitter (aleatoriedad) los dispersa. NUNCA reintentes un 400 (tu request
está mal) ni un 401/403 (credenciales): solo hace el bug más caro.

Este archivo simula una llamada "inestable" que falla las primeras 2 veces
y responde bien a la tercera, para que veas con tus propios ojos los
tiempos de espera crecientes (backoff) y el hecho de que nunca son
exactamente iguales (jitter).

No necesita internet ni API key: la "llamada al modelo" está simulada
a propósito para poder provocar fallos a demanda.

Cómo correrlo:
    python 05_retries.py
"""

import random
import time
from collections import namedtuple


class ErrorTransitorio(Exception):
    # Un tipo de error propio para simular anthropic.RateLimitError /
    # InternalServerError / APITimeoutError sin depender de la librería real.
    pass


intentos_realizados = {"n": 0}


def llamada_inestable():
    # Simulamos una llamada al modelo que falla las primeras 2 veces
    # (como un 529 "overloaded_error" que se resuelve solo) y responde
    # bien en el tercer intento.
    intentos_realizados["n"] += 1
    if intentos_realizados["n"] < 3:
        raise ErrorTransitorio(f"servidor sobrecargado (intento {intentos_realizados['n']})")
    return {"texto": "¡respuesta exitosa del modelo!"}


def with_backoff(fn, max_retries=5):
    # Función "envoltorio": recibe OTRA función (fn) y la ejecuta con
    # reintentos automáticos si falla por un error transitorio.
    for attempt in range(max_retries):
        # Intentamos como máximo max_retries veces (0, 1, 2, 3, 4...).
        try:
            return fn()
            # Si fn() no lanza ningún error, devolvemos su resultado y
            # terminamos aquí mismo.
        except ErrorTransitorio as e:
            # Solo atrapamos errores transitorios: un 400 o 401 real
            # NO debería atraparse aquí, se debe dejar propagar siempre.
            print(f"  intento {attempt}: falló ({e})")
            if attempt == max_retries - 1:
                # Si este ya era el último intento permitido, dejamos
                # que el error se propague de verdad.
                raise
            espera = min(60, 2**attempt) * random.random()
            # 2**attempt duplica la espera "base" en cada vuelta
            # (1s, 2s, 4s, 8s...) sin pasar nunca de 60 segundos.
            # Multiplicar por random.random() (0.0 a 1.0) es el "jitter":
            # evita que muchos clientes esperen exactamente lo mismo.
            print(f"    esperando {espera:.2f}s antes de reintentar...")
            time.sleep(espera)


# --- Bonus del deck: run_tool_safe, la versión segura de ejecutar una tool ---

ToolOut = namedtuple("ToolOut", ["content", "failed"])


def run_tool_safe(nombre_tool, args, tools_disponibles):
    # Versión segura: si la tool lanza cualquier error inesperado, lo
    # atrapamos en vez de tumbar el resto del programa.
    try:
        fn = tools_disponibles[nombre_tool]
        return ToolOut(fn(**args), False)
    except Exception as e:
        return ToolOut({"error": str(e)}, True)


def main():
    print("Simulando una llamada que falla 2 veces y responde bien a la 3ra:\n")
    resultado = with_backoff(llamada_inestable)
    print("\nResultado final:", resultado)

    print("\n--- Bonus: run_tool_safe no tumba el programa ante un error ---")

    def tool_que_falla(x):
        raise ValueError("algo salió mal dentro de la tool")

    salida = run_tool_safe("mi_tool", {"x": 1}, {"mi_tool": tool_que_falla})
    print("salida:", salida)


if __name__ == "__main__":
    main()
