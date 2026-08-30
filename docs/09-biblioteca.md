# 09 · Biblioteca y club de lectura

**Fecha:** 30 de agosto de 2026
**Estado:** estructura montada, catálogo con 2 piezas y las dos pendientes de escribir

Dos secciones nuevas del sitio: un **club de lectura** (`biblioteca/libros.html`)
y una **biblioteca** de artículos, noticias, videos y podcasts
(`biblioteca/index.html`). Ambas se generan desde un solo `catalogo.yaml`.

La guía operativa está en [`biblioteca/README.md`](../biblioteca/README.md).
Aquí quedan las decisiones.

## El motor ya existía

Las páginas de video de los talleres ya hacían exactamente esto: catálogo en
YAML, página generada, y cuatro campos que son criterio propio —`resumen`,
`valioso`, `conecta`, `reparos`— con un estado de pendiente cuando falta. La
biblioteca no inventa un formato: **extiende ese**.

Lo que faltaba no era el motor: era la puerta. Los 24 videos solo se alcanzaban
desde un día concreto de un taller. Nadie que no estuviera haciendo la sesión 04
iba a encontrarlos nunca. Por eso el índice de la biblioteca los lee de
`talleres/videos.yaml` y los lista junto a lo demás, pero **enlaza a la página
que ya genera `talleres/build.py`**: se listan, no se copian. Un video sigue
teniendo una sola definición, en un solo archivo.

## Por qué dos portadas y no una lista

La ficha de un libro y la de un artículo tienen el mismo esqueleto, así que la
tentación era una sola lista filtrable. Se descartó por el **ritmo**, no por el
formato:

- Un artículo es puntual. Se lee en una sentada, se opina y se cierra.
- Un libro dura semanas. Tiene estado (leyendo, terminado, abandonado), tiene
  avance, tiene tramos y, si de verdad es un club, tiene preguntas para
  discutir en la sesión.

Metidos en la misma lista, el libro se ve como un artículo largo y se pierde
justo lo que lo hace un club. Son dos portadas sobre un catálogo y un
generador: cambiar el sistema visual sigue siendo tocar un archivo.

## La decisión de fondo: capturar y fichar son dos cosas

Es lo único que decide si estas secciones siguen vivas dentro de seis meses.

Escribir una ficha honesta cuesta media hora. Encontrar un artículo cuesta diez
segundos. Si la única forma de guardar algo fuera escribir la ficha, no se
guardaría nada; y si todo lo guardado tuviera ficha, quedaría un montón de
enlaces con resúmenes tibios, que es lo que ya hace cualquier gestor de
marcadores.

Por eso el catálogo tiene dos listas:

| Lista    | Coste       | Qué genera                              |
| -------- | ----------- | --------------------------------------- |
| `inbox`  | 10 segundos | nada; se lista al pie de la biblioteca  |
| `piezas` | media hora  | su ficha en `biblioteca/<slug>.html`    |

Del inbox solo asciende lo que a los pocos días sigue pareciendo importante.

## `reparos` es el producto

De los cuatro campos de contenido, tres los podría escribir cualquiera que haya
leído la pieza. El cuarto no viene con la pieza y es la razón de que la sección
exista: **dónde se queda corta, qué está desactualizado, en qué se discrepa**.

La regla de los videos —"un video sin reparos suele ser un video que no se vio
con cuidado"— se hereda entera. Si una pieza no tiene ningún reparo,
probablemente no merece ficha.

## Las portadas se descargan, no se enlazan

Ninguna imagen apunta al servidor de otro: se baja una vez a
`biblioteca/portadas/` y se versiona. Es la regla del código de los talleres
—lo que se muestra es lo que hay— aplicada a las imágenes. Un `<img>` a un
dominio ajeno rompe la página sola, sin que nadie toque nada, y de paso le
cuenta a un tercero quién está leyendo el sitio.

Cuando no hay imagen decente —la mitad de los artículos— **no se pone ninguna**:
`build.py` compone una portada tipográfica con el título y la fuente sobre el
degradado de la marca. Ni hueco roto ni foto de archivo de un robot mirando al
horizonte.

## Los artículos se caen

Un enlace a un blog tiene fecha de caducidad y no avisa. Por eso cada pieza
puede llevar `archivo:` con su copia en web.archive.org, que se muestra como un
segundo botón junto al original. No se automatiza: se pega a mano al añadir la
pieza, que es el único momento en que se sabe con certeza que la URL funciona.

## Lo que rompe el build a propósito

`build.py` valida el YAML antes de escribir nada, y falla ruidosamente ante un
campo inexistente, un `tipo` desconocido, un campo de libro en un artículo, una
portada que no está descargada o un id de `sesiones` que no resuelve contra un
archivo real.

El motivo es el mismo fallo que ya documenta `talleres/enlaces.py`: un enlace
roto o un campo mal escrito **no se ven** en el HTML generado —simplemente no
salen— y se descubren meses después, cuando ya nadie recuerda a qué apuntaban.

## Lo que queda pendiente

- Escribir las fichas de las dos piezas del catálogo. Las dos están en estado
  pendiente a propósito: el contenido se escribe después de leer.
- Decidir si el club de lectura necesita una vista de "sesión del club" (una
  página por tramo discutido) o si basta con el plan dentro de la ficha del
  libro. Se decide con el primer libro terminado, no antes.
