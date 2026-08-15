"""
Explicación 5: RAG v0.4, el pipeline mejorado con las ideas del paper CLaRa

Basado en: "CLaRa: Bridging Retrieval and Generation with Continuous Latent
Reasoning" (Apple + U. Edinburgh, arXiv:2511.18659). El diagnóstico central
del paper aplica a NUESTRO pipeline v0.3 (03_rag_completo.py):

    "El retrieval y la generación se optimizan por separado: el retriever
     elige documentos por similitud SUPERFICIAL, mientras que el generador
     necesita documentos útiles para RAZONAR la respuesta."

CLaRa lo resuelve ENTRENANDO todo junto (LoRAs + un top-k diferenciable).
Eso no lo podemos hacer llamando a una API, pero tres de sus ideas sí se
pueden imitar a nivel de prompt, y eso es esta v0.4:

  1. QUERY REASONER (sección 3 del paper): su retriever aprende a "anticipar"
     el contenido del documento relevante (a la pregunta sobre Olimpiadas le
     agrega internamente "Athens 1896"). Nuestra imitación: un paso previo
     donde el modelo EXPANDE la pregunta con las palabras que espera
     encontrar en la respuesta, y buscamos con esa versión expandida.

  2. RERANKING ALINEADO CON GENERACIÓN (secciones 3 y 4.4): similitud alta
     no garantiza utilidad. Nuestra imitación: recuperamos MÁS candidatos
     (k=6 en vez de 4) y un paso intermedio del modelo decide cuáles
     realmente sirven para responder, descartando los que solo "se parecen".

  3. COMPRESIÓN DE CONTEXTO (sección 2, framework SCP): comprimen documentos
     16x conservando solo la información saliente, sin perder calidad de
     respuesta. Nuestra imitación: ese mismo paso intermedio extrae de cada
     chunk útil SOLO las frases que responden la pregunta, así el contexto
     final que ve el generador es mucho más corto y limpio.

El pipeline v0.3 era:   pregunta → retrieval → generación
El pipeline v0.4 es:    pregunta → EXPANSIÓN → retrieval amplio
                                 → RERANK + COMPRESIÓN → generación

Cuesta 2 llamadas extra al modelo por pregunta; a cambio, el retrieval
encuentra respuestas aunque la pregunta no comparta palabras con el
documento, y el generador recibe menos ruido.

Necesita ANTHROPIC_API_KEY en tu shell y que 01_ingesta.py ya haya corrido.

Cómo correrlo:
    python ejemplos/04_rag_v04.py
"""

import re

from pathlib import Path

import anthropic
import chromadb

# --- Configuración (igual que en 02 y 03) -----------------------------------
ruta_db = Path(__file__).parent / "rag_db"
chroma = chromadb.PersistentClient(str(ruta_db))
collection = chroma.get_or_create_collection("docs", metadata={"hnsw:space": "cosine"})
client = anthropic.Anthropic()
MODELO = "claude-sonnet-4-6"  # El modelo del deck, para las 3 etapas.
UMBRAL = 0.40  # Calibrado para MiniLM local (ver 02_retrieval.py).


# ---------------------------------------------------------------------------
# PASO 1: Expansión de consulta (la idea del "query reasoner" de CLaRa)
# ---------------------------------------------------------------------------
def expandir_consulta(pregunta):
    # El problema que ataca: la pregunta del usuario y el documento que la
    # responde muchas veces NO comparten palabras. "¿Cuánto tengo antes de
    # perder eventos?" no contiene "reintentos" ni "entrega", que es donde
    # está la respuesta. CLaRa entrena su retriever para anticipar esas
    # palabras; nosotros se las pedimos al modelo explícitamente.
    resp = client.messages.create(
        model=MODELO,
        max_tokens=100,  # Solo queremos una línea de keywords: tope corto.
        system=(
            "Eres el paso de expansión de consulta de un buscador. "
            "Dada una pregunta, responde SOLO con 5-8 palabras clave que "
            "probablemente aparezcan en el documento que la responde. "
            "Sin explicaciones, solo las palabras separadas por espacios."
        ),
        messages=[{"role": "user", "content": pregunta}],
    )
    keywords = resp.content[0].text.strip()
    # Buscamos con pregunta + keywords JUNTAS: la pregunta aporta la
    # intención y las keywords acercan el embedding al vocabulario del
    # documento relevante.
    return f"{pregunta} {keywords}", keywords


# ---------------------------------------------------------------------------
# PASO 2: Retrieval amplio (más candidatos, el rerank filtra después)
# ---------------------------------------------------------------------------
def recuperar(consulta, k=6):
    # k=6 en vez de 4: como ahora hay un paso que filtra con criterio
    # (el rerank), podemos permitirnos traer más candidatos y dejar que
    # sea ese paso, no la similitud a secas, quien decida qué entra.
    results = collection.query(query_texts=[consulta], n_results=k)
    return [
        {**meta, "texto": doc, "similitud": round(1 - dist, 3)}
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
        if 1 - dist >= UMBRAL  # El umbral sigue siendo la primera defensa:
        # si NADA se parece ni un poco, ni gastamos las llamadas siguientes.
    ]


