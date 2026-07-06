# 🏋️ Kata 04 — De CSV a JSON: leer, transformar, escribir

| Metadato                | Valor                                                                                                                        |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| **Fase**                | Pre-Fase 0.5 — Fundamentos de Python                                                                                       |
| **Sesión en que se asigna** | Sesión N04                                                                                                             |
| **Tiempo estimado**     | 60–75 min                                                                                                                  |
| **Skill que entrena**   | `pathlib`, `with` / context managers, `csv.DictReader`, `json.dump`, conversión de tipos por columna, manejo de filas malformadas |
| **Stack**               | Python 3.10+ stdlib (`csv`, `json`, `pathlib`), `pytest`. **Sin** `pandas`                                                  |

---

## Contexto

Leer un archivo, transformarlo y escribir otro es el 80% del trabajo de datos antes de que entre cualquier modelo. Parece trivial — y por eso casi nadie lo hace bien. El dev que viene de otro lenguaje suele caer en los mismos cuatro vicios: concatena rutas con strings (`ruta + "/" + nombre`) en vez de usar `pathlib`; abre archivos sin `with` y los deja colgando; parsea CSV con `linea.split(",")` (que se rompe en cuanto un campo trae una coma dentro de comillas); y deja que una sola fila basura tumbe todo el proceso con una excepción no controlada.

Python tiene en su **biblioteca estándar** la respuesta idiomática a las cuatro cosas: `pathlib.Path` para rutas que funcionan en cualquier SO, `with` para que los archivos se cierren solos pase lo que pase, `csv.DictReader` para parsear CSV de verdad (respeta comillas, te da cada fila como `dict`), y `json.dump` para serializar. La habilidad real no es conocer estos módulos — es combinarlos en un pipeline que **convierte tipos por columna** y que, ante una fila malformada, la **descarta y la cuenta** en vez de reventar. Contar lo que descartas es lo que separa un script de juguete de un pipeline de producción: si no sabes cuántas filas perdiste, no sabes si tu dataset es confiable.

Esta kata te da un dataset pequeño y variado —un catálogo de productos— y te pide el pipeline completo de punta a punta, con su invariante de conteo. Sin `pandas`: aquí entrenas los cimientos que `pandas` te esconde.

## Enunciado

Implementa la función `procesar(ruta_csv, ruta_json) -> dict` en `solution.py`. El pipeline es:

`CSV en disco → csv.DictReader → conversión de tipos por fila → filtrado de filas malas → lista enriquecida → json.dump → dict resumen`

El CSV de entrada tiene exactamente tres columnas: `nombre`, `precio`, `stock`.

```csv
nombre,precio,stock
Teclado mecánico,129.90,5
Mouse inalámbrico,49.50,0
Monitor 27",899.00,3
```

Por cada fila debes:

1. Convertir `precio` a `float` y `stock` a `int`.
2. Si una fila tiene un campo no numérico (p. ej. `precio = "abc"`) **o le falta una columna**, descártala y cuéntala — **no revientes**.
3. Enriquecer cada producto válido con un campo derivado `agotado = (stock == 0)`.

Escribe la lista de productos válidos como **JSON indentado** (`indent=2`, `ensure_ascii=False`) en `ruta_json`, y devuelve un `dict` resumen:

```python
{"validos": int, "descartados": int, "total": int}
```

### Ejemplo de entrada → salida

**Entrada** (`catalogo.csv`):

```csv
nombre,precio,stock
Teclado mecánico,129.90,5
Mouse inalámbrico,49.50,0
Cámara web,abc,2
Cable HDMI,12.00
Monitor 27",899.00,3
```

**Salida** — JSON escrito en `ruta_json` (solo las 3 filas válidas, enriquecidas):

```json
[
  {
    "nombre": "Teclado mecánico",
    "precio": 129.9,
    "stock": 5,
    "agotado": false
  },
  {
    "nombre": "Mouse inalámbrico",
    "precio": 49.5,
    "stock": 0,
    "agotado": true
  },
  {
    "nombre": "Monitor 27\"",
    "precio": 899.0,
    "stock": 3,
    "agotado": false
  }
]
```

