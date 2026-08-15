# 03 · Versiones del curso

Historial de las fases por las que ha pasado el programa. Cada entrada dice qué
era el curso en ese momento, qué se cambió y por qué. Las fechas salen del
historial de git del repositorio.

---

## v1 · La plataforma inicial

**14 de junio de 2026** · commits `6b67be2`, `2e54490`

Nace la plataforma: portal, 14 decks y el AI Gym. Formato de sesión: **90
minutos, una vez por semana**, con la estructura repaso → tema central → manos
al código → reto de la semana.

Decisiones que se mantienen hasta hoy:

- **Construir > consumir.** El alumno escribe el sistema, no mira cómo alguien
  lo escribe.
- **Evals-first.** Se mide antes de opinar.
- **Evidencia real.** Cada semana un entregable en un repo.
- Sin frameworks mágicos: cada pieza del pipeline se entiende por dentro.

También en esta versión: visor de Markdown en GitHub Pages, para que las guías
del coach y los retos del gym se lean desde el portal.

---

## v2 · Nivelación de Python y storytelling

**6 de julio de 2026** · commits `57b34cf`, `cfc1705`, `d226942`, `e61479a`

Se detecta que parte del alumnado no llega con el Python suficiente para la
sesión 01. Cambios:

- Se agregan **6 decks de nivelación** (`prefase-00` a `prefase-05`): un curso
  de Python completo, separado en el portal para que no estorbe a quien no lo
  necesita. El curso pasa de 14 a **20 decks**.
- Se reescriben los 20 decks con storytelling: cada uno abre con el problema
  real que resuelve, no con la definición del tema.
- **Botón de copiar** en todos los bloques de código.
- Commit `e61479a`: **"Cierra 88 huecos de reproducibilidad en los 20 decks
  (código ejecutable al pie de la letra)"**.

Ese último commit es el dato importante de esta versión. 88 huecos encontrados y
parchados a mano, y el problema volvió a aparecer. Es la evidencia de que la
causa no era el descuido: era el formato. Ver
[01 · Análisis del formato deck](01-analisis-formato-decks.md).

---

## v3 · 30 minutos diarios

**Agosto de 2026**

El formato de 90 minutos semanales no alcanzaba para cubrir lo que la sesión
pretendía mostrar. Los 30 minutos de "manos al código" de la sesión 04, por
ejemplo, tenían que recorrer 643 líneas repartidas en 5 archivos: 6 minutos por
archivo, escribiendo en vivo.

**Cambio:** de una sesión de 90 minutos semanal a **sesiones de 30 minutos
diarias**, cada una centrada en un código. La sesión grande sigue existiendo
como unidad temática, pero por dentro se parte en tramos de un día.

Consecuencias:

- El alumno toca el código todos los días en vez de una vez por semana.
- Cada tramo tiene que ser autocontenido: empezar, avanzar y cerrar en 30
  minutos, con un punto de verificación al final.
- El alumno necesita poder **retomar donde quedó** sin depender del coach.

---

## v4 · Talleres interactivos

**15 de agosto de 2026** · en piloto

El formato deck no soporta ni el volumen de código ni la nueva cadencia diaria.
Se adopta el **formato taller**: páginas de pasos generadas desde el repositorio
ejecutable. Ver [02 · Decisión: formato taller](02-decision-formato-taller.md).

Qué entra en esta versión:

- `talleres/build.py` · generador: lee `taller.yaml` + el código real y produce
  el HTML. Detecta líneas que ningún paso explica.
- `talleres/verificar.py` · comprueba que pegando los bloques de la página en
  orden sale el archivo original byte a byte. Pensado para CI.
- `talleres/plantilla.html` · la plantilla del taller: navegación por días,
  progreso persistido, botón de copiar, notas del coach conmutables.
- `talleres/sesion-04/` · **el piloto**: 6 días, 28 pasos, 643 líneas de código
  con sus salidas reales capturadas.
- El código de la sesión 04, que vivía fuera del repositorio, entra a
  `talleres/sesion-04/codigo/`.

Qué **no** cambia: los 20 decks siguen publicados y siguen siendo el material de
la parte teórica en vivo.

---

## v4.1 · Fase 1 completa y sistema visual propio

**15 de agosto de 2026**

El piloto se extiende a las sesiones 01, 02 y 03, y la plantilla recibe una
pasada de diseño. La Fase 1 del programa (fundamentos) queda cubierta de punta
a punta con talleres.

| Taller                         | Días | Pasos | Origen del código                                        |
| ------------------------------ | ---: | ----: | -------------------------------------------------------- |
| 01 · Tokens, dinero y vectores |    6 |    20 | Escrito desde cero a partir del deck                     |
| 02 · La API por dentro         |    7 |    27 | Reescritos los 7 archivos sueltos de `test-ai/sesion-02` |
| 03 · Tool use                  |    7 |    30 | Convertidos tal cual desde `test-ai/session-03/ejemplos` |
| 04 · RAG desde cero            |    6 |    28 | El piloto                                                |

**El enlace entre talleres se activa solo.** Cada `taller.yaml` declara cuál es
el siguiente; el generador comprueba si ese archivo existe en disco. Mientras no
exista, la tarjeta sale en ámbar como _"aún no publicado"_ con el deck como
alternativa. Al publicar el taller 03, el enlace del 02 se encendió sin tocar
nada.

