# 08 · La voz del coach

**Fecha:** 19 de agosto de 2026
**Alcance:** la prosa de los `taller.yaml`. El código y los números no cambian.

## El diagnóstico

Se midieron las 16.622 palabras de prosa del curso buscando marcas de voz:

| Marca | Veces | Por mil palabras |
| ----- | ----: | ---------------: |
| Trato directo al alumno (`tú`, `vas a`) | 208 | 12,5 |
| Primera persona del coach | 2 | 0,1 |
| Opinión explícita | **0** | **0,0** |

El curso **hablaba al alumno sin que hablara nadie**. Instrucciones bien
dirigidas, correctas y sin emisor. Un manual, no un coach.

## Las cinco reglas

**1. El coach existe y se le nota.** Usa la primera persona para las decisiones
del taller, que son suyas: *"esas cuatro preguntas las elegí yo"*, *"te puse esa
fila ahí a propósito"*, *"no te doy el reranker todavía"*.

**2. Tiene opinión y la dice.** *"Si te acuerdas de una sola frase de este
taller, que sea esta."* Un coach que no prioriza no está enseñando, está
enumerando.

**3. Acompaña.** Reconoce dónde cuesta: *"no te asustes con la cantidad de
código"*, *"si te dejaste engañar, no pasa nada: es la lectura que hace casi todo
el mundo"*. El alumno hace esto solo, de noche, después de trabajar.

**4. Nunca inventa biografía.** El coach opina sobre el material y sobre el
diseño del taller, que es lo que conoce de primera mano. Las anécdotas reales de
producción no se fabrican: van en `nota_coach`, que solo se ve con el botón, y
las cuenta él en vivo.

**5. La voz cambia, los números no.** Ninguna cifra, ningún nombre de función y
ninguna salida capturada se toca para que suene mejor.

## Antes y después

> **Antes.** Acabas de ver el fallo con tus propios ojos: el chunk correcto
> recuperado de cuarto y cortado por trece milésimas. Pero fallaron dos de cuatro
> preguntas que **tú elegiste**, y ese 50% no significa nada.

> **Después.** Acabas de verlo con tus propios ojos: el chunk correcto recuperado
> de cuarto y cortado por trece milésimas. Ahora te voy a quitar el gusto del
> hallazgo. Fallaron dos de cuatro preguntas que **elegí yo**, y ese 50% no
> significa absolutamente nada. Yo lo acabo de hacer contigo.

El dato no cambió. Cambió quién lo cuenta, y que ahora hay alguien enseñando en
vez de un texto describiendo.

## Dónde falta lo que solo puede poner Romel

La voz está, pero le falta lo que ningún generador puede escribir: **las
historias reales**. Los sitios donde el material las pide a gritos:

- El fallo silencioso del taller 05, que es el argumento central de la sesión.
  Cualquier incidente real de un sistema que falló sin dar error vale más que
  toda la explicación.
- La idempotencia del taller 03. Trabajar en pagos y haber visto un cobro doble
  es la credencial que hace que esa sección se lea distinto.
- El costo del taller 01, cuando aparece la factura real de un proyecto.

Van en `nota_coach` y se cuentan en vivo. El material deja el hueco preparado.

## Cómo se mide

Sobre la prosa de un `taller.yaml`, contando marcas de primera persona del coach
y de acompañamiento. En el taller 05, la reescritura pasó de **1 a 22** marcas de
voz y de **0 a 10** de acompañamiento, con 363 palabras más sobre 1.058. El
volumen no es el objetivo: si el texto crece y no aparece nadie detrás, la
reescritura falló.
