# 🏋️ Kata 07: Capstone a elección (un programita completo)

| Metadato                  | Valor                                                                                                                                                              |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Fase**                  | Pre-Fase 0.5: Fundamentos de Python                                                                                                                              |
| **Sesión en que se asigna** | Sesión 5 (N05), capstone de cierre                                                                                                                            |
| **Tiempo estimado**       | 90–150 min                                                                                                                                                        |
| **Skill que entrena**     | Integración de amplitud: estructuras + funciones + archivos/errores + una clase/dataclass + tests, en un programa pequeño y completo                              |
| **Stack**                 | Python 3.10+ stdlib + `pytest`. Una dependencia opcional permitida si el capstone lo justifica (`argparse` es stdlib). Sin frameworks pesados                     |

---

## Contexto

Las seis katas anteriores aislaron un fundamento cada una: un día fueron `dict`/`set`, otro las comprehensions, otro `try`/`except` con excepciones concretas, otro leer y escribir archivos, otro dataclasses, otro tests. Eso es necesario pero no suficiente. Un dev que viene de Java o de Go puede saber la sintaxis de cada pieza por separado y aun así escribir Python que "funciona pero se siente ajeno": bucles con índices manuales donde iría un `enumerate`, contadores `+= 1` donde iría un `Counter`, `try` gigantes que se tragan todo, clases para lógica que cabría en una función.

Este capstone entrena lo que ninguna kata individual puede: **la fluidez de juntar todos los fundamentos en un programa pequeño pero completo, de punta a punta, que tú diseñas y defiendes**. No es re-implementar una kata anterior con otro nombre, es producir algo que corre, pasa sus tests, tiene un README de tres líneas, y que puedes recorrer en voz alta explicando cada decisión: por qué un `set` y no una `list`, por qué esta función es pura y aquella hace E/S, por qué este `except` atrapa `KeyError` y no `Exception` pelado.

La habilidad que se mide aquí es la que distingue "sé Python" de "drilleé un ejercicio": cuando ya no piensas en la sintaxis, el diseño del programita se vuelve la parte interesante. Eliges **una** opción según lo que quieras ejercitar, pero todas te obligan a tomar las mismas decisiones de amplitud.

## Enunciado

Elige **UNA** de las siguientes opciones y constrúyela **completa**: que corra de punta a punta sobre una entrada de ejemplo incluida en el repo, con tests `pytest` propios (golden inline) y un README breve. No empieces dos; termina una.

| Opción | Programa | Dominio de datos | Núcleo que ejercita |
| ------ | -------- | ---------------- | ------------------- |
| **A** | **CLI de tareas (to-do)** con `argparse` | Tareas en un `tasks.json` | persistencia JSON + `dataclass Tarea` + subcomandos `add`/`list`/`done` + error de archivo ausente |
| **B** | **Mini procesador de datos** | Un CSV variado **que no sea logs** (ventas, calificaciones, gastos…) | agregación por clave con `Counter`/`defaultdict` + descarte de filas malas + reporte JSON o tabla |
| **C** | **Juego de texto por turnos** (adivina-el-número o ahorcado) | Estado del juego en memoria | `class Juego` con estado + validación de input + bucle principal |
| **D** | **Agenda de contactos** | Contactos en un `contacts.json` | `dataclass Contacto` + CRUD en memoria + búsqueda/filtrado con comprehensions |
| **E** | **Analizador de un dataset a elección** (puede ser un log, pero **no** es obligatorio) | El dataset que quieras parsear | parseo + agrupación + estadísticas + descarte+conteo de líneas malas |

Cualquiera que sea la opción, el programa debe usar **al menos**:

- **una estructura no trivial** (un `dict` indexado por clave, un `set` para deduplicar/pertenencia, un `Counter`/`defaultdict` para agregar);
- **funciones puras con type hints** (entrada → salida, sin tocar disco ni `print`), separadas de la capa de E/S;
- **lectura o escritura de un archivo** (`json` o `csv` de la stdlib);
- **un `except` de tipo concreto** (`FileNotFoundError`, `json.JSONDecodeError`, `ValueError`, `KeyError`… nunca `except Exception` pelado);
- **una `dataclass` o `class` con `__repr__`** que modele tu dominio.

### Ejemplo trabajado (opción A: CLI de tareas)

Para que veas el nivel de "completo" esperado, aquí está la opción A de punta a punta. **Las demás opciones tienen la misma profundidad**: esto es una referencia, no la única respuesta.

