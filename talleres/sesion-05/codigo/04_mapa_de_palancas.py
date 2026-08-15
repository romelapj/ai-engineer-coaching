"""
Paso 6. Mapa de palancas: no es una lista de pasos, es un menú por síntoma

Cubre las slides "Query rewriting y expansión", "Metadata filtering",
"Contextual retrieval (Anthropic)" y "Parent-document retrieval".

Estas cuatro técnicas NO son "los siguientes pasos" después del reranking.
Son respuestas a síntomas específicos, y si tu golden set no muestra ese
síntoma, aplicarlas es complejidad sin retorno. El método de la sesión no
cambia: identificas el síntoma, activas la palanca, corres el golden set y
el número decide.

    Si el síntoma es...                          | Entonces prueba...
    ---------------------------------------------|-----------------------
    el usuario pregunta con siglas ambiguas o    | query rewriting
    con palabras que no están en tus documentos  |
    hay documentos que NUNCA deberían competir   | metadata filtering
    (año viejo, otro tenant, sin permiso)        |
    el chunk aislado no se entiende sin su       | contextual retrieval
    documento ("la tasa subió 3%": ¿de qué?)    |
    encuentras bien con chunks chicos, pero el   | parent-document
    modelo necesita más contexto para responder  | retrieval

Cada demo de abajo es deliberadamente corta: muestra el síntoma y la
mecánica, no una evaluación completa. Esa la haces tú, en tu corpus, con
tu golden set.

Llama a la API de Anthropic (rewriting, self-query y contextual opcional).

Cómo correrlo:
    python ejemplos/04_mapa_de_palancas.py
    python ejemplos/04_mapa_de_palancas.py --contextual   # + 23 llamadas
"""

import json
import sys

import anthropic

import base
import metricas
import retrieval

client = anthropic.Anthropic()
MODELO = "claude-sonnet-4-6"


def titulo(letra, texto):
    print("\n" + "=" * 72)
    print(f"{letra}) {texto}")
    print("=" * 72)


# ---------------------------------------------------------------------------
# A. Query rewriting: la query del usuario no es la query óptima del índice
# ---------------------------------------------------------------------------
def rewrite(query):
    # Un paso barato ANTES de buscar: expande siglas y agrega sinónimos.
    # Importante: la query reescrita se usa solo para BUSCAR. La original se
    # conserva para el generador, porque el usuario preguntó lo que preguntó.
    resp = client.messages.create(
        model=MODELO,
        max_tokens=200,
        system=(
            "Reescribe la query para un motor de búsqueda. "
            "Expande siglas y agrega sinónimos clave. "
            "Devuelve SOLO la query reescrita."
        ),
        messages=[{"role": "user", "content": query}],
    )
    return resp.content[0].text.strip()


def demo_rewriting(collection, chunks, golden):
    titulo("A", "QUERY REWRITING · síntoma: la pregunta no habla como el doc")
    query = "¿cómo firmo mis webhooks?"
    reescrita = rewrite(query)
    print(f"\n  original : {query}")
    print(f"  reescrita: {reescrita}")

    buscadores = retrieval.construir_buscadores(chunks, collection)
    hibrido = buscadores["híbrido RRF"]
    esperado = golden[query]
    for etiqueta, q in [("con la original", query), ("con la reescrita", reescrita)]:
        ranking = hibrido(q)
        pos = ranking.index(esperado) + 1 if esperado in ranking else None
        print(f"  {etiqueta:<18} → chunk correcto en pos {pos or 'fuera del top-10'}")
    print(
        "\n  Cuándo NO usarlo: cuesta una llamada (~300-500 ms) en CADA query y\n"
        "  su salida no es determinista, así que la misma query puede medir\n"
        "  distinto entre corridas. Mídelo varias veces antes de decidir."
    )


