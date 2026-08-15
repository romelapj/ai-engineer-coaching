# 🏋️ Reto 04: Tuning de retrieval con métricas

| Campo                   | Valor                                                                                   |
| ----------------------- | --------------------------------------------------------------------------------------- |
| **Fase**                | Fase 2                                                                                  |
| **Se asigna en**        | Sesión 5                                                                                |
| **Tiempo estimado**     | 8–12 h (una semana de gym)                                                              |
| **Prerequisito**        | Reto 03 (RAG funcional con índice vectorial)                                            |
| **Skill de entrevista** | Evaluación de sistemas RAG: métricas de IR (recall@k, MRR), búsqueda híbrida, reranking |

---

## Contexto

Cualquiera puede armar un RAG demo en una tarde: embeddings, vector store, top-5, prompt. Lo que separa a un dev que "jugó con LangChain" de un AI engineer contratable es la respuesta a una sola pregunta: **"¿cómo sabes que tu retrieval funciona, y cómo lo mejorarías si no?"**. Esa pregunta (o una variante) aparece en prácticamente toda entrevista de AI engineering con componente RAG. Responder "se ve bien cuando lo pruebo a mano" es eliminatorio.

La respuesta profesional tiene tres partes: (1) un **golden set** de evaluación con pares pregunta→chunks relevantes, (2) **métricas de information retrieval** medidas contra ese set (recall@k para "¿está lo relevante en el top-k?" y MRR para "¿qué tan arriba aparece?"), y (3) un **ciclo de mejora medible**: cambias una cosa (híbrido, reranking, chunking), corres el eval, comparas números. Sin el paso 1 y 2, el paso 3 es superstición.

Este reto te obliga a hacer ese ciclo completo una vez, de punta a punta, sobre tu propio RAG del reto 3. Al terminar vas a poder decir en una entrevista: "construí un golden set de N pares, mi baseline de búsqueda vectorial pura daba recall@5 de X, implementé híbrido BM25+vectores con RRF y un reranker cross-encoder, y subí a Y, y sé exactamente qué tipo de queries mejoraron y por qué". Eso es una historia de entrevista, no un tutorial seguido.

## Enunciado

Vas a construir un **harness de evaluación de retrieval** sobre el corpus de tu RAG del reto 3, medir un baseline, e implementar dos mejoras (búsqueda híbrida con RRF y reranking) demostrando con números que mejoran.

> **Si tu reto 3 quedó flojo o el corpus es muy chico** (< 200 chunks), re-indexa primero un corpus más rico. Sugerencias: la documentación de FastAPI (`fastapi/fastapi` carpeta `docs/en/`), la documentación de Stripe sobre pagos, o el handbook de GitLab. Necesitas un corpus donde existan queries con respuesta repartida en varios documentos, si no, el híbrido no tiene nada que aportar.

### Parte A: Golden set (el 50 % del valor del reto)

Construye un archivo `golden_set.jsonl` con **mínimo 25 pares** pregunta→chunks relevantes. Cada línea:

```json
{
  "query_id": "q014",
  "query": "¿Cómo declaro un parámetro de path con validación de rango en FastAPI?",
  "relevant_chunk_ids": [
    "docs/path-params-numeric-validations.md::chunk_2",
    "docs/path-params-numeric-validations.md::chunk_3"
  ],
  "query_type": "factual",
  "notes": "La respuesta requiere Path() + ge/le; chunk_2 tiene el import, chunk_3 el ejemplo."
}
```

Requisitos del golden set:

- Los `relevant_chunk_ids` deben ser **IDs estables de tu índice** (define un esquema de ID determinista al chunkear: `archivo::chunk_N`). Si re-indexas, los IDs no pueden cambiar.
- Mezcla deliberada de **al menos 3 tipos de query** y etiqueta cada una en `query_type`:
  - `factual`: respuesta en 1 chunk, vocabulario similar al documento (aquí BM25 brilla).
  - `parafraseada`: misma intención pero con vocabulario distinto al del documento: sinónimos, descripción coloquial (aquí los vectores brillan).
  - `multi_chunk`: la respuesta completa requiere ≥ 2 chunks (mide recall de verdad).
