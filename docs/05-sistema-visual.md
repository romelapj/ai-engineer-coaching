# 05 · Sistema visual de los talleres

**Fecha:** 15 de agosto de 2026, ampliado el 21 de agosto
**Alcance:** todo el sitio. Empezó en `talleres/plantilla.html` y el 21 de agosto
llegó al portal, las 24 páginas de video, los 20 decks, el AI Gym y el visor.

Las decisiones de abajo están en un solo archivo. Cambiarlas ahí cambia los
cinco talleres a la vez, porque el HTML se genera.

## Qué se midió antes de tocar nada

|                                   | Antes                                         | Después                                          |
| --------------------------------- | --------------------------------------------- | ------------------------------------------------ |
| Colores de acento compitiendo     | 4 (verde 11 usos, cian 8, violeta 8, ámbar 5) | 1 acento + 2 estados                             |
| Reglas `:focus-visible`           | 0                                             | 1 regla global para enlaces, botones y `summary` |
| Padding de la unidad de contenido | 1.5rem                                        | 2rem, y sin tarjeta                              |
| `prefers-reduced-motion`          | no contemplado                                | contemplado                                      |

## Las reglas

### Un solo acento

**Cian (`--acento`) es el único color de interfaz.** Hover, foco, paso activo,
enlaces, badges.

Verde y ámbar **no son acentos: son estado**. Verde = verificado (salidas
capturadas, checkpoints, pasos hechos), ámbar = atención (notas del coach,
"si te falla", "aún no publicado"). Un color que significa algo concreto puede
convivir con el acento sin competir por la atención.

El degradado violeta→cian sobrevive **solo** en la marca y la barra de
progreso. Es identidad del curso, no color de interfaz.

### Base neutra, no gris de fábrica

Zinc profundo (`#0a0a0c` → `#26262c`). Se eligió neutro cálido en vez del azul
del deck para que el código, que trae su propio color en el resaltado, sea lo
más saturado de la pantalla.

### Contraste tipográfico drástico

El título de portada es `clamp(2.4rem, 5.6vw, 4.2rem)` a peso **900** con
`letter-spacing: -0.045em`; el subtítulo justo debajo es `1.02rem` a peso 400 en
color atenuado. El salto es deliberado: los tamaños intermedios diluyen la
jerarquía y hacen que todo parezca igual de importante.

Máximo tres escalones por pantalla.

**El ancho de lectura se acota en los titulares, no en la prosa.** La regla de
libro son 60 a 75 caracteres por línea, y aquí no aplica: la columna de texto ya
está limitada por la retícula (barra lateral + margen del paso), así que un
`max-width` en `p` no protegía nada y sí dejaba una franja muerta a la derecha
en pantallas anchas, justo al lado de bloques de código que sí usan todo el
ancho. El contraste se notaba. Los `max-width` que quedan son los de los
titulares (20 a 26 caracteres), donde el objetivo es forzar el salto de línea en
un punto concreto, no facilitar la lectura.

### Disposición editorial, no tarjetas apiladas

Los pasos **no son tarjetas**. Son secciones abiertas separadas por una línea de
un píxel, con la cifra del paso y su marcador en el margen izquierdo, fuera de
la columna de texto.

Dos razones. La primera es de lectura: 28 tarjetas idénticas una debajo de otra
son un muro, y la retícula asimétrica da un punto de anclaje al ojo. La segunda
es funcional: quitar la tarjeta elimina un nivel de anidación
(tarjeta › bloque › `pre`) y **le devuelve el ancho completo al código**, que es
el protagonista de la página.

Los días llevan una cifra grande en contorno, en el mismo margen.

### Estados completos

- **Hover**: cambio de borde, nunca de fondo chillón. `0.2s ease` en todo.
- **Foco**: una sola regla `:focus-visible` con `outline` de 2px y
  `outline-offset`. Es accesibilidad, no decoración: el taller se puede
  recorrer entero con teclado.
- **Hecho**: el paso baja a 45% de opacidad y vuelve a 100% al pasar por encima
  o al enfocar algo dentro. Se ve el avance sin perder el acceso.
- **Error**: `si_falla` es un `<details>` en ámbar con el mensaje literal del
  error y su arreglo.
