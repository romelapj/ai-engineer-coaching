# 🏋️ Kata 05 — Entradas malas, errores específicos

| Metadato                | Valor                                                                                                  |
| ----------------------- | ------------------------------------------------------------------------------------------------------ |
| **Fase**                | Pre-Fase 0.5 — Fundamentos de Python                                                                   |
| **Sesión en que se asigna** | Sesión N04                                                                                          |
| **Tiempo estimado**     | 45–60 min                                                                                               |
| **Skill que entrena**   | `try`/`except`/`else`/`finally`, capturar tipos concretos, `raise` con excepción propia, EAFP, jerarquía de excepciones |
| **Stack**               | Python 3.10+ (stdlib), `pytest`. **Sin** librerías externas                                            |

---

## Contexto

El manejo de errores es donde se nota, en cinco líneas de código, si quien lo escribió entiende Python o solo lo tolera. El anti-patrón clásico —el que cualquier reviewer marca de inmediato— es el "manejo por superstición": un `try/except Exception: pass` envolviendo media función "por si acaso". Ese bloque se traga el error real, oculta la línea que falló, y convierte un bug de cinco minutos en una sesión de depuración a ciegas. Si vienes de un lenguaje con `checked exceptions` (Java) o con un patrón de `error como valor de retorno` (Go), tu instinto te va a empujar a comprobar todo antes de actuar o a capturar de más; en Python idiomático eso casi siempre es ruido.

Python tiene una filosofía propia que esta kata te obliga a internalizar: **EAFP** — _Easier to Ask Forgiveness than Permission_. En lugar de `if not es_entero(x): ...` (LBYL, _Look Before You Leap_), intentas `int(x)` y capturas el `ValueError` concreto cuando no lo es. Es más limpio, evita condiciones de carrera, y captura exactamente el caso que sabes manejar — ni más, ni menos. La regla de oro es **scope mínimo y tipo concreto**: el `try` envuelve la línea que puede fallar, no el bloque entero; el `except` nombra `ValueError`, no `Exception`.

Lo otro que entrena esta kata es **construir tu propio vocabulario de errores**. Una función de producción no relanza el `ValueError` crudo de `int()` hacia arriba: lo traduce a una excepción de tu dominio (`ValidacionError`) que el código que llama puede capturar con intención, **preservando la causa original** con `raise ... from e` para no perder el rastro. Vas a hacer las tres cosas: capturar tipos concretos, definir y lanzar una excepción propia con causa encadenada, y acumular fallos sin que el primero tumbe el lote.

## Enunciado

Construye, en un solo archivo `solution.py`, un **mini-validador de formularios** que ejercita el manejo de errores en sus tres formas. No hay archivos ni I/O: es la mecánica pura de excepciones sobre un dominio pequeño y real (campos de un formulario que llegan como texto y pueden venir mal).

Primero define tu excepción de dominio:

```python
class ValidacionError(Exception):
    pass
```

Luego implementa tres funciones:

### 1. `parsear_edad(valor) -> int`

Recibe la edad como viene de un formulario (un `str`) y devuelve el entero. Reglas:

- Si `valor` no representa un entero (`"abc"`, `"3.5"`, `""`), lanza `ValidacionError` con un mensaje útil que incluya el valor ofensor.
- Debes **capturar el `ValueError` que lanza `int(valor)`** y relanzar como `ValidacionError` usando `raise ... from e` para preservar la causa.
- Si el entero es **negativo**, lanza `ValidacionError` (una edad negativa no es válida). Aquí no hay `ValueError` que capturar: es una regla de dominio, la validas y lanzas tú.

```python
>>> parsear_edad("30")
30
>>> parsear_edad("abc")
ValidacionError: edad inválida: 'abc' no es un entero
>>> parsear_edad("-5")
ValidacionError: edad inválida: -5 es negativa
```

### 2. `procesar_lote(valores) -> dict`

Recibe una lista de edades crudas y procesa **todas**, sin que una mala detenga el resto. Devuelve:

```python
{"validas": list[int], "errores": list[str]}
```

Las que parsean bien van a `"validas"`; por cada una que falle, acumula su mensaje de error en `"errores"`. La función **nunca propaga** una `ValidacionError` hacia afuera: la captura dentro del loop y la convierte en una entrada de la lista de errores.

```python
>>> procesar_lote(["20", "x", "30", "-1"])
{"validas": [20, 30], "errores": ["edad inválida: 'x' no es un entero",
                                  "edad inválida: -1 es negativa"]}
```

### 3. `dividir_seguro(a, b) -> float`

Divide `a / b`, pero **captura el `ZeroDivisionError`** y lo traduce a `ValidacionError("no se puede dividir por cero")`. EAFP en su forma más pura: no compruebes `if b == 0` — intenta la división y captura el tipo concreto cuando falla.

```python
>>> dividir_seguro(10, 2)
5.0
>>> dividir_seguro(10, 0)
ValidacionError: no se puede dividir por cero
```

