# 🏋️ Kata 06 — Modelar un dominio con dataclass

| Metadato            | Valor                                                                                                                  |
| ------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **Fase**            | Pre-Fase 0.5 — Fundamentos de Python                                                                                   |
| **Sesión en que se asigna** | Sesión 5                                                                                                       |
| **Tiempo estimado** | 45–60 min                                                                                                              |
| **Skill que entrena** | `dataclass`: `__init__`/`__repr__`/`__eq__` generados, métodos derivados, `default_factory`, modelar sin sobre-ingeniería |
| **Stack**           | Python 3.10+ stdlib (`dataclasses`), `pytest`. **Sin** Pydantic en esta kata: dataclass pura                          |

---

## Contexto

Si vienes de Java, C# o TypeScript, tu reflejo al modelar un registro de datos es escribir una clase con su constructor a mano: declarar los campos, asignarlos uno por uno en `__init__`, y luego pelear con `equals()`/`hashCode()` y un `toString()` que siempre se queda desactualizado. En Python ese boilerplate es innecesario, y escribirlo a mano delata que no conoces el lenguaje.

`@dataclass` resuelve exactamente ese caso: anotas los campos con tipos y el decorador **genera por ti** `__init__`, `__repr__` y `__eq__`. Tú agregas debajo solo los métodos que aportan comportamiento real. Es la herramienta correcta para un **registro con datos + un par de comportamientos derivados** — ni una función suelta (que no agrupa estado), ni una jerarquía de herencia (sobre-ingeniería para tres campos).

Esta kata entrena dos cosas que separan al que sabe Python del que lo escribe como si fuera otro lenguaje:

1. **Saber cuándo una clase es la herramienta correcta** y cuándo una función basta. Para un carrito de compras —datos más comportamiento derivado— la dataclass es el punto justo.
2. **El default mutable**, una de las trampas clásicas de Python. Si escribes `items: list = []` como default, **todas** las instancias comparten la misma lista. La solución idiomática es `field(default_factory=list)`, y conocerla es señal de que ya te quemaste con el bug (o de que estudiaste bien).

El objetivo no es "hacer OOP". Es OOP-lite con criterio: el mínimo de estructura que el dominio necesita, sin una línea de boilerplate de más.

## Enunciado

Modela un **carrito de compras** en `solution.py` usando dataclasses. El dominio es minúsculo y real: ítems con nombre, precio y cantidad, y un carrito que los agrega y calcula totales.

### Modelo de referencia

```python
from dataclasses import dataclass, field

@dataclass
class Item:
    nombre: str
    precio: float
    cantidad: int = 1

    def subtotal(self) -> float:
        ...  # precio * cantidad, redondeado a 2 decimales

@dataclass
class Carrito:
    items: list[Item] = field(default_factory=list)

    def agregar(self, item: Item) -> None:
        ...

    def total(self) -> float:
        ...  # suma de subtotales, a 2 decimales

    def cantidad_items(self) -> int:
        ...  # suma de cantidades

    def aplicar_descuento(self, pct: float) -> float:
        ...  # total con pct% de descuento, a 2 decimales
```

### Ejemplo de uso → resultado

```python
carrito = Carrito()
carrito.agregar(Item("Taza", 10.0, 3))    # subtotal 30.0
carrito.agregar(Item("Pin", 2.5))         # cantidad default 1 → subtotal 2.5

carrito.total()             # 32.5
carrito.cantidad_items()    # 4   (3 + 1)
carrito.aplicar_descuento(10)  # 29.25  (32.5 * 0.90)

Item("Taza", 10.0, 3) == Item("Taza", 10.0, 3)   # True  (__eq__ generado)
repr(Item("Taza", 10.0, 3))   # "Item(nombre='Taza', precio=10.0, cantidad=3)"
```

Fíjate en las decisiones que el modelo te obliga a tomar:

- **`cantidad: int = 1`** es un default inmutable (un `int`) — seguro de poner directo.
- **`items: list[Item] = field(default_factory=list)`** es un default **mutable** — `= []` aquí sería un bug. Esa es la diferencia que la kata mide.
- `subtotal`, `total` y `aplicar_descuento` son comportamiento **derivado** del estado: van como métodos, no como atributos que tengas que mantener sincronizados.

## Requisitos

1. **`@dataclass Item`** con `nombre: str`, `precio: float`, `cantidad: int = 1`, y un método `subtotal() -> float` que devuelva `precio * cantidad` redondeado a 2 decimales.
2. **`@dataclass Carrito`** con `items: list[Item] = field(default_factory=list)` y los métodos:
   - `agregar(item: Item) -> None`: añade un ítem a la lista.
   - `total() -> float`: suma de los subtotales, redondeada a 2 decimales.
   - `cantidad_items() -> int`: suma de las cantidades de todos los ítems.
   - `aplicar_descuento(pct: float) -> float`: el total con un `pct`% de descuento aplicado, redondeado a 2 decimales.
