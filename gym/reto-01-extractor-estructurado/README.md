# 🏋️ Reto 01 — Extractor estructurado

| Metadato                            | Valor                                                                                                                                                    |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Fase**                            | Fase 1 — Fundamentos de LLM engineering                                                                                                                  |
| **Sesión en que se asigna**         | Sesión 2                                                                                                                                                 |
| **Tiempo estimado**                 | 4–6 horas (repartidas en la semana)                                                                                                                      |
| **Skill de entrevista que entrena** | Structured output: prompting disciplinado, validación con esquemas y evaluación contra golden set                                                        |
| **Stack**                           | Python 3.11+, Pydantic v2, SDK del LLM de tu elección (Anthropic u OpenAI). **Sin** LangChain, **sin** `instructor`, **sin** tool use / function calling |

---

## Contexto

La tarea más común que un AI Engineer hace en producción no es "construir un chatbot": es convertir texto libre y caótico en datos estructurados que un sistema downstream pueda consumir. Pipelines de enriquecimiento de CRM, triage de tickets de soporte, parsing de facturas, normalización de ofertas de empleo — todo es la misma habilidad: **lograr que un LLM emita JSON correcto, completo y validable, de forma consistente, sobre entradas que nunca viste**.

La trampa en la que cae la mayoría de devs que vienen de backend es tratar al LLM como una API determinista: escriben un prompt una vez, ven que "funciona" con 2 ejemplos y lo dan por terminado. En entrevista eso se nota de inmediato. La pregunta que este reto te prepara para responder es: _"¿Cómo garantizas que la salida de un LLM cumple un esquema, y cómo mides qué tan bien extrae?"_. La respuesta esperada no es "le pido que devuelva JSON" — es: esquema explícito en el prompt, parsing tolerante, validación con Pydantic, política de reintentos, y un **eval con golden set y métrica por campo**. Eso es exactamente lo que vas a construir.

Este reto es deliberadamente **sin tool use ni structured-output nativo del proveedor**: cuando aprendas esas features en la Fase 2 vas a entender exactamente qué problema resuelven y qué hacían por ti. Primero hay que sufrir (un poco) el problema a mano.

## Enunciado

Construye un **extractor de datos estructurados** sobre un corpus de **20 textos libres** de un mismo dominio. Elige **uno** de estos dos dominios (o propone otro al coach antes del miércoles):

- **Ofertas de trabajo** (recomendado): descripciones de vacantes copiadas de LinkedIn / Get on Board / portales locales. Fáciles de conseguir, ricas en campos opcionales y rangos salariales ambiguos.
- **Emails de soporte técnico**: mensajes de clientes reportando problemas (puedes redactarlos tú o adaptarlos de foros públicos), con campos como producto, severidad, categoría del problema y datos del cliente.

El pipeline es: `texto crudo → prompt → LLM → parsing → validación Pydantic → JSON persistido`.

### Esquema de referencia (dominio: ofertas de trabajo)

Define un modelo Pydantic con **al menos 8 campos**, mezclando tipos. Referencia mínima (puedes ajustar nombres, no bajar la complejidad):

```python
from pydantic import BaseModel, Field
from typing import Literal

class OfertaTrabajo(BaseModel):
    titulo: str
    empresa: str | None          # None si el texto no lo dice — NO inventar
    ubicacion: str | None
    modalidad: Literal["remoto", "hibrido", "presencial"] | None
    seniority: Literal["junior", "mid", "senior", "staff", "lead"] | None
    salario_min: int | None      # normalizado a mensual
    salario_max: int | None
    moneda: str | None           # ISO 4217: "USD", "COP", "MXN"...
    skills: list[str]            # lowercase, sin duplicados
    anios_experiencia_min: int | None
```

### Ejemplo de entrada → salida

**Entrada** (texto libre, tal como aparece en el portal):

> Buscamos Backend Dev Ssr/Sr para fintech en CDMX 🚀. Esquema híbrido (3 días oficina). Sueldo: $60,000 - $85,000 MXN brutos. Requisitos: 4+ años con Python, Django, PostgreSQL. Plus: AWS, Docker.

