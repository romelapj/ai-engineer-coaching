```markdown
# 🏋️ Kata 03: Transformar una colección con funciones puras

| Metadato                | Valor                                                                                              |
| ----------------------- | -------------------------------------------------------------------------------------------------- |
| **Fase**                | Pre-Fase 0.5: Fundamentos de Python                                                                |
| **Sesión en que se asigna** | Sesión N03                                                                                      |
| **Tiempo estimado**     | 45–60 min                                                                                           |
| **Skill que entrena**   | Descomposición en funciones puras, type hints, comprehensions, funciones como argumento (predicados), defaults seguros |
| **Stack**               | Python 3.10+ stdlib, `pytest`. Sin estado global, sin efectos secundarios                           |

---

## Contexto

El dev que viene de un backend imperativo (Java, C#, Go viejo) tiende a caer en uno de dos extremos cuando le toca transformar datos: o escribe un bloque de 60 líneas con tres `for` anidados y cero funciones, o se va al otro lado y modela una clase `ContactoManager` con estado mutable para algo que es, en el fondo, `entrada → salida`. El punto medio Pythonic, el que casi nunca enseñan en otros lenguajes, son **funciones puras pequeñas que se componen**: cada una recibe datos, devuelve datos nuevos, no toca nada de afuera y no muta lo que le pasaste.

Esta kata entrena exactamente eso sobre un dominio chico y real: una agenda de contactos. Vas a **filtrar, agrupar, transformar y resumir** una lista de registros con funciones que se prueban trivialmente porque su único contrato es entrada → salida. No hay `self`, no hay variable global, no hay "y de paso actualizo este otro estado". Esa disciplina es la que hace que tu código sea testeable sin montar mocks ni fixtures elaborados.

De paso practicas algo que en muchos lenguajes se siente ceremonioso y en Python es natural: **pasar una función como argumento**. La función `filtrar` recibe un predicado (otra función que devuelve `bool`) y lo aplica. Esa es la semilla de los callbacks, los `key=` de `sorted`, los handlers y los hooks que vas a ver en todo el programa. Si te suena a "funciones de orden superior", sí: es eso, pero sin la palabra grandilocuente.

La trampa típica del que viene de imperativo es **mutar la entrada sin darse cuenta**: hacer `lista.sort()` en vez de `sorted(lista)`, o `contactos.append(...)` dentro de una función que "solo lee". En Python las listas y dicts se pasan por referencia, así que mutar el argumento le explota en la cara a quien te llamó. Esta kata tiene un test de pureza explícito para que eso te duela aquí, en 45 minutos, y no en producción.

## Enunciado

Implementa en `solution.py` **cuatro funciones puras con type hints** que operan sobre una lista de contactos. Cada contacto es un `dict` con esta forma:

```python
{"nombre": "Ana", "edad": 30, "ciudad": "Bogota"}
```

Las funciones a construir:

1. **`mayores_de(contactos, edad)`** → `list[dict]`
   Devuelve solo los contactos cuya `edad` sea **mayor o igual** al umbral recibido. No modifica la lista de entrada.

2. **`nombres_por_ciudad(contactos)`** → `dict[str, list[str]]`
   Agrupa los **nombres** de los contactos por su `ciudad`. Dentro de cada ciudad, los nombres van **ordenados alfabéticamente**.

3. **`filtrar(contactos, predicado)`** → `list[dict]`
   Aplica una **función booleana** (`predicado`) recibida como argumento y devuelve solo los contactos para los que el predicado da `True`. El llamador decide el criterio; tu función no sabe ni le importa cuál es.

4. **`resumen(contactos)`** → `dict`
   Devuelve un dict con tres claves:
   - `"total"`: cantidad de contactos (`int`).
   - `"edad_promedio"`: promedio de edades como `float` **redondeado a 1 decimal**.
   - `"ciudades"`: las ciudades presentes, como un `set`.

### Ejemplo de entrada → salida

**Entrada:**

```python
contactos = [
    {"nombre": "Ana",    "edad": 30, "ciudad": "Bogota"},
    {"nombre": "Bruno",  "edad": 25, "ciudad": "Medellin"},
    {"nombre": "Carla",  "edad": 41, "ciudad": "Bogota"},
    {"nombre": "Diego",  "edad": 19, "ciudad": "Medellin"},
]
```

**Salidas esperadas:**

```python
mayores_de(contactos, 26)
# [{"nombre": "Ana", "edad": 30, "ciudad": "Bogota"},
#  {"nombre": "Carla", "edad": 41, "ciudad": "Bogota"}]