# ---------------------------------------------------------------------------
# B. Metadata filtering: sacar del juego lo que nunca debió competir
# ---------------------------------------------------------------------------
def demo_metadata(collection):
    titulo("B", "METADATA FILTERING · síntoma: compiten docs que no aplican")

    # El corpus tiene dos changelogs que responden DISTINTO a la misma
    # pregunta: en 2025 el TLS mínimo era 1.2; en 2026 es 1.3. Ningún
    # reranker arregla esto, porque los dos chunks son igual de relevantes
    # al TEMA. El problema no es de ranking: es que uno no debería estar.
    query = "¿Qué versión mínima de TLS exige la API?"
    print(f"\n  Query: {query}\n")

    sin_filtro = collection.query(query_texts=[query], n_results=3)["ids"][0]
    print("  Sin filtro (top-3):")
    for cid in sin_filtro:
        print(f"    - {cid}")

    # where= aplica el filtro DENTRO del índice: la búsqueda vectorial solo
    # considera chunks con anio=2026. Eso es pre-filter. El post-filter
    # (buscar top-3 y DESPUÉS descartar los de 2025) puede dejarte con cero
    # resultados válidos aunque existan en el corpus.
    con_filtro = collection.query(
        query_texts=[query], n_results=3, where={"anio": 2026}
    )["ids"][0]
    print("\n  Con where={'anio': 2026} (pre-filter, top-3):")
    for cid in con_filtro:
        print(f"    - {cid}")
    print(
        "\n  El mismo mecanismo ES tu control de acceso: con\n"
        "  where={'tenant': 'acme'} el RAG no puede recuperar lo prohibido,\n"
        "  ni siquiera por accidente. Eso no se delega a un prompt."
    )


def self_query(query):
    # Self-query: el modelo convierte la parte ESTRUCTURADA de la query en
    # filtros y deja la parte semántica para el vector search. Es el mismo
    # patrón de tool use de la sesión 02: extraer argumentos tipados de
    # texto libre, y es la puerta de entrada a la sesión 06.
    resp = client.messages.create(
        model=MODELO,
        max_tokens=150,
        system=(
            "Extrae filtros de la query del usuario para una base de "
            "documentos con metadata: anio (int) y tipo (uno de: "
            "'referencia', 'guia', 'changelog'). Responde SOLO un JSON "
            'con dos claves: "filtros" (objeto, puede ser vacío) y '
            '"query_semantica" (la query sin la parte ya filtrada). '
            'Ejemplo: {"filtros": {"anio": 2025}, "query_semantica": '
            '"cambios de seguridad"}'
        ),
        messages=[{"role": "user", "content": query}],
    )
    texto = resp.content[0].text.strip()
    # Los modelos a veces envuelven el JSON en ```json ... ``` aunque pidas
    # "SOLO un JSON" (lección de la sesión 03: nunca confíes en el formato).
    if texto.startswith("```"):
        texto = texto.split("```")[1].removeprefix("json").strip()
    return json.loads(texto)


def demo_self_query(collection):
    query = "¿Qué cambió en la plataforma durante 2025?"
    plan = self_query(query)
    print(f"\n  Self-query (el LLM deduce el filtro solo):")
    print(f"    query natural    : {query}")
    print(f"    filtros extraídos: {plan['filtros']}")
    print(f"    query semántica  : {plan['query_semantica']}")

    filtros = plan["filtros"]
    # Chroma exige envolver filtros múltiples en $and; con uno va directo.
    where = (
        {"$and": [{k: v} for k, v in filtros.items()]}
        if len(filtros) > 1 else (filtros or None)
    )
    ids = collection.query(
        query_texts=[plan["query_semantica"]], n_results=3, where=where
    )["ids"][0]
    print("    resultado (top-3):")
    for cid in ids:
        print(f"      - {cid}")