**Salida** — `dict` devuelto por `procesar`:

```python
{"validos": 3, "descartados": 2, "total": 5}
```

Nota las dos filas que se descartan y por qué: `Cámara web` tiene `precio = "abc"` (no convierte a `float`), y `Cable HDMI` no trae la columna `stock` (le falta un campo). Ambas se cuentan en `descartados`, ninguna tumba el run. `total` es **todas** las filas de datos leídas, no las del archivo menos la cabecera por casualidad: es `validos + descartados`, y esa igualdad es tu invariante.

## Requisitos

1. **Firma exacta**: `procesar(ruta_csv, ruta_json) -> dict`. Acepta tanto `str` como `pathlib.Path` para ambas rutas (convierte internamente con `Path(...)`).
2. **Lectura con `pathlib` + `with`**: abre el CSV con `Path(ruta_csv).open(encoding="utf-8", newline="")` dentro de un `with`. Prohibido concatenar rutas con `+` o abrir sin `with`.
3. **Parsing con `csv.DictReader`**: cada fila llega como `dict`. Prohibido `linea.split(",")`.
4. **Conversión de tipos por columna**: `precio → float`, `stock → int`. La conversión va en un `try/except` que captura **solo** los errores esperados (`ValueError`, `TypeError`, `KeyError`) — no un `except:` desnudo que se trague todo.
5. **Filas malformadas**: una fila con un campo no numérico, con una columna faltante (`None`/`KeyError`) o con campo vacío se **descarta y se cuenta**; el run continúa.
6. **Enriquecimiento**: cada producto válido es un `dict` con `nombre` (str), `precio` (float), `stock` (int) y `agotado` (bool, `= stock == 0`).
7. **Escritura JSON**: `json.dump(productos, f, indent=2, ensure_ascii=False)` sobre `ruta_json` abierto con `pathlib` + `with` en modo escritura. El archivo resultante debe ser parseable con `json.load`.
8. **Resumen**: devuelve `{"validos": v, "descartados": d, "total": v + d}`.
9. **`FileNotFoundError`**: si `ruta_csv` no existe, relanza `FileNotFoundError` con un mensaje que **nombre el archivo** (p. ej. `f"No existe el CSV de entrada: {ruta_csv}"`). No devuelvas un resumen vacío silencioso.
10. **Sin dependencias externas**: solo stdlib (`csv`, `json`, `pathlib`) + `pytest` para los tests. Nada de `pandas`.

## Criterios de aceptación

- [ ] `pytest -q` pasa todos los tests en verde.
- [ ] Con el CSV golden inline (que incluye **al menos 2 filas malformadas**: una con `precio = "abc"` y otra con una columna faltante), `procesar` devuelve el resumen exacto `{"validos": N, "descartados": 2, "total": N + 2}`.
- [ ] El JSON escrito en `ruta_json` es parseable con `json.load` y contiene **exactamente** los productos válidos, cada uno con `precio` de tipo `float`, `stock` de tipo `int` y `agotado` de tipo `bool`.
- [ ] El campo `agotado` es `True` **solo** para los productos con `stock == 0`, y `False` para el resto.
- [ ] El test verifica la invariante `validos + descartados == total` y se cumple.
- [ ] Llamar `procesar` con una ruta inexistente lanza `FileNotFoundError` cuyo mensaje **contiene el nombre del archivo** (verificado con `pytest.raises(FileNotFoundError, match=...)`).
- [ ] El `try/except` de conversión captura solo `ValueError`/`TypeError`/`KeyError`, no excepciones genéricas (revisable a ojo en el código).

## Cómo se evalúa

El harness usa `pytest` con la fixture `tmp_path`: escribe un CSV golden **inline** (con filas válidas y malformadas) en un archivo temporal, llama `procesar`, lee de vuelta el JSON y lo compara contra la lista esperada; además verifica el `dict` resumen, la invariante de conteo, los tipos de cada campo y el caso de ruta inexistente con `pytest.raises`.

Esqueleto que tu solución debe pasar (los datos golden van **inline**; este código es correcto, cópialo y corre tu `solution.py` contra él):

