"""
Paso 7. Cierre: el retrieval medido, listo para ser una herramienta

Cierra la sesión 05 y abre la 06.

Recorrido de las tres sesiones, en una línea cada una:

    04: ¿cómo le doy al modelo acceso confiable a mis documentos?
         → un RAG con chunks, embeddings, Chroma, top-k, umbral y citas.
    05: ya funciona; ¿recupera el contexto correcto y cómo lo mejoro?
         → ese mismo RAG, ahora medido, híbrido y justificado con datos.
    06: ¿cuándo el modelo debe DECIDIR qué herramienta usar y en qué orden?
         → un agente que usa este RAG mejorado como una herramienta más.

Este script hace explícito el traspaso. Primero muestra lo único que
cambiamos en el RAG de la sesión 04: la función de recuperación. El
generador, el umbral y las citas son los mismos de hace una semana.

Después envuelve todo eso en un tool schema de Anthropic y deja que el
modelo decida solo cuándo invocarlo. Eso ya no es un pipeline fijo
pregunta → buscar → responder: es el modelo eligiendo. Ahí empieza la
sesión 06.

Llama a la API de Anthropic (rerank, generación y una vuelta de tool use).

Cómo correrlo:
    python ejemplos/05_puente_a_agentes.py
"""

import json

import anthropic

import base
import rag
import retrieval

client = anthropic.Anthropic()
MODELO = "claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# 1. El retrieval que salió de esta sesión, con la firma que rag.py espera
# ---------------------------------------------------------------------------
def construir_recuperador(chunks, collection, k=4):
    # Híbrido + reranking, exactamente lo que el golden set justificó en los
    # scripts 02 y 03. Devuelve evidencias en el MISMO formato que
    # rag.recuperar_vectorial, así que es intercambiable con él.
    ids = [c["id"] for c in chunks]
    id_a_chunk = {c["id"]: c for c in chunks}
    bm25 = retrieval.construir_bm25(chunks)

    def recuperar(pregunta):
        candidatos = retrieval.buscar_hibrido(collection, bm25, ids, pregunta)
        ordenados = retrieval.rerank(pregunta, candidatos, id_a_chunk)[:k]
        return [
            {
                "id": cid,
                "texto": id_a_chunk[cid]["texto"],
                "fuente": id_a_chunk[cid]["fuente"],
                "seccion": id_a_chunk[cid]["seccion"],
                # Sin similitud de coseno que filtrar: el reranker ya juzgó
                # relevancia leyendo query y documento juntos, que es un
                # criterio más fuerte que el umbral. El umbral fue nuestra
                # defensa mientras la similitud era lo único que teníamos.
                "pasa_umbral": True,
            }
            for cid in ordenados
        ]

    return recuperar


# ---------------------------------------------------------------------------
# 2. El mismo RAG, con el retrieval nuevo enchufado
# ---------------------------------------------------------------------------
def demo_mismo_rag(collection, recuperar):
    print("=" * 72)
    print("1) EL MISMO RAG DE LA SESIÓN 04, con el retrieval de la sesión 05")
    print("=" * 72)

    # Justo la pregunta con la que el script 00 se quedó sin evidencia.
    pregunta = "¿Cómo evito cobros duplicados cuando reintento un pago?"
    print(f"\nPregunta: {pregunta}\n")

    antes = rag.responder(pregunta, lambda p: rag.recuperar_vectorial(collection, p))
    print("  con retrieval de la sesión 04:")
    print(f"    {antes['respuesta'].strip()}")

    despues = rag.responder(pregunta, recuperar)
    print("\n  con retrieval de la sesión 05 (híbrido + rerank):")
    print(f"    {despues['respuesta'].strip()}")
    print("\n    evidencia usada:")
    for e in despues["evidencias"]:
        print(f"      - {e['id']}")

    print(
        "\n  Lo único que cambió entre las dos respuestas es la función de\n"
        "  recuperación. Mismo generador, mismo prompt, mismas citas. Por eso\n"
        "  medir retrieval por separado vale la pena: es la pieza que manda."
    )