3. **`__init__`, `__repr__` y `__eq__` generados por la dataclass**: no los escribas a mano. `Item` igual a otro `Item` con los mismos campos debe dar `True`.
4. **Prohibido**: herencia, clases con `__init__` escrito a mano, y `items=[]` como default (default mutable compartido). Permitido y esperado: `@dataclass`, `field(default_factory=list)`, type hints, comprehensions dentro de los métodos.
5. **Todo en `solution.py`**, stdlib pura (`from dataclasses import dataclass, field`). Sin dependencias externas.

## Criterios de aceptación

- [ ] `Item("Taza", 10.0, 3).subtotal() == 30.0` y `Item("Pin", 2.5).subtotal() == 2.5` (la cantidad default de 1 se aplica).
- [ ] `Carrito()` arranca con `items == []`, y dos instancias `Carrito()` distintas **no comparten** la misma lista (agregar a una no afecta a la otra) — prueba de que usaste `default_factory`.
- [ ] Tras agregar `Item("Taza", 10.0, 3)` e `Item("Pin", 2.5)`: `total() == 32.5` y `cantidad_items() == 4`.
- [ ] `aplicar_descuento(10)` sobre un total de `32.5` devuelve `29.25` (redondeado a 2 decimales).
- [ ] `Item("Taza", 10.0, 3) == Item("Taza", 10.0, 3)` es `True`, y `repr(Item("Taza", 10.0, 3))` contiene `nombre`, `precio` y `cantidad`.
- [ ] La solución usa `@dataclass` y `field(default_factory=list)`; **cero** `__init__` escrito a mano y **cero** herencia (se revisa en code review).
- [ ] `pytest -q` pasa todos los tests en verde.

## Cómo se evalúa

El harness es un archivo `test_solution.py` con **datos golden inline**: los ítems y carritos se construyen dentro de cada test y los totales/subtotales/descuentos esperados están escritos a mano (no calculados con tu propio código, para que el test sea verdad independiente). Hay un test dedicado a verificar que dos `Carrito()` tienen listas **independientes** —la trampa del default mutable— y otro al `__eq__` generado.

Corre con `pytest -q` desde la carpeta de la kata. Esqueleto del harness (los valores esperados son los golden):

```python
# test_solution.py
from solution import Item, Carrito


def test_subtotal_con_cantidad():
    assert Item("Taza", 10.0, 3).subtotal() == 30.0


def test_subtotal_cantidad_default():
    assert Item("Pin", 2.5).subtotal() == 2.5  # cantidad = 1 por default


def test_total_y_cantidad():
    carrito = Carrito()
    carrito.agregar(Item("Taza", 10.0, 3))
    carrito.agregar(Item("Pin", 2.5))
    assert carrito.total() == 32.5
    assert carrito.cantidad_items() == 4


def test_aplicar_descuento():
    carrito = Carrito()
    carrito.agregar(Item("Taza", 10.0, 3))
    carrito.agregar(Item("Pin", 2.5))            # total 32.5
    assert carrito.aplicar_descuento(10) == 29.25


def test_carritos_no_comparten_lista():
    a = Carrito()
    b = Carrito()
    a.agregar(Item("Taza", 10.0, 1))
    assert a.items != b.items          # b sigue vacío
    assert b.items == []               # default_factory: lista propia por instancia


def test_item_eq_y_repr():
    assert Item("Taza", 10.0, 3) == Item("Taza", 10.0, 3)
    assert Item("Taza", 10.0, 3) != Item("Taza", 10.0, 2)
    r = repr(Item("Taza", 10.0, 3))
    assert "nombre" in r and "precio" in r and "cantidad" in r


def test_carrito_vacio():
    vacio = Carrito()
    assert vacio.total() == 0.0
    assert vacio.cantidad_items() == 0
```

En la revisión, el coach va a abrir `solution.py` y mirar dos cosas concretas: que el default de `items` use `field(default_factory=list)` (no `[]`), y que **no** haya un `__init__` ni un `__eq__` escritos a mano. Si los escribiste a mano, aunque pasen los tests, cuenta como hallazgo: el punto de la kata es que la dataclass te los regale.

## Pistas

<details><summary>Pista 1 — Qué te genera <code>@dataclass</code> y dónde van tus métodos</summary>