nombres_por_ciudad(contactos)
# {"Bogota": ["Ana", "Carla"], "Medellin": ["Bruno", "Diego"]}

filtrar(contactos, lambda c: c["ciudad"] == "Bogota")
# [{"nombre": "Ana", "edad": 30, "ciudad": "Bogota"},
#  {"nombre": "Carla", "edad": 41, "ciudad": "Bogota"}]

resumen(contactos)
# {"total": 4, "edad_promedio": 28.8, "ciudades": {"Bogota", "Medellin"}}
```

Fíjate en las decisiones que el ejemplo te obliga a tomar: `mayores_de(contactos, 26)` **incluye a Ana (30) y Carla (41)** pero la frontera es `>=`, no `>`; el promedio `(30+25+41+19)/4 = 28.75` se redondea a `28.8` (no truncar, **redondear**); y `ciudades` es un `set`, no una lista: el orden no importa y los duplicados se colapsan solos.

## Requisitos

1. **Cuatro funciones en `solution.py`** con las firmas exactas del enunciado y **type hints** en parámetros y retorno (`list[dict]`, `dict[str, list[str]]`, etc.).
2. **Pureza total**: ninguna función modifica la lista de entrada, ni los dicts que contiene, ni usa variables globales o estado de módulo. Si necesitas ordenar, usa `sorted(...)` (devuelve copia), nunca `.sort()` sobre el argumento.
3. **`mayores_de`** filtra por `edad >= umbral` (frontera inclusiva).
4. **`nombres_por_ciudad`** agrupa nombres por ciudad y ordena **alfabéticamente** los nombres dentro de cada ciudad.
5. **`filtrar`** recibe el predicado **como argumento** y lo aplica; no hardcodees ningún criterio dentro de la función.
6. **`resumen`** calcula `total`, `edad_promedio` (float a 1 decimal con `round`) y `ciudades` como `set`.
7. **Sin efectos secundarios**: nada de `print`, escritura a disco, ni mutación de argumentos. Entrada → salida y nada más.
8. **Idiomático**: usa comprehensions para filtrar/transformar; `defaultdict` o `setdefault` para agrupar. Evita el `for` con `append` manual cuando una comprehension lo expresa más limpio.

## Criterios de aceptación

- [ ] `pytest -q` pasa **todos** los tests en verde.
- [ ] `mayores_de(contactos, 26)` devuelve exactamente los contactos con `edad >= 26`, y un assert verifica que la lista original quedó **idéntica** antes y después de la llamada.
- [ ] `nombres_por_ciudad(contactos)` devuelve el golden inline exacto, con los nombres de cada ciudad **ordenados alfabéticamente**.
- [ ] `filtrar` se prueba con **al menos 2 predicados distintos** (p. ej. por ciudad y por edad) y devuelve solo los contactos que cumplen.
- [ ] `resumen` devuelve `total` exacto, `edad_promedio` como `float` redondeado a 1 decimal (`28.8`, no `28.75` ni `28`) y `ciudades` como `set`.
- [ ] Un **test de pureza** llama a cada función y luego asevera que la lista de entrada (y sus dicts) no cambió.
- [ ] Las cuatro funciones tienen **type hints** en firma y retorno.
- [ ] No hay variables globales, `print`, ni `.sort()` / `.append()` / `.pop()` sobre la lista de entrada.

## Cómo se evalúa

El harness es un único archivo `test_solution.py` con una lista de contactos golden **inline** y salidas esperadas exactas por función, más un test de pureza que verifica que la entrada no se mutó, y tests de `filtrar` con dos predicados distintos pasados como `lambda`. El coach corre `pytest -q` y revisa que todo esté verde, y de paso lee `solution.py` para confirmar que las funciones son realmente puras (no que "pasan los tests por casualidad").

Esqueleto del harness (los golden son reales y correctos; tu trabajo es hacer que pasen):

```python
# test_solution.py
import copy
from solution import mayores_de, nombres_por_ciudad, filtrar, resumen

