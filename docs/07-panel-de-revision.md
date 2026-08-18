<!-- Informe generado por un panel de 6 agentes revisores (18 ago 2026).
     Cada recomendación pasó por un verificador que fue al repo a desmontarla:
     27 sobrevivieron de 39. Los bloqueadores del consenso 1 ya están corregidos;
     el resto está pendiente de decisión. -->

# Informe del panel · Curso AI Engineer Coaching

**Fecha:** 18 de agosto de 2026 · **Base:** 27 recomendaciones confirmadas, 12 descartadas, 6 perfiles
**Repo:** `/Users/romel/Documents/repositorios/Otros/ai-engineer-coaching`

---

## 1. El veredicto en tres frases

Hoy esto es el mejor material de ingeniería LLM que he revisado a nivel de **disciplina de código** (el YAML sin código, `verificar.py` reconstruyendo 36 archivos byte a byte, el diagnóstico por síntoma de `metricas.py`, la fila de "solo BM25" dejada a propósito para enseñar a leer una tabla en contra de uno mismo) envuelto en un **producto de entrega que no funciona**: el taller 05, el más grande del curso, tiene dos bloqueadores duros y no arranca en ninguna máquina que no sea la de Romel.

Le sobra **prosa derivable**: el `porque` reescribe el docstring que está tres líneas arriba (81% y 87% de 4-gramas compartidos en dos pasos), el mismo hecho se cuenta hasta cuatro veces por día en el taller 05, y 28 de 37 checkpoints preguntan algo cuya respuesta está impresa unos párrafos más arriba.

Le falta **maquinaria que vigile todo lo que no es una línea de código dentro de un rango declarado** (claves de YAML, archivos en disco, salidas capturadas, enlaces, y CI: no existe `.github/`), un **botón de retomar** donde el alumno dejó, y **conexión con el resto del curso**: el taller es el 100% del tiempo diario del alumno y tiene cero aristas de entrada desde los 20 decks, los 16 READMEs del gym y `progress.md`.

---

## 2. Los tres consensos

### Consenso 1 · El taller 05 no arranca. Cuatro perfiles de seis lo encontraron por su cuenta

**Quién:** UX ("Arregla el día 0"), El alumno objetivo ("Entregar requirements.txt y el corpus"), Especialista en evaluación ("Dale al taller 05 corpus y red de recuperación"), Arquitecto ("Verificar cobertura contra los archivos en disco").

Y son **dos** bloqueadores independientes, no uno. El segundo lo destapó la verificación y es tan grave como el primero:

1. **El corpus no existe para el alumno.** `talleres/sesion-05/codigo/docs/` tiene 5 Markdown (159 líneas) que ningún paso ni ningún `archivo_completo` entrega. Verificado: `grep -n "docs/" talleres/sesion-05/taller.yaml` devuelve solo prosa (líneas 154 y 160). El Día 0 manda `mkdir -p ~/talleres/sesion-05` sobre carpeta vacía, afirma "cinco documentos Markdown que ya vienen en `docs/`" y enseña un `ls docs/` con los cinco nombres. `base.py:37` hace `sorted((CARPETA/"docs").glob("*.md"))`, que sobre carpeta inexistente devuelve `[]` **sin excepción**: el alumno obtiene 0 chunks y un RAG que contesta "no tengo evidencia" a todo. Es el fallo silencioso que esta sesión existe para enseñar, servido en el día 0. Copiar el corpus del taller 04 tampoco salva: `api-pagos.md` cambió (`## Códigos de error` → `## Límites de tasa`) y `golden.json` apunta a la sección nueva.

2. **El día 5 importa un módulo que se escribe el día 6.** `talleres/sesion-05/codigo/01_medir_el_baseline.py:33` hace `import retrieval`, y `retrieval.py` se reparte entero en los 6 pasos del Día 6 (`taller.yaml`, día 6, rangos 1-30 … 123-140). El alumno que sigue día a día se estrella con `ModuleNotFoundError: No module named 'retrieval'` en el único paso ejecutable del día 5. Confirmado parseando el YAML.

Y encima el taller 05 es el único con **cero** `si_falla` en sus 41 pasos (el 04, la mitad de largo, tiene 5). No hay red debajo de ninguno de los dos.

Lo que hace este consenso decisivo: **ni `build.py --estricto` ni `verificar.py` lo detectan.** `revisar_cobertura` (`build.py:692`) itera el diccionario `uso`, que se llena en `build.py:404` solo con archivos que algún paso referencia. Un archivo que nadie nombra es invisible por construcción. Ambas herramientas firman "sin huecos" sobre un taller de 340 minutos que no se puede correr.