Al poner `@dataclass` sobre una clase con campos anotados (`nombre: str`, `precio: float`, ...), el decorador genera `__init__`, `__repr__` y `__eq__` a partir de esos campos. No escribas ninguno de los tres. Tus métodos con lógica (`subtotal`, `total`, ...) van como métodos normales **debajo** de los campos, con `self` como primer parámetro:

```python
@dataclass
class Item:
    nombre: str
    precio: float
    cantidad: int = 1

    def subtotal(self) -> float:
        return round(self.precio * self.cantidad, 2)
```

Los campos con default (`cantidad: int = 1`) deben ir **después** de los que no tienen default, igual que en una firma de función.

</details>

<details><summary>Pista 2 — El default mutable y por qué <code>= []</code> es un bug</summary>

Si escribes `items: list[Item] = []`, ese `[]` se crea **una sola vez** cuando Python define la clase, y todas las instancias de `Carrito` comparten esa misma lista: agregar a un carrito aparecería en todos. Es la trampa clásica de Python (la misma de los default mutables en argumentos de función). La dataclass de hecho te lanza un error si lo intentas. La forma correcta es pasar una **fábrica** que se llama una vez por instancia:

```python
from dataclasses import dataclass, field

@dataclass
class Carrito:
    items: list[Item] = field(default_factory=list)
```

Así cada `Carrito()` nace con su propia lista vacía. El test `test_carritos_no_comparten_lista` existe justo para cazar esto.

</details>

<details><summary>Pista 3 — Los métodos derivados, idiomáticos (casi-spoiler)</summary>

Los tres cálculos del carrito salen en una línea cada uno con una comprehension/`sum`, sin bucles manuales con acumuladores:

```python
def total(self) -> float:
    return round(sum(item.subtotal() for item in self.items), 2)

def cantidad_items(self) -> int:
    return sum(item.cantidad for item in self.items)

def aplicar_descuento(self, pct: float) -> float:
    return round(self.total() * (1 - pct / 100), 2)
```

Nota que `aplicar_descuento` **reutiliza** `total()` en vez de recalcular la suma: un método derivado puede apoyarse en otro. Y `sum` sobre una lista vacía devuelve `0` de forma natural, así que el carrito vacío (`total() == 0.0`) funciona sin un caso especial.

</details>

## Bonus

1. **`@dataclass(frozen=True)` para `Item`**: hazlo inmutable. Un `Item` congelado no se puede mutar tras crearse (`item.precio = 5` lanza `FrozenInstanceError`) y se vuelve hasheable, así que podrías usarlo en un `set` o como clave de dict. Discute en 2 líneas cuándo conviene que un registro de dominio sea inmutable.
2. **`@dataclass(order=True)`**: agrega ordenamiento a `Item` para poder hacer `sorted(carrito.items)`. Investiga qué campo manda el orden por default y cómo controlarlo con `field(compare=...)` si solo quieres ordenar por precio.
3. **Método `quitar(nombre: str)`**: elimina del carrito el primer ítem cuyo nombre coincida, y devuelve `True`/`False` según si encontró algo. Te obliga a recorrer la lista buscando, no solo a sumar.

## Qué demuestra

Demuestra que modelas un dominio pequeño con la herramienta justa de Python: una `@dataclass` que te regala `__init__`, `__repr__` y `__eq__`, métodos derivados idiomáticos (`sum` + comprehension, reutilizando un método desde otro), y el manejo correcto del default mutable con `field(default_factory=list)`. Es decir: que sabes hacer OOP-lite **sin** arrastrar boilerplate de otro lenguaje ni sobre-ingeniería (nada de herencia ni `__init__` a mano para tres campos). Conocer `default_factory` en particular delata que ya entiendes una de las trampas más características de Python, no que la copiaste.

## Entregable

**Al repo** (carpeta `gym/kata-06-dataclass-de-dominio/` de tu repo de soluciones):

- `solution.py` con `Item` y `Carrito` (dataclasses, métodos derivados, sin `__init__`/`__eq__` a mano, sin herencia).
- `test_solution.py` con el harness de arriba en verde (puedes añadir tests propios, no quitar los golden).
- Opcional: `README.md` de una línea con cómo correr (`pytest -q`) y cualquier bonus que hayas hecho.

**En la sesión de revisión** (5 minutos, comparte pantalla):

1. Corre `pytest -q` en vivo: todo verde.
2. Abre `solution.py` y muestra que `items` usa `field(default_factory=list)` y que no escribiste `__init__` ni `__eq__`.
3. Explica en una frase por qué `= []` como default habría sido un bug (la trampa del default mutable compartido).