- **Tú validas cada par a mano.** Puedes usar un LLM para _proponer_ preguntas por chunk, pero cada par del golden set lleva tu revisión: ¿la pregunta es natural? ¿los chunks marcados realmente la responden? ¿falta algún chunk relevante que no marcaste? (los falsos negativos en el golden set te van a dar métricas mentirosas).

### Parte B: Baseline

Mide tu retrieval actual del reto 3 (vectorial puro, top-k) contra el golden set:

- **recall@5**: fracción de chunks relevantes que aparecen en el top-5, promediada sobre queries.
- **MRR@10**: media del recíproco del rank del _primer_ chunk relevante dentro del top-10 (0 si no aparece).

Reporta también las métricas **desglosadas por `query_type`**: esa tabla es la que cuenta la historia.

### Parte C: Mejoras

1. **Búsqueda híbrida**: añade un índice léxico **BM25** (sugerido: `rank_bm25` en memoria, o FTS5 de SQLite si quieres algo más serio) sobre los mismos chunks, y fusiona los rankings vectorial + BM25 con **Reciprocal Rank Fusion** (RRF, `k=60` como punto de partida).
2. **Reranking**: sobre el top-20 del híbrido, aplica un **cross-encoder** (sugerido: `BAAI/bge-reranker-base` vía `sentence-transformers`, o Cohere Rerank si prefieres API) y quédate con el top-5 reordenado.

Mide **cada configuración por separado**; necesitas saber cuánto aporta cada pieza:

| Configuración        | recall@5 | MRR@10 | latencia p50 (ms) |
| -------------------- | -------- | ------ | ----------------- |
| Vectorial (baseline) | -        | -      | -                 |
| BM25 solo            | -        | -      | -                 |
| Híbrido (RRF)        | -        | -      | -                 |
| Híbrido + reranker   | -        | -      | -                 |

### Parte D: Análisis

Un apartado escrito (en el README de tu solución, máx. 1 página) que responda: ¿qué configuración ganó y por qué? ¿Qué `query_type` mejoró más con el híbrido? ¿El reranker ayudó a recall, a MRR, o solo a MRR (y por qué eso es lo esperado)? Incluye **2 queries concretas** donde el baseline fallaba y el sistema mejorado acierta, con la explicación del mecanismo (p. ej., "query factual con el término exacto `lifespan`: el vector la confundía con chunks de eventos; BM25 la clava por match léxico").

## Requisitos

1. Golden set `golden_set.jsonl` con ≥ 25 pares, IDs de chunk estables, los 3 tipos de query etiquetados y validados a mano.
2. Script `eval.py` ejecutable con un solo comando (`python eval.py --config baseline|bm25|hybrid|hybrid_rerank`) que imprime recall@5, MRR@10 y latencia p50, global y por `query_type`.
3. Implementación de BM25 sobre exactamente los mismos chunks del índice vectorial (mismo chunking, mismos IDs).
4. Fusión RRF implementada **por ti** (la fórmula son 5 líneas; nada de `EnsembleRetriever` mágico de framework: tienes que poder explicarla en pizarra).
5. Reranking con cross-encoder sobre el top-20 del híbrido, configurable el modelo.
6. Resultados reproducibles: semillas fijas donde aplique, versiones pinneadas en `requirements.txt`, y el corpus indexado de forma determinista.
7. Tabla comparativa de las 4 configuraciones en el README de tu solución, con la latencia incluida (la mejora de calidad tiene un costo; debes conocerlo).
8. Análisis escrito de la Parte D con los 2 casos de fallo→acierto.

## Criterios de aceptación

- [ ] `golden_set.jsonl` tiene ≥ 25 queries; ≥ 6 son `parafraseada` y ≥ 5 son `multi_chunk`.
- [ ] Cada query del golden set tiene ≥ 1 `relevant_chunk_id` que existe en el índice (hay un check automático en `eval.py` que falla si no).
- [ ] `python eval.py --config hybrid_rerank` corre de punta a punta en < 5 min en tu máquina y produce la tabla de métricas sin intervención manual.
- [ ] Las 4 configuraciones están medidas y reportadas con 3 decimales en la tabla del README.
- [ ] La mejor configuración supera al baseline en **al menos +0.05 absoluto en recall@5 o +0.05 en MRR@10**, sin que la otra métrica caiga más de 0.02. Si tras esfuerzo honesto no lo logras, el criterio alternativo es un análisis de error que explique con ≥ 3 queries concretas por qué el techo está donde está, pero el camino esperado es la mejora.
- [ ] El desglose por `query_type` está reportado y el análisis lo referencia (no es decoración).
- [ ] La función de RRF está escrita por ti y tiene un test unitario con un caso a mano (2 rankings pequeños → fusión esperada).
- [ ] Latencia p50 reportada por configuración.
- [ ] Cero resultados copiados a mano: la tabla del README sale de la salida de `eval.py` (ideal: `eval.py --markdown` la genera).

