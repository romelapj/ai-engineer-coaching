# 🏋️ Kata 02: Frecuencia de palabras con ranking

| Metadato                  | Valor                                                                                                            |
| ------------------------- | --------------------------------------------------------------------------------------------------------------- |
| **Fase**                  | Pre-Fase 0.5: Fundamentos de Python                                                                             |
| **Sesión en que se asigna** | Sesión N02                                                                                                      |
| **Tiempo estimado**       | 45–60 min                                                                                                        |
| **Skill que entrena**     | Agrupar/contar con `dict` y `Counter`, comprehensions, `sorted` con key de tupla y desempate, slicing para top-N |
| **Stack**                 | Python 3.10+ stdlib (`collections`), pytest. **Sin** pandas, **sin** contadores manuales                        |

---

## Contexto

Agrupar por clave es la operación más repetida de cualquier procesamiento de datos. Contar cuántas veces aparece cada cosa, sumar montos por categoría, juntar registros por usuario. Todo es la misma mecánica: recorrer una colección y acumular en un diccionario indexado por una clave.

Si vienes de otro lenguaje, la primera vez la vas a escribir a mano:

```python
conteo = {}
for palabra in texto.split():
    if palabra not in conteo:      # 👈 el síntoma de nivel 3
        conteo[palabra] = 0
    conteo[palabra] += 1
```

Eso **funciona**, pero es exactamente el código que un entrevistador marca como no idiomático. Python tiene `collections.Counter` y `collections.defaultdict` precisamente para que ese patrón desaparezca. La diferencia entre escribir `Counter(palabras)` y el bloque de arriba es la diferencia entre un dev que conoce la stdlib y uno que la reimplementa sin saberlo.

La segunda mitad de la kata es el **ranking**. Contar es fácil; ordenar por dos criterios a la vez (conteo descendente, y ante empate alfabético ascendente) es donde se separa quien sabe usar `sorted(key=...)` con una tupla de quien hace tres pasadas y un `if` anidado. `Counter.most_common()` te tienta porque ordena por conteo, pero su desempate **no** es alfabético ni determinista, así que cae en la trampa. Esta kata aísla esa mecánica del ruido del parseo: el texto llega limpio (ya sin puntuación pegada) y solo evalúas si **cuentas con la colección correcta** y **ordenas con la clave compuesta correcta**.

El dominio es texto plano: cuentas palabras de un párrafo y sacas un ranking de frecuencias. Nada de logs.

## Enunciado

Implementa una función en `solution.py`:

```python
def frecuencias(texto: str, top: int | None = None) -> list[tuple[str, int]]:
    ...
```

que:

1. **Normalice** el texto a minúsculas.
2. **Parta** en palabras por espacios en blanco (asume que el texto ya viene sin puntuación pegada a las palabras: no es trabajo de esta kata limpiar comas ni puntos).
3. **Cuente** cuántas veces aparece cada palabra.
4. **Devuelva** una lista de tuplas `(palabra, conteo)` ordenada por **conteo DESCENDENTE** y, ante empate, por **palabra ASCENDENTE** (alfabético).
5. Si `top` no es `None`, **recorte** la lista a las `top` palabras más frecuentes _después_ de ordenar.

### Ejemplo de entrada → salida

**Entrada:**

```python
frecuencias("el gato y el perro y el pez")
```

**Salida:**

```python
[("el", 3), ("y", 2), ("gato", 1), ("perro", 1), ("pez", 1)]
```

Lee el resultado con cuidado: `el` (3) va antes que `y` (2) por conteo. Pero `gato`, `perro` y `pez` empatan en 1, así que salen en orden **alfabético**, no en el orden en que aparecieron en el texto, no en el orden en que un `dict` los insertó. Ese desempate es el corazón de la kata.

**Con recorte:**

```python
frecuencias("el gato y el perro y el pez", top=2) == [("el", 3), ("y", 2)]
```

