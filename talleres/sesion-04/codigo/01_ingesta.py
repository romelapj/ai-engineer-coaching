"""
Explicación 2: Ingesta. Chunks → embeddings → vector store (Chroma)

Del deck: el pipeline RAG en una línea es
    Ingesta → Chunking → Embeddings → Vector Store → Retrieval → Generación

Este archivo hace la mitad izquierda: toma los chunks de 00_chunking.py,
los convierte en embeddings (vectores de números que capturan el
SIGNIFICADO del texto) y los guarda en Chroma, una base de datos vectorial
que corre embebida en tu máquina, ideal para prototipar, como dice el deck
(pgvector y Qdrant son las opciones para producción).

No llama a la API de Anthropic. Chroma usa un modelo de embeddings local
(all-MiniLM-L6-v2) que se descarga la primera vez (~80 MB), así que la
primera ejecución tarda un poco más.

Cómo correrlo:
    python ejemplos/01_ingesta.py
"""

from pathlib import Path

import chromadb  # La librería del vector store. Se instala con: pip install chromadb

# Reutilizamos el chunking del ejemplo anterior en lugar de copiarlo.
# (Python puede importar funciones de otro archivo .py de la misma carpeta,
# pero como el nombre "00_chunking" empieza con número, el "import" normal
# no lo acepta y usamos importlib, que recibe el nombre como texto.)
import importlib

chunk_markdown = importlib.import_module("00_chunking").chunk_markdown


def ingestar():
    # --- 1. Chunking (lo que ya vimos en 00_chunking.py) -------------------
    # operator overloading
    carpeta_docs = Path(__file__).parent / "docs"
    chunks = []
    for archivo in sorted(carpeta_docs.glob("*.md")):
        texto = archivo.read_text(encoding="utf-8")
        chunks.extend(chunk_markdown(texto, archivo.name))
    print(f"1) Chunking: {len(chunks)} chunks generados")

    # --- 2. Abrir (o crear) la base vectorial ------------------------------
    # PersistentClient guarda todo en la carpeta ./rag_db, así que la
    # ingesta sobrevive entre ejecuciones: los siguientes scripts (02 y 03)
    # solo abren esta carpeta, no vuelven a ingestar.
    ruta_db = Path(__file__).parent / "rag_db"
    chroma = chromadb.PersistentClient(str(ruta_db))

    # IMPORTANTE: la ingesta debe ser IDEMPOTENTE (correrla dos veces deja
    # el mismo resultado). collection.add NO sobreescribe ids que ya
    # existen: los salta en silencio. Si cambias el chunking y re-corres
    # sin borrar, la base queda con una MEZCLA de chunks viejos y nuevos
    # (duplicados + fragmentos huérfanos). Por eso: borrar y re-crear.
    try:
        chroma.delete_collection("docs")
    except Exception:
        pass  # La primera vez la colección no existe todavía: no pasa nada.

    # Una "collection" es como una tabla: agrupa documentos del mismo tipo.
    collection = chroma.get_or_create_collection(
        "docs",
        # IMPORTANTE: le decimos a Chroma que mida distancias con COSENO.
        # Con coseno, distancia = 1 - similitud, así que en los siguientes
        # scripts podremos calcular "similitud = 1 - distancia" (como en el
        # deck). El default de Chroma es otra métrica (L2) y esa cuenta
        # no funcionaría.
        metadata={"hnsw:space": "cosine"},
    )

    # --- 3. Embeddings + guardado ------------------------------------------
    # collection.add hace las DOS cosas de una vez: calcula el embedding de
    # cada texto (con el modelo local de Chroma) y lo guarda junto con su
    # metadata. En producción usarías un modelo de embeddings de pago
    # (voyage-3.5-lite, text-embedding-3-small...) por mejor calidad.
    collection.add(
        ids=[
            f"chunk-{i}" for i in range(len(chunks))
        ],  # Cada chunk necesita un id único.
        documents=[c["texto"] for c in chunks],  # El texto que se convierte en vector.
        metadatas=[  # Lo que NO se vectoriza pero sí se guarda:
            {
                "fuente": c["fuente"],
                "seccion": c["seccion"],
            }  # fuente y sección, para citar después.
            for c in chunks
        ],
    )
    print(
        f"2) Embeddings + guardado: {collection.count()} chunks en la colección 'docs'"
    )
    print(f"3) Base persistida en: {ruta_db}")
    return collection


if __name__ == "__main__":
    ingestar()
