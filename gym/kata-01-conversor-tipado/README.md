# 🏋️ Kata 01 — Conversor de unidades tipado

| Metadato                  | Valor                                                                                                          |
| ------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Fase**                  | Pre-Fase 0.5 — Fundamentos de Python                                                                            |
| **Sesión en que se asigna** | Sesión N01                                                                                                     |
| **Tiempo estimado**       | 45–60 min                                                                                                      |
| **Skill que entrena**     | Conversión explícita entre `str` y números, truthiness, f-strings con formato, redondeo, casos borde de entrada |
| **Stack**                 | Python 3.10+ stdlib, `pytest`. **Sin** librerías de formato externas                                            |

---

## Contexto

El error fundacional que delata a un dev que "sabe programar" pero no domina Python es **no distinguir tipos**: comparar `'500' >= '400'` como si fueran números (y obtener el resultado correcto por pura casualidad léxica), o asumir que un campo que "se ve numérico" ya es un `int`. En lenguajes con tipado estático el compilador te frena; en Python no hay nadie que te avise hasta que `'9' < '10'` te devuelve `False` en producción.

Si vienes de Java, C# o Go, tu instinto es que la conversión "pasa sola" o que el tipo está declarado. En Python la conversión es **una decisión que tomas tú, explícitamente, en el momento exacto en que el dato cruza la frontera del mundo real hacia tu lógica**. Los datos llegan como `str` —desde un input, un CSV, un query param, un JSON laxo— a veces vacíos, a veces con espacios sobrantes. Tu trabajo es convertir a propósito con `int()`/`float()`, calcular sobre números de verdad, y formatear la salida con f-strings.

Esta kata aísla justo eso sobre un dominio mínimo y real: **un conversor de unidades** (temperaturas y distancias). No hay logs, no hay framework, no hay nada que esconda la decisión de tipo. Es pequeño a propósito, para que el único músculo que entrenes sea la frontera entre tratar un texto como texto y convertirlo, a conciencia, en un número.

## Enunciado

Implementa en `solution.py` tres funciones. Los valores de entrada llegan **como llegan del mundo real**: a veces `str`, a veces ya numéricos, a veces vacíos o con espacios.

### 1. `c_a_f(celsius) -> float`

Convierte grados Celsius a Fahrenheit con la fórmula `F = C * 9/5 + 32`. Debe aceptar **tanto `'37.5'` (str) como `37.5` (float)** y redondear a **1 decimal**.

```python
c_a_f('37')    # -> 98.6
c_a_f(100.0)   # -> 212.0
```

### 2. `km_a_millas(km) -> float`

Convierte kilómetros a millas (`1 km = 0.621371 millas`), análoga a la anterior, redondeada a **2 decimales**.

```python
km_a_millas('10')   # -> 6.21
km_a_millas(0)      # -> 0.0
```

### 3. `formatear_tabla(filas) -> str`

Recibe una lista de tuplas `(etiqueta, valor, unidad)` y devuelve un `str` con las columnas alineadas mediante f-strings:

- **etiqueta**: alineada a la izquierda, ancho 12 (`:<12`).
- **valor**: alineado a la derecha, 2 decimales, ancho 8 (`:>8.2f`).
- **unidad**: tal cual, después del valor (precedida de un espacio).

Cada fila es una línea; las filas se unen con `\n` (sin salto final).

### Ejemplo entrada → salida

**Entrada:**

```python
formatear_tabla([
    ("Temperatura", 98.6, "F"),
    ("Distancia", 6.21, "millas"),
])
```

**Salida** (la cadena exacta, donde `␣` representa un espacio):

```
Temperatura␣␣␣␣␣␣98.60 F
Distancia␣␣␣␣␣␣␣␣␣6.21 millas
```

Es decir: `"Temperatura "` ocupa 12 caracteres (1 espacio de relleno), `"   98.60"` ocupa 8, luego `" F"`. La segunda línea: `"Distancia   "` son 12 caracteres (3 de relleno), `"    6.21"` son 8, luego `" millas"`.

### La regla que no puedes romper