CONTACTOS = [
    {"nombre": "Ana",   "edad": 30, "ciudad": "Bogota"},
    {"nombre": "Bruno", "edad": 25, "ciudad": "Medellin"},
    {"nombre": "Carla", "edad": 41, "ciudad": "Bogota"},
    {"nombre": "Diego", "edad": 19, "ciudad": "Medellin"},
]


def test_mayores_de():
    esperado = [
        {"nombre": "Ana",   "edad": 30, "ciudad": "Bogota"},
        {"nombre": "Carla", "edad": 41, "ciudad": "Bogota"},
    ]
    assert mayores_de(CONTACTOS, 26) == esperado


def test_mayores_de_frontera_inclusiva():
    # edad == umbral debe entrar (>=, no >)
    nombres = [c["nombre"] for c in mayores_de(CONTACTOS, 25)]
    assert nombres == ["Ana", "Bruno", "Carla"]


def test_nombres_por_ciudad():
    assert nombres_por_ciudad(CONTACTOS) == {
        "Bogota": ["Ana", "Carla"],
        "Medellin": ["Bruno", "Diego"],
    }


def test_filtrar_por_ciudad():
    res = filtrar(CONTACTOS, lambda c: c["ciudad"] == "Bogota")
    assert [c["nombre"] for c in res] == ["Ana", "Carla"]


def test_filtrar_por_edad():
    res = filtrar(CONTACTOS, lambda c: c["edad"] < 26)
    assert [c["nombre"] for c in res] == ["Bruno", "Diego"]


def test_resumen():
    assert resumen(CONTACTOS) == {
        "total": 4,
        "edad_promedio": 28.8,        # (30+25+41+19)/4 = 28.75 -> round 28.8
        "ciudades": {"Bogota", "Medellin"},
    }


def test_pureza_no_muta_la_entrada():
    original = copy.deepcopy(CONTACTOS)
    mayores_de(CONTACTOS, 26)
    nombres_por_ciudad(CONTACTOS)
    filtrar(CONTACTOS, lambda c: True)
    resumen(CONTACTOS)
    assert CONTACTOS == original   # la lista y sus dicts quedaron intactos
```

> Nota: si tu `mayores_de` devuelve `[c for c in contactos if ...]`, los dicts del resultado son **los mismos objetos** que los de la entrada (referencias compartidas). Eso está bien para esta kata mientras **no los mutes**. El test de pureza pasa porque nadie modifica esos dicts.

## Pistas

<details><summary>Pista 1: Filtrar y transformar con comprehensions</summary>

Para `mayores_de`, una comprehension con `if` es todo lo que necesitas:

```python
def mayores_de(contactos: list[dict], edad: int) -> list[dict]:
    return [c for c in contactos if c["edad"] >= edad]
```

No hace falta `filter()` ni un `for` con `append`. La comprehension ya crea una **lista nueva**, así que la entrada nunca se toca. La frontera es `>=` (mayor **o igual**), no `>`.

</details>

<details><summary>Pista 2: Agrupar por ciudad y ordenar dentro de cada grupo</summary>

Para `nombres_por_ciudad`, agrupa primero y ordena al final. `defaultdict(list)` te evita el `if ciudad not in dict` repetitivo:

```python
from collections import defaultdict

def nombres_por_ciudad(contactos: list[dict]) -> dict[str, list[str]]:
    grupos = defaultdict(list)
    for c in contactos:
        grupos[c["ciudad"]].append(c["nombre"])
    return {ciudad: sorted(nombres) for ciudad, nombres in grupos.items()}
