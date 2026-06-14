# 🏋️ Reto 03 — RAG básico con citas

| Metadato                            | Valor                                                                                                      |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **Fase**                            | Fase 2                                                                                                     |
| **Sesión en que se asigna**         | Sesión 4                                                                                                   |
| **Tiempo estimado**                 | 10–14 horas (repartidas en 1 semana)                                                                       |
| **Skill de entrevista que entrena** | Diseño de pipelines RAG end-to-end: justificar chunking, retrieval y evaluación con métricas, no con vibes |
| **Prerrequisitos**                  | Reto 02 completado (llamadas a LLM con structured output), Python 3.11+, una API key de LLM                |

---

## Contexto

RAG (Retrieval-Augmented Generation) es, junto con tool use, el patrón más demandado en posiciones de AI Engineer. Casi cualquier empresa que contrata para este rol tiene el mismo problema de fondo: "tenemos documentación/tickets/contratos y queremos que un LLM responda preguntas sobre eso sin alucinar". La diferencia entre un dev que "ha jugado con LangChain" y un AI engineer contratable es que el segundo puede explicar **por qué** eligió cada pieza del pipeline y **cómo sabe** que funciona.

Este reto te obliga a tomar todas las decisiones que en un tutorial vienen dadas: cómo partir los documentos (chunking), qué modelo de embeddings usar, cuántos chunks recuperar, cómo forzar al modelo a citar sus fuentes, y —lo más importante— cómo medir si el sistema responde bien. La exigencia de **citas verificables** es deliberada: una respuesta correcta sin cita correcta es un fallo, porque en producción la cita es lo que permite a un humano auditar al sistema.

La pregunta de entrevista que dominar esto te permite responder con autoridad es: _"Cuéntame cómo construirías un sistema de Q&A sobre nuestra documentación interna. ¿Cómo decides el tamaño de chunk? ¿Cómo evalúas que funciona antes de ponerlo frente a usuarios?"_. Si tu única respuesta es "usaría LangChain con los defaults", la entrevista se acabó ahí. Después de este reto, tu respuesta incluye números: tu tamaño de chunk, tu top-k, tu accuracy sobre un set de evaluación, y los trade-offs que descartaste.

## Enunciado

Construye un pipeline RAG completo, en Python, sobre **documentación técnica real** que tú elijas. Corpus sugeridos (elige UNO):