```python
# test_solution.py
import json
from pathlib import Path

import pytest

from solution import procesar

CSV_GOLDEN = """\
nombre,precio,stock
Teclado mecánico,129.90,5
Mouse inalámbrico,49.50,0
Cámara web,abc,2
Cable HDMI,12.00
Monitor 27",899.00,3
"""

ESPERADO = [
    {"nombre": "Teclado mecánico", "precio": 129.90, "stock": 5, "agotado": False},
    {"nombre": "Mouse inalámbrico", "precio": 49.50, "stock": 0, "agotado": True},
    {"nombre": 'Monitor 27"', "precio": 899.00, "stock": 3, "agotado": False},
]


def _escribir_csv(tmp_path: Path) -> Path:
    ruta = tmp_path / "catalogo.csv"
    ruta.write_text(CSV_GOLDEN, encoding="utf-8")
    return ruta


def test_resumen_exacto(tmp_path):
    ruta_csv = _escribir_csv(tmp_path)
    ruta_json = tmp_path / "salida.json"

    resumen = procesar(ruta_csv, ruta_json)

    assert resumen == {"validos": 3, "descartados": 2, "total": 5}


def test_invariante_de_conteo(tmp_path):
    ruta_csv = _escribir_csv(tmp_path)
    resumen = procesar(ruta_csv, tmp_path / "salida.json")

    assert resumen["validos"] + resumen["descartados"] == resumen["total"]


def test_json_escrito_es_correcto(tmp_path):
    ruta_csv = _escribir_csv(tmp_path)
    ruta_json = tmp_path / "salida.json"

    procesar(ruta_csv, ruta_json)
    productos = json.loads(ruta_json.read_text(encoding="utf-8"))

    assert productos == ESPERADO


def test_tipos_de_cada_campo(tmp_path):
    ruta_csv = _escribir_csv(tmp_path)
    ruta_json = tmp_path / "salida.json"

    procesar(ruta_csv, ruta_json)
    productos = json.loads(ruta_json.read_text(encoding="utf-8"))

    for p in productos:
        assert isinstance(p["precio"], float)
        assert isinstance(p["stock"], int)
        assert isinstance(p["agotado"], bool)


def test_agotado_solo_si_stock_cero(tmp_path):
    ruta_csv = _escribir_csv(tmp_path)
    ruta_json = tmp_path / "salida.json"

    procesar(ruta_csv, ruta_json)
    productos = json.loads(ruta_json.read_text(encoding="utf-8"))

    for p in productos:
        assert p["agotado"] == (p["stock"] == 0)


def test_archivo_inexistente(tmp_path):
    ruta_csv = tmp_path / "no_existe.csv"

    with pytest.raises(FileNotFoundError, match="no_existe.csv"):
        procesar(ruta_csv, tmp_path / "salida.json")
```

El coach correrá tu `pytest -q` en vivo y luego abrirá tu `solution.py` para revisar dos cosas a ojo: que el `try/except` capture excepciones **específicas** (no un `except:` desnudo) y que no haya ningún `split(",")` ni concatenación de rutas con `+`. Si cualquiera de las dos aparece, cuenta como hallazgo aunque los tests pasen en verde.

## Pistas

<details><summary>Pista 1 — Leer el CSV y recorrer filas como dicts</summary>

`csv.DictReader` usa la primera línea como cabecera y te entrega cada fila siguiente como un `dict` con esas claves. El patrón base:

```python
from pathlib import Path
import csv

ruta = Path(ruta_csv)
if not ruta.exists():
    raise FileNotFoundError(f"No existe el CSV de entrada: {ruta_csv}")

with ruta.open(encoding="utf-8", newline="") as f:
    lector = csv.DictReader(f)
    for fila in lector:
        ...  # fila == {"nombre": "...", "precio": "...", "stock": "..."}
```

El `newline=""` no es opcional: es lo que el módulo `csv` recomienda para que las comillas y los saltos de línea internos se manejen bien en todos los SO. Si a una fila le falta una columna, `DictReader` pone `None` en esa clave — eso te servirá para detectarla en la conversión.

</details>

<details><summary>Pista 2 — Convertir tipos sin reventar y contar lo descartado</summary>