- **Carga y vacío**: no aplican. La página es estática y se genera con todo el
  contenido dentro; no hay petición que esperar ni lista que pueda venir vacía.
  Un _skeleton_ aquí sería decorativo.
- **Movimiento reducido**: `prefers-reduced-motion` anula transiciones y el
  scroll suave.

### Volver donde lo dejaste

El curso son 30 minutos diarios, así que **retomar es la acción más frecuente**
y era la peor resuelta: con 26 de 41 pasos hechos, el alumno aterrizaba en
`scrollY = 0` sobre miles de píxeles de portada que ya había leído.

Arriba del todo, antes de la marca, aparece ahora una barra con el primer paso
**sin hacer**. No el siguiente al último marcado: el primero pendiente, porque
la gente salta pasos y vuelve. La barra no existe para quien empieza (no hay
nada que reanudar) ni para quien terminó.

### El control de "hecho" vive donde termina la lectura

Cada paso tiene **dos** controles para marcarlo, y no es redundancia: el círculo
del margen izquierdo y un botón al cierre del paso. El del margen sirve para
ver el estado de un vistazo; el del cierre, para marcarlo en el momento en que
de verdad terminas de leer, sin subir a buscarlo.

Además, el marcador del margen lleva `align-self: start`. Sin eso su
`position: sticky` era decorativo: como celda de grid se estiraba a la altura de
toda la fila (1800px en un paso largo), y un elemento pegajoso tan alto como su
contenedor no tiene recorrido, así que su contenido se quedaba arriba y salía de
pantalla. Con `start` mide lo que ocupa el número más el círculo, y acompaña la
lectura de verdad.

### Nada flotando encima del contenido

En pantallas anchas los controles viven en la barra lateral. Por debajo de
1080px la barra se vuelve un cajón y aparece una **barra superior sticky**, que
ocupa su propio espacio en el flujo.

Es una regla dura, y viene de un fallo real: los botones flotantes tapaban el
texto de las notas al pie de página. Se verifica en cada revisión muestreando
nueve puntos del viewport y comprobando que ninguno cae sobre un elemento fijo.

### El código manda

El bloque de código es la unidad visual más fuerte: fondo más oscuro que la
página, cabecera con la ruta y el rango de líneas, badge de líneas nuevas y
botón de copiar.

Las **salidas** siempre envuelven (son texto de terminal: una respuesta del
modelo puede venir en una sola línea de 385 caracteres). El **código** no
envuelve por defecto (la sangría es sintaxis en Python), pero hay un botón
`↩ Ajustar líneas` que se activa solo por debajo de 1400px, el ancho medido a
partir del cual la línea más larga cabe entera. Al envolver, la continuación
entra 4 espacios con sangría colgante para no confundirse con una sentencia
nueva.

## Cómo se verifica

No a ojo. En cada cambio de la plantilla se mide, para cada taller y en anchos
de 320 a 1920px:

- bloques de código recortados (debe ser 0)
- elementos que se salen del viewport (0)
- puntos del viewport tapados por algo fijo (0)
- scroll horizontal de página (falso)

Y por separado, `verificar.py` comprueba que lo que se ve, lo que copia el botón
y el archivo fuente son el mismo texto.

## Cuando el sistema llegó al resto del sitio

**21 de agosto de 2026.** Durante un tiempo convivieron dos paletas. Los talleres
usaban el zinc de arriba y las otras 22 páginas seguían en el azul `#0b0f1a` con
el violeta como acento. Medido en el navegador, las seis familias de página
daban dos combinaciones distintas de fondo, texto y acento. Hoy dan una.

### Qué se cambió

Los colores ya estaban tokenizados en un único bloque `:root` que 21 de los 22
archivos compartían byte a byte, así que la paleta se movió entera con una
sustitución de diez valores. No había un solo hex suelto repartido por el markup,
y eso es lo que hizo el cambio barato.

El violeta `#8b5cf6` desapareció como color de interfaz y se fusionó con el cian.
Antes de fusionarlos se comprobó que ninguna regla usara los dos acentos a la vez:
cero coincidencias, así que la fusión no borró ninguna distinción que alguien
hubiera diseñado.