Las conversiones deben usar `int()`/`float()` **de forma explícita** y **nunca** comparar ni operar `str` como si fueran números. Si te descubres escribiendo `if valor >= '0'` o sumando strings, paraste de entender el ejercicio.

## Requisitos

1. **`c_a_f(celsius)`** acepta `str` o numérico, convierte explícitamente con `float()`, aplica la fórmula y retorna un `float` redondeado a 1 decimal.
2. **`km_a_millas(km)`** acepta `str` o numérico, convierte con `float()`, retorna un `float` redondeado a 2 decimales.
3. **`formatear_tabla(filas)`** formatea con f-strings (`:<12`, `:>8.2f`), una línea por fila, unidas con `\n` y **sin** salto de línea final.
4. **Tipos de retorno reales**: las dos conversiones retornan `float` (no `str`, no `Decimal`), verificable con `isinstance`.
5. **Entrada inválida ruidosa**: pasar una cadena no numérica (`''`, `'abc'`, `'  '`) a una conversión debe **dejar subir el `ValueError`** de `float()` — no lo silencies, no lo conviertas en `0`, no lo envuelvas en un `None`.
6. **Sin dependencias externas**: solo stdlib y `pytest`. Nada de `tabulate`, `rich`, `numpy` ni similares.

## Criterios de aceptación

- [ ] `c_a_f('37') == 98.6` y `c_a_f(100.0) == 212.0` (acepta `str` y `float`, redondeo a 1 decimal).
- [ ] `km_a_millas('10') == 6.21` y `km_a_millas(0) == 0.0` (redondeo a 2 decimales).
- [ ] `formatear_tabla([...])` produce **exactamente** la cadena golden del test, carácter a carácter (alineación `:<12` y `:>8.2f` correcta).
- [ ] `isinstance(c_a_f('37'), float)` e `isinstance(km_a_millas('10'), float)` son `True` (las conversiones retornan `float`, no `str`).
- [ ] `c_a_f('')`, `c_a_f('abc')` y `km_a_millas('  ')` lanzan `ValueError` (la entrada inválida **no** se silencia).
- [ ] `pytest -q` pasa **todos** los tests en verde, sin warnings de tipo ni excepciones no controladas.

## Cómo se evalúa

El harness es un único archivo `test_solution.py` con **golden inline**: parejas entrada→salida exactas para cada conversión (cubriendo `str` y numérico), la cadena de tabla esperada carácter a carácter, una verificación de tipo de retorno con `isinstance`, y un test de `pytest.raises(ValueError)` para la entrada inválida.

El coach lo correrá con `pytest -q`. Tu `solution.py` debe exponer las tres funciones con esas firmas exactas. Este es el esqueleto del harness (los golden son los reales que se usarán):

```python
# test_solution.py
import pytest
from solution import c_a_f, km_a_millas, formatear_tabla


@pytest.mark.parametrize("entrada, esperado", [
    ("37", 98.6),       # str
    (37, 98.6),         # int
    (100.0, 212.0),     # float
    (0, 32.0),
    ("-40", -40.0),     # el punto donde C y F coinciden
])
def test_c_a_f(entrada, esperado):
    assert c_a_f(entrada) == esperado


@pytest.mark.parametrize("entrada, esperado", [
    ("10", 6.21),
    (0, 0.0),
    ("100", 62.14),
    (1, 0.62),
])
def test_km_a_millas(entrada, esperado):
    assert km_a_millas(entrada) == esperado


def test_retornan_float():
    assert isinstance(c_a_f("37"), float)
    assert isinstance(km_a_millas("10"), float)


def test_formatear_tabla():
    filas = [
        ("Temperatura", 98.6, "F"),
        ("Distancia", 6.21, "millas"),
    ]
    esperado = (
        "Temperatura       98.60 F\n"
        "Distancia          6.21 millas"
    )
    assert formatear_tabla(filas) == esperado


@pytest.mark.parametrize("malo", ["", "abc", "  ", "12,5"])
def test_entrada_invalida_lanza(malo):
    with pytest.raises(ValueError):
        c_a_f(malo)
```

Nota que `"12,5"` (coma decimal) **debe** fallar: `float()` no entiende la coma, y silenciar ese error sería esconder un bug de localización real. Si tu implementación "arregla" la coma por su cuenta, rompe el contrato del ejercicio.

