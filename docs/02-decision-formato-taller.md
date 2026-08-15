# 02 · Decisión: el formato taller

**Fecha:** 15 de agosto de 2026
**Estado:** adoptado, en piloto con la sesión 04
**Contexto:** [01 · Análisis del formato deck](01-analisis-formato-decks.md)

## La decisión

Los builds del curso se entregan en **talleres**: páginas de pasos numerados,
organizadas por días de 30 minutos, donde el código completo se copia paso a
paso y cada paso trae su salida esperada.

Y la parte que de verdad importa:

> **El taller se genera desde el repositorio ejecutable. No se escribe al lado.**

El `taller.yaml` no contiene código. Contiene el guion: qué archivo, qué rango
de líneas, qué objetivo, qué salida, qué explicar. `build.py` lee los archivos
reales y los inyecta al publicar.

## Por qué esa restricción y no otra

Porque es la única que elimina los huecos **por construcción** en vez de por
disciplina:

- El código de la página es el código que se probó. Si el archivo corre, la
  página corre.
- No puede haber dos fuentes de verdad: hay una, y la página es una vista.
- Un cambio en un ejemplo se propaga a la página con un `build`.
- El generador **verifica**: si entre todos los pasos queda una línea del
  archivo sin mostrar, lo reporta. `verificar.py` va más lejos y comprueba que
  pegando los bloques en orden sale el archivo byte a byte.

Ese último punto convierte "no hay huecos" en algo que una máquina puede
comprobar en cada commit, en vez de algo que alguien tiene que revisar a mano
en 20 decks.

## Qué se descartó, y por qué

**Ejecutar Python en el navegador (Pyodide, REPL embebido).** Tentador y falso:
`chromadb` y las llamadas a la API no corren ahí, así que el alumno vería un
entorno de juguete distinto al que va a usar. Además, montar el entorno local es
parte de lo que se enseña: es una habilidad del oficio, no un obstáculo.

**Escribir el código dentro del taller (Markdown o HTML a mano).** Es exactamente
el problema actual con otra piel: vuelve a haber dos copias.

**Reescribir los 20 decks de una.** Se piloteó primero la sesión 04, que ya tenía
el código escrito y probado, para medir con el alumno real antes de invertir en
las otras 19.

**Eliminar los decks.** Los decks resuelven bien lo que un deck resuelve: el
porqué, las comparaciones, la idea fuerza. Se quedan, más cortos. Deck y taller
se enlazan mutuamente.

## Reparto de responsabilidades

|           | Deck                                            | Taller                                   |
| --------- | ----------------------------------------------- | ---------------------------------------- |
| Formato   | Slides, lineal, al ritmo del coach              | Página de pasos, al ritmo del alumno     |
| Contenido | Por qué, comparaciones, trade-offs, idea fuerza | El build completo, paso a paso           |
| Momento   | Los minutos de teoría en vivo                   | Los 30 min diarios y todo el repaso solo |
| Estado    | No guarda nada                                  | Progreso persistido por paso             |
| Código    | Fragmentos ilustrativos                         | Archivos completos, verificados          |

## A qué nos compromete

1. **Todo build nuevo necesita su código ejecutable primero.** No se puede
   escribir un taller sobre código que no existe y no corre. Esto es una
   restricción real y es deliberada.
2. **Las salidas hay que capturarlas corriendo los ejemplos**, y recapturarlas
   cuando el código cambie. Viven en `talleres/<id>/salidas/`.
3. **`build.py` hay que correrlo** después de tocar el código o el guion. Se
   recomienda `verificar.py` en CI para que un despiste no llegue a producción.
4. El progreso del alumno vive en `localStorage`: es por navegador, no se
   sincroniza entre dispositivos y se pierde al limpiar el navegador. Es una
   ayuda para estudiar, **no un registro de evaluación**. El registro sigue
   siendo el entregable del AI Gym.

## Cómo se sabrá si funcionó

El piloto de la sesión 04 se mide contra estas preguntas, con el alumno real:

- ¿Completa un día de 30 minutos sin preguntarle nada al coach?
- ¿Le corre el código copiado y pegado, a la primera?
- ¿Vuelve al taller solo, entre sesiones?
- ¿Cuánto tarda el coach en armar el taller de la sesión 05, comparado con lo
  que tardaba en armar un deck?

Si las respuestas son buenas, se migran las sesiones restantes. Si no, este
documento se actualiza con lo que se aprendió.
