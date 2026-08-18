# 04 · Cómo crear un taller

Guía operativa. Para el porqué, ver
[02 · Decisión: formato taller](02-decision-formato-taller.md).

## Estructura

```
talleres/
├── build.py              # generador
├── verificar.py          # comprueba que no haya huecos (para CI)
├── plantilla.html        # la plantilla visual, con placeholders
├── sesion-04/
│   ├── taller.yaml       # el guion: aquí NO se escribe código
│   ├── codigo/           # los archivos ejecutables: la única fuente de verdad
│   │   ├── 00_chunking.py
│   │   ├── requirements.txt
│   │   └── docs/
│   └── salidas/          # salidas reales capturadas al correr los ejemplos
└── sesion-04.html        # GENERADO: no editar a mano
```

## El orden de trabajo

**1. Primero el código, y que corra.** Un taller no se escribe sobre código que
no existe. Escribe los archivos en `codigo/`, comentados línea por línea, cada
uno ejecutable por separado.

**2. Captura las salidas reales.** Nunca las escribas de memoria: son el
criterio de "me funcionó" del alumno.

```bash
cd talleres/sesion-04/codigo
for f in 0*.py; do python "$f" > "../salidas/${f%.py}.txt" 2>&1; done
```

**3. Escribe el guion en `taller.yaml`.** Apunta a rangos de líneas, no pegues
código.

**4. Genera y verifica.**

```bash
python talleres/build.py sesion-04
python talleres/verificar.py sesion-04
```

## `taller.yaml`

```yaml
id: sesion-04
titulo: "Taller 04 · ..."
kicker: "AI Engineer Coaching · Fase 2 · Sesión 04"
subtitulo: "El problema real que resuelve, en dos líneas."
enlaces:
  - { texto: "📊 Deck", url: "../sesiones/sesion-04-rag-fundamentos.html" }
como_funciona: "Cómo se usa el taller. Se muestra en la portada."

dias:
  - etiqueta: "Día 1"
    titulo: "Lo que se logra hoy"
    minutos: 30
    meta: "Un párrafo de contexto del día."
    archivo_completo: [00_chunking.py] # panel plegable al cierre, para comparar
    checkpoint: "Cómo sabe el alumno que el día quedó cerrado."
    video: # opcional; la tarjeta va después del checkpoint
      id: 8OJC21T2SL4 # tiene que estar en talleres/videos.yaml
      porque: "Por qué ESTE video en ESTE día." # no el resumen del video
    pasos:
      - titulo: "Nombre del paso"
        minutos: 8
        objetivo: "Qué se logra en este paso."
        codigo:
          archivo: 00_chunking.py
          lineas: "21-48" # un solo rango contiguo; sin esto, archivo completo
          nuevo: true # muestra el badge "+N líneas nuevas"
        bloques: # bloques sueltos (comandos, ejemplos que no son de un archivo)
          - { lenguaje: bash, texto: "pip install -r requirements.txt" }
        python: # opcional: glosario de sintaxis, plegado, va antes del "por qué"
          - de: "**METADATA_DOCS[fuente]" # el símbolo, tal cual aparece
            es: "Qué significa, para quien no domina Python."
        corre: "python 00_chunking.py"
        salida: { archivo: 00_chunking.txt, lineas: "1-12" }
        porque: "El razonamiento. Es lo que antes era la slide."
        si_falla:
          - error: "FileNotFoundError: docs"
            arreglo: "Estás en otra carpeta. Haz `cd` a donde está el script."
        nota_coach: "Solo visible con el botón 👁 Notas del coach."
```

Campos de texto admiten `**negrita**`, `*cursiva*`, `` `código` `` y
`[enlace](url)`. Una línea en blanco separa párrafos.

### El cierre: qué hace el alumno cuando termina

Al final de la página va un bloque de cierre con el enlace al taller siguiente.
Se declara al mismo nivel que `dias`:

```yaml
inicio: "../index.html" # a dónde lleva "AI Engineer Coaching" (este es el default)

cierre:
  titulo: "Ya tienes un RAG que cita sus fuentes"
  texto: |
    Qué acaba de construir y por qué importa lo que sigue.
  siguiente:
    id: sesion-05 # el generador mira si existe talleres/sesion-05.html
    titulo: "Taller 05 · RAG II: retrieval híbrido, reranking y evaluación"
    resumen: "Una línea de qué va a lograr allí."
    deck: "../sesiones/sesion-05-rag-avanzado.html" # alternativa mientras no exista
  acciones:
    - { texto: "🏋️ Entrega el reto 03", url: "../gym/index.html" }
```

**El enlace al siguiente se activa solo.** El generador no le cree al guion:
mira el disco. Si `talleres/sesion-05.html` todavía no existe, la tarjeta sale
en ámbar como _"aún no publicado"_ y ofrece el deck de esa sesión mientras
tanto. El día que publiques el taller 05, el enlace se enciende con el
siguiente `build.py` sin que tengas que volver a tocar el taller 04.

## Las dos reglas que no se rompen

**Un rango por paso, contiguo.** Si un paso necesita dos trozos separados del
archivo, son dos pasos. Esto no es una limitación técnica: es lo que hace que la
verificación de huecos signifique algo.

