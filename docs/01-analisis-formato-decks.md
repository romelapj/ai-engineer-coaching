# 01 · Análisis del formato deck

**Fecha:** 15 de agosto de 2026
**Motivo:** los decks "tienen huecos". Antes de rediseñar nada, medir de dónde
salen esos huecos.

## Resumen

Los huecos no son descuidos de redacción. Son una consecuencia matemática del
formato: **un deck no tiene espacio para un build**, y este curso es un curso de
builds. Parchear los huecos uno por uno ya se intentó (commit `e61479a`, "Cierra
88 huecos de reproducibilidad") y volvieron, porque la causa sigue ahí.

## Lo que se midió

Sobre los 20 decks publicados, a 15 de agosto de 2026:

| Métrica                                             | Valor                                            |
| --------------------------------------------------- | ------------------------------------------------ |
| Decks totales                                       | 20 (14 del programa AI + 6 de nivelación Python) |
| Slides totales                                      | 319                                              |
| Bloques de código en total                          | 91                                               |
| Promedio de bloques por deck                        | 4.6                                              |
| Sesión 12 (System Design) / Sesión 13 (Entrevistas) | 1 bloque cada una                                |
| Sesión 06 (Agentes: el loop)                        | 2 bloques                                        |

Y el caso concreto que disparó el análisis, la **sesión 04**:

| Métrica                                                          | Valor    |
| ---------------------------------------------------------------- | -------- |
| Slides                                                           | 16       |
| Bloques de código en el deck                                     | 4        |
| Líneas de código en esos 4 bloques                               | 106      |
| Líneas de código realmente necesarias para construir el pipeline | **643**  |
| Cobertura                                                        | **16 %** |

## Las tres causas

### 1. El deck solo cabe el 16 % del material

Para que el alumno construya el RAG de la sesión 04 hacen falta 643 líneas
repartidas en 5 archivos. El deck muestra 106. El 84 % restante no está "mal
explicado": **no está**. Cualquier intento de meterlo produce slides ilegibles,
y cualquier intento de resumirlo produce fragmentos que no corren.

De ahí sale el fragmento literal de la slide 12:

```
# ...seguimos dentro de responder(pregunta), ya con los hits del retrieval:
```

Un bloque que empieza a mitad de una función. No hay dónde pegar eso.

### 2. El material bueno vive fuera del repositorio publicado

El deck de la sesión 04 menciona la carpeta `ejemplos/` **7 veces**: la slide
13 dedica los 30 minutos de "manos al código" a recorrerla.

Esa carpeta no existía en el repositorio publicado. Vivía en
`~/Documents/repositorios/Otros/test-ai/session-04/`, en el disco del coach. El
alumno no tenía forma de llegar a ella.

Ese código, además, es **el mejor material del curso**: comentado línea por
línea, probado, con las salidas reales verificadas y un ejemplo que aterriza un
paper de investigación reciente. Estaba invisible.

### 3. Dos fuentes de verdad para el mismo dato

El deck dice `UMBRAL = 0.7`. El código usa `UMBRAL = 0.40`.

La diferencia está bien razonada (el deck piensa en embeddings comerciales, el
código usa MiniLM local, cuyas similitudes son más bajas) y está documentada. No
es el error: **es el síntoma**. Cuando el mismo hecho vive en dos archivos que
nadie obliga a coincidir, se separan. Siempre. Y el commit de los 88 huecos
demuestra que la reconciliación manual no escala a 20 decks.

## El problema de tiempo, que apareció en paralelo

El formato original era una sesión de 90 minutos semanal, con 30 minutos de
"manos al código". Recorrer 643 líneas en 30 minutos son **6 minutos por
archivo** escribiendo en vivo. No alcanzaba, y en la práctica no alcanzó.

Por eso el curso pasó a **30 minutos diarios** (ver
[03 · Versiones del curso](03-versiones-del-curso.md)). Ese cambio agrava el
problema del deck: un deck es lineal y va al ritmo del coach. Seis sesiones
cortas necesitan que el alumno pueda **entrar, ubicarse donde quedó, avanzar un
tramo y salir**, y un deck no tiene memoria de dónde iba nadie.

## Conclusión

El formato deck sirve para lo que un deck sirve: contar un porqué, comparar
opciones, dejar una idea fuerza. Todo eso está bien resuelto en estos 20 decks
y no hay que tocarlo.

Lo que no puede hacer un deck es **acompañar un build**. Para eso hace falta un
formato donde el código quepa completo, se pueda copiar, se pueda verificar
contra una salida esperada, y recuerde dónde iba el alumno.

La decisión está en [02 · Decisión: formato taller](02-decision-formato-taller.md).
