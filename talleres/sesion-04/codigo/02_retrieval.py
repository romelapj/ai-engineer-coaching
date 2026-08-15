"""
Explicación 3: Top-k retrieval y umbrales de similitud

Del deck: recuperar es hacerle una pregunta al vector store y quedarte con
los k chunks más parecidos (top-k, típicamente 3-5)... pero "los más
parecidos" no significa "parecidos de verdad". Por eso se aplica un UMBRAL:
si la similitud del mejor chunk no supera cierto valor, es mejor no
responder que responder con contexto irrelevante.

Este archivo NO llama a la API de Anthropic: solo consulta la base Chroma
que creó 01_ingesta.py y te muestra los números crudos (similitudes) para
que veas al umbral trabajando. Corre primero 01_ingesta.py.

Cómo correrlo:
    python ejemplos/02_retrieval.py
"""

from pathlib import Path

import chromadb

# El umbral de similitud: por debajo de este valor, un chunk se descarta.
# OJO: el valor correcto depende del modelo de embeddings. El deck usa 0.7
# pensando en modelos comerciales (voyage, openai); con el modelo local
# de Chroma (MiniLM) las similitudes salen más bajas. Midiendo con estos
# docs: las preguntas legítimas puntúan 0.42-0.66 y la pregunta fuera de
# tema llega máximo a 0.36, así que 0.40 separa limpio. La lección: el
# umbral SIEMPRE se calibra mirando los números de tu propio modelo,
# no se copia de un tutorial.
UMBRAL = 0.40


def recuperar(pregunta, collection, n_results=4):
    # Hace la búsqueda semántica y aplica el umbral. Devuelve los "hits":
    # los chunks que sí son suficientemente parecidos a la pregunta.
    results = collection.query(
        query_texts=[pregunta],   # Chroma convierte la pregunta en embedding automáticamente...
        n_results=n_results,      # ...y trae los k vecinos más cercanos (top-k). Aquí k=4.
    )
    # Chroma devuelve listas paralelas (documento i ↔ metadata i ↔ distancia i).
    # zip() las recorre juntas para armar un diccionario por resultado.
    hits = [
        {**meta, "texto": doc, "similitud": 1 - dist}
        # {**meta, ...} copia la metadata (fuente, seccion) y le agrega
        # el texto y la similitud. Como la colección usa distancia coseno,
        # similitud = 1 - distancia (1.0 = idéntico, 0.0 = nada que ver).
        for doc, meta, dist in zip(
            results["documents"][0],   # El [0] es porque preguntamos con UNA sola query.
            results["metadatas"][0],
            results["distances"][0],
        )
        if 1 - dist >= UMBRAL
        # El filtro del umbral: solo pasan los chunks con similitud >= UMBRAL.
    ]
    return hits, results  # Devolvemos también los crudos para poder imprimirlos.


def demo(pregunta, collection):
    # Imprime el top-k completo (con y sin filtro) para UNA pregunta.
    print(f"\nPregunta: \"{pregunta}\"")
    hits, results = recuperar(pregunta, collection)
    for doc, meta, dist in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        sim = 1 - dist
        marca = "PASA  " if sim >= UMBRAL else "FUERA "  # ¿Superó el umbral?
        print(f"  {marca} sim={sim:.3f}  {meta['fuente']} § {meta['seccion']}")
    print(f"  → {len(hits)} chunk(s) superan el umbral de {UMBRAL}")
    if not hits:
        print("  → Sin evidencia: el pipeline debería negarse a responder.")


def main():
    # Abrimos la base que 01_ingesta.py dejó en disco (no re-ingestamos).
    ruta_db = Path(__file__).parent / "rag_db"
    chroma = chromadb.PersistentClient(str(ruta_db))
    collection = chroma.get_or_create_collection("docs", metadata={"hnsw:space": "cosine"})

    if collection.count() == 0:
        # Guardia amable: si la base está vacía es que faltó el paso anterior.
        print("La base está vacía. Corre primero: python ejemplos/01_ingesta.py")
        return

    # Caso 1: pregunta que SÍ está en los documentos → varios chunks pasan.
    demo("¿Cuál es el timeout default de la API?", collection)

    # Caso 2: pregunta relacionada pero de otro documento → pasa el chunk correcto.
    demo("¿Cómo verifico la firma de un webhook?", collection)

    # Caso 3: pregunta que NO tiene nada que ver con los docs → nadie pasa
    # el umbral. Esto es lo que evita que el modelo alucine una respuesta.
    demo("¿Cuál es la capital de Francia?", collection)


if __name__ == "__main__":
    main()
