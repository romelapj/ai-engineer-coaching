"""
Explicación 4: El pipeline RAG completo. Generación con citas obligatorias

Del deck: la última pieza es la generación. Le pasamos al modelo SOLO los
chunks que superaron el umbral, numerados [1], [2]..., y le exigimos dos
cosas en el system prompt:
  1. Responder ÚNICAMENTE con ese contexto (no con su memoria).
  2. Citar cada afirmación con su marcador [n], así toda respuesta es
     verificable: puedes ir al chunk [n] y comprobar que lo dice.
Y si ningún chunk supera el umbral, ni siquiera llamamos al modelo:
respondemos "No tengo evidencia para responder." Eso es grounding.

Este archivo SÍ llama a la API de Anthropic (necesitas ANTHROPIC_API_KEY
en tu shell) y necesita que 01_ingesta.py ya haya corrido.

Cómo correrlo:
    python ejemplos/03_rag_completo.py
"""

from pathlib import Path

import anthropic  # El SDK oficial de Anthropic: pip install anthropic
import chromadb

# --- Configuración (igual que en los scripts anteriores) --------------------
ruta_db = Path(__file__).parent / "rag_db"
chroma = chromadb.PersistentClient(str(ruta_db))
collection = chroma.get_or_create_collection("docs", metadata={"hnsw:space": "cosine"})
client = anthropic.Anthropic()
# Anthropic() sin argumentos lee la variable de entorno ANTHROPIC_API_KEY.
UMBRAL = 0.40  # Calibrado para el modelo de embeddings local (ver 02_retrieval.py).

# El system prompt define las reglas del juego ANTES de ver la pregunta.
# Es la parte que convierte "un chat" en "un sistema con grounding".
SYSTEM = (
    "Responde SOLO con el contexto provisto. "          # Regla 1: prohibido usar la memoria del modelo.
    "Cita cada afirmación con su marcador [n]. "        # Regla 2: toda afirmación debe ser rastreable.
    "Si el contexto no alcanza, responde exactamente: "  # Regla 3: escape honesto en vez de inventar.
    "'No tengo evidencia para responder.'"
)


def responder(pregunta):
    # ---- RETRIEVAL (lo que vimos en 02_retrieval.py) -----------------------
    results = collection.query(
        query_texts=[pregunta],  # La pregunta se embebe y se busca por similitud semántica.
        n_results=4,             # top-k = 4: los 4 chunks más parecidos.
    )
    hits = [
        {**meta, "texto": doc}   # Copiamos la metadata y agregamos el texto del chunk.
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
        if 1 - dist >= UMBRAL    # Umbral: fuera los chunks poco parecidos.
    ]
    if not hits:
        # Si NADA supera el umbral, ni gastamos tokens: la respuesta honesta
        # sale gratis y sin riesgo de alucinación.
        return "No tengo evidencia para responder."

    # ---- ARMAR EL CONTEXTO -------------------------------------------------
    # Numeramos cada chunk como [1], [2]... y anotamos su origen
    # (archivo § sección): esos son los marcadores que el modelo va a citar.
    contexto = "\n\n".join(
        f"[{i + 1}] ({c['fuente']} § {c['seccion']})\n{c['texto']}"
        for i, c in enumerate(hits)
    )

    # ---- GENERACIÓN --------------------------------------------------------
    resp = client.messages.create(
        model="claude-sonnet-4-6",  # El modelo del deck.
        max_tokens=1024,            # Tope de largo de la respuesta.
        system=SYSTEM,              # Las 3 reglas de grounding de arriba.
        messages=[{
            "role": "user",
            # Un solo mensaje con las dos partes: primero el contexto
            # recuperado, después la pregunta real del usuario.
            "content": f"Contexto:\n{contexto}\n\nPregunta: {pregunta}",
        }],
    )
    # La respuesta llega como lista de bloques; el texto está en el primero.
    return resp.content[0].text


def main():
    preguntas = [
        # Caso 1: la respuesta está en api-pagos.md → responde con citas [n].
        "¿Cuál es el timeout default?",
        # Caso 2: la respuesta cruza información de webhooks.md.
        "¿Cuántas veces se reintenta un webhook si mi servidor no responde?",
        # Caso 3: nada en los docs habla de esto → "No tengo evidencia...".
        "¿Cuál es la capital de Francia?",
    ]
    for p in preguntas:
        print(f"\n{'=' * 60}\nPregunta: {p}\n{'-' * 60}")
        print(responder(p))


if __name__ == "__main__":
    main()