**Sistema visual.** La plantilla pasó a paleta neutra profunda con **un solo
acento**, tipografía de contraste drástico y disposición editorial (la cifra del
paso vive en el margen, fuera de la columna de texto). Antes competían cuatro
acentos y no había `focus-visible` en ningún control. Ver
[05 · Sistema visual](05-sistema-visual.md).

**Tres hallazgos del material** que quedaron dentro de los talleres porque
enseñan más que la versión "que funciona":

1. **Sesión 01** · el modelo de embeddings local (`all-MiniLM-L6-v2`) ordena
   bien en inglés y **se rompe en español**: "receta de arepas" puntúa más alto
   que "checkout con visa". No falla ni avisa. Es el mejor ejemplo de fallo
   silencioso del curso.
2. **Sesión 01** · el mismo texto cuenta 63 tokens en Sonnet y 85 en Opus.
   Tokenizadores distintos; el conteo no se extrapola entre modelos.
3. **Sesión 02** · el golden set original (10 casos) daba 100% con las dos
   versiones del prompt: no discriminaba. Se le agregaron 6 casos límite y ahora
   separa 81% (v1) de 88% (v2). El caso 12 lo fallan las dos, y eso también
   enseña: el problema no es el prompt, es la taxonomía de clases.

Pendiente de medir: ver "Cómo se sabrá si funcionó" en el documento 02.

---

## v4.2 · La sesión 05 y dos ajustes de plantilla

**15 de agosto de 2026**

Entra el taller de la sesión 05 (retrieval avanzado), el más grande del curso:
**10 días, 41 pasos, 1.376 líneas** repartidas en 10 archivos. Más del doble que
el piloto. La razón es que esta sesión no construye otro RAG: construye el
instrumento que decide si el que ya existe sirve.

| Taller                  | Días | Pasos | Líneas | Origen del código             |
| ----------------------- | ---: | ----: | -----: | ----------------------------- |
| 05 · Retrieval avanzado |   10 |    41 |  1.376 | `test-ai/session-05/ejemplos` |

Es el primer taller con **módulos compartidos** (`base.py`, `rag.py`,
`metricas.py`, `retrieval.py`) además de los seis scripts numerados. Eso obligó a
repartir cada módulo en su propio día en vez de meterlo dentro del script que lo
usa, y salió mejor: el día 2 (`rag.py`) es el único de todo el curso cuyo
contenido es "aquí no cambia nada, y ese es el punto".

**El resultado que el taller persigue, medido:**

| variante              | recall@1 | recall@5 | recall@10 |  MRR | latencia |
| --------------------- | -------: | -------: | --------: | ---: | -------: |
| vectorial (sesión 04) |     0.60 |     0.87 |      0.93 | 0.71 |   0.08 s |
| solo BM25             |     0.73 |     0.93 |      0.93 | 0.81 |   0.00 s |
| híbrido RRF           |     0.73 |     0.87 |      1.00 | 0.82 |   0.08 s |
| híbrido + rerank      |     1.00 |     1.00 |      1.00 | 1.00 |   1.63 s |

La fila de "solo BM25" está en el taller **a propósito**: empata al híbrido en
recall@1 y le gana en recall@5, y aun así es la peor opción. Solo la columna
recall@10 lo desmiente. Enseñar a leer esa tabla sin engañarse vale más que el
1.00 final.

**Dos ajustes de plantilla:**

1. **Se quitaron los `max-width` de la prosa.** La columna ya está acotada por la
   retícula; el tope adicional dejaba una franja muerta a la derecha, visible
   justo al lado de bloques de código que sí usan todo el ancho. Se conservan los
   de titulares. Ver [05 · Sistema visual](05-sistema-visual.md).
2. **Se eliminó la raya larga de todo el material.** Reemplazada por coma, dos
   puntos o punto según el caso. Quedan dos apariciones, ambas **dentro de
   respuestas generadas por el modelo** en salidas capturadas: editarlas rompería
   la regla de que la salida es lo que de verdad se imprimió.

El segundo punto tuvo un efecto lateral que vale registrar: al barrer el código,
seis salidas capturadas de la sesión 01 quedaron desincronizadas con sus propios
`print`. Es la primera vez que se ve el fallo que `verificar.py` **no** cubre:
comprueba código contra página, no salida capturada contra código.

---

## Ideas evaluadas y descartadas

Se registran para no volver a discutirlas desde cero:

| Idea                                        | Cuándo | Por qué se descartó                                                                                      |
| ------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------- |
| Ejecutar Python en el navegador (Pyodide)   | v4     | `chromadb` y las llamadas a la API no corren ahí; y montar el entorno local es parte de lo que se enseña |
| Reescribir los 20 decks a taller de una     | v4     | Se pilotea primero la sesión 04 y se mide con el alumno real                                             |
| Eliminar los decks                          | v4     | Resuelven bien el porqué y las comparaciones; se quedan, más cortos                                      |
| Escribir el código dentro del taller a mano | v4     | Reintroduce las dos fuentes de verdad que causaron los 88 huecos                                         |