# ---------------------------------------------------------------------------
# PASO 3: Rerank + compresión en una sola llamada (ideas 2 y 3 de CLaRa)
# ---------------------------------------------------------------------------
def rerank_y_comprimir(pregunta, candidatos):
    # Le mostramos al modelo TODOS los candidatos numerados y le pedimos dos
    # cosas a la vez: (a) decidir cuáles sirven de verdad para responder
    # (rerank: utilidad, no similitud) y (b) copiar de cada uno SOLO las
    # frases que responden (compresión: menos contexto = menos ruido).
    lista = "\n\n".join(
        f"[{i + 1}] ({c['fuente']} § {c['seccion']})\n{c['texto']}"
        for i, c in enumerate(candidatos)
    )
    resp = client.messages.create(
        model=MODELO,
        max_tokens=500,
        system=(
            "Eres el paso de selección de evidencia de un sistema RAG. "
            "Recibes una pregunta y chunks numerados. Para CADA chunk que "
            "contenga información que responda la pregunta, escribe una "
            "línea con el formato:\n"
            "[n] <las frases exactas del chunk que responden, resumidas>\n"
            "Ignora los chunks que solo se parecen a la pregunta pero no "
            "la responden. Si NINGÚN chunk responde, escribe exactamente: "
            "NINGUNO"
        ),
        messages=[{
            "role": "user",
            "content": f"Pregunta: {pregunta}\n\nChunks:\n{lista}",
        }],
    )
    texto = resp.content[0].text.strip()
    if texto == "NINGUNO":
        return []  # Segunda defensa: pasó el umbral pero no responde nada.

    seleccion = []
    for linea in texto.splitlines():
        m = re.match(r"\[(\d+)\]\s*(.+)", linea.strip())
        # Cada línea útil empieza con "[n]": la parseamos para saber QUÉ
        # chunk original respalda cada extracto (eso mantiene las citas
        # verificables: el extracto se puede comparar contra el chunk).
        if m:
            idx = int(m.group(1)) - 1  # De número humano [1] a índice 0.
            if 0 <= idx < len(candidatos):
                seleccion.append(
                    {
                        "fuente": candidatos[idx]["fuente"],
                        "seccion": candidatos[idx]["seccion"],
                        "extracto": m.group(2),  # La versión comprimida.
                    }
                )
    return seleccion


# ---------------------------------------------------------------------------
# PASO 4: Generación (igual que v0.3, pero sobre el contexto comprimido)
# ---------------------------------------------------------------------------
SYSTEM_GENERACION = (
    "Responde SOLO con el contexto provisto. "
    "Cita cada afirmación con su marcador [n]. "
    "Si el contexto no alcanza, responde exactamente: "
    "'No tengo evidencia para responder.'"
)


def generar(pregunta, seleccion):
    contexto = "\n\n".join(
        f"[{i + 1}] ({s['fuente']} § {s['seccion']})\n{s['extracto']}"
        for i, s in enumerate(seleccion)
    )
    resp = client.messages.create(
        model=MODELO,
        max_tokens=1024,
        system=SYSTEM_GENERACION,
        messages=[{
            "role": "user",
            "content": f"Contexto:\n{contexto}\n\nPregunta: {pregunta}",
        }],
    )
    return resp.content[0].text


# ---------------------------------------------------------------------------
# El pipeline v0.4 completo, imprimiendo cada etapa para poder estudiarla
# ---------------------------------------------------------------------------
def responder_v04(pregunta):
    print(f"\n{'=' * 70}\nPregunta: {pregunta}\n{'-' * 70}")

    consulta, keywords = expandir_consulta(pregunta)
    print(f"1) Expansión     → + \"{keywords}\"")

    candidatos = recuperar(consulta)
    print(f"2) Retrieval     → {len(candidatos)} candidato(s) sobre el umbral:")
    for c in candidatos:
        print(f"      sim={c['similitud']:.3f}  {c['fuente']} § {c['seccion']}")
    if not candidatos:
        print("   → Nada se parece: respondemos sin llamar más al modelo.")
        print("\nRespuesta: No tengo evidencia para responder.")
        return

    seleccion = rerank_y_comprimir(pregunta, candidatos)
    print(f"3) Rerank+compr. → {len(seleccion)} chunk(s) útiles de verdad:")
    for s in seleccion:
        print(f"      [{s['fuente']} § {s['seccion']}] \"{s['extracto'][:70]}...\"")
    if not seleccion:
        # Este caso es EXACTAMENTE el que motiva el paper: había chunks
        # "parecidos" (pasaron el umbral) pero ninguno era útil. La v0.3
        # se los habría pasado igual al generador.
        print("   → Se parecían pero no respondían: rechazo honesto.")
        print("\nRespuesta: No tengo evidencia para responder.")
        return

    print(f"\nRespuesta: {generar(pregunta, seleccion)}")


def main():
    preguntas = [
        # Caso 1: directa (la v0.3 también la resolvía); sanity check.
        "¿Cuál es el timeout default?",
        # Caso 2: la estrella de la v0.4. La pregunta NO comparte
        # vocabulario con el documento ("caído", "perder eventos" no
        # aparecen en webhooks.md; la respuesta vive en "Reintentos de
        # entrega"). La expansión tiende ese puente.
        "Si mi endpoint de webhooks está caído, ¿cuánto tiempo tengo "
        "para arreglarlo antes de perder eventos?",
        # Caso 3: fuera del corpus → debe negarse, igual que la v0.3.
        "¿Cuál es la capital de Francia?",
    ]
    for p in preguntas:
        responder_v04(p)


if __name__ == "__main__":
    main()