## Cómo se evalúa

El coach va a clonar tu repo, correr `eval.py` y comparar tu tabla contra lo que sale. Después va a abrir `golden_set.jsonl` y auditar 5 pares al azar: si encuentra 2 pares mal etiquetados (chunks marcados que no responden la pregunta, o relevantes obvios sin marcar), el reto se devuelve. La estructura esperada del harness:

```python
# eval.py: estructura, no solución
import json, time, statistics

def load_golden_set(path: str) -> list[dict]: ...

def retrieve(query: str, config: str, k: int = 10) -> list[str]:
    """Devuelve chunk_ids ordenados por relevancia según la config:
    'baseline' | 'bm25' | 'hybrid' | 'hybrid_rerank'."""
    ...

def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """|relevantes ∩ top-k| / |relevantes|"""
    ...

def reciprocal_rank(retrieved: list[str], relevant: set[str], k: int) -> float:
    """1/rank del primer relevante en el top-k; 0.0 si no aparece."""
    ...

def run_eval(config: str, golden_path: str = "golden_set.jsonl") -> dict:
    rows = []
    for ex in load_golden_set(golden_path):
        t0 = time.perf_counter()
        retrieved = retrieve(ex["query"], config, k=10)
        latency_ms = (time.perf_counter() - t0) * 1000
        relevant = set(ex["relevant_chunk_ids"])
        rows.append({
            "query_id": ex["query_id"],
            "query_type": ex["query_type"],
            "recall@5": recall_at_k(retrieved, relevant, 5),
            "mrr@10": reciprocal_rank(retrieved, relevant, 10),
            "latency_ms": latency_ms,
        })
    return aggregate(rows)  # global + por query_type + p50 latencia

if __name__ == "__main__":
    # argparse: --config, --markdown
    ...
```

Preguntas que el coach va a hacer en vivo (prepáralas): _"¿por qué RRF y no promediar scores?"_, _"¿qué pasa con recall@5 si el reranker solo reordena el top-20?"_, _"¿por qué MRR y no nDCG aquí?"_, _"¿cómo evitaste contaminar el golden set si usaste un LLM para generar preguntas?"_.

## Pistas

<details><summary>Pista 1: El golden set se te está haciendo eterno</summary>

No escribas 25 preguntas mirando al techo. Recorre tu índice, toma una muestra de ~40 chunks, y pídele a un LLM que proponga 1–2 preguntas _naturales_ por chunk ("pregunta que un usuario real haría y que este texto responde"). Luego tu trabajo humano es: descartar las preguntas que solo tienen sentido si ya viste el chunk (esas son trampa fácil para el retrieval), reescribir ~un tercio con vocabulario distinto al del documento para crear las `parafraseada`, y para las `multi_chunk` buscar temas que tu corpus parte en varios archivos (en docs técnicas: "concepto + ejemplo" suelen vivir separados). Presupuesta 3–4 h solo para esto; es normal y es donde más aprendes sobre tu corpus.

</details>

<details><summary>Pista 2: El híbrido no mejora nada</summary>

Tres causas típicas, en orden de probabilidad: (1) **IDs desalineados**: BM25 y el índice vectorial devuelven identificadores distintos para el mismo chunk, así que RRF nunca suma los dos votos; imprime los dos top-10 para una query y verifica a ojo que se intersectan. (2) **Tokenización pobre en BM25**: `texto.split()` deja puntuación pegada (`lifespan,` ≠ `lifespan`); usa lowercase + un tokenizador simple con regex `\w+`. (3) Tu golden set casi no tiene queries `factual` con términos exactos, que es donde BM25 aporta; revisa el desglose por `query_type`: si el híbrido sube en `factual` y baja el promedio por otra cosa, el desglose te lo va a mostrar y el promedio te lo va a ocultar. La fórmula de RRF para referencia: `score(d) = Σ_r 1/(k + rank_r(d))` sobre cada ranking `r` donde aparece `d`, con `k=60`.