### Consenso 2 · La maquinaria vigila el código y nada más

**Quién:** Arquitecto (3 de sus 4 recomendaciones), Especialista en evaluación, UX, El alumno objetivo.

El núcleo del sistema hace imposible **por construcción** el defecto que costó 88 parches a mano en los decks (`e61479a`). Fuera de ese núcleo no hay nada:

- **El guion.** `build.py` lee el YAML entero con `.get()`: 50 lecturas blandas contra 4 accesos duros. Reproducido: renombrando `porque:` → `porqué:` en los 20 pasos del taller 01, `build.py --estricto` imprime "sin huecos" y sale 0, `verificar.py` sale 0, y la página queda con 0 de 20 bloques "Por qué". `docs/04:232` dice "el `porque` es la clase". Hoy se puede borrar la clase entera sin que nada avise. En español el riesgo es real: `porqué` con tilde es un error de escritura frecuente, y el bloque se rotula "Por qué".
- **Los archivos en disco.** El consenso 1.
- **Las salidas capturadas.** Ya falló una vez, registrada en `docs/03` v4.2: al barrer la raya larga, seis salidas de la sesión 01 quedaron desincronizadas con sus propios `print`.
- **Los enlaces.** `build.py:769` hace `"../" + taller.get("inicio", "../index.html").lstrip("./")`; el `lstrip` se come el `..` y produce `../index.html`, que desde `talleres/videos/` resuelve a `talleres/index.html`, que no existe. Las **24** páginas de video tienen el enlace de marca muerto desde que se generaron. A 20 talleres serán ~100.
- **No hay CI.** `docs/02` (compromiso 3), `docs/04:11` y `docs/04:134` ya lo prescriben. `docs/03` v4 dice que `verificar.py` está "pensado para CI". Nunca se creó `.github/`. Y hoy `git diff --exit-code talleres/` arrancaría en rojo: hay 8 archivos modificados sin commitear y `talleres/sesion-04/salidas/01_ingesta.txt:3` tiene commiteada la ruta home completa de Romel en un repo público, con el HTML anonimizado a mano después.

### Consenso 3 · El taller 05 rompe el contrato que él mismo imprime

**Quién:** UX, El alumno objetivo, Especialista en evaluación, Estratega de contenidos.

Su `como_funciona` promete "Un día = 30 minutos = un archivo que corre… esa salida es tu criterio de 'me funcionó', sin tener que preguntarle a nadie". Medido: los días 1 (`base.py`), 2 (`rag.py`), 4 (`metricas.py`) y 6 (`retrieval.py`) no tienen ni un `corre` ni una `salida`. Son los cuatro días con **más** prosa del taller (1.386, 1.015, 1.012 y 1.170 palabras contra 187-609 en el resto): los cuatro días de más lectura son exactamente los cuatro sin recompensa. Sus checkpoints son autodeclaración ("Puedes explicar por qué el id de un chunk es `archivo § sección`"), respondible con el archivo roto.

No es una decisión de diseño, es una regresión: los 26 días de trabajo de los talleres 01-04 tienen `corre` + `salida` sin una sola excepción, y `docs/04:226` es explícito ("Si un día no termina en algo ejecutable, está mal partido"). Es el precio no visto de la estructura nueva del 05: el día de módulo compartido, que `docs/03` v4.2 celebra sin notar que se quedó sin artefacto verificable.

**Cerca de consenso, vale nombrarlo:** las definiciones de dominio salen **después** del código que explican, y lo vieron tres perfiles por su cuenta (UX, Contenidos, El alumno). `build.py:435-437` lleva escrito "Van ANTES del código" y el `piezas.append` está en la 444, detrás del bloque de código, los bloques inline, el comando y la salida. `docs/04:170` documenta lo mismo. El generador hace lo contrario de lo que su propio comentario y la bitácora declaran, en los 8 casos, verificado en el HTML publicado.

---

## 3. Las contradicciones, y a quién le hago caso

### a) Contenidos dice "sobra texto"; el alumno dice "falta explicación"

Contenidos midió 4.648 líneas de YAML y pide cortar. El alumno pide más definiciones, más notas de sintaxis, más glosario.