# ---------------------------------------------------------------------------
# C. Contextual retrieval: situar el chunk antes de indexarlo
# ---------------------------------------------------------------------------
def contextualizar(chunks):
    # 1 llamada por chunk. Es una mejora de INDEXACIÓN: se paga una vez, al
    # indexar, no en cada query. (En la sesión 09 verás prompt caching para
    # no repagar el documento completo en cada llamada.)
    documentos = {fuente: texto for texto, fuente in base.cargar_documentos()}
    textos = []
    for c in chunks:
        prompt = (
            f"<document>{documentos[c['fuente']]}</document>\n"
            "Sitúa este chunk dentro del documento:\n"
            f"<chunk>{c['texto']}</chunk>\n"
            "Responde SOLO con 2-3 frases de contexto que ayuden a "
            "recuperar este chunk en una búsqueda. Describe de qué trata "
            "y a qué documento pertenece; NO menciones otras secciones ni "
            "la posición del chunk."
            # Esa última instrucción salió de MEDIR, no de la teoría: con un
            # prompt genérico el modelo escribía "está justo antes del error
            # E-7777", y ese contexto metía códigos de OTROS chunks en el
            # embedding, empeorando recall@1. Iterar el prompt de
            # contextualización también es tuning de retrieval.
        )
        resp = client.messages.create(
            model=MODELO, max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        textos.append(resp.content[0].text.strip() + "\n\n" + c["texto"])
    return textos


def demo_contextual(chunks, golden, ejecutar):
    titulo("C", "CONTEXTUAL RETRIEVAL · síntoma: el chunk solo no se entiende")
    print(
        "\n  Un chunk suelto pierde su marco: 'la tasa subió 3%' no dice de qué\n"
        "  ni de cuándo. Antes de indexar, el modelo escribe 2-3 frases que lo\n"
        "  sitúan en su documento, y se embebe contexto + chunk."
    )
    if not ejecutar:
        print(
            "\n  (Demo omitida: son 23 llamadas al modelo. Córrelo con\n"
            "   --contextual para medirlo de verdad.)\n"
            "  El paper de Anthropic reporta −35% de fallos en el top-20, y\n"
            "  −67% combinándolo con BM25 y reranking."
        )
        return

    print(f"\n  Generando contexto para {len(chunks)} chunks...")
    textos = contextualizar(chunks)
    i = next(j for j, c in enumerate(chunks) if "E-5001" in c["id"])
    print(f"\n  Ejemplo · contexto generado para [{chunks[i]['id']}]:")
    print(f"    \"{textos[i].split(chr(10) + chr(10))[0][:200]}...\"")

    # Segunda colección con los MISMOS ids pero textos contextualizados: así
    # el golden set (que apunta a ids) sigue sirviendo para comparar.
    col_ctx = base.crear_coleccion("docs_ctx", chunks, textos=textos)
    col_normal = base.crear_coleccion("docs", chunks)
    print("\n" + metricas.encabezado())
    for nombre, col in [("chunks pelados", col_normal), ("chunks + contexto", col_ctx)]:
        res = metricas.evaluar(golden, lambda q, c=col: retrieval.buscar_vectores(c, q))
        print(metricas.fila(nombre, golden, res))


# ---------------------------------------------------------------------------
# D. Parent-document: buscar con el chico, entregar el grande
# ---------------------------------------------------------------------------
def demo_parent(collection):
    titulo("D", "PARENT-DOCUMENT · síntoma: encuentras bien, respondes corto")
    print(
        "\n  El conflicto: chunks chicos hacen matching fino, chunks grandes\n"
        "  dan mejor contexto al generador. El patrón resuelve las dos: busca\n"
        "  con el hijo, entrega el padre. El retrieval no cambia; cambia LO\n"
        "  QUE LE PASAS al modelo."
    )
    documentos = {fuente: texto for texto, fuente in base.cargar_documentos()}
    query = "¿Qué es el header X-Signature?"
    hijo_id = collection.query(query_texts=[query], n_results=1)["ids"][0][0]
    hijo = collection.get(ids=[hijo_id])["documents"][0]
    fuente = hijo_id.split(" § ")[0]  # Nuestro id ya codifica al padre.
    padre = documentos[fuente]

    print(f"\n  Query: {query}")
    print(f"  1) HIJO que hizo match : {hijo_id}")
    print(f"     {len(hijo)} caracteres, preciso para buscar")
    print(f"  2) PADRE que se entrega: {fuente} completo")
    print(f"     {len(padre)} caracteres, la sección correcta MÁS la")
    print("     configuración y los reintentos, que el modelo puede necesitar")
    print(
        "\n  Trade-off explícito: más tokens al generador = más costo y más\n"
        "  latencia en cada respuesta. Combina bien con contextual retrieval:\n"
        "  uno mejora ENCONTRAR, el otro mejora RESPONDER."
    )


def main():
    ejecutar_contextual = "--contextual" in sys.argv
    chunks = base.todos_los_chunks()
    collection = base.crear_coleccion("docs", chunks)
    golden = base.cargar_golden()

    demo_rewriting(collection, chunks, golden)
    demo_metadata(collection)
    demo_self_query(collection)
    demo_contextual(chunks, golden, ejecutar_contextual)
    # demo_contextual puede recrear la colección "docs": la reabrimos.
    demo_parent(base.crear_coleccion("docs", chunks))

    print("\n" + "=" * 72)
    print(
        "La regla que ordena las cuatro: ninguna se activa 'porque sí'.\n"
        "Primero el síntoma en tu golden set, después la palanca, y siempre\n"
        "volver a medir. Una técnica sofisticada que no sube tu recall es\n"
        "complejidad que vas a mantener para siempre a cambio de nada."
    )


if __name__ == "__main__":
    main()