</details>

<details><summary>Pista 3, casi-spoiler: armado concreto</summary>

Stack mínimo que funciona: `chromadb` (o lo que usaste en el reto 3) para vectores + `rank_bm25.BM25Okapi(tokenized_corpus)` en memoria, construido desde la **misma lista de chunks con los mismos IDs**. Para RRF: pide top-50 a cada retriever, construye `dict[chunk_id, float]` acumulando `1/(60 + rank)` (rank empezando en 1), ordena descendente, corta a 20. Para el reranker: `from sentence_transformers import CrossEncoder; ce = CrossEncoder("BAAI/bge-reranker-base"); scores = ce.predict([(query, chunk_text) for ...])` sobre esos 20, reordena, corta a 5. Detalle que importa: el reranker necesita el **texto** del chunk, así que guarda un mapa `chunk_id → texto` al indexar. Y el patrón de resultados esperado para que sepas si vas bien: el híbrido sube sobre todo **recall** (mete documentos que el vector solo no encontraba), el reranker sube sobre todo **MRR** (ordena mejor lo que ya estaba en el top-20). El reranker _no puede_ subir recall@20, pero sí recall@5.

</details>

## Bonus

1. **Sweep de chunking**: re-indexa con 2 tamaños de chunk adicionales (p. ej. 256 y 1024 tokens, con/sin overlap) y añade esas filas a la tabla. Ojo: necesitas re-mapear el golden set a los nuevos IDs; documenta cómo lo resolviste (mapear por offsets de carácter en el documento original es el camino limpio). Esto convierte el reto en una historia de "evalué el sistema completo, no solo el retriever".
2. **Curva costo-calidad**: mide recall@5 y latencia para top-k de reranking ∈ {5, 10, 20, 50} y grafica. Poder decir "rerankear 50 en vez de 20 me daba +0.01 de recall por 3x la latencia, así que elegí 20" es exactamente el tipo de trade-off que se discute en una entrevista de system design.

## Qué demuestra en entrevista

- _"No evalúo retrieval a ojo: construí un golden set de 25+ pares con tres tipos de query y medí recall@5 y MRR@10 por tipo. El desglose me mostró que las queries con términos exactos fallaban en vectorial puro; el promedio global me lo habría ocultado."_
- _"Implementé híbrido BM25+vectores fusionando con RRF: lo escribí a mano, es una suma de recíprocos de ranks con k=60, y la ventaja sobre fusionar scores es que no requiere normalizar escalas incomparables. El híbrido me subió recall; el cross-encoder encima me subió MRR, que es el reparto esperado porque el reranker solo reordena candidatos."_
- _"Sé lo que costó: el reranker añadió ~N ms p50 por query. Tengo la tabla calidad-latencia y puedo justificar el punto de operación que elegí."_

## Entregable

**En el repo** (carpeta `reto-04/` de tu repo del programa, o repo aparte enlazado):

```
reto-04/
├── README.md            # tabla comparativa (generada por eval.py), análisis Parte D
├── golden_set.jsonl
├── eval.py
├── retrievers.py        # baseline, bm25, hybrid (RRF propio), rerank
├── tests/test_rrf.py    # caso a mano de RRF
├── requirements.txt     # versiones pinneadas
└── data/                # corpus o script para descargarlo (no subas binarios pesados)
```

**En la sesión de revisión** (15 min):

1. Demo en vivo: `python eval.py --config hybrid_rerank` corriendo de cero (5 min).
2. La tabla comparativa y el desglose por `query_type`: cuenta la historia de qué mejoró y por qué (5 min).
3. Los 2 casos fallo→acierto, mostrando los rankings reales del baseline vs. el sistema mejorado para esas queries (5 min).

El coach va a auditar 5 pares del golden set al azar y a preguntarte la fórmula de RRF en pizarra. Ven preparado para ambas.