**No es la misma prosa y los dos tienen razón.** El criterio que resuelve: **borra lo que el alumno puede leer tres líneas más arriba, añade lo que no está en ninguna parte.** Lo que Contenidos ataca es prosa **derivable**: el `porque` del día 6 del 05 (`taller.yaml:1053-1056`) repite el docstring de `retrieval.py:6-8` cambiando un verbo ("meterlas" → "pasarlas"); el `porque` del día 7 recorre punto por punto lo que `02_hibrido_bm25_rrf.py:92-113` ya imprime en la salida capturada. Lo que el alumno pide es prosa **no derivable**: qué significa `**args` en `fn(**args)` (`02_el_loop.py:63`, cuyo `porque` explica `json.dumps` y el `if fn is None` y calla el `**`), qué es `if __name__ == "__main__":` (25 de 26 archivos de los talleres 01-04 lo tienen, 2 lo explican). Hacer caso a los dos, en el mismo pase: cada `porque` que se recorta libera el hueco donde va el trade-off que hoy no cabe.

### b) Contenidos quiere partir los muros del 05 invocando "4 a 6 pasos"; esa regla la rompen 8 de 32 días

El argumento de la regla se le vuelve en contra: partir el paso B del día 9 lo deja en **7** pasos, por encima del techo que invoca. Y el taller 01 día 4 tiene 2 pasos, el 02 días 2 y 5 también incumplen.

**Le hago caso al corte, no a la regla.** Los tres muros hay que partirlos por su argumento propio: el día 7 paso 2 son 85 líneas con 22 minutos y el mejor `porque` del taller compitiendo con el bloque; el día 10 paso 4 son 82 líneas con 25 palabras de `porque` (0,30 palabras por línea, el peor de los 133 pasos del curso, y es el cierre del curso). El día 9 se justifica porque dura 45 minutos, no porque la regla lo mande.

> **Decisión pendiente de Romel (criterio, no técnica):** o el barrido cubre los 8 días que rompen la regla, o `docs/04:228` se reescribe a "4 a 6 salvo cuando un paso es una sola unidad ejecutable, y nunca más de ~50 líneas por paso" y se registra en `docs/03`. Dejar `docs/04` mintiendo sobre el repo es exactamente el fallo que la bitácora existe para evitar.

### c) UX quiere etiquetar días "solo lectura" para leer en el metro; el curso no tiene ninguno

La verificación lo desmontó: la regla propuesta (derivar la etiqueta de si el día tiene `corre`) etiquetaría "solo lectura" 9 días y los 9 estarían mal, empezando por los días 1 de los talleres 01-04, que son `mkdir`/`venv`/`pip install`, el día más atado al terminal de todos.

**Gana el diseño del curso, no el UX.** `docs/02` fija que el taller ES el build y que el progreso vive en localStorage sin sincronizar entre dispositivos: el móvil es canal de lectura secundario, no sesión de trabajo. Lo que sí se implementa de esa recomendación es el HUD con día y paso, que es barato y real (a 390×844 el taller 05 mide 80.820px, 96 pantallas, y lo único fijo es el título del taller, cortado con puntos suspensivos).

### d) El AI Engineer quiere medir el embedding multilingüe; el propio código registró que no se descarga

`retrieval.py:92-95` documenta la decisión deliberada de evitar `sentence-transformers` "para no descargar un modelo de ~2 GB", y `requirements.txt` solo pinnea chromadb, anthropic y rank_bm25. La propuesta se vende como "un parámetro más, cero llamadas a API" y es falsa.

**Le hago caso a la incoherencia pedagógica, no a la medición inmediata.** La incoherencia es real y grave: la sesión 01 mide y enseña que MiniLM se rompe en español ("receta de arepas" 0.449 por encima de "checkout con visa" 0.229) y `docs/03` v4.1 lo celebra como el hallazgo #1 del curso; tres días después las sesiones 04 y 05 montan 17 días de taller sobre ese mismo modelo con corpus y queries 100% en español, y el único comentario es "con MiniLM las similitudes salen más bajas" (`sesion-04/taller.yaml:449`), que degrada un modelo fuera de distribución a una constante de calibración. Peor: `04_mapa_de_palancas.py:13-23` publica "el menú de palancas" con 4 filas y **sin** la del modelo de embeddings, que es la única que la sesión 01 declaró decisiva.

Se arregla hoy con dos frases (una en `sesion-04/taller.yaml:449`, otra en el día 3 del 05 cerrando el círculo con las arepas y avisando que la palanca del modelo queda aparcada hasta el día 9). La medición va después, detrás de un flag `--multilingue` con la salida capturada, y con la quinta fila en `04_mapa_de_palancas.py`, no en `03_reranking.py` (esa tabla compara estrategias de ranking sobre un embedding fijo; mezclar ejes la arruina). Y ojo: la parte causal de la acusación no está probada. Reproduje el baseline: recall@1 0.60 y recall@10 0.93 contra 0.043 y 0.435 de azar sobre 23 chunks. El modelo **no** recupera al azar en este corpus; afirmar que el 0.60 es el idioma es la misma falta que se le imputa al día 3.