# ---------------------------------------------------------------------------
# 3. El mismo RAG, ahora como herramienta que el modelo puede invocar
# ---------------------------------------------------------------------------
HERRAMIENTA = {
    "name": "buscar_documentacion",
    "description": (
        "Busca en la documentación interna de PagosYa (API de pagos, "
        "webhooks, catálogo de errores E-XXXX y changelogs) y devuelve los "
        "fragmentos más relevantes con su fuente. Úsala siempre que la "
        "pregunta dependa de detalles específicos de PagosYa: códigos de "
        "error, headers, límites, versiones o fechas."
    ),
    # El schema es el contrato. La descripción de arriba es lo que el modelo
    # lee para DECIDIR si la llama: escribir bien esa frase es ingeniería de
    # agentes, y es el tema de la sesión 06.
    "input_schema": {
        "type": "object",
        "properties": {
            "pregunta": {
                "type": "string",
                "description": "La pregunta a buscar, en lenguaje natural.",
            }
        },
        "required": ["pregunta"],
    },
}


def demo_como_herramienta(recuperar):
    print("\n" + "=" * 72)
    print("2) EL MISMO RAG, EXPUESTO COMO HERRAMIENTA (preview de la sesión 06)")
    print("=" * 72)

    pregunta = "Un pago me devolvió E-4012. ¿Qué pasó y puedo reintentarlo?"
    print(f"\nPregunta del usuario: {pregunta}\n")

    mensajes = [{"role": "user", "content": pregunta}]
    resp = client.messages.create(
        model=MODELO, max_tokens=1024, tools=[HERRAMIENTA], messages=mensajes
    )

    # A diferencia del RAG, aquí NADIE forzó la búsqueda: el modelo decidió.
    usos = [b for b in resp.content if b.type == "tool_use"]
    if not usos:
        print("  El modelo respondió sin buscar:")
        print(f"    {resp.content[0].text.strip()}")
        return

    mensajes.append({"role": "assistant", "content": resp.content})
    resultados = []
    for uso in usos:
        print(f"  → el modelo decidió llamar a {uso.name}({json.dumps(uso.input, ensure_ascii=False)})")
        evidencias = recuperar(uso.input["pregunta"])
        for e in evidencias:
            print(f"      recuperado: {e['id']}")
        resultados.append({
            "type": "tool_result",
            "tool_use_id": uso.id,
            "content": "\n\n".join(
                f"({e['fuente']} § {e['seccion']})\n{e['texto']}" for e in evidencias
            ),
        })

    # Le devolvemos el resultado y el modelo cierra la respuesta.
    mensajes.append({"role": "user", "content": resultados})
    final = client.messages.create(
        model=MODELO, max_tokens=1024, tools=[HERRAMIENTA], messages=mensajes
    )
    texto = "".join(b.text for b in final.content if b.type == "text")
    print(f"\n  Respuesta final:\n    {texto.strip()}")

    print(
        "\n  Nota la diferencia con el RAG: el pipeline de la sesión 04 SIEMPRE\n"
        "  busca, aunque la pregunta no lo necesite. Aquí el modelo decidió\n"
        "  buscar, con qué query, y cuándo ya tenía suficiente para responder.\n"
        "  Esa decisión (qué herramienta, con qué argumentos, en qué orden) es\n"
        "  la sesión 06. Y llega apoyada en un retrieval que ya sabemos medir:\n"
        "  una herramienta cuya calidad no puedes medir es una herramienta en\n"
        "  la que un agente no debería confiar."
    )


def main():
    chunks = base.todos_los_chunks()
    collection = base.crear_coleccion("docs", chunks)
    recuperar = construir_recuperador(chunks, collection)

    demo_mismo_rag(collection, recuperar)
    demo_como_herramienta(recuperar)


if __name__ == "__main__":
    main()