**Modelo de dominio** (`dataclass` con `__repr__` gratis):

```python
from dataclasses import dataclass, asdict

@dataclass
class Tarea:
    id: int
    texto: str
    hecha: bool = False
```

**Núcleo puro** (testeable sin tocar disco: entra una lista, sale una lista):

```python
def agregar(tareas: list[Tarea], texto: str) -> list[Tarea]:
    siguiente_id = max((t.id for t in tareas), default=0) + 1
    return [*tareas, Tarea(id=siguiente_id, texto=texto)]

def completar(tareas: list[Tarea], id_: int) -> list[Tarea]:
    if not any(t.id == id_ for t in tareas):
        raise KeyError(f"no existe tarea con id {id_}")
    return [Tarea(t.id, t.texto, hecha=True) if t.id == id_ else t for t in tareas]
```

**Capa de E/S** (aislada, con `except` concreto):

```python
import json
from pathlib import Path

def cargar(ruta: Path) -> list[Tarea]:
    try:
        crudas = json.loads(ruta.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []                      # primera corrida: aún no hay archivo
    return [Tarea(**d) for d in crudas]

def guardar(ruta: Path, tareas: list[Tarea]) -> None:
    ruta.write_text(json.dumps([asdict(t) for t in tareas], ensure_ascii=False, indent=2))
```

**Sesión de uso** (lo que el coach corre en vivo):

```
$ python todo.py add "comprar café"
añadida #1: comprar café
$ python todo.py add "pagar arriendo"
añadida #2: pagar arriendo
$ python todo.py done 1
completada #1
$ python todo.py list
[x] #1 comprar café
[ ] #2 pagar arriendo
```

Fíjate en las decisiones que el ejemplo te obliga a tomar y defender: `FileNotFoundError` se atrapa (primera corrida legítima) pero un JSON corrupto **no** se traga; `completar` levanta `KeyError` en vez de fallar en silencio; el núcleo no imprime ni guarda, así que se testea con una lista en memoria. Ese reparto de responsabilidades es lo que se evalúa, no la temática.

## Requisitos

1. **Una sola opción, completa**: elige A–E (o propón otra al coach antes de empezar) y constrúyela de punta a punta. No se evalúan dos a medias.
2. **Entrada de ejemplo versionada**: incluye en el repo el archivo de entrada con el que el programa corre (`tasks.json` semilla, un `datos.csv`, etc.) para que `corra sin preparación previa.
3. **Estructura no trivial**: usa al menos un `dict` indexado, un `set`, o un `Counter`/`defaultdict` con un propósito real (no un `list` disfrazado).
4. **Núcleo puro separado de la E/S**: las funciones que transforman datos llevan **type hints**, no imprimen ni leen disco, y reciben/devuelven valores. La E/S (archivos, `input`, `print`) vive en funciones aparte.
5. **Persistencia o lectura de archivo**: lee o escribe `json`/`csv` de la stdlib al menos una vez (las opciones C/E pueden leer su dataset de entrada en lugar de persistir).
6. **`except` de tipo concreto**: maneja al menos un error específico (`FileNotFoundError`, `json.JSONDecodeError`, `ValueError`, `KeyError`…). Prohibido `except Exception:` pelado o `except:` desnudo.
7. **`dataclass` o `class` con `__repr__`**: modela tu dominio con un tipo propio (la `dataclass` da `__repr__` gratis; si usas `class` a mano, escríbelo).
8. **Manejo de entrada inválida**: al menos una entrada mala (fila CSV corrupta, id inexistente, número fuera de rango, JSON malformado) se **descarta + cuenta**, se **reporta**, o se **rechaza con mensaje claro**, nunca revienta con traceback.
9. **Tests propios con golden inline**: ≥ 4 tests `pytest` con datos fijos y salidas esperadas escritas en el propio test, cubriendo camino feliz **y** ≥ 2 casos borde (vacío, malformado, límite).
10. **README de ~10 líneas máximo**: qué hace, cómo se corre (comando exacto), y qué fundamentos de Python ejercita.

## Criterios de aceptación

- [ ] El programa corre de punta a punta sin errores sobre la entrada de ejemplo incluida (`python <programa>.py ...` produce la salida esperada, no un traceback).
- [ ] `pytest -q` da **verde** con ≥ 4 tests propios: ≥ 1 de camino feliz y ≥ 2 de casos borde (vacío, entrada malformada, límite).
- [ ] El núcleo de lógica está en **funciones puras con type hints** que no imprimen ni tocan disco, verificable porque sus tests no usan `tmp_path`, `capsys` ni `monkeypatch`.
- [ ] Hay **exactamente un tipo de dominio** (`dataclass` o `class`) con `__repr__` (gratis vía `dataclass`, o escrito a mano) usado por el programa.
- [ ] El código contiene **al menos un `except` de tipo concreto** y **cero** `except Exception:` / `except:` pelados (`grep -rn "except Exception\|except:" .` no devuelve nada en tu código).
- [ ] Al dar una entrada inválida deliberada, el programa **no** imprime un traceback: la descarta+cuenta, la reporta, o la rechaza con mensaje claro y exit code distinto de 0 si aplica.
- [ ] El código es **idiomático**: comprehensions donde aplican, `enumerate`/`zip` en vez de índices manuales, `Counter`/`defaultdict` en vez de `+= 1` a mano, sin clases para lógica que cabe en una función.
- [ ] Existe un `README.md` de ≤ 10 líneas con: qué hace, comando exacto para correrlo, y los fundamentos que ejercita.

## Cómo se evalúa

El harness es `pytest -q` sobre **tus propios** tests con golden inline (datos fijos y salida esperada escritos dentro del test, sin archivos externos ni red). El coach corre `pytest -q`, debe ver verde, y luego te pide **agregar un caso borde en vivo** para confirmar que tu diseño lo soporta sin reescribir nada. La nota combina: tests verdes + revisión de idiomática + defensa oral de 5 minutos.

Esqueleto de tests para la opción A (sirve de plantilla; **adáptalo a tu opción**, con tus propios datos golden inline):

```python
# test_todo.py: golden inline, sin tocar disco
import pytest
from todo import Tarea, agregar, completar