### e) Evals quiere los ejes de la rúbrica y los días del taller en `progress.md`; `docs/02` prohíbe la mitad

`docs/02`, compromiso 4: el progreso del taller "es una ayuda para estudiar, **no un registro de evaluación**".

**Los 5 ejes sí, los días del taller no.** Los ejes (Funcionalidad, Comprensión, Medición, Proceso, Criterio AI, 1-4) son el instrumento **del coach**, los pone Romel en la sesión y hoy no tienen dónde vivir: `progress.md:35` tiene `Estado | Score de evals | Notas` y ninguna columna para ellos. Sin la serie temporal, las dos reglas de decisión que Romel ya escribió son inejecutables por construcción: "Un 2 en Comprensión dos semanas seguidas = conversación franca" (`coach/guia-sesion-semanal.md:71`) y "Dos semanas planas o a la baja = se rediseñan los retos" (`:206`). El anti-patrón que ese documento se autoimpone evitar ("Semana 9 y no sabes si va mejor que en la semana 4") está codificado en el tracker. Una columna "días de taller hechos", en cambio, sería autoreporte de un dato que vive en el navegador del alumno: eso sí choca con `docs/02`.

Corrección al hallazgo: **no reemplaces** `Score de evals`, añade las 5 columnas. Esa columna es el único registro de la Pre-Fase (`pytest ✓`, `Fluidez 1-5` en las filas 37-43).

### f) Evals quiere adelantar el juez al taller 04; el 04 existe para no juzgar todavía

El `te_deja` del día 5 del taller 04 dice: "cada mejora la juzgaste leyendo las respuestas. En la sesión 05 lo primero que harás es dejar de juzgar a ojo". Es uno de los 37 ganchos construidos a propósito.

**El hueco es real, el vehículo estaba mal.** El hueco: los retos 03 (semana 5), 05 (semana 7) y 06 (semana 8) exigen construir un LLM-as-judge, y la sesión que enseña qué hace confiable a un juez es la 08, semana 9. Conteo de `judge|juez`: `sesion-04`=0, `sesion-06`=0, `sesion-07`=0, `sesion-08`=26, y en los cinco talleres cero. Cuatro semanas cerrando gates con un instrumento que el alumno improvisó. La solución barata: el juez entra en el **taller 05, día 4**, que se titula "El instrumento: recall@k, MRR y el diagnóstico por síntoma", como contraparte de generación (retrieval se mide con conjuntos, generación con un juez, el juez se mide contra tus etiquetas), reutilizando `golden.json`, `rag.py` y `metricas.py`. Y la semana de desfase de reto-03 se arregla en el reto, con dos líneas: "etiqueta a mano las 15 respuestas ANTES de ver el veredicto y reporta el % de acuerdo", calcado del criterio que reto-07 ya tiene.

---

## 4. Tabla priorizada

Las 27 confirmadas, colapsadas en 23 filas (cuatro perfiles proponen el mismo arreglo del corpus; dos proponen lo mismo sobre `define` y sobre los días sin ejecutar). Orden: impacto alto + esfuerzo bajo primero.

