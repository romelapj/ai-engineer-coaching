# 🏋️ Kata 00: Smoke test de entorno

| Metadato                  | Valor                                                                                                                                  |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| **Fase**                  | Pre-Fase 0.5: Fundamentos de Python                                                                                                  |
| **Sesión en que se asigna** | Sesión N00                                                                                                                          |
| **Tiempo estimado**       | 30–45 min                                                                                                                             |
| **Skill que entrena**     | venv/pip reproducible, verificar contra ground truth con un test, leer la versión del intérprete                                       |
| **Stack**                 | Python 3.10+, `venv`, `pip`, `pytest`. **Sin** Poetry, **sin** conda, **sin** Docker: stdlib + pip                                     |

---

## Contexto

El fallo más caro de las primeras horas de cualquier programa no es conceptual: es _"no me corrió nada"_, _"me explotó el import"_, _"el venv quedó mezclado con el del sistema"_. Cero líneas de lógica y media tarde perdida en plumbing. Si vienes de otro lenguaje, esto te va a sonar familiar pero distinto: Python no tiene un `node_modules` local por defecto ni un `cargo`/`go.mod` que aísle el proyecto solo. El aislamiento es **explícito y opt-in**: si no creas y activas un entorno virtual, `pip install` te ensucia el Python del sistema (o el del SO, que en macOS/Linux es sagrado y no debes tocar). Entender esto el día 0 te ahorra el clásico _"a mí me funciona"_ que en realidad significa _"tengo tres paquetes globales que olvidé que instalé"_.

Esta kata de-riskea exactamente eso: construyes un repo que **se prueba a sí mismo** que está bien montado. De paso interiorizas el hábito que recorre todo el curso: **verificar contra ground truth en vez de confiar en que "debería funcionar"**. Un test que asevera `suma(2, 3) == 5` no es trivial por ingenuo: es la versión mínima de la disciplina que vas a aplicar en las 7 katas siguientes, donde "parece que corre" no cuenta y solo el verde de `pytest` cuenta.

Es la kata **más corta a propósito**. Su valor no es lo que aprendes de Python (casi nada de lógica), sino garantizar que nadie arrastra un entorno roto a las katas siguientes. Un entorno sano hoy = cero horas perdidas en plumbing mañana.

## Enunciado

Crea el repo `nivelacion-python/` que alojará las **8 katas** del curso. En esta solo montas el cimiento: un **entorno reproducible** y un **test de humo** que lo valida.

El test (`test_smoke.py`) debe verificar **tres cosas que SIEMPRE pasan en verde** sin red ni secretos:

1. Que `pytest` **importa** sin `ImportError` (el entorno tiene la dependencia instalada).
2. Que la versión de Python es **3.10 o superior**, leída de `sys.version_info`.
3. Que una **función propia trivial** (`suma(a, b)` en `solution.py`) devuelve el valor esperado, demostrando que tu código se importa y corre desde el test.

### Forma del entorno

El repo de esta kata debe tener esta estructura mínima:

```
nivelacion-python/
├── .venv/              # entorno virtual: NO se versiona
├── requirements.txt    # curado, con pytest pineado
├── solution.py         # tu función suma(a, b)
├── test_smoke.py       # los 3 tests de humo
├── .gitignore          # ignora .venv/ y __pycache__/
└── README.md           # comando exacto de setup, copiable tal cual
```

### Ejemplo de lo que produce un setup sano

```console
$ python -m venv .venv
$ source .venv/bin/activate
(.venv) $ pip install -r requirements.txt
...
Successfully installed pytest-8.x.x ...
(.venv) $ which python
/ruta/al/repo/nivelacion-python/.venv/bin/python   # ← apunta DENTRO de .venv
(.venv) $ pytest -q
...                                                              [100%]
3 passed in 0.02s
```

El detalle que importa: tras `source .venv/bin/activate`, `which python` debe apuntar **dentro** de `.venv/`. Si apunta a `/usr/bin/python` o a un Homebrew global, el entorno no está activado y todo lo demás es una ilusión.

## Requisitos