**Los rangos de un archivo, sumados, tienen que cubrirlo entero.** Es lo que
garantiza que el alumno pueda reconstruirlo copiando y pegando en orden.
`build.py` avisa si falta algo:

```
⚠ hueco en 00_chunking.py: 21–22
```

Con `--estricto` eso falla en vez de avisar; úsalo en CI:

```bash
python talleres/build.py --estricto && python talleres/verificar.py
```

Si un archivo se muestra solo como referencia y no se enseña línea por línea
(por ejemplo un `.md` de datos), va en `archivo_completo` del día, no en
`codigo` de un paso: no entra en la verificación.

## La narrativa: el arco, los enlaces y las definiciones

Un taller que solo explica pasos enseña la mecánica y no la historia. Se midió
en el taller 05 antes de tocar nada: **0 de 11 días miraban hacia adelante**, y
había 2692 palabras de razonamiento repartidas en los `porque` de cada paso
contra 361 de contexto de día. Una proporción de 7,5 a 1. El arco existía, pero
solo se leía cuando ya estabas dentro del paso mirando el código.

Tres campos lo suben a la superficie:

```yaml
historia: # nivel taller: el arco, antes del primer día
  entrada: |
    Dónde estás, qué se rompe, y qué vas a hacer al respecto.
  actos:
    - titulo: "Verlo fallar"
      texto: "Qué pasa en este tramo."
      dias: "días 1 a 3"
  cierre: "Qué te llevas de verdad, más allá del código."

dias:
  - etiqueta: "Día 3"
    vienes_de: "Una o dos frases que enlazan con ayer." # va ARRIBA del título
    te_deja: "Qué queda abierto, y por qué eso lleva a mañana." # al final del día
    pasos:
      - titulo: "..."
        define: # términos de dominio, ANTES del código que los usa
          - termino: "recall@k"
            es: "En qué fracción de tus preguntas el correcto salió en el top-k."
```

**La regla que evita que esto se vuelva relleno.** Cada frase que añadas tiene
que hacer una de tres cosas:

| | |
| --------- | ------------------------------------------------ |
| Anticipar | Qué vas a ver, en concreto y verificable         |
| Definir   | Qué significa este término, antes de usarlo      |
| Conectar  | Por qué esto viene después de aquello            |

Si no hace ninguna, se borra. El código sigue siendo el protagonista de la
página, y el texto está para que se entienda, no para acompañarlo.

**`define` no es lo mismo que `python`.** El primero explica el dominio
(`recall@k`, `BM25`, `cross-encoder`); el segundo, el lenguaje (`**`,
`.extend()`). Un alumno puede necesitar uno y no el otro.

## Las notas de sintaxis

Un paso puede llevar un glosario de **sintaxis de Python**, plegado, entre el
código y el "por qué". Es un tipo de nota distinto y conviene no mezclarlos:

| Nota      | Responde                                        |
| --------- | ----------------------------------------------- |
| `python`  | Qué **dice** el código: qué significa este símbolo |
| `porque`  | Por qué está escrito **así**: la decisión detrás  |

Va plegado a propósito: quien ya sabe Python no necesita ver el glosario en los
41 pasos, y quien no sabe lo abre. Se escribe pensando en alguien que programa
en otro lenguaje y no conoce la nomenclatura, así que explica el símbolo (`**`,
`.extend()`, `[::-1]`) y no el dominio.

Dos avisos prácticos: si el símbolo lleva comillas simples, hay que duplicarlas
(`'f"{e[''x'']}"'`), que es como YAML las escapa. Y el símbolo entra literal, tal
cual aparece en el archivo, para que se pueda buscar en la página con `Cmd+F`.

## El video del día

Un día puede cerrar con la tarjeta de un video: miniatura, título y una línea de
por qué. Al hacer clic abre en pestaña nueva su página propia, con el video
embebido y el material del curso alrededor. Los metadatos viven una sola vez en
`talleres/videos.yaml`; el día solo referencia el id y escribe el `porque`.

El `porque` **no es el resumen del video**: es la razón de ponerlo en ese día
concreto. "Tu corte por títulos es uno de sus cinco niveles" sirve; "buen video
sobre chunking" no.

Ver [06 · Videos de los talleres](06-videos.md) para el detalle, incluido por
qué los resúmenes no se generan automáticamente.

## Diseñar los días

- **Un día = 30 minutos = un archivo que corre.** Si un día no termina en algo
  ejecutable, está mal partido.
- **4 a 6 pasos por día.** Menos se siente como un muro de texto; más se
  fragmenta.
- **El checkpoint es obligatorio.** Es lo que le permite al alumno cerrar el día
  sin preguntarle nada a nadie.
- **El `porque` es la clase.** Es donde va lo que antes decías en vivo sobre la
  slide: el trade-off, el bug que causa, la decisión que hay detrás.
- **El `si_falla` se llena con los errores reales**, los que el alumno de verdad
  cometió. Después de la primera corrida del taller, vuelve y agrégalos.

## Publicar

`build.py` escribe `talleres/<id>.html` junto a los decks; GitHub Pages lo sirve
sin configuración extra. El HTML generado no se edita a mano: el siguiente
`build` lo sobrescribe. Para cambiar el aspecto, se edita `plantilla.html`.