| # | Qué | Por qué | Dónde | Imp. | Esf. | Quién |
|---|-----|---------|-------|------|------|-------|
| 1 | Entregar los 5 `.md` del corpus como `archivo_completo` del Día 0 | Sin ellos el taller 05 entero (11 días, 340 min) no corre, y falla en silencio | `talleres/sesion-05/taller.yaml` día 0 | alto | bajo | ux, alumno, evals, arquitecto |
| 2 | Arreglar el orden día 5 / día 6: `01_medir_el_baseline.py:33` importa `retrieval` que se escribe el día siguiente | Segundo bloqueador duro del 05, sin `si_falla` que lo explique | `talleres/sesion-05/taller.yaml` días 5-6 | alto | bajo | evals (verificación) |
| 3 | `revisar_cobertura` contra `git ls-files` bajo `codigo/`, no contra `uso` | Es lo único que impide que el fallo #1 se repita en la 06; 5 hits reales, 1 falso hoy | `talleres/build.py:692` | alto | bajo | arquitecto, evals, ux |
| 4 | `validar_esquema()` con conjuntos cerrados de claves + `difflib` para sugerir | Un typo (`porqué`) borra la clase de un taller y el build sale 0 | `talleres/build.py`, `docs/04` | alto | bajo | arquitecto |
| 5 | CI `.github/workflows`: `--estricto`, `git diff --exit-code`, `verificar.py`, enlaces | El HTML publicado (1,8 MB) no está garantizado que venga del YAML actual; el build tarda 0,26 s | nuevo | alto | bajo | arquitecto |
| 6 | Borrar `.lstrip("./")` de `build.py:769` + sanear la ruta home de `01_ingesta.txt:3` | 24 enlaces de marca muertos; ruta `/Users/romel/...` commiteada en repo público | `talleres/build.py:769`, `talleres/sesion-04/salidas/` | alto | bajo | arquitecto, alumno |
| 7 | 5 columnas `Fun\|Com\|Med\|Pro\|AI` en la tabla de `progress.md` | Sin la serie, las reglas de `guia-sesion-semanal.md:71` y `:206` son inejecutables | `progress.md` | alto | bajo | evals |
| 8 | Conectar el taller: cadencia real en `index.html`, tercer bullet al alumno, enlace en 5 decks, "prior art y delta" en retos 03/04 | El taller es 37 días de trabajo diario con 0 aristas de entrada; `docs/02` ya se comprometió a "deck y taller se enlazan mutuamente" | `index.html:640,690`, `sesiones/sesion-0{1..5}`, `gym/reto-0{1..4}` | alto | bajo | alumno, ux |
| 9 | `strict: true` + `ConfigDict(extra='forbid')` en el **Día 4** del taller 03; el retry loop se queda al lado como invariante de dominio | El día se titula "JSON garantizado" y enseña un patrón que no garantiza; el SDK pinneado (`0.116.0`) ya lo trae | `sesion-03/codigo/04_json_garantizado.py`, `taller.yaml:515`, deck `:762-806` | alto | bajo | ai-engineer |
| 10 | Tamaño de muestra: `n=15 · 1 query = 6.7 pts` en el encabezado, `n/15` en la tabla, y reescribir la `nota_coach` del día 10 | Hoy la respuesta "correcta" que enseña es "confío porque su recall@10 es 1.00", desarmable en una pregunta | `sesion-05/codigo/metricas.py`, `taller.yaml:962,1628`, `gym/reto-04:97` | alto | bajo | ai-engineer |
| 11 | Mover el `define` a la **primera** pieza del paso (antes del `objetivo`) + aserción en `verificar.py` | El generador contradice su propio comentario y `docs/04:170` en los 8 casos | `talleres/build.py:435-444` | medio | bajo | ux, contenidos |
| 12 | Smoke test ejecutable en los días 1, 2, 4 y 6 del 05, con salida capturada | 4 días sin recompensa, error del día 1 que aparece el día 3. Usa `if __name__ == "__main__":` en el módulo real | `sesion-05/{taller.yaml,codigo,salidas}` | alto | medio | ux, alumno |
| 13 | Barra de reanudación en portada + HUD, y `nav.scrollTop` (no `scrollIntoView`) | Retomar es la acción más frecuente y no existe: con 26/41 hechos, se aterriza en scrollY=0 sobre 3.000px de portada; `docs/03` v3 ya lo pidió | `talleres/plantilla.html`, `index.html` | alto | medio | ux |
| 14 | Separar la pregunta del checkpoint, respuesta en `<details>`, + campo `predice:` de paso | 28 de 37 checkpoints preguntan lo que el `porque` responde arriba; 1 sola predicción en 1.075 min | `build.py`, los 5 `taller.yaml` | alto | medio | evals |
| 15 | Juez mínimo en el día 4 del taller 05 + criterio de calibración en `gym/reto-03` | 3 retos (semanas 5, 7, 8) exigen un juez que se enseña en la semana 9 | `sesion-05/`, `gym/reto-03:96` | alto | medio | evals |
| 16 | El `porque` deja de reescribir docstrings **y `print`s**; reparto documentado en `docs/04` | 8 pasos con ≥30% de 4-gramas compartidos, dos en 81% y 87%; se gasta el único hueco del trade-off | `sesion-05/taller.yaml` días 6, 7, 9; `sesion-01` día 5; `docs/04` | alto | medio | contenidos |
| 17 | Partir los tres muros del 05 (85, 84 y 82 líneas) | El paso final del curso son 82 líneas con 25 palabras de `porque`, el peor ratio de 133 pasos | `sesion-05/taller.yaml` días 7, 9, 10 | alto | medio | contenidos |
| 18 | `if __name__ == "__main__":` explicado en `sesion-01` día 1 (comentario inline, no nota) y `**args` en `sesion-03` día 2 | 25 de 26 archivos lo usan, 2 lo explican, y la explicación llega en la semana 6 | `sesion-01`, `sesion-03` | alto | medio | alumno |
| 19 | Razonamiento nativo: partir la slide de CoT (sesión 02) y arreglar el routing de la sesión 09 | Cero ocurrencias de `thinking`/`effort`/`budget_tokens` en 20 decks, 5 talleres y 16 retos; el curso vende preparación de entrevista | `sesiones/sesion-02:681-714`, `sesion-09:731-760` | alto | medio | ai-engineer |
| 20 | Tercer chequeo en `verificar.py`: literales de `print()` vía `ast` contra la salida homónima | El fallo que ya ocurrió (`docs/03` v4.2, 6 salidas) y que nada cubre. ~40 líneas, 0,2 s, cero API | `talleres/verificar.py` | alto | medio | arquitecto |
| 21 | Embedding multilingüe: dos frases hoy, quinta fila en `04_mapa_de_palancas.py` detrás de `--multilingue` después | El curso declara el fallo en español su hallazgo #1 y lo ignora tres días después; el mapa de palancas omite la palanca decisiva | `sesion-04/taller.yaml:449`, `sesion-05/` día 3 | alto | medio | ai-engineer |
| 22 | Unificar "sesión" (semana) y "día" (30 min) en los 5 subtítulos; arreglar las 3 cifras del taller 04 y los 2 `cierre.siguiente.titulo` | El taller 04 dice 6, 5 y 6 días en la misma página; el enlace al 05 lo anuncia con un título que no existe | los 5 `taller.yaml` | medio | bajo | contenidos |
| 23 | Las 9 `duracion` adjetivadas ("corto"/"medio"/"largo") con minutaje real | El propio catálogo escribe "No se rellenan a ojo" (`videos.yaml:14`) y 8 de las 9 no tienen fuente | `talleres/videos.yaml`, `docs/06` | medio | bajo | alumno |