1. **Entorno virtual aislado**: el proyecto usa un `.venv/` creado con `python -m venv .venv`. No se instala nada con `sudo pip` ni en el Python del sistema.
2. **`requirements.txt` curado**: existe, no está vacío y pinea **al menos** `pytest` (formato `pytest==X.Y.Z`, no `pytest` a secas: reproducibilidad significa misma versión en cualquier máquina).
3. **`solution.py`** con una función `suma(a, b)` que devuelve `a + b`. Usa type hints (`def suma(a: int, b: int) -> int:`).
4. **`test_smoke.py`** con **exactamente 3 tests**, uno por cada verificación del enunciado (import de `pytest`, versión del intérprete, función propia).
5. **Test de versión explícito**: asevera `sys.version_info >= (3, 10)` (comparación de tuplas, no parseo de strings).
6. **Test de función propia**: importa `suma` desde `solution.py` y asevera `suma(2, 3) == 5`.
7. **`.gitignore`** que ignora `.venv/` y `__pycache__/` (y `*.pyc`). El repo no versiona ni el entorno ni los bytecodes.
8. **`README.md`** con el comando de setup **copiable tal cual** (las cuatro líneas: crear venv, activar, instalar, correr tests).

## Criterios de aceptación

- [ ] `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` deja el entorno listo **sin errores en una máquina limpia** (probado en un clon nuevo, no en tu máquina con paquetes globales).
- [ ] `python -c "import pytest"` no lanza `ImportError` y termina con **exit code 0** (verificable con `echo $?`).
- [ ] `pytest -q` corre **exactamente 3 tests** y termina en `3 passed`: verde total, sin depender de red ni secretos.
- [ ] El test de versión verifica explícitamente que `sys.version_info >= (3, 10)` es `True` (no `assert True`, no lectura de string).
- [ ] El test de la función propia **importa `suma` desde `solution.py`** y asevera `suma(2, 3) == 5`.
- [ ] `requirements.txt` existe, no está vacío y pinea al menos `pytest` con `==`.
- [ ] El repo **NO versiona** `.venv/` ni `__pycache__/`, verificable con `git status` limpio tras correr los tests (cubierto por `.gitignore`).
- [ ] El `README.md` documenta el comando de setup copiable tal cual, y al pegarlo en una terminal limpia funciona sin editar nada.

## Cómo se evalúa

El harness es el propio `pytest` corriendo sobre tu repo recién clonado y montado: el coach hace `python -m venv .venv`, activa, instala desde tu `requirements.txt` y corre `pytest -q`. Si no salen **3 passed** sin tocar nada, la kata no está lista. No hay red, ni API keys, ni datos externos: el verde está **garantizado en cualquier máquina con Python 3.10+** si el entorno y los tests están bien.

Los datos golden son triviales y van **inline en el propio test** (la versión mínima esperada y el resultado esperado de `suma`). Esqueleto correcto y completo:

```python
# test_smoke.py
import sys


def test_pytest_se_importa():
    # Si llegamos aquí, pytest ya importó (lo está ejecutando).
    # Lo hacemos explícito para que el test falle con mensaje claro
    # si alguien corre el archivo en un entorno sin pytest.
    import pytest

    assert pytest.__version__  # no vacío


def test_version_de_python():
    # Golden inline: el piso mínimo del curso es Python 3.10.
    assert sys.version_info >= (3, 10), f"Python {sys.version} es < 3.10"


def test_suma_funciona():
    from solution import suma

    assert suma(2, 3) == 5
```

```python
# solution.py
def suma(a: int, b: int) -> int:
    return a + b
```

El coach corre `pytest -q` y espera ver, palabra por palabra:

```console
3 passed
```

Si ve `2 passed, 1 error` por un import roto, o `collected 4 items` porque hay un test colado, o un fallo de versión, la kata se devuelve. El criterio es binario: verde de 3 o nada.

## Pistas

<details><summary>Pista 1 (venv): crearlo no basta, hay que activarlo</summary>

`python -m venv .venv` solo **crea** la carpeta del entorno; no lo activa. Activar es un paso aparte y depende del shell:

- macOS / Linux (bash/zsh): `source .venv/bin/activate`
- Windows (PowerShell): `.venv\Scripts\Activate.ps1`

Cómo confirmar que quedó activado: tras activar, tu prompt muestra `(.venv)` al inicio, y `which python` (o `where python` en Windows) apunta **dentro** de `.venv/`. Si `which python` te devuelve `/usr/bin/python` o un path de Homebrew, no está activado, y cualquier `pip install` que hagas va al Python global, no al del proyecto. Regla mental: si no ves `(.venv)` en el prompt, asume que estás en el entorno equivocado.