**Salida** (lo que tu pipeline persiste, ya validado):

```json
{
  "titulo": "Backend Developer",
  "empresa": null,
  "ubicacion": "Ciudad de México",
  "modalidad": "hibrido",
  "seniority": "senior",
  "salario_min": 60000,
  "salario_max": 85000,
  "moneda": "MXN",
  "skills": ["python", "django", "postgresql", "aws", "docker"],
  "anios_experiencia_min": 4
}
```

Nota las decisiones que el ejemplo te obliga a tomar y documentar: ¿"Ssr/Sr" mapea a `mid` o `senior`? ¿"CDMX" se normaliza? ¿los "plus" cuentan como skills? No hay una única respuesta correcta — **hay una convención que tú defines, escribes en el prompt y aplicas consistentemente en el golden set**.

### Golden set

Para los 20 textos, construye **a mano** el JSON correcto (`golden/NNN.json`). Este es el corazón del reto: el golden set ES tu definición de "correcto". Hazlo antes de iterar el prompt, no después (si lo haces después, vas a ajustar la verdad a tu salida — eso en producción se llama hacer trampa).

Al menos **5 de los 20 textos** deben ser "difíciles": campos ausentes, rangos salariales en otra moneda o por hora, emojis y ruido, seniority ambiguo, texto en spanglish.

## Requisitos

1. **Corpus versionado**: 20 textos en `data/raw/NNN.txt` (001–020), con un `data/SOURCES.md` indicando de dónde salió cada uno.
2. **Golden set versionado**: 20 archivos `data/golden/NNN.json`, válidos contra tu modelo Pydantic (incluye un script o test que lo verifique).
3. **Modelo Pydantic** con ≥ 8 campos, incluyendo: ≥ 2 campos `Literal`/enum, ≥ 1 lista, ≥ 1 numérico y ≥ 3 campos opcionales que deben ser `null` cuando la información no está en el texto.
4. **Extractor por prompting puro**: una llamada de chat normal (texto → texto). Prohibido: tool use, function calling, modos JSON nativos del proveedor (`response_format`, structured outputs), librerías tipo `instructor`/`outlines`/LangChain. Permitido y esperado: esquema y reglas dentro del prompt, few-shot examples.
5. **Parsing robusto**: tu código debe extraer el JSON aunque el modelo lo envuelva en ` ```json ` o agregue texto alrededor, y validar con `OfertaTrabajo.model_validate(...)`.
6. **Política de reintentos**: si el parsing o la validación fallan, reintenta máximo 2 veces inyectando el error de Pydantic en el mensaje de reintento. Tras 3 fallos, registra el caso como fallido y continúa (el run nunca crashea).
7. **CLI reproducible**: `python extract.py --input data/raw --output runs/<timestamp>/` procesa los 20 textos y persiste un JSON por texto + un `meta.json` con modelo usado, temperatura, versión del prompt y conteo de reintentos.
8. **Eval automatizado**: `python evaluate.py --run runs/<timestamp>/` compara contra el golden set y emite exactitud por campo + global (ver sección de evaluación).
9. **Prompt versionado en archivo** (`prompts/v1.md`, `prompts/v2.md`, ...): nunca hardcodeado en un string dentro del código. Cada versión nueva se crea porque el eval mostró un fallo concreto; el porqué va en `PROMPTLOG.md`.
10. **Determinismo razonable**: temperatura ≤ 0.2 y dos runs consecutivos del eval no difieren en más de 2 puntos porcentuales de exactitud global.

## Criterios de aceptación

- [ ] `extract.py` procesa los 20 textos de punta a punta sin intervención manual y sin crashear, en < 5 minutos.
- [ ] **Exactitud por campo ≥ 90%** en cada uno de los campos del esquema (no solo el promedio global), medida por `evaluate.py` contra el golden set.
- [ ] **Exactitud global ≥ 90%** (campos correctos / campos totales = correctos sobre 20 × N campos).
- [ ] 100% de las salidas persistidas validan contra el modelo Pydantic (0 archivos malformados en el run final).
- [ ] Tasa de reintento ≤ 25% (≤ 5 de 20 textos necesitaron reintento en el run final) — si necesitas más, el prompt está flojo.
- [ ] Los campos `null` del golden set se respetan: 0 alucinaciones de datos que no están en el texto (un campo inventado cuenta como error aunque "suene plausible").
- [ ] Existen ≥ 2 versiones de prompt en `prompts/` y `PROMPTLOG.md` documenta qué fallo del eval motivó cada cambio, con números antes/después.
- [ ] Dos runs consecutivos difieren ≤ 2 pp en exactitud global (pegar ambas tablas en el README del repo).
- [ ] El repo incluye `README.md` propio con: cómo correr, tabla final de exactitud por campo, y 3 errores del modelo que encontraste interesantes (con el texto y la salida).

## Cómo se evalúa

El harness compara campo a campo cada salida contra su golden. Reglas de comparación que debes implementar (y documentar si las cambias):

- **Escalares** (`str`, `int`, `Literal`): igualdad exacta tras normalizar (strip, lowercase para strings). `None` solo matchea `None`.
- **Listas** (`skills`): comparación como conjuntos normalizados; reporta **F1 por texto** y cuenta el campo como "correcto" si F1 ≥ 0.8.
- La exactitud de un campo = textos donde ese campo fue correcto / 20.

Estructura sugerida del eval (esqueleto, no solución):

```python
# evaluate.py — esqueleto
import json
from pathlib import Path
from collections import defaultdict