Fuera de tabla por ser cosmético con dependencia: las rutas `python ejemplos/<archivo>.py` en 12 archivos de `sesion-04/codigo` y `sesion-05/codigo` (se renderizan, `grep` sobre los HTML devuelve los 11 scripts). Prioriza `02_retrieval.py:81`, que no es docstring sino un `print` que el alumno ve cuando ya se equivocó y le da un comando que también falla; hay que cambiar en el mismo commit `sesion-04/taller.yaml:516`, que lo cita textualmente. Es la carpeta `ejemplos/` que `docs/01:56-60` declaró el defecto fundacional del formato deck, sobreviviendo dentro del formato creado para matarlo.

---

## 5. Los tres siguientes movimientos

### Movimiento 1 · Que el taller 05 se pueda abrir, y cerrar la puerta detrás (filas 1-6)

Medio día de trabajo. Va primero porque **todo lo demás de esta lista mejora un material que hoy el alumno no puede correr**, y porque los dos bloqueadores están en el taller que `docs/03` describe como el que "construye el instrumento que decide si el que ya existe sirve": si ese taller falla en silencio el día 0, el alumno aprende exactamente la lección contraria.

El guardrail (fila 3) va en el **mismo** movimiento, no después. Si se arregla el corpus a mano y no el chequeo, el taller 06 repite el fallo, y ese es el argumento entero del repo: `docs/02` dice que la restricción existe "porque es la única que elimina los huecos por construcción en vez de por disciplina".

Orden dentro del movimiento: (a) `build.py:769` y la ruta home de `01_ingesta.txt` primero, porque sin eso el paso de `git diff` del CI arranca en rojo y el próximo `build.py` republica la ruta personal de Romel en GitHub Pages; (b) el corpus y el orden de los días 5-6; (c) `revisar_cobertura` invertido y `validar_esquema`; (d) el workflow, ya en verde.

### Movimiento 2 · Que el taller 05 cumpla su propio contrato hacia dentro (filas 12, 14, 16, 17)

Una semana. Va segundo porque son los cuatro arreglos que **solo el 05 necesita** y que juntos se pagan entre sí: partir los muros libera espacio para los `porque` vacíos, recortar la prosa derivable libera el hueco donde entra la pregunta oculta, y los smoke tests convierten cuatro checkpoints de autodeclaración en cuatro números. Hacerlos por separado obliga a tocar `taller.yaml` cuatro veces con recaptura de salidas cada vez.

Va después del movimiento 1 y no antes por una razón operativa: recortar rangos de línea en el YAML es exactamente donde un typo silencioso muerde, y el `validar_esquema` de la fila 4 tiene que existir antes.

### Movimiento 3 · Sacar el taller de su aislamiento y darle instrumento al coach (filas 7, 8)

