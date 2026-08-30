# Biblioteca y club de lectura

Dos puertas al mismo catálogo:

| Página                 | Qué hay                                    | Se genera desde |
| ---------------------- | ------------------------------------------ | --------------- |
| `biblioteca/index.html`  | artículos, noticias, videos y podcasts     | `catalogo.yaml` + `talleres/videos.yaml` |
| `biblioteca/libros.html` | el club de lectura                         | `catalogo.yaml` (las piezas con `tipo: libro`) |
| `biblioteca/<slug>.html` | una ficha por pieza                        | `catalogo.yaml` |

**Nada de eso se edita a mano.** Se escribe en `catalogo.yaml` y se genera:

```bash
python biblioteca/build.py              # genera las dos portadas y todas las fichas
python biblioteca/build.py --pendientes # solo lista lo que falta escribir
python talleres/enlaces.py              # comprueba que ningún enlace quedó roto
```

## Dónde va cada cosa

```
biblioteca/
├── catalogo.yaml        ← AQUÍ SE ESCRIBE TODO. El resto se genera.
├── build.py             el generador
├── plantilla-ficha.html  la página de una pieza
├── plantilla-indice.html las dos portadas
├── portadas/            las imágenes, descargadas y versionadas
├── index.html           ⟵ generado
├── libros.html          ⟵ generado
└── <slug>.html          ⟵ generado, uno por pieza
```

## Las dos velocidades

El catálogo tiene dos listas y la diferencia entre ellas es el punto entero del
diseño:

- **`inbox`** — captura barata. Url, fecha y una línea de por qué te llamó. Diez
  segundos. No genera página: sale listado al final de la biblioteca como "por
  leer".
- **`piezas`** — la ficha con criterio. Media hora de trabajo. Genera su página.

Solo sube de `inbox` a `piezas` lo que a los pocos días te siga pareciendo
importante. Si la única forma de guardar algo fuera escribir la ficha completa,
no guardarías nada; y si todo lo capturado tuviera ficha, la biblioteca sería un
montón de enlaces con resúmenes tibios, que es exactamente lo que ya hace
cualquier gestor de marcadores.

## El contenido se escribe después de leer

`resumen`, `valioso`, `conecta` y `reparos` son opcionales. Sin `resumen`, la
ficha se genera igual —con su portada, su ficha técnica y el enlace al
original— pero muestra el estado **pendiente** en lugar de inventarse una
opinión.

Es la misma decisión que ya rige los videos de los talleres, y del mismo tipo
que la del código: igual que el taller nunca muestra código que no corre, la
biblioteca no resume algo que nadie leyó. Un resumen inventado se lee perfecto y
es justo lo que un alumno no puede detectar.

`reparos` es el campo que hace que esto valga la pena. Es el único que no trae
la pieza original.

## Añadir una pieza

1. Se escribe en `catalogo.yaml`, bajo `piezas`, con su slug en minúsculas y
   guiones (será el nombre del archivo).
2. Si tiene una imagen decente, se descarga a `portadas/` (ver
   [`portadas/README.md`](portadas/README.md)). Si no, se deja sin `portada` y
   se compone una tipográfica.
3. `python biblioteca/build.py`.

El generador valida el YAML antes de escribir nada: un campo mal escrito, un
`tipo` que no existe, un id de sesión que no resuelve o una portada que no está
descargada **rompen el build** en vez de desaparecer silenciosamente de la
página.

## Los videos de los talleres no se copian

Los 24 videos de `talleres/videos.yaml` ya tienen su ficha y su página. La
biblioteca los **lee y los lista** —si no, seguirían escondidos detrás de un día
de taller, que era su único acceso— pero enlaza a la página que ya genera
`talleres/build.py`. Se corrigen allí, no aquí.

En `catalogo.yaml` solo van los videos sueltos: los que no cuelgan de un día.

## Enganchar con el programa

El campo `sesiones` acepta ids cortos que se resuelven contra los archivos que
existen de verdad:

| Se escribe   | Resuelve a                                   |
| ------------ | -------------------------------------------- |
| `sesion-08`  | `sesiones/sesion-08-evals.html`              |
| `prefase-03` | `sesiones/prefase-03-…​.html`                 |
| `taller-04`  | `talleres/sesion-04.html`                    |
| `reto-05`    | `gym/reto-05-…/README.md` (por el visor)     |
| `kata-02`    | `gym/kata-02-…/README.md` (por el visor)     |

Un id inventado rompe el build. Es a propósito: el enlace muerto se descubre
meses después y para entonces nadie recuerda a qué apuntaba.