## Requisitos

1. **Excepción propia**: define `ValidacionError(Exception)` en `solution.py`. Todas tus funciones lanzan ese tipo, nunca el `ValueError`/`ZeroDivisionError` crudo hacia el llamador.
2. **Tipos concretos en cada `except`**: captura `ValueError` y `ZeroDivisionError` por nombre. Prohibido `except Exception` (o `except:` pelado) en cualquiera de las tres funciones.
3. **Causa encadenada**: la `ValidacionError` que nace de un `int()` fallido debe usar `raise ValidacionError(...) from e`, de modo que su `__cause__` sea el `ValueError` original.
4. **Scope mínimo**: el `try` envuelve solo la operación que puede fallar (la conversión, la división), no toda la función.
5. **EAFP, no LBYL**: en `parsear_edad` y `dividir_seguro`, intenta y captura; no uses `str.isdigit()` ni `if b == 0` como guardia preventiva para el caso que el `except` ya cubre. (La regla de negocio de "edad negativa" sí es un `if` legítimo — esa no la cubre ningún `except`.)
6. **Acumulación sin reventar**: `procesar_lote` recorre toda la lista; un fallo va a `"errores"` y el loop continúa. No uses `except` fuera del loop que aborte el resto.
7. **Sin I/O ni librerías externas**: solo stdlib y `pytest` para los tests.

## Criterios de aceptación

- [ ] `parsear_edad("30") == 30`; `parsear_edad("abc")` lanza `ValidacionError`; `parsear_edad("-5")` lanza `ValidacionError`.
- [ ] La `ValidacionError` de `parsear_edad("abc")` **preserva la causa**: su `__cause__` es una instancia de `ValueError` (efecto del `raise ... from e`).
- [ ] `parsear_edad("-5")` lanza `ValidacionError` cuyo `__cause__` es `None` (es regla de dominio, no nace de un `ValueError` capturado).
- [ ] `procesar_lote(["20", "x", "30", "-1"]) == {"validas": [20, 30], "errores": [<2 mensajes, en orden>]}` y **no** propaga excepción.
- [ ] `dividir_seguro(10, 2) == 5.0`; `dividir_seguro(10, 0)` lanza `ValidacionError`.
- [ ] **Code review**: cada `except` nombra un tipo concreto (`ValueError`, `ZeroDivisionError`). Cero `except Exception` / `except:` pelados en las tres funciones.
- [ ] `pytest -q` pasa todos los tests en verde.

## Cómo se evalúa

El harness es `pytest`. Usa `pytest.raises(ValidacionError)` para los casos malos, inspecciona `excinfo.value.__cause__` para verificar el `raise ... from`, y compara el `dict` de `procesar_lote` contra un golden inline. Los datos golden están escritos directamente en el test (no hay fixtures externas): lo que entra y exactamente qué sale.

Esqueleto de `test_solution.py` (este es el harness, no la solución):

```python
import pytest
from solution import ValidacionError, parsear_edad, procesar_lote, dividir_seguro


def test_parsea_entero_valido():
    assert parsear_edad("30") == 30


@pytest.mark.parametrize("malo", ["abc", "3.5", ""])
def test_no_entero_lanza_validacion_error(malo):
    with pytest.raises(ValidacionError):
        parsear_edad(malo)


def test_negativo_lanza_validacion_error():
    with pytest.raises(ValidacionError):
        parsear_edad("-5")


def test_causa_encadenada_en_no_entero():
    with pytest.raises(ValidacionError) as excinfo:
        parsear_edad("abc")
    assert isinstance(excinfo.value.__cause__, ValueError)  # raise ... from e


def test_negativo_no_encadena_value_error():
    with pytest.raises(ValidacionError) as excinfo:
        parsear_edad("-5")
    assert excinfo.value.__cause__ is None  # regla de dominio, no ValueError


def test_procesar_lote_acumula_sin_reventar():
    resultado = procesar_lote(["20", "x", "30", "-1"])
    assert resultado["validas"] == [20, 30]
    assert len(resultado["errores"]) == 2
    assert all(isinstance(m, str) for m in resultado["errores"])


def test_procesar_lote_todas_validas():
    assert procesar_lote(["1", "2", "3"]) == {"validas": [1, 2, 3], "errores": []}


def test_division_normal():
    assert dividir_seguro(10, 2) == 5.0


def test_division_por_cero_lanza_validacion_error():
    with pytest.raises(ValidacionError):
        dividir_seguro(10, 0)
```

En la revisión, el coach va a abrir tu `solution.py` y leer los `except`. Si encuentra un `except Exception` o un `try` que envuelve toda la función en vez de solo la línea que puede fallar, cuenta como hallazgo aunque los tests pasen en verde — el objetivo de la kata es el _scope_ y el _tipo_, no solo el resultado.

## Pistas

<details><summary>Pista 1 — Definir tu excepción y lanzarla con causa</summary>

Una excepción propia es literalmente una clase vacía que hereda de `Exception`:

```python
class ValidacionError(Exception):
    pass
```

Para preservar la causa cuando relanzas, usa `from`:

```python
try:
    n = int(valor)
except ValueError as e:
    raise ValidacionError(f"edad inválida: {valor!r} no es un entero") from e
```

El `from e` es lo que hace que `nueva_excepcion.__cause__` apunte al `ValueError` original. Sin él, el `__cause__` queda en `None` y pierdes el rastro de qué falló por debajo. El `!r` en el f-string te da las comillas (`'abc'`) gratis.

</details>

<details><summary>Pista 2 — EAFP vs. la regla de dominio (cuándo SÍ va un if)</summary>

Distingue dos cosas que parecen iguales pero no lo son:

- **"¿es un entero?"** → no lo compruebes con `isdigit()`; deja que `int()` lo intente y captura el `ValueError`. EAFP. (Bonus: `"-5".isdigit()` es `False`, así que `isdigit` ni siquiera te serviría para negativos — otra razón para no usarlo.)
- **"¿es negativo?"** → aquí no hay ninguna excepción que capturar; el `int()` ya tuvo éxito. La regla "edad ≥ 0" es lógica de tu dominio, así que un `if n < 0: raise ValidacionError(...)` es lo correcto y lo idiomático. No todo se resuelve con `try`.

El patrón completo: primero el `try/except` para la conversión, y _después_ (en el camino feliz, ya con el `int` en mano) el `if` de la regla de negocio.

</details>

<details><summary>Pista 3 — `procesar_lote` acumulando sin reventar (casi-spoiler)</summary>

El truco es poner el `try/except` **dentro** del loop, capturando tu propia `ValidacionError` (la que ya lanza `parsear_edad`), no el `ValueError` crudo. Así cada elemento se procesa de forma aislada:

```python
def procesar_lote(valores):
    validas, errores = [], []
    for v in valores:
        try:
            validas.append(parsear_edad(v))
        except ValidacionError as e:
            errores.append(str(e))
    return {"validas": validas, "errores": errores}
```

Fíjate: reutilizas `parsear_edad` (no repites la lógica de parseo), capturas `ValidacionError` (tu tipo, no `Exception`), y el `except` está dentro del `for`, así que el fallo de un elemento no aborta los demás. `str(e)` recupera el mensaje que pusiste al construir la `ValidacionError`.

</details>

## Bonus

1. **`finally` con un contador**: agrega un cuarto helper que use `try/except/else/finally` completo —por ejemplo, un `parsear_edad_con_log(valor, log: list)` que en `else` agregue `"ok"` al log, en `except` agregue `"fail"`, y en `finally` incremente un contador de intentos— para sentir las cuatro ramas. ¿Cuándo corre `else` y cuándo no? (Pista: `else` corre solo si el `try` no lanzó.)
2. **Mensajes accionables**: haz que cada `ValidacionError` incluya el índice del elemento en `procesar_lote` (`"[idx 1] edad inválida: 'x' no es un entero"`) usando `enumerate`. En producción, un mensaje que dice _dónde_ falló vale el doble.
3. **Jerarquía de excepciones**: divide `ValidacionError` en dos subclases (`TipoInvalidoError`, `RangoInvalidoError`) que heredan de ella, y lánzalas según el caso. El llamador puede capturar la base `ValidacionError` para atrapar ambas, o una específica para distinguir — demuestra para qué sirve una jerarquía.

## Qué demuestra

Que manejas errores **por diseño, no por superstición**: capturas el tipo concreto que sabes manejar y nada más, con el `try` ceñido a la línea que falla. Que sabes construir tu propio vocabulario de errores —una excepción de dominio— y relanzarla **preservando la causa** con `raise ... from`, en vez de filtrar errores crudos de la stdlib hacia el código que te llama. Que distingues cuándo EAFP gana (probar y capturar la conversión) de cuándo una regla de negocio pide un `if` explícito (la edad negativa). Y que sabes **acumular fallos** procesando un lote entero sin que el primer error tumbe el resto — el patrón exacto que usarás en cualquier pipeline que procese registros en producción. Es fluidez en el modelo de excepciones de Python, no memorización de sintaxis.

## Entregable

**Al repo** (carpeta `gym/kata-05-errores-robustos/` de tu repo de soluciones):

- `solution.py` con `ValidacionError`, `parsear_edad`, `procesar_lote` y `dividir_seguro`.
- `test_solution.py` con los tests (puedes partir del esqueleto de arriba y ampliarlo; los golden van inline).
- Opcional: lo que hayas hecho de los bonus, claramente separado.

**En la sesión de revisión** (5 minutos, comparte pantalla):

1. Corre `pytest -q` en verde sobre las tres funciones (1 min).
2. Abre `solution.py` y justifica cada `except`: qué tipo capturas y por qué no `Exception` (2 min).
3. Explica por qué la edad negativa va con `if` y no con `try`, y qué hace exactamente el `from e` en el `__cause__` (2 min).