Un día. Va tercero porque es el único de los tres que no toca código de talleres, así que puede solaparse con el 2 si hay tiempo, pero **no puede esperar al arranque del alumno**: hoy el portal le dice "una sesión de 90 minutos por semana" (`index.html:690-693`) y "cada semana una sesión en vivo" (`:640`), formato v2 que `docs/03` v3 declaró reemplazado, mientras `README.md:3` y `:47` ya dicen "30 min diarios". El primer contacto del alumno con el curso desmiente al curso. Y sin los 5 ejes en `progress.md`, la primera señal dura de si el programa funciona llega en la semana 4 de 16.

**Lo que dejo fuera del mes a propósito:** las filas 19 y 21 (razonamiento nativo, embedding multilingüe). Son las dos de más valor técnico y las dos más caras: un día de taller nuevo o una medición con descargas de GB. Su versión barata (las dos frases de la fila 21, la slide partida de la 19) sí cabe; el día de taller no. `docs/02` es claro en que un build nuevo necesita su código ejecutable primero.

---

## 6. Lo que NO hay que tocar

1. **El diagnóstico por síntoma de `talleres/sesion-05/codigo/metricas.py:56-81`** (`sintoma`, `diagnostico`, `K_UTIL = 4`). Lo señalaron intocable el AI Engineer y el especialista en evaluación por separado. Ata la ventana de evaluación a cuántos chunks entrega de verdad `rag.py` al generador, separa fallo de recuperación de fallo de orden, y de ahí saca un orden de trabajo no negociable. Convierte una métrica en una decisión, que es el salto que casi ningún curso de evals da.

2. **La fila "solo BM25" de la tabla y la autocrítica de `03_reranking.py:88-92`.** Cuatro perfiles la nombraron. Dejar en la tabla la variante que empata en recall@1, gana en recall@5 y aun así es la peor opción, y relativizar el 1.00 del reranker por el tamaño del corpus, enseña a leer una métrica sin engañarse. Nota para la fila 10: el aviso del corpus pequeño **ya está** en `salidas/03_reranking.txt`; no hay que añadirlo, hay que no borrarlo.

3. **El fallo del embedding en español del taller 01 día 5** (`04_embeddings.py`, arepas 0.449 > "checkout con visa" 0.229). El alumno lo señaló como lo que le cambió la forma de mirar el resto del material. La fila 21 lo **refuerza**; si alguien propone "arreglarlo" cambiando el modelo del taller 01, es al revés.

4. **La regla de oro y `verificar.py` byte a byte.** El alumno lo pidió explícitamente: "no la debiliten para tapar los huecos que señalo". El corpus se entrega con `archivo_completo` (mecanismo existente, `docs/04:140-142`), no con `curl` a una URL raw ni con `cat <<'EOF'` duplicando el archivo dentro del YAML.

5. **El campo `vienes_de`.** Contenidos lo midió: 9 a 21 palabras en los 37 días, nunca repite resultado, siempre orienta. Es el mejor campo calibrado del curso y el modelo de cómo debería escribirse `te_deja`.

6. **El ajuste automático de líneas por debajo de 1400px** (66 bloques de código a 390px, cero con scroll horizontal) y **el `<details>` de `archivo_completo`** con "para comparar con el tuyo" (`build.py:525-531`). La salida de emergencia exactamente donde hace falta, plegada para quien no la necesita.

7. **`render_cierre` mirando el disco con `destino.exists()`** (`build.py:608-642`) en vez de creerle al guion. Ese es el patrón que las filas 3 y 20 extienden, no reemplazan.

8. **El criterio juez-vs-humano ≥80% de `gym/reto-07`.** Único sitio del material donde se exige demostrar que el instrumento de medición merece confianza antes de usarlo.

9. **El `te_deja` del día 5 del taller 04** ("cada mejora la juzgaste leyendo las respuestas"). Es el gancho deliberado hacia el 05, no un descuido. Por eso el juez de la fila 15 va al 05 y no al 04.

10. **El `target="_blank"` de las tarjetas de video y la jerarquía visual** (`--acento` reservado a `.dia-deja`, miniatura atenuada a `opacity: 0.82`). Ya está resuelto al revés de como lo describía una de las recomendaciones descartadas.

---

## 7. Lo que el panel descartó, y por qué

Para que no vuelva a proponerse:

| Propuesta | Por qué se cae |
|---|---|
| Quitar el `with_backoff` propio (el SDK ya reintenta) | **Ya resuelta.** El aviso está dos veces en el material que el alumno lee: `sesion-03/taller.yaml:766-769` y el deck `:888-890`. Además `resp._request_id` **es** público por documentación del SDK, y mover el backoff alrededor del loop de tool use contradice la lección de idempotencia del mismo día |
| Reemplazar la v0.4 del taller 04 por un golden set | El día está etiquetado "Día 5 · Extra"; la ausencia de números es el gancho declarado tres veces hacia el taller 05, no un descuido. El golden set ya existe en `sesion-05/codigo/golden.json`, y con 10 chunks no discriminaría (fallo ya registrado en `docs/03` v4.1) |
| Cerrar el día con el gancho, no con el video | **Incorrecta.** Los 24 días con video tienen `te_deja` **después**; `build.py:548` lo declara. El `_blank` es lo que impide que el alumno se vaya, no la puerta de salida |
| Convertir `te_deja` en gancho puro quitando el recap | La prueba mecánica ("borra la primera oración") rompe la anáfora en 4 de 5 casos; y borraría los 1,63 s por query del cierre del día 8, que no están en su checkpoint |
| Cambiar "30 minutos" por un rango de tiempos | Son 11 días desviados, no 13; la mitad ya está construida (`build.py:569` pinta los minutos en la cabecera) y `docs/04:226` usa el invariante como restricción de autoría, no como promesa de marketing |
| Sacar el "nosotros" del taller 04 | La densidad de 2ª persona del 04 (30,6/1.000) es igual que la del 03 y mayor que la del 05; su deck es el que **menos** usa "nosotros" de los cinco. La historia causal no existe |
| Renombrar dos pasos del taller 03 | El "qué loguear y qué no" está en el docstring renderizado del propio paso; el renombre propuesto duplicaría el título del día 3 |
| Renumerar el calendario porque la semana 6 no cabe | El desborde son 3 días, no 4, y las semanas 2-5 dejan 6 días de holgura. Además suma los "+90 min de sesión en vivo", que es texto v2 muerto |
| Golden set con múltiples relevantes en el reto 04 | `gym/reto-04` no toca `metricas.py` ni una vez: otro archivo, otro esquema, otro entrypoint, con el esqueleto entregado. Y rompería el arco 0.60 → 1.00 que está en ~10 puntos del guion |
| Convertir la semana 2 en un "reto 00" evaluable | Cuatro errores de hecho, incluido que `00_tokens.py:27` tiene 3 textos y no 10; el "Challenge 01" ya existe en el deck con dos partes; y `coach/validacion-curso.md` ya refutó esta línea |
| Resincronizar rangos de línea con `difflib` | El punto ciego es real (transpuse dos rangos y las dos herramientas salieron 0), pero `difflib` no representa movimientos: reescribiría los mismos rangos equivocados. Y el código se ha editado **cero** veces después de construir su taller, en 14 commits |
| Sacar el glosario de Python a un catálogo del curso | Los 66 símbolos del taller 05 son 66 símbolos **distintos**: la duplicación que el catálogo ahorraría es cero. El 35% de las claves `de` no aparecen literalmente en el código, así que `python: auto` no puede funcionar |

---

## Decisiones pendientes de Romel

Ninguna es técnica. Las cinco bloquean ejecución si no se resuelven antes:

1. **La regla "4 a 6 pasos" de `docs/04:228`.** ¿Se hace cumplir en los 8 días que la rompen, o se reescribe con la excepción de "un paso es una sola unidad ejecutable"? (Contradicción b.)
2. **Cómo se cuentan los días.** `index.html` cuenta con día 0 (6/7/7/6/11), los subtítulos cuentan de tres formas distintas, y `docs/03` registra el piloto como "6 días". Elige una y aplícala a los cinco subtítulos, los cinco badges y la bitácora. Sub-decisión: en el taller 04, ¿el "Día 5 · Extra" cuenta como día del pipeline?
3. **El presupuesto de la medición multilingüe.** ¿Se instala `sentence-transformers` + torch para medir de verdad (y se acepta que el alumno no lo instale, leyendo la salida capturada), o se publica el control barato: traducir corpus y queries al inglés y remedir con el mismo MiniLM? El segundo cuesta cero y desconfunde igual: si el patrón persiste en inglés, no es el idioma.
4. **`omitir[]` en `build.py:699`.** Está implementado y no lo usa ningún taller. Es la única puerta de salida de la regla central del repo. O se borra, o se documenta **junto con** la condición que lo hace legítimo. Documentar un bypass que nadie usa invita a usarlo.
5. **El `<textarea>` de las preguntas ocultas (fila 14).** Si persiste en localStorage es útil y sigue sin ser registro de evaluación; si no persiste, el alumno vuelve al repaso y encuentra su respuesta en blanco, que es peor que no ponerlo. `docs/02` permite lo primero, pero conviene que quede escrito antes de construirlo.