def test_agregar_sobre_lista_vacia():
    resultado = agregar([], "comprar café")
    assert resultado == [Tarea(id=1, texto="comprar café", hecha=False)]

def test_ids_consecutivos_y_no_muta_original():
    base = [Tarea(id=1, texto="a")]
    nuevo = agregar(base, "b")
    assert [t.id for t in nuevo] == [1, 2]
    assert base == [Tarea(id=1, texto="a")]      # camino feliz: pureza

def test_completar_marca_solo_la_tarea_pedida():
    base = [Tarea(1, "a"), Tarea(2, "b")]
    resultado = completar(base, 2)
    assert resultado == [Tarea(1, "a", hecha=False), Tarea(2, "b", hecha=True)]

def test_completar_id_inexistente_levanta_keyerror():  # caso borde 1
    with pytest.raises(KeyError):
        completar([Tarea(1, "a")], 99)

def test_agregar_sobre_lista_vacia_genera_id_1():      # caso borde 2: vacío
    assert agregar([], "x")[0].id == 1
```

Nota que los tests del núcleo no usan `tmp_path` ni `capsys`: eso es la prueba viva de que separaste lógica pura de E/S. Si para testear `agregar` necesitaras un archivo temporal, el diseño estaría mal. En la defensa, el coach tomará un test al azar y te pedirá justificar el golden: _"¿por qué aquí esperas `KeyError` y no que devuelva la lista sin cambios?"_. Si la respuesta no está en tu diseño, cuenta como hallazgo.

## Pistas

<details><summary>Pista 1: Si no sabes por dónde empezar</summary>

Empieza por el **contrato**, no por el código: para tu opción, escribe en una línea qué entra, qué sale y qué falla. Para la CLI de tareas: _entra un comando + un `tasks.json`; sale el `tasks.json` actualizado y un mensaje; falla si el id no existe o el JSON está corrupto_. Con eso claro, escribe **1–2 tests antes de la implementación** (el `test_agregar_sobre_lista_vacia` de arriba se escribe sin que exista `agregar` todavía). Los tests fijan el contrato y la implementación se vuelve "rellenar para que pasen". Es la versión chica de TDD y te ahorra rediseñar a mitad de camino.

</details>

<details><summary>Pista 2: Qué herramienta de la stdlib usar para cada pieza</summary>

Mapa directo: **CLI/subcomandos** → `argparse` (`add_subparsers()` para `add`/`list`/`done`); **persistir** → `json.load`/`json.dump` (o `csv.DictReader` para leer tablas); **modelo de dominio** → `@dataclass` (te da `__init__`, `__repr__` y `__eq__` gratis, que es justo lo que tus tests con `==` necesitan); **agregar por clave** → `collections.Counter` (`Counter(filas)` o `c[clave] += 1` sin inicializar) o `defaultdict(list)`; **convertir `dataclass` ↔ `dict` para JSON** → `dataclasses.asdict` / `Modelo(**d)`. Si te encuentras escribiendo un `for` con un índice o un `total = 0; total += 1`, casi siempre hay un builtin (`enumerate`, `sum`, `Counter`) que lo hace idiomático.

</details>

<details><summary>Pista 3: El reparto lógica-pura / E/S que el coach va a buscar (casi-spoiler)</summary>

Estructura el archivo en tres capas y se cae solo:

1. **Modelo** (`@dataclass`): solo datos.
2. **Núcleo puro**: funciones `lista → lista` / `dict → dict` con type hints, **sin** `print`, `input` ni acceso a disco. Aquí va toda la lógica (agregar, completar, agrupar, calcular). Estas son las que testeas con golden inline en memoria.
3. **Cáscara de E/S**: `cargar(ruta)` / `guardar(ruta, datos)` con el `except` concreto, y un `main()` que parsea args, llama al núcleo y hace `print`. El `main` es delgado y casi no se testea.

La regla operativa: **si una función tanto calcula como imprime/guarda, pártela en dos**. Cuando el núcleo no importa `json` ni `pathlib`, sabes que lo lograste, y tus tests, al no necesitar `tmp_path`, lo demuestran. Esa separación es exactamente lo que convierte el programita en "idiomático y defendible" en vez de "un script que funciona".

</details>

## Bonus

1. **Cobertura del caso borde en vivo sin tocar el código**: prepara tu diseño para que el caso borde que el coach pida en la defensa (p. ej. "dos tareas con el mismo texto", "CSV con una columna de más", "número en el límite exacto del rango") pase agregando **solo un test**, sin modificar la implementación. Si tienes que tocar el núcleo, el diseño tenía un supuesto oculto: anótalo.
2. **Property-based mínimo**: agrega un test que afirme una invariante en vez de un valor fijo (p. ej. "tras `completar(t, id)`, la longitud de la lista no cambia y exactamente una tarea más está `hecha`"). Es el primer paso hacia tests que no enumeran casos a mano.
3. **Tipado estricto**: corre `python -m mypy <programa>.py` sin errores. Te obliga a que los type hints del núcleo sean honestos.

## Qué demuestra

- _"Integré los fundamentos del curso en un programita completo: un modelo `dataclass`, un núcleo de funciones puras con type hints, una cáscara de E/S con `except` concretos y tests con golden inline, todo de punta a punta y defendible decisión por decisión."_: demuestra amplitud, no haber drilleado un ejercicio.
- _"Separé lógica pura de E/S a propósito: mis tests del núcleo no tocan disco, así que son triviales y rápidos, y la capa de archivos quedó delgada y con manejo de error específico."_: demuestra que el diseño limpio es un reflejo, no un esfuerzo.
- _"Cuando me pidieron un caso borde nuevo lo cubrí agregando un solo test, sin tocar la implementación: el contrato ya lo soportaba."_: demuestra que escribes Python pensando en el contrato, que es la fluidez que este curso buscaba construir.

## Entregable

**Al repo** (carpeta `gym/kata-07-capstone-a-eleccion/` de tu repo de soluciones, antes del domingo 23:59):

- El programa (`todo.py` / `procesar.py` / `juego.py` / `agenda.py` / `analizar.py`, según tu opción), con las tres capas: modelo, núcleo puro, E/S.
- La entrada de ejemplo versionada (`tasks.json` semilla, `datos.csv`, etc.) para que corra sin preparación.
- `test_<programa>.py` con ≥ 4 tests de golden inline (≥ 1 camino feliz, ≥ 2 borde).
- `README.md` de ≤ 10 líneas: qué hace, comando exacto para correrlo, y fundamentos que ejercita.

**En la sesión de revisión** (5 minutos, comparte pantalla):

1. Di qué opción elegiste y recita el contrato en una línea: qué entra, qué sale, qué falla (30 s).
2. Corre el programa en vivo sobre la entrada de ejemplo y luego `pytest -q` en verde (1.5 min).
3. Recorre las tres capas señalando una función pura, el `except` concreto y la `dataclass` (2 min).
4. Agrega en vivo el caso borde que el coach proponga y muéstralo pasar (1 min).