El degradado de marca se usaba en 84 sitios: el kicker, las cifras grandes, la
regla bajo cada `h2` y la barra de progreso. Sobrevive en dos, que son los que el
sistema permite. El kicker es la marca del curso, el mismo elemento que
`.marca` en la plantilla de talleres, y por eso conserva el degradado; la barra
de progreso también. Las cifras grandes pasaron a `--texto`, que es lo que hacen
las del portal y las de la portada de cada taller.

Los halos de fondo de las diapositivas eran uno violeta y otro cian. Al fusionar
los acentos quedaron los dos del mismo color y juntos teñían la esquina hasta
`rgb(12, 30, 35)`, veinte puntos de verde por encima del negro de los talleres.
Bajados a la mitad, la esquina queda en `rgb(11, 20, 23)` y la diapositiva
conserva la profundidad que la distingue de una página de lectura.

Se quitaron 228 emoji decorativos: 125 en un `<span class="icon">` que no tenía
ni una regla de CSS asociada, 42 en el botón de copiar, que en los talleres dice
"Copiar" a secas, y 61 que abrían un titular. Los emoji que quedan están en los
enlaces de acción, donde los talleres también los usan, y en tres frases de prosa.

### Dos cosas que salieron mal por el camino

La primera fue mía y la corrigió la medición: pasé el kicker de los decks a color
plano por parecerme decoración, y resultó ser la marca. La plantilla de talleres
lo pinta con el degradado desde el principio. Volvió a su sitio.

La segunda fue una regex que trató `👨‍💻` como un carácter cuando son tres.
Quitó el primero y dejó el resto pegado al título en cuatro decks. Se ve raro y
se arregla, pero el aviso vale para cualquier limpieza de texto: los emoji
compuestos no se cortan por el primer codepoint.

### Un hallazgo que no era de estilo

Al revisar el enlace de la portada de cada deck salió que los cinco anunciaban
mal el taller que enlazan. El de la sesión 05 prometía diez días y 41 pasos
cuando el taller tiene siete y 44, y los otros cuatro se dejaban un día. Nadie
lo habría notado leyendo el deck, porque el dato solo se contradice al abrir la
otra página. Los cinco están sincronizados con lo que declara cada taller.

### Lo que la primera pasada no vio

Una auditoría de 46 agentes contra el commit anterior encontró tres cosas que la
verificación había dado por buenas, y las tres eran ciertas.

La peor la había introducido la propia migración. El portal declara sus tokens en
español (`--fondo-2`, `--linea`) y conservaba dos atributos `style=` en línea que
pedían `var(--bg2)` y `var(--border)`, nombres de la paleta anterior que ese
archivo ya no declara. Las declaraciones caían inválidas y, como el atributo en
línea gana por especificidad, las dos bandas alternas de la portada se
renderizaban sin fondo y sin ninguno de sus dos filos.

La segunda fue una isla entera: `coach/index.html` y `_template.html` seguían con
la paleta azul y el violeta como acento primario. Nadie los enlaza, pero Pages los
sirve, y mientras `_template.html` existiera, cualquier deck nuevo nacería con el
sistema viejo.

La tercera fue tinte azul dentro de páginas ya migradas. Los tokens tenían el
valor correcto y el bloque de código seguía pintándose sobre `#090d16` navy con
texto `#c9d4e3` y comentarios `#64748b` slate, más 73 usos de un violeta claro
`#c4b5fd` repartidos entre las píldoras, el código en línea y el resaltado de
sintaxis. Solo el último es legítimo: los talleres colorean las palabras clave con
ese mismo violeta, así que los 27 de `pre .k` se quedaron y los demás se fueron.

**Por qué se escaparon.** La comprobación que dijo "no hay hex sueltos" filtraba
el bloque `:root` con un `awk` que usaba `\s`, una secuencia que awk no entiende,
de modo que el filtro se comió cada archivo entero y devolvió vacío. Y la
comprobación de "no queda violeta" buscaba `#8b5cf6`, sin saber que había un
segundo violeta en juego. Las dos dieron verde sobre nada. Una verificación que no
puede fallar nunca no está verificando: conviene probarla contra un caso que sí
debería encontrar antes de confiar en su silencio.