- **Docs de FastAPI** (https://github.com/fastapi/fastapi — carpeta `docs/en/docs/`, ~150 archivos markdown).
- **Docs de la API de Anthropic** (https://docs.anthropic.com — descargables como markdown agregando `.md` a las URLs, o vía el archivo `llms.txt`).
- Otro corpus técnico de tu interés, **siempre que** tenga ≥ 40 documentos/páginas y ≥ 100 KB de texto total. Valídalo con el coach por Slack antes de empezar.

El pipeline tiene cinco etapas, todas escritas por ti (puedes usar librerías para embeddings y vector store, pero NO frameworks que encadenen el pipeline entero por ti — nada de `RetrievalQA.from_chain_type()` ni equivalentes):

1. **Ingesta**: script que descarga/lee el corpus y lo normaliza a una lista de documentos con metadata (`source_id`, `title`, `url_o_ruta`).
2. **Chunking**: parte cada documento en chunks. La estrategia (tamaño, overlap, respeto de headers/bloques de código) debe estar **justificada por escrito** en una sección `## Decisiones de chunking` de tu propio README, con al menos una alternativa considerada y descartada.
3. **Embeddings + vector store local**: indexa los chunks en un vector store que corra en tu máquina (Chroma, LanceDB, FAISS o sqlite-vec). Nada de servicios cloud para el store.
4. **Retrieval**: dada una pregunta, recupera los top-k chunks más relevantes. El valor de k es una decisión tuya y debe estar justificada (probaste al menos 2 valores).
5. **Generación con citas**: el LLM responde usando SOLO los chunks recuperados y cita el `source_id` de cada documento que usó. La salida es JSON estructurado.

**Ejemplo de entrada/salida** (corpus = docs de FastAPI):

Entrada:

```
¿Cómo declaro un parámetro de query opcional con valor por defecto en FastAPI?
```

Salida (JSON):

```json
{
  "answer": "Declara el parámetro en la firma de la función con un valor por defecto, p. ej. `q: str | None = None`. FastAPI lo interpreta como query param opcional...",
  "citations": ["tutorial/query-params.md"],
  "confidence": "high"
}
```

Cuando la respuesta no está en el corpus, el sistema debe decirlo en lugar de inventar:

Entrada:

```
¿Cuál es el precio del plan enterprise de FastAPI Cloud?
```

Salida:

```json
{
  "answer": "No encontré información sobre esto en la documentación indexada.",
  "citations": [],
  "confidence": "none"
}
```

Además del pipeline, escribes el **set de evaluación**: 15 preguntas con su respuesta esperada (resumida) y el/los `source_id` correcto(s), en un archivo `eval/questions.jsonl`. Mínimo 12 preguntas respondibles con el corpus y mínimo 2 preguntas **trampa** (no respondibles con el corpus, donde la respuesta correcta es abstenerse).

## Requisitos

1. CLI o script `ingest.py` que construye el índice desde cero en una sola ejecución (`python ingest.py`) y reporta: nº de documentos, nº de chunks, tiempo total.
2. CLI `ask.py` que recibe una pregunta por argumento (`python ask.py "¿cómo...?"`) e imprime el JSON de salida con `answer`, `citations` (lista de `source_id`) y `confidence`.
3. El chunking respeta límites semánticos: ningún chunk corta un bloque de código por la mitad ni mezcla contenido de dos headers H2 distintos.
4. Cada chunk almacenado conserva metadata suficiente para citar: `source_id` y `title` como mínimo.
5. El vector store es local y persistente: ejecutar `ask.py` NO re-indexa; carga el índice ya construido.
6. El prompt de generación instruye explícitamente: responder solo con el contexto, citar fuentes, y abstenerse si el contexto no alcanza.
7. La salida del LLM se parsea como JSON estructurado con validación (Pydantic o equivalente); una salida malformada se reintenta al menos 1 vez antes de fallar.
8. Archivo `eval/questions.jsonl` con las 15 preguntas (12+ respondibles, 2+ trampa), cada línea con `question`, `expected_answer`, `expected_sources` (lista; vacía para las trampa).
9. Script `eval/run_eval.py` que ejecuta las 15 preguntas contra el pipeline y reporta por pregunta: respuesta correcta (sí/no), cita correcta (sí/no), y el resumen agregado.
10. README propio del reto con: instrucciones de setup reproducibles (de cero a eval corriendo en ≤ 5 comandos), sección `## Decisiones de chunking` y sección `## Resultados de evaluación` con la tabla final.
11. Las API keys se leen de variables de entorno; ninguna key en el código ni en el repo.
12. Costo total de construir el índice + correr el eval completo ≤ 2 USD (reporta tu estimación de tokens/costo en el README).

## Criterios de aceptación

- [ ] El corpus indexado tiene ≥ 40 documentos y ≥ 100 KB de texto.
- [ ] `python ingest.py` corre de cero a índice persistido sin intervención manual y en < 10 minutos.
- [ ] `python ask.py "<pregunta>"` responde en < 15 segundos por pregunta (sin contar cold start de modelos locales).
- [ ] El JSON de salida valida contra el schema (`answer: str`, `citations: list[str]`, `confidence: "high"|"medium"|"low"|"none"`) en el 100 % de las 15 preguntas del eval (con el reintento permitido).
- [ ] **≥ 12 de 15** preguntas obtienen respuesta correcta según el juez del eval.
- [ ] **≥ 11 de 15** preguntas obtienen respuesta correcta **Y** citan al menos un `source_id` de `expected_sources` (las trampa cuentan como correctas si `citations == []` y el sistema se abstiene).
- [ ] Las 2+ preguntas trampa producen abstención (cero alucinación: 0 respuestas inventadas sobre las trampa).
- [ ] Ninguna cita devuelta apunta a un `source_id` que no existe en el índice (0 citas fantasma en todo el eval).
- [ ] La sección `## Decisiones de chunking` documenta: tamaño elegido, overlap, al menos 1 alternativa descartada y por qué.
- [ ] La sección `## Resultados de evaluación` incluye la tabla de las 15 preguntas con ✅/❌ por respuesta y por cita, y la comparación de al menos 2 valores de k.
- [ ] Repo reproducible: el coach puede clonar, exportar su API key y correr el eval con ≤ 5 comandos documentados.

## Cómo se evalúa

El harness corre las 15 preguntas contra tu pipeline y evalúa dos cosas por separado: (a) corrección de la respuesta con **LLM-as-judge** comparando contra `expected_answer`, y (b) corrección de la cita con **comparación exacta de conjuntos** contra `expected_sources` (esto NO se lo preguntas a un LLM: es determinista). El coach correrá tu `eval/run_eval.py` tal cual; estructura sugerida:

```python
# eval/run_eval.py — estructura del harness (no la solución)
import json
from pipeline import answer_question  # tu función: pregunta -> dict validado

def judge_answer(question: str, expected: str, actual: str) -> bool:
    """LLM-as-judge: ¿'actual' es consistente con 'expected'?
    Prompt al juez pidiendo verdict JSON {"correct": true/false} con
    temperatura 0. El juez NO ve las citas, solo compara contenido."""
    ...

def judge_citations(expected_sources: list[str], citations: list[str]) -> bool:
    if not expected_sources:                      # pregunta trampa
        return citations == []                    # debe abstenerse
    return bool(set(citations) & set(expected_sources))

results = []
for line in open("eval/questions.jsonl"):
    case = json.loads(line)
    out = answer_question(case["question"])       # {"answer", "citations", "confidence"}
    results.append({
        "question": case["question"],
        "answer_ok": judge_answer(case["question"], case["expected_answer"], out["answer"]),
        "citation_ok": judge_citations(case["expected_sources"], out["citations"]),
    })

answer_score = sum(r["answer_ok"] for r in results)
full_score = sum(r["answer_ok"] and r["citation_ok"] for r in results)
print(f"Respuestas correctas: {answer_score}/15  (mínimo: 12)")
print(f"Correctas + bien citadas: {full_score}/15  (mínimo: 11)")
```

En la sesión de revisión, el coach además hará 2–3 preguntas **fuera de tu eval set** en vivo para verificar que no sobreajustaste el prompt a tus 15 preguntas.

## Pistas

<details><summary>Pista 1 (empujón suave)</summary>

Empieza por el final: escribe primero las 15 preguntas del eval, leyendo el corpus a mano. Esto te obliga a conocer tus documentos y te da un objetivo medible desde el día 1. Un pipeline RAG sin eval es un tutorial; con eval es ingeniería. Para el corpus, los docs de FastAPI ya están en markdown limpio dentro del repo de GitHub — un `git clone --depth 1` y tienes la ingesta casi resuelta.

</details>

<details><summary>Pista 2 (dirección concreta)</summary>

Para markdown técnico, el chunking que mejor suele funcionar es **por estructura, no por caracteres**: parte por headers (H2/H3) y solo subdivide si una sección supera ~1.000–1.500 tokens, manteniendo los bloques de código intactos (un chunk que corta un `code fence` por la mitad envenena el retrieval). Guarda el título del header en la metadata del chunk y antepónlo al texto antes de calcular el embedding — el embedding de "Query Parameters > valores por defecto" recupera mucho mejor que el del párrafo suelto. Para el store, Chroma en modo persistente (`PersistentClient`) es lo que menos fricción te dará; para embeddings, `text-embedding-3-small` o un sentence-transformers local tipo `all-MiniLM-L6-v2` están bien a este nivel.

</details>

<details><summary>Pista 3 (casi spoiler)</summary>

Para que las citas sean fiables, no le pidas al modelo que "cite sus fuentes" en abstracto: numera los chunks en el prompt (`[1] source: tutorial/query-params.md\n<texto>`) y pídele que devuelva los números que usó; luego TÚ mapeas números → `source_id` en código. Así es imposible una cita fantasma (criterio de las 0 citas inventadas). Para la abstención, añade al prompt una instrucción explícita con el formato exacto del caso "no encontrado" y un umbral en código: si la similaridad del mejor chunk recuperado queda por debajo de un valor que calibras con tus preguntas trampa, ni siquiera llames al LLM y devuelve la abstención directamente. Para elegir k: corre tu eval con k=3 y k=6, mete ambas filas en la tabla de resultados, y quédate con el que gane — esa tabla ES la justificación que pide el requisito 10.

</details>

## Bonus

1. **Evaluación de retrieval aislada**: además del eval end-to-end, mide `recall@k` del retriever solo (¿el chunk correcto está entre los top-k?) para k ∈ {1, 3, 5, 10} y grafica/tabula el resultado. Esto te permite responder en entrevista la pregunta de oro: "¿tu error está en el retrieval o en la generación?".
2. **Re-ranking**: añade un paso de re-rank (cross-encoder local como `ms-marco-MiniLM-L-6-v2`, o re-rank con LLM) sobre los top-20 del vector store antes de pasar top-k al generador, y demuestra con tu eval si mejora o no el score (un resultado negativo bien medido también vale).

## Qué demuestra en entrevista

- _"Construí un pipeline RAG desde cero, sin frameworks de orquestación, sobre los docs de FastAPI: chunking estructural por headers respetando bloques de código, Chroma local, y generación con citas verificadas en código — el modelo devuelve índices de chunks y yo resuelvo las fuentes, así que las citas fantasma son imposibles por construcción."_
- _"Lo evalué con un harness de 15 preguntas con ground truth: LLM-as-judge para la corrección de la respuesta y matching determinista para las citas. Cerré con 13/15 correctas y bien citadas, y las preguntas trampa con 0 alucinaciones gracias a un umbral de similaridad calibrado."_
- _"Puedo defender cada decisión con datos: probé k=3 contra k=6 con el mismo eval y elegí con la tabla delante, no por intuición — y sé separar fallos de retrieval de fallos de generación porque medí recall@k del retriever aislado."_

## Entregable

**En el repo** (carpeta `reto-03-rag-basico/` de tu repo del gym, o repo propio enlazado):

- `ingest.py`, `ask.py`, código del pipeline, `requirements.txt`/`pyproject.toml`.
- `eval/questions.jsonl` (las 15 preguntas) y `eval/run_eval.py`.
- `eval/results.json` o equivalente: la salida cruda de tu última corrida del eval.
- README del reto con: setup en ≤ 5 comandos, `## Decisiones de chunking`, `## Resultados de evaluación` (tabla de 15 preguntas + comparación de k), y estimación de costo.
- NO subas el índice vectorial ni el corpus crudo si pesa > 10 MB (gitignore + script que lo regenera).

**En la sesión de revisión** (15 min):

1. Demo en vivo: 2 preguntas tuyas + 2–3 preguntas sorpresa del coach, mostrando el JSON con citas.
2. Corrida de `eval/run_eval.py` en vivo (o resultados de la corrida del día, con timestamp).
3. Defensa de 2 decisiones: por qué ese chunking y por qué ese k, con la evidencia de tu tabla.
4. La pregunta del coach que debes poder responder: _"Si mañana el score baja a 8/15, ¿cómo diagnosticas si el problema está en el retrieval o en la generación?"_
