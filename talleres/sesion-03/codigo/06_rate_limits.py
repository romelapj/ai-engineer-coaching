"""
Explicación 2/4 (Acto 2, Pilar de robustez). Rate limits: 429 vs 529 vs 500 vs 400

Del deck: "¿Es culpa tuya? No reintentes. ¿Es transitorio? Backoff."
Lee el encabezado anthropic-ratelimit-requests-remaining y frena antes del
429: el throttling proactivo gana al reactivo.

Tabla de decisión del deck:
    429 rate_limit_error     -> espera retry-after, luego backoff
    529 overloaded_error     -> backoff + jitter; degrada si persiste
    500 api_error            -> reintentar con backoff
    400 invalid_request_error -> NO reintentar, loguear y arreglar

Este archivo convierte esa tabla en código real y corre casos de prueba
para cada código, sin necesitar internet.

Cómo correrlo:
    python 06_rate_limits.py
"""

import time


def deberia_reintentar(codigo_http: int) -> bool:
    # Dado un código de error HTTP, decide si vale la pena reintentar la
    # llamada o si hay que rendirse de inmediato.
    if codigo_http == 429:
        # Superaste tu cuota (peticiones o tokens por minuto).
        return True  # Sí, pero respetando primero el retry-after del servidor.
    if codigo_http == 529:
        # La API está sobrecargada en general: no es culpa tuya.
        return True  # Sí, con espera creciente y aleatoriedad.
    if codigo_http == 500:
        # Error interno transitorio, normalmente se resuelve solo.
        return True  # Sí, suele resolverse en 1 o 2 intentos.
    if codigo_http == 400:
        # Tu petición está mal armada (falta un campo, JSON incorrecto...).
        return False  # NO: reintentar un bug propio solo lo hace más caro.
    # Para cualquier otro código no contemplado, por seguridad no
    # reintentamos automáticamente.
    return False


class FakeResponse:
    # Objeto simple para simular una respuesta HTTP real y poder mostrar
    # el "pro tip" de throttling proactivo sin conectarnos a internet.
    def __init__(self, restantes: int):
        self.headers = {"anthropic-ratelimit-requests-remaining": str(restantes)}


def frenar_si_hace_falta(response: FakeResponse):
    # Leemos del encabezado de la respuesta cuántas peticiones nos
    # quedan disponibles antes de tocar el límite.
    restantes = int(response.headers["anthropic-ratelimit-requests-remaining"])
    print(f"  peticiones restantes según el servidor: {restantes}")
    if restantes < 5:
        # Nos estamos quedando sin margen: frenamos por adelantado,
        # ANTES de que el servidor nos rechace con un 429.
        print("  -> quedan pocas: frenamos 1s de forma preventiva (throttling proactivo)")
        time.sleep(1)
    else:
        print("  -> hay margen de sobra, seguimos sin frenar")


def main():
    print("Tabla de decisión (código HTTP -> ¿reintentar?):\n")
    casos = [429, 529, 500, 400, 404]
    for codigo in casos:
        decision = "SÍ reintentar" if deberia_reintentar(codigo) else "NO reintentar"
        print(f"  {codigo} -> {decision}")

    print("\nThrottling proactivo con headers simulados:")
    print("caso A: quedan 20 peticiones")
    frenar_si_hace_falta(FakeResponse(restantes=20))
    print("caso B: quedan 3 peticiones")
    frenar_si_hace_falta(FakeResponse(restantes=3))


if __name__ == "__main__":
    main()