</details>

<details><summary>Pista 2: `sys.version_info` es una tupla comparable, no un string</summary>

La tentación de quien viene de otro lenguaje es parsear `sys.version` (que es un string tipo `"3.11.4 (main, ...)"`) con split y casteos. No lo hagas. Python expone `sys.version_info`, que es una tupla con orden natural, así que puedes compararla directo:

```python
import sys
sys.version_info >= (3, 10)   # True en 3.10, 3.11, 3.12...
```

La comparación es **lexicográfica por componentes**: `(3, 9) < (3, 10) < (3, 10, 1) < (4, 0)`. No necesitas convertir nada. Esto es idiomático en Python y es lo que se espera ver en el test, no un `int(sys.version.split(".")[1])`.

</details>

<details><summary>Pista 3: import de tu propio módulo y `.gitignore` mínimo (casi-spoiler)</summary>

**Import del módulo propio:** como `pytest` se corre desde la raíz del repo (donde viven `solution.py` y `test_smoke.py`), `from solution import suma` funciona sin tocar `PYTHONPATH` ni crear `__init__.py`: pytest agrega la raíz al `sys.path` automáticamente (modo rootdir). Si te falla el import, casi seguro estás corriendo `pytest` desde otra carpeta; corre `pytest -q` parado en la raíz del repo.

**`.gitignore` mínimo** que cubre el criterio de "no versionar entorno ni bytecodes":

```gitignore
.venv/
__pycache__/
*.pyc
```

**`requirements.txt` pineado** (saca la versión exacta con `pip freeze | grep pytest` tras instalar, y pégala):

```
pytest==8.3.4
```

Con eso, un clon limpio + las 4 líneas del README dan `3 passed` sin sorpresas. Verifica que `git status` esté limpio tras correr los tests: si aparece `.venv/` o `__pycache__/` como untracked, tu `.gitignore` no está cubriendo lo que debe.

</details>

## Bonus

1. **Matriz de versiones con `tox` o a mano**: confirma que tu test pasa en Python 3.10, 3.11 y 3.12 (si tienes varias instaladas, crea un `.venv` por versión y corre los 3). Documenta en el README en qué versiones validaste. Es la semilla del concepto de _matriz de compatibilidad_ que verás en CI más adelante.
2. **CI mínimo en GitHub Actions**: un workflow que en cada push crea el venv, instala `requirements.txt` y corre `pytest -q`. Si los 3 tests pasan en un runner limpio de GitHub (no tu máquina), tienes la prueba definitiva de reproducibilidad: la kata corre en un entorno que nunca tocaste.

## Qué demuestra

Que montas un **entorno reproducible** y escribes un **test que verifica el setup antes de escribir lógica**: el reflejo de "no confío, verifico" aplicado al plumbing. Demuestra que distingues un entorno **sano** de uno que _"parece que funciona"_: sabes que `pip install` sin venv activo es una bomba de tiempo, que reproducibilidad significa **versión pineada** y no "la que tenga a mano", y que `sys.version_info` se compara como tupla en vez de parsear strings a lo bruto. No es fluidez de algoritmos; es la fluidez de plumbing sin la cual ninguna de las otras 7 katas arranca limpia.

## Entregable

**Al repo** (carpeta raíz `nivelacion-python/`, que reutilizarás para las 8 katas):

- `solution.py` con `suma(a, b)` tipada.
- `test_smoke.py` con los **3 tests** de humo (import de `pytest`, versión, función propia).
- `requirements.txt` con `pytest` pineado con `==`.
- `.gitignore` que ignora `.venv/`, `__pycache__/` y `*.pyc`.
- `README.md` con las **4 líneas de setup** copiables tal cual (crear venv, activar, instalar, correr tests).
- **No** versiones `.venv/` ni `__pycache__/`.

**En la sesión de revisión** (5 minutos, comparte pantalla):

1. Clona el repo en una carpeta nueva y corre las 4 líneas del README en vivo → `3 passed` (2 min).
2. Muestra `which python` con el venv activo apuntando dentro de `.venv/` (1 min).
3. Corre `git status` y muestra que está limpio (nada de `.venv/` ni `__pycache__/` colado) (1 min).
4. Explica en una frase por qué `sys.version_info >= (3, 10)` es mejor que parsear `sys.version` (1 min).