"""
retrieval.py: las estrategias de búsqueda, todas con la MISMA firma

Cubre las slides "Búsqueda híbrida: BM25 + vectores con RRF" y "Rerankers".

Cada estrategia es una función que recibe una query y devuelve una lista de
ids ordenada. Esa firma común no es cosmética: es lo que permite meterlas
todas por el mismo `metricas.evaluar()` y comparar peras con peras.

El orden del archivo es el orden de la sesión:

    vectorial  → lo que ya teníamos (sesión 04)
    BM25       → lo exacto, que es justo donde el vector falla
    RRF        → cómo fusionar las dos listas sin calibrar nada
    reranking  → reordenar los pocos candidatos que ya recuperaste

Este archivo no se ejecuta directamente: los scripts numerados lo importan.
"""

import re

import anthropic
from rank_bm25 import BM25Okapi  # BM25 puro-Python: pip install rank_bm25

import base

client = anthropic.Anthropic()
MODELO = "claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# 1. Vectorial: el buscador de la sesión 04
# ---------------------------------------------------------------------------
def buscar_vectores(collection, query, k=10):
    # Pedimos solo los ids: para MEDIR retrieval lo único que importa es qué
    # chunk salió y en qué posición. (El RAG completo sí necesita el texto;
    # eso vive en rag.py.)
    return collection.query(query_texts=[query], n_results=k)["ids"][0]


# ---------------------------------------------------------------------------
# 2. BM25: coincidencia léxica, exacta donde el embedding es difuso
# ---------------------------------------------------------------------------
def construir_bm25(chunks):
    # El índice BM25 se construye UNA vez sobre todo el corpus. Cada chunk se
    # tokeniza con base.tokenizar (minúsculas + limpieza de signos): sin eso,
    # "E-4012?" nunca igualaría al "E-4012" del documento.
    return BM25Okapi([base.tokenizar(c["texto"]) for c in chunks])


def buscar_bm25(bm25, ids, query, k=10):
    # get_scores devuelve un score por chunk (en el orden del corpus);
    # argsort()[::-1] los ordena de mayor a menor y tomamos el top-k.
    scores = bm25.get_scores(base.tokenizar(query))
    return [ids[i] for i in scores.argsort()[::-1][:k]]


# ---------------------------------------------------------------------------
# 3. RRF: fusionar dos rankings usando solo POSICIONES
# ---------------------------------------------------------------------------
def rrf(rankings, k=60):
    # Reciprocal Rank Fusion, tal cual el deck:
    #     score(doc) = Σ 1 / (k + rank)
    # La gracia: un coseno de 0.62 y un BM25 de 14.2 no son comparables,
    # están en escalas distintas y calibrarlas es un problema en sí mismo.
    # Pero "quedó de tercero" significa lo mismo en los dos mundos. RRF
    # ignora los scores y suma puntos por posición, así que fusiona sin
    # calibrar nada. k=60 es el valor del paper original: amortigua cuánto
    # pesa la diferencia entre estar de 1° y estar de 5°.
    scores = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
    return sorted(scores, key=scores.get, reverse=True)


def buscar_hibrido(collection, bm25, ids, query, k=10):
    # Los dos buscadores corren por separado sobre TODO el corpus y RRF los
    # mezcla. Tres líneas, cero modelos nuevos, cero llamadas a la API.
    ranking_vec = buscar_vectores(collection, query, k=k)
    ranking_bm25 = buscar_bm25(bm25, ids, query, k=k)
    return rrf([ranking_vec, ranking_bm25])[:k]


# ---------------------------------------------------------------------------
# 4. Reranking: reordenar los pocos candidatos ya recuperados
# ---------------------------------------------------------------------------
def rerank(query, candidatos_ids, id_a_chunk, top=10):
    # El deck usa un cross-encoder (Cohere Rerank, bge-reranker-v2...): un
    # modelo que lee query y documento JUNTOS, en vez de comparar dos
    # vectores calculados por separado. Aquí ese rol lo hace Claude para no
    # descargar un modelo de ~2 GB; lo que importa (y lo que se enseña) es
    # su LUGAR en el pipeline: recibe pocos candidatos ya recuperados y los
    # reordena por relevancia real. Nunca busca sobre el corpus completo,
    # porque es demasiado caro para eso.
    lista = "\n\n".join(
        f"[{i + 1}] {id_a_chunk[cid]['texto']}"
        for i, cid in enumerate(candidatos_ids)
    )
    resp = client.messages.create(
        model=MODELO,
        max_tokens=100,
        system=(
            "Eres un reranker. Recibes una query y documentos numerados. "
            "Devuelve SOLO los números de los documentos ordenados del más "
            "al menos relevante para responder la query, separados por "
            "comas. Ejemplo: 3,1,7,2"
        ),
        messages=[{
            "role": "user",
            "content": f"Query: {query}\n\nDocumentos:\n{lista}",
        }],
    )
    # Parseamos "3,1,7,2" → índices → ids. Si el modelo omite alguno, lo
    # agregamos al final en su orden original: reordenar nunca debe PERDER
    # candidatos, solo cambiarlos de lugar.
    orden = [int(n) - 1 for n in re.findall(r"\d+", resp.content[0].text)]
    reordenados = [candidatos_ids[i] for i in orden if 0 <= i < len(candidatos_ids)]
    faltantes = [cid for cid in candidatos_ids if cid not in reordenados]
    return (reordenados + faltantes)[:top]


# ---------------------------------------------------------------------------
# El retrieval que sale de esta sesión, ya listo para usar
# ---------------------------------------------------------------------------
def construir_buscadores(chunks, collection):
    # Devuelve las cuatro variantes que la sesión compara, ya cerradas sobre
    # el corpus. Todas tienen la firma query → [ids]: eso es lo que las hace
    # intercambiables y medibles con el mismo código.
    ids = [c["id"] for c in chunks]
    id_a_chunk = {c["id"]: c for c in chunks}
    bm25 = construir_bm25(chunks)
    return {
        "vectorial (sesión 04)": lambda q: buscar_vectores(collection, q),
        "solo BM25": lambda q: buscar_bm25(bm25, ids, q),
        "híbrido RRF": lambda q: buscar_hibrido(collection, bm25, ids, q),
        "híbrido + rerank": lambda q: rerank(
            q, buscar_hibrido(collection, bm25, ids, q), id_a_chunk
        ),
    }
