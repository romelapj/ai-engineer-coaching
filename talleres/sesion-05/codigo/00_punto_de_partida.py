"""
Paso 1 y 2. El RAG de la sesión 04, y por qué el umbral no basta

    Sesión 04: "¿cómo le doy al modelo acceso confiable a mis documentos?"
    Sesión 05: "ya funciona; ¿cómo sé si recupera el contexto correcto?"

Este script no construye nada nuevo. Corre el RAG de la sesión 04 (rag.py,
sin un solo cambio) sobre el mismo corpus, y lo hace fallar a propósito.

La idea que hay que dejar clara antes de tocar código nuevo:

    La similitud de coseno y el umbral evitan que el modelo INVENTE.
    No garantizan que la evidencia CORRECTA llegue al contexto.

Son dos problemas distintos y la sesión 04 solo resolvió el primero. Fíjate
en el segundo caso de la demo: el chunk correcto SÍ estaba entre los
recuperados, pero quedó de cuarto con similitud 0.387 y el umbral (0.40) lo
cortó, mientras dos chunks irrelevantes, con similitud más alta, pasaron.
El umbral filtra por similitud, así que cuando la similitud se equivoca, el
umbral se equivoca con ella.

Y el síntoma final es traicionero: el RAG responde "No tengo evidencia para
responder" y parece que se está portando bien (¡no alucinó!) cuando en
realidad la respuesta SÍ está en el corpus y no supo encontrarla. Sin
métricas, ese fallo es invisible.

Llama a la API de Anthropic (la generación): necesita ANTHROPIC_API_KEY.

Cómo correrlo (desde session-05, con el venv activo):
    python ejemplos/00_punto_de_partida.py
"""

import base
import rag

# Dos preguntas que el RAG de la sesión 04 contesta perfecto, y dos que no.
# Las cuatro tienen respuesta EXPLÍCITA en el corpus: la diferencia no está
# en los documentos, está en si el retrieval sabe encontrarla. Para las que
# fallan anotamos dónde estaba la respuesta, que es lo que convierte la
# demo en diagnóstico.
PREGUNTAS = [
    ("¿Cuál es el timeout default de la API?", None),
    ("¿Qué significa el error E-4012?", None),
    (
        "¿Cómo evito cobros duplicados cuando reintento un pago?",
        "api-pagos.md § Timeouts y reintentos: el header Idempotency-Key.\n"
        "     El chunk correcto no apareció ni entre los cuatro candidatos.",
    ),
    (
        "¿puedo usar sk_test_ en producción?",
        "api-pagos.md § Autenticación: llaves sk_test_ vs. sk_live_.\n"
        "     Peor aún: el chunk correcto SÍ se recuperó, de cuarto, y el\n"
        "     umbral lo cortó (0.387 < 0.40) mientras dejaba pasar dos\n"
        "     chunks irrelevantes con similitud más alta.",
    ),
]


def mostrar(pregunta, collection):
    print("\n" + "=" * 72)
    print(f"Pregunta: {pregunta}")
    print("-" * 72)

    # Recuperamos SIN filtrar todavía, para poder ver el corte del umbral.
    evidencias = rag.recuperar_vectorial(collection, pregunta)
    print("Top-4 por similitud de coseno:")
    for i, e in enumerate(evidencias, 1):
        marca = "pasa " if e["pasa_umbral"] else "CORTA"
        print(f"  [{i}] sim={e['similitud']:.3f} {marca} {e['id']}")

    # Y ahora el pipeline completo: umbral + generación con citas.
    salida = rag.responder(pregunta, lambda p: evidencias)
    print(f"\nRespuesta del RAG v0.3:\n  {salida['respuesta'].strip()}")


def main():
    # Mismo corpus, mismo chunking, misma ingesta que la sesión 04.
    chunks = base.todos_los_chunks()
    collection = base.crear_coleccion("docs", chunks)
    print(f"Corpus: {len(chunks)} chunks de {len(base.METADATA_DOCS)} documentos")
    print("Pipeline: pregunta → top-4 vectorial → umbral 0.40 → generación con citas")

    for pregunta, donde_estaba in PREGUNTAS:
        mostrar(pregunta, collection)
        if donde_estaba:
            print(f"\n  ↑ Pero la respuesta SÍ está en el corpus:\n     {donde_estaba}")

    print("\n" + "=" * 72)
    print(
        "Diagnóstico honesto:\n"
        "  · El umbral y las citas hicieron su trabajo: el modelo no inventó.\n"
        "  · El retrieval no hizo el suyo: la evidencia correcta no llegó.\n"
        "  · Un 'No tengo evidencia' cuando la evidencia existe es un fallo\n"
        "    de recuperación DISFRAZADO de buen comportamiento.\n\n"
        "Aquí fallaron dos de cuatro preguntas, pero ese 50% no significa nada:\n"
        "yo elegí las cuatro. Con ejemplos escogidos a mano puedes demostrar lo\n"
        "que quieras, en cualquier dirección. Eso es una anécdota, no una\n"
        "medición. Antes de arreglar nada, hay que medir → script 01."
    )


if __name__ == "__main__":
    main()