La conversión y el filtrado son la misma operación: intenta convertir; si falla, esa fila es descartada. Captura **solo** las excepciones que un dato malo produce (`ValueError` por `float("abc")`, `TypeError` por `int(None)`, `KeyError` por una clave ausente):

```python
validos = []
descartados = 0
for fila in lector:
    try:
        precio = float(fila["precio"])
        stock = int(fila["stock"])
    except (ValueError, TypeError, KeyError):
        descartados += 1
        continue
    validos.append({
        "nombre": fila["nombre"],
        "precio": precio,
        "stock": stock,
        "agotado": stock == 0,
    })
```

El `continue` tras contar es lo que hace que el run no se caiga. Nunca uses `except:` o `except Exception:` desnudos aquí: te tragarían bugs reales (un typo en una clave) haciéndolos pasar por "fila mala".

</details>

<details><summary>Pista 3 — Escribir el JSON y devolver el resumen (casi-spoiler)</summary>

`int(None)` lanza `TypeError`, y un campo vacío (`""`) lanza `ValueError` — ambos caen en tu `except`, así que las columnas faltantes y los campos vacíos se descartan solos sin código extra. Para escribir y cerrar el pipeline:

```python
ruta_salida = Path(ruta_json)
with ruta_salida.open("w", encoding="utf-8") as f:
    json.dump(validos, f, indent=2, ensure_ascii=False)

return {
    "validos": len(validos),
    "descartados": descartados,
    "total": len(validos) + descartados,
}
```

`ensure_ascii=False` preserva los acentos (`Cámara`, no `C\u00e1mara`) y `indent=2` lo hace legible. El `total` se calcula como `validos + descartados` **a propósito** — así la invariante se cumple por construcción, sin contar líneas del archivo por separado.

</details>

## Bonus

1. **Reporte de descartes**: además del conteo, acumula los descartados en una lista con el número de fila y el motivo (`{"fila": 4, "motivo": "precio no numérico: 'abc'"}`) y escríbelos en un `descartes.json` aparte. En datos reales, *qué* se cayó importa tanto como *cuántos*.
2. **CLI con `argparse`**: envuelve `procesar` en un `python solution.py entrada.csv salida.json` que imprima el resumen por stdout. Es el primer paso para que tu pipeline sea ejecutable, no solo importable.
3. **Validación de rango**: descarta también filas con `precio < 0` o `stock < 0` (un precio negativo es un dato corrupto, aunque convierta a `float`), y cuéntalas como descartadas. Decide y documenta si eso es un descarte o un error distinto.

## Qué demuestra

- Que combinas `pathlib`, `with`, `csv` y `json` de la stdlib en un pipeline leer-transformar-escribir **idiomático**, sin alcanzar `pandas` para algo que la biblioteca estándar resuelve con cuatro módulos.
- Que conviertes tipos por columna dentro de un `try/except` **específico** y manejas filas malas **contándolas en vez de reventar** — el reflejo de robustez que distingue código de producción de un script de una sola pasada.
- Que razonas con una **invariante** (`validos + descartados == total`) en vez de confiar en que "los números cuadran": el hábito de verificar tu propio procesamiento, que es exactamente el trabajo de datos del mundo real antes de que entre cualquier modelo.

## Entregable

**Al repo** (carpeta `gym/kata-04-csv-a-json-pipeline/` de tu repo de soluciones):

- `solution.py` con `procesar(ruta_csv, ruta_json) -> dict`.
- `test_solution.py` (puedes partir del esqueleto de arriba; agrégale los casos extra que se te ocurran).
- Si hiciste algún bonus, déjalo en el mismo archivo o en uno aparte claramente nombrado.

**En la sesión de revisión** (5 minutos, comparte pantalla):

1. Corre `pytest -q` en vivo y muestra todo verde (1 min).
2. Abre `solution.py` y explica por qué tu `except` captura esas excepciones y no otras (2 min).
3. El coach añadirá una fila malformada nueva al CSV golden (p. ej. un `stock` vacío) y te pedirá predecir el nuevo resumen antes de correr — defiende tu invariante (2 min).