FIELDS_SCALAR = ["titulo", "empresa", "ubicacion", "modalidad", "seniority",
                 "salario_min", "salario_max", "moneda", "anios_experiencia_min"]
FIELDS_LIST = ["skills"]

def compare_scalar(pred, gold) -> bool:
    ...  # normalizar y comparar; None solo matchea None

def f1_listas(pred: list, gold: list) -> float:
    ...  # sets normalizados → precision, recall, f1

def evaluate(run_dir: Path, golden_dir: Path) -> dict:
    hits = defaultdict(int)
    total = 0
    for gold_file in sorted(golden_dir.glob("*.json")):
        gold = json.loads(gold_file.read_text())
        pred = json.loads((run_dir / gold_file.name).read_text())
        for f in FIELDS_SCALAR:
            hits[f] += compare_scalar(pred[f], gold[f])
        for f in FIELDS_LIST:
            hits[f] += f1_listas(pred[f], gold[f]) >= 0.8
        total += 1

    report = {f: hits[f] / total for f in FIELDS_SCALAR + FIELDS_LIST}
    report["__global__"] = sum(hits.values()) / (total * len(report))
    return report  # imprimir como tabla: campo | aciertos | exactitud

if __name__ == "__main__":
    ...  # argparse: --run, --golden; exit code 1 si algún campo < 0.90
