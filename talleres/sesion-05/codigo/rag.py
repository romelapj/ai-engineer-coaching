"""
rag.py: EL RAG DE LA SESIÓN 04, sin cambios de fondo

Esta sesión NO construye otro RAG. Construye encima del que ya funciona.
Por eso el pipeline de la sesión 04 vive aquí, intacto y en un solo lugar:

    pregunta → recuperar top-k por similitud → filtrar por umbral
             → generar respuesta citando la evidencia

La pieza clave del archivo es que `responder()` recibe la función de
recuperación como PARÁMETRO. Esa firma es toda la tesis de la sesión 05:

    responder(pregunta, recuperar=recuperar_vectorial)   ← sesión 04
    responder(pregunta, recuperar=hibrido_con_rerank)    ← sesión 05

El generador, el umbral y las citas no se tocan en ninguna de las dos.
Lo único que cambia (y lo único que vamos a medir) es QUÉ evidencia llega.

Este archivo no se ejecuta directamente: los scripts numerados lo importan.
"""

import anthropic

client = anthropic.Anthropic()  # Lee ANTHROPIC_API_KEY del entorno.
MODELO = "claude-sonnet-4-6"  # El modelo del deck.

# El umbral calibrado en la sesión 04 para el modelo de embeddings local de
# Chroma (MiniLM). Su trabajo es evitar que un chunk que no se parece a NADA
# entre al contexto. Ojo con lo que NO puede hacer, que es el tema de hoy:
# el umbral filtra por similitud, así que cuando la similitud misma se
# equivoca, el umbral se equivoca con ella.
UMBRAL = 0.40

SYSTEM_GENERACION = (
    "Responde SOLO con el contexto provisto. "
    "Cita cada afirmación con su marcador [n]. "
    "Si el contexto no alcanza, responde exactamente: "
    "'No tengo evidencia para responder.'"
)


def recuperar_vectorial(collection, pregunta, k=4, umbral=UMBRAL):
    # La recuperación de la sesión 04: similitud de coseno, top-k, umbral.
    # Devolvemos también la similitud de cada chunk porque en el script 00
    # queremos VER dónde cortó el umbral y qué dejó pasar.
    res = collection.query(query_texts=[pregunta], n_results=k)
    evidencias = []
    for cid, doc, meta, dist in zip(
        res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        similitud = 1 - dist  # Con hnsw:space=cosine, similitud = 1 - distancia.
        evidencias.append(
            {
                "id": cid,
                "texto": doc,
                "fuente": meta["fuente"],
                "seccion": meta["seccion"],
                "similitud": round(similitud, 3),
                "pasa_umbral": similitud >= umbral,
            }
        )
    return evidencias


def generar(pregunta, evidencias):
    # El generador de la sesión 04, sin cambios: recibe evidencia numerada y
    # solo puede responder con ella. Las citas [n] hacen la respuesta
    # verificable; el "No tengo evidencia" evita que invente.
    if not evidencias:
        return "No tengo evidencia para responder."
    contexto = "\n\n".join(
        f"[{i + 1}] ({e['fuente']} § {e['seccion']})\n{e['texto']}"
        for i, e in enumerate(evidencias)
    )
    resp = client.messages.create(
        model=MODELO,
        max_tokens=500,
        system=SYSTEM_GENERACION,
        messages=[{
            "role": "user",
            "content": f"Contexto:\n{contexto}\n\nPregunta: {pregunta}",
        }],
    )
    return resp.content[0].text


def responder(pregunta, recuperar):
    # El pipeline completo. `recuperar` es una función pregunta → evidencias:
    # cambiarla es cambiar TODO el retrieval sin tocar una línea del
    # generador. En el script 05 le enchufamos el retrieval mejorado y el
    # RAG entero mejora solo.
    evidencias = [e for e in recuperar(pregunta) if e.get("pasa_umbral", True)]
    return {"evidencias": evidencias, "respuesta": generar(pregunta, evidencias)}