```

`sorted(nombres)` devuelve una lista **nueva** ordenada: usa eso, no `nombres.sort()`. (Aquí `append` es sobre tu acumulador local `grupos`, no sobre la entrada: eso es perfectamente puro.)

</details>

<details><summary>Pista 3: Predicado como argumento y resumen (casi-spoiler)</summary>

`filtrar` es `mayores_de` pero genérica: en vez de comparar contra una edad fija, llama al predicado que te pasaron. Una función es un valor más; la recibes y la invocas con `()`:

```python
from typing import Callable

def filtrar(contactos: list[dict], predicado: Callable[[dict], bool]) -> list[dict]:
    return [c for c in contactos if predicado(c)]
```

Y `resumen` combina las tres operaciones (contar, promediar, deduplicar) sin mutar nada:

```python
def resumen(contactos: list[dict]) -> dict:
    total = len(contactos)
    promedio = round(sum(c["edad"] for c in contactos) / total, 1)
    ciudades = {c["ciudad"] for c in contactos}
    return {"total": total, "edad_promedio": promedio, "ciudades": ciudades}
```

`sum(... ) / total` con `round(_, 1)` te da el float a 1 decimal; el set comprehension `{...}` deduplica las ciudades gratis. (Si quieres blindar contra lista vacía, decide tú: `round(sum/total, 1) if total else 0.0`, pero el golden no lo exige.)

</details>

## Bonus

1. **Compón en vez de duplicar**: reescribe `mayores_de` en términos de `filtrar`, pasándole un predicado (`lambda c: c["edad"] >= edad`). Ahora `mayores_de` es un caso particular de `filtrar`: eso es composición de funciones, y demuestra que entendiste que el predicado es solo un argumento más.
2. **Agrupador genérico**: generaliza `nombres_por_ciudad` a `agrupar_por(contactos, clave, valor)` donde `clave` y `valor` son funciones (`clave=lambda c: c["ciudad"]`, `valor=lambda c: c["nombre"]`). Mismo resultado, pero ahora sirve para agrupar por cualquier campo. Es el patrón `key=` de `sorted`/`groupby` aplicado a tu dominio.
3. **Property test ligero**: agrega un test que genere listas aleatorias de contactos y verifique invariantes que deben cumplirse siempre: p. ej. `len(mayores_de(xs, 0)) == len(xs)`, o que la suma de los tamaños de los grupos de `nombres_por_ciudad` es igual a `len(xs)`. Verificar propiedades en vez de casos puntuales es una técnica que escala.

## Qué demuestra

Que sabes **descomponer una transformación de datos en funciones puras pequeñas** con type hints, en vez de un bloque monolítico o una clase con estado innecesario. Que transformas con **comprehensions** (de lista, de dict y de set) en lugar de bucles con `append` manual. Que entiendes que una **función es un valor** que se puede pasar como argumento (predicados), la base de todo el estilo de orden superior que verás después. Y, sobre todo, que respetas la **inmutabilidad de la entrada**: no mutas lo que te pasaron, devuelves cosas nuevas: la disciplina que hace que tu código sea testeable, paralelizable y predecible. En una palabra: Python idiomático sin sobre-ingeniería.

## Entregable

**Al repo** (carpeta `gym/kata-03-transformar-coleccion-funciones-puras/` de tu repo de soluciones):

- `solution.py` con las cuatro funciones puras (`mayores_de`, `nombres_por_ciudad`, `filtrar`, `resumen`), todas con type hints.
- `test_solution.py` con los tests (puedes partir del esqueleto de arriba y ampliarlo: frontera inclusiva, dos predicados para `filtrar`, y el test de pureza).
- Opcional: lo que hayas hecho de la sección Bonus, en el mismo `solution.py` o en un `test_solution.py` ampliado.

**En la sesión de revisión** (5–10 min):

1. Corre `pytest -q` en vivo y muestra el verde.
2. El coach va a abrir `solution.py` y preguntar: _"¿alguna de estas funciones puede mutar lo que recibe?"_. Defiende por qué cada una es pura.
3. Explica en una frase por qué `filtrar` no necesita saber cuál es el criterio, y dónde más has visto ese patrón (callbacks, `key=`, handlers).
```