```

El coach va a correr tu eval en la sesión de revisión, va a tomar 2 textos del corpus al azar y te va a pedir que defiendas el golden: _"¿por qué aquí seniority es `mid` y no `senior`?"_. Si la respuesta no está en tus convenciones escritas, cuenta como hallazgo.

## Pistas

<details><summary>Pista 1 — Si la exactitud está estancada y no sabes por qué</summary>

Deja de mirar el prompt y mira los errores. Agrega a `evaluate.py` un modo `--show-errors` que imprima, por cada campo fallido: id del texto, valor predicho vs. golden. Clasifica los errores en tres cubetas: (a) el modelo se equivocó, (b) tu golden está mal, (c) tu convención es ambigua y ambos valores son defendibles. En la primera iteración, típicamente la mitad de los "errores" son (b) y (c) — arregla esos primero, son gratis.

</details>

<details><summary>Pista 2 — Si el modelo inventa datos o no respeta los null</summary>

Dos técnicas que casi siempre lo resuelven: (1) en el prompt, define cada campo con una línea propia que incluya tipo, valores permitidos y la regla explícita _"si el texto no menciona X, devuelve null; nunca infieras"_ — una regla general al final del prompt no funciona tan bien como la regla pegada al campo. (2) Agrega 2–3 few-shot examples donde el output correcto **tiene varios null**: el modelo aprende del patrón de los ejemplos mucho más que de las instrucciones, y si todos tus ejemplos tienen campos completos, va a rellenar todo siempre.

</details>

<details><summary>Pista 3 — Si el JSON sale malformado o envuelto en texto (casi-spoiler)</summary>

Estrategia en capas que llega a ~100% de parseo: (1) en el prompt, termina con _"Responde únicamente con el objeto JSON, sin markdown ni explicación"_ y prellena el turno del asistente con `{` si tu SDK lo permite (en la API de Anthropic: agrega un mensaje final con `role: "assistant"` y `content: "{"`, y antepones `{` a la respuesta). (2) En el parser, busca el primer `{` y el último `}` y parsea ese slice antes de rendirte. (3) Si `json.loads` o Pydantic fallan, reintenta con un mensaje que incluya la salida anterior y el error textual: _"Tu respuesta anterior falló la validación con este error: {error}. Corrige y devuelve solo el JSON"_. Con esas tres capas, los reintentos bajan a 1–2 de 20.

</details>

## Bonus

1. **Matriz de modelos**: corre el mismo eval con un modelo barato/rápido y uno frontier (p. ej. Haiku vs. Sonnet) y agrega al README una tabla exactitud-por-campo × modelo + costo por 20 extracciones. Concluye en 3 líneas cuándo usarías cada uno. Esto convierte el reto en una historia de _model selection_ para entrevista.
2. **Eval como gate de CI**: GitHub Action que corre `evaluate.py` sobre un run cacheado (o en vivo con un secret) y falla el build si algún campo baja de 90%. Es la semilla del concepto de _regression eval_ que vas a usar el resto del programa.

## Qué demuestra en entrevista

- _"Construí un pipeline de extracción estructurada evaluado contra un golden set de 20 ejemplos anotados a mano, con exactitud por campo ≥ 90%. La métrica era por campo, no global, porque un 95% global puede esconder un campo que falla la mitad de las veces."_ — demuestra que piensas en evaluación antes que en prompts.
- _"La validación era Pydantic con reintento acotado: el error de validación se reinyectaba al modelo, máximo 2 reintentos, y el caso fallido se registraba sin tumbar el run. La tasa de reintento era una métrica de salud del prompt, no solo un mecanismo de recuperación."_ — demuestra ingeniería de robustez, no fe en el modelo.
- _"Versioné los prompts como artefactos y cada cambio estaba justificado por un fallo medible del eval — puedo mostrarte el log de v1 a v3 con los números antes/después."_ — demuestra que iteras con método científico, que es lo que diferencia a un AI engineer de alguien que 'le pega al prompt hasta que sale'.

## Entregable

**Al repo** (carpeta `gym/reto-01-extractor-estructurado/` de tu repo de soluciones, antes del domingo 23:59):

- `data/raw/` (20 textos) + `data/SOURCES.md` + `data/golden/` (20 JSON).
- `schema.py`, `extract.py`, `evaluate.py`, `prompts/v*.md`, `PROMPTLOG.md`.
- `runs/` con al menos el run final y el anterior (para ver la mejora).
- `README.md` con instrucciones de ejecución, tabla final de exactitud por campo, las dos tablas de los runs consecutivos y los 3 errores interesantes comentados.

**En la sesión de revisión** (10 minutos, comparte pantalla):

1. Corre `extract.py` + `evaluate.py` en vivo sobre los 20 textos (2 min).
2. Muestra la evolución v1 → vN del prompt con los números de cada versión (3 min).
3. Defiende 2 decisiones del golden set que el coach elija al azar (3 min).
4. Una cosa que harías distinto si fueran 20.000 textos en vez de 20 (2 min).