## Requisitos

1. **Una sola función pública** `frecuencias(texto, top=None)` en `solution.py`, con type hints en la firma.
2. **El conteo usa `Counter` o `defaultdict`** de `collections`. Prohibido inicializar el contador a mano con `if clave not in d: d[clave] = 0` (se revisa en code review).
3. **El orden es determinista**: conteo descendente; ante empate, palabra ascendente alfabéticamente. No te apoyes en el orden de inserción del `dict` ni en `Counter.most_common()` para el desempate.
4. **`top` se aplica después de ordenar**, recortando con slicing. `top=None` devuelve todas las palabras. `top` mayor que el número de palabras únicas devuelve todas sin error.
5. **Casos borde**: `frecuencias("")` devuelve `[]`. Texto con una sola palabra devuelve `[(palabra, 1)]`.
6. **Sin dependencias externas**: solo stdlib. Nada de pandas.

## Criterios de aceptación

- [ ] `frecuencias("el gato y el perro y el pez") == [("el", 3), ("y", 2), ("gato", 1), ("perro", 1), ("pez", 1)]`: orden exacto, incluyendo el desempate alfabético de las tres palabras empatadas en 1.
- [ ] `frecuencias("el gato y el perro y el pez", top=2) == [("el", 3), ("y", 2)]`: devuelve solo las 2 primeras tras ordenar.
- [ ] `frecuencias("")` == `[]` (texto vacío).
- [ ] `frecuencias("hola")` == `[("hola", 1)]` (palabra única).
- [ ] El desempate alfabético es determinista y está verificado comparando la **lista completa** contra el golden, no solo el primer elemento.
- [ ] La normalización a minúsculas funciona: `frecuencias("El el EL")` == `[("el", 3)]`.
- [ ] `top` mayor que el número de palabras únicas no rompe: `frecuencias("a b", top=99)` devuelve las 2 palabras.
- [ ] El conteo se hace con `Counter` o `defaultdict` (revisado en code review; nada de `if clave not in d`).
- [ ] `pytest -q` pasa todos los tests en verde.

## Cómo se evalúa

El harness es un archivo `test_solution.py` con golden sets **inline**: textos fijos y la lista de tuplas esperada **completa** (no solo el primer elemento), de modo que el desempate alfabético se fuerza en cada comparación. El coach correrá `pytest -q` sobre tu `solution.py`.

```python
# test_solution.py
import pytest
from solution import frecuencias


def test_ranking_completo_con_desempate_alfabetico():
    # 'el' (3) > 'y' (2) por conteo; gato/perro/pez empatan en 1 -> alfabético
    texto = "el gato y el perro y el pez"
    esperado = [("el", 3), ("y", 2), ("gato", 1), ("perro", 1), ("pez", 1)]
    assert frecuencias(texto) == esperado


def test_top_recorta_despues_de_ordenar():
    texto = "el gato y el perro y el pez"
    assert frecuencias(texto, top=2) == [("el", 3), ("y", 2)]


def test_texto_vacio():
    assert frecuencias("") == []


def test_palabra_unica():
    assert frecuencias("hola") == [("hola", 1)]


def test_normaliza_a_minusculas():
    assert frecuencias("El el EL") == [("el", 3)]


def test_top_mayor_que_unicas_no_rompe():
    assert frecuencias("a b", top=99) == [("a", 1), ("b", 1)]


def test_desempate_es_alfabetico_no_de_insercion():
    # 'zebra' aparece primero en el texto pero debe salir despues de 'alfa'
    assert frecuencias("zebra alfa") == [("alfa", 1), ("zebra", 1)]
```

Fíjate en el último test: `zebra` aparece **antes** que `alfa` en el texto. Si tu implementación devuelve `[("zebra", 1), ("alfa", 1)]`, estás dejando que el orden de inserción mande y el desempate no es alfabético. Ese test es el que descarta `most_common()` y las soluciones que confían en el orden del `dict`.