## Pistas

<details><summary>Pista 1 — Convierte explícito y deja subir el error</summary>

`float('37')` funciona y devuelve `37.0`. `float('')` y `float('abc')` lanzan `ValueError` — eso es **lo que quieres**: no lo envuelvas en un `try/except` que devuelva `0` o `None`. La conversión es una sola línea: `c = float(celsius)`. Funciona igual si `celsius` ya es un `int` o `float`, porque `float(37)` también devuelve `37.0`. No necesitas comprobar el tipo de antemano; convierte y ya.

</details>

<details><summary>Pista 2 — Redondeo y formato son cosas distintas</summary>

`round(x, n)` devuelve un `float` con `n` decimales para el **valor** (`round(98.5999, 1) == 98.6`). Eso es lo que retornan tus conversiones. El **formato de columnas** es otra cosa: vive en el f-string, no en el valor. `f'{x:<12}'` alinea a la izquierda en 12 caracteres; `f'{x:>8.2f}'` alinea a la derecha en 8 y fuerza 2 decimales. Mezclar las dos (intentar alinear con `round`, o redondear con el f-string para el valor de retorno) es el error típico aquí.

</details>

<details><summary>Pista 3 — La solución completa, casi entera (casi-spoiler)</summary>

```python
def c_a_f(celsius) -> float:
    c = float(celsius)
    return round(c * 9 / 5 + 32, 1)


def km_a_millas(km) -> float:
    return round(float(km) * 0.621371, 2)


def formatear_tabla(filas) -> str:
    return "\n".join(
        f"{etiqueta:<12}{valor:>8.2f} {unidad}"
        for etiqueta, valor, unidad in filas
    )
```

Fíjate en tres cosas: (1) ningún `try/except` —el `ValueError` sube solo—; (2) `round(...)` devuelve `float`, así que `isinstance(..., float)` pasa sin esfuerzo; (3) `formatear_tabla` usa `str.join` sobre un **generador** con `enumerate`/desempaquetado de la tupla, no un bucle con concatenación manual ni un `\n` colgando al final.

</details>

## Bonus

1. **Conversión inversa con un solo helper**: agrega `f_a_c(fahrenheit)` y `millas_a_km(millas)` y refactoriza para que las cuatro funciones compartan un único helper de "convierte-calcula-redondea" que reciba el factor/fórmula. Objetivo: cero duplicación, mismas garantías de tipo.
2. **Tabla con encabezado y separador**: extiende `formatear_tabla` para aceptar un encabezado opcional (`("Etiqueta", "Valor", "Unidad")`) y dibujar una línea de guiones del ancho correcto debajo. El reto está en calcular el ancho total a partir de los mismos anchos de columna, sin hardcodear el número.

## Qué demuestra

Que distingues `str` de número y conviertes **a propósito**, en la frontera correcta, en vez de confiar en que el tipo "ya viene bien". Que sabes que `round` produce el valor y el f-string produce el formato, y que no confundes los dos. Que dejas que una entrada inválida **falle ruidosamente** con su `ValueError` en lugar de comparar strings o tragarte el error con un `except` perezoso. Y que escribes formato de salida idiomático —un `str.join` sobre un generador con desempaquetado de tupla— en vez de concatenar a mano con un acumulador. Es la frontera exacta entre escribir Python con acento de otro lenguaje y escribirlo como Python.

## Entregable

**Al repo** (carpeta `gym/kata-01-conversor-tipado/` de tu repo de soluciones):

- `solution.py` con las tres funciones (`c_a_f`, `km_a_millas`, `formatear_tabla`) y sus type hints.
- `test_solution.py` con tus propios tests (puedes partir del esqueleto de arriba y añadir casos borde).
- Opcional: las funciones del Bonus si lo intentaste.

**En la sesión de revisión** (5 minutos, comparte pantalla):

1. Corre `pytest -q` en vivo y muestra el verde.
2. Explica por qué `c_a_f('')` lanza `ValueError` y por qué eso es correcto y no un bug.
3. Señala en tu código las dos líneas exactas donde ocurre la conversión de tipo, y explica qué pasaría si las quitaras.