## Pistas

<details><summary>Pista 1: Contar sin reinventar la rueda</summary>

`collections.Counter` cuenta de un solo golpe: `Counter("el gato y el".split())` te da `Counter({'el': 2, 'gato': 1, 'y': 1})`. Si no quieres `Counter`, `defaultdict(int)` también te deja escribir `conteo[palabra] += 1` sin el `if clave not in d`. Cualquiera de los dos elimina el patrón que la kata prohíbe. Recuerda normalizar a minúsculas **antes** de contar (`texto.lower().split()`), no después.

</details>

<details><summary>Pista 2: Por qué <code>most_common()</code> no alcanza</summary>

`Counter(...).most_common()` ordena por conteo descendente (y por eso es tentador), pero ante empate **conserva el orden de inserción** (en CPython moderno), que no es alfabético. Para `"el gato y el perro y el pez"` te puede dar `gato, perro, pez` solo por suerte del orden del texto; cambia el texto a `"pez gato"` y verás que el desempate se rompe. Necesitas ordenar tú con un criterio explícito, no delegar el desempate al `Counter`.

</details>

<details><summary>Pista 3: La key de tupla que resuelve todo en una pasada (casi-spoiler)</summary>

`sorted` ordena por la tupla que devuelve la `key`, campo por campo, en orden ascendente. El truco para mezclar "descendente por conteo" con "ascendente por palabra" es **negar** el conteo:

```python
ordenado = sorted(conteo.items(), key=lambda kv: (-kv[1], kv[0]))
```

`-kv[1]` hace que mayor conteo quede primero (porque ascendente sobre el negativo = descendente sobre el original); `kv[0]` rompe el empate alfabéticamente. Una sola pasada, sin `if` anidados. Luego, el recorte:

```python
return ordenado[:top] if top is not None else ordenado
```

`lista[:None]` también devolvería la lista completa, pero el `if` explícito deja la intención clara.

</details>

## Bonus

1. **Stop-words**: agrega un parámetro opcional `ignorar: set[str] | None = None` que excluya palabras del conteo (artículos, conectores) usando una comprehension de filtrado: `[p for p in palabras if p not in ignorar]`. Mantén el desempate intacto.
2. **Frecuencia relativa**: una segunda función `frecuencias_pct(texto)` que devuelva `(palabra, porcentaje)` con el conteo como fracción del total de palabras, redondeado a 2 decimales. Practica `round` y división sin caer en división por cero con texto vacío.
3. **Property test**: con `hypothesis` (si quieres ir más allá de stdlib), verifica la invariante de que la suma de los conteos siempre es igual al número de palabras del texto, para cualquier entrada.

## Qué demuestra

Que agrupas y cuentas con la colección idiomática de la stdlib (`Counter`/`defaultdict`) en vez de parchar un `dict` a mano, y que rankeas con una **key de tupla con desempate determinista** (`(-conteo, palabra)`) en una sola pasada de `sorted`, en lugar de varias pasadas con `if` anidados o de confiar en el orden de inserción. Es la diferencia exacta entre un 3 y un 4 en manejo de estructuras de datos: no es que "te salga el resultado", es que lo logras con el modismo que cualquier dev de Python reconoce a primera vista.

## Entregable

**Al repo** (carpeta `gym/kata-02-frecuencia-de-palabras/` de tu repo de soluciones):

- `solution.py` con la función `frecuencias(texto, top=None)`.
- `test_solution.py` con los tests de arriba en verde (puedes añadir más casos).
- Opcional: las funciones del Bonus si las intentaste.

**En la sesión de revisión** (5 minutos, comparte pantalla):

1. Corre `pytest -q` en vivo.
2. Explica por qué `(-kv[1], kv[0])` resuelve los dos criterios de orden a la vez (1 min).
3. Justifica por qué no usaste `most_common()` para el desempate (1 min).