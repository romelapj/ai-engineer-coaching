"""
Paso 5. Segunda mejora, solo porque los datos la justifican: reranking

Cubre la slide "Rerankers: precisión cara, úsala al final".

Este script existe por una razón que el script 02 dejó por escrito: después
del híbrido, el chunk correcto YA está entre los candidatos (recall@10 alto)
pero no siempre de primero (recall@1 bajo). El deck da la regla:

    "Si recall@k grande es alto pero recall@1..5 es bajo, el problema es de
     ORDEN, no de recuperación. Ahí el reranker paga su latencia."

Y al revés, que es lo que suele olvidarse: si el chunk correcto no está
entre los candidatos, reordenarlos no lo va a inventar. Un reranker sobre
un mal recall es dinero y latencia tirados.

Por qué funciona: el vector search compara dos embeddings calculados por
SEPARADO (bi-encoder). El reranker lee query y documento JUNTOS
(cross-encoder) y produce un score de relevancia real. Es mucho más
preciso y mucho más caro, y de ahí su lugar: al final, sobre pocos
candidatos que ya recuperaste barato.

Llama a la API de Anthropic: 1 llamada por query (15 aquí). También mide la
latencia, porque una mejora de recall que triplica el tiempo de respuesta
es una decisión de producto, no solo un número bonito.

Cómo correrlo:
    python ejemplos/03_reranking.py
"""

import time

import base
import metricas
import retrieval


def main():
    chunks = base.todos_los_chunks()
    collection = base.crear_coleccion("docs", chunks)
    golden = base.cargar_golden()
    buscadores = retrieval.construir_buscadores(chunks, collection)

    # La tabla final de la sesión: las cuatro variantes, mismo golden set.
    variantes = [
        "vectorial (sesión 04)",
        "solo BM25",
        "híbrido RRF",
        "híbrido + rerank",
    ]

    print(f"Golden set: {len(golden)} queries")
    print("El reranker hace 1 llamada al modelo por query: esto tarda.\n")
    print(metricas.encabezado())
    resultados, latencias = {}, {}
    for nombre in variantes:
        t0 = time.time()
        resultados[nombre] = metricas.evaluar(golden, buscadores[nombre])
        latencias[nombre] = (time.time() - t0) / len(golden)
        print(metricas.fila(nombre, golden, resultados[nombre]))

    # El costo, en la misma pantalla que el beneficio. Siempre juntos.
    print("\n=== Latencia media por query (el precio de cada variante) ===")
    for nombre in variantes:
        print(f"  {nombre:<26} {latencias[nombre]:>6.2f} s")

    # Qué arregló exactamente el reranker: las queries de síntoma "orden".
    hib = resultados["híbrido RRF"]
    rer = resultados["híbrido + rerank"]
    print("\n=== Queries que el híbrido tenía mal ordenadas y el reranker subió ===")
    for q in golden:
        antes = metricas.posicion(golden, hib, q)
        despues = metricas.posicion(golden, rer, q)
        if antes and despues and despues < antes:
            print(f"  pos {antes} → {despues}   {q}")

    print(
        "\nFíjate en '¿cómo firmo mis webhooks?': BM25 solo la perdía del todo,\n"
        "el híbrido la trajo de octava y el reranker la puso de primera. Ninguno\n"
        "de los dos pasos habría bastado solo. Ese es el argumento del pipeline\n"
        "completo, y salió de los datos, no de la teoría."
    )

    print(
        "\nCómo se lee este resultado sin engañarse:\n"
        "  · El reranker sube recall@1 porque el trabajo pesado ya estaba\n"
        "    hecho: el híbrido le entregó 10 candidatos con el correcto\n"
        "    adentro. Reordenar 10 buenos candidatos es un problema fácil.\n"
        "  · En un corpus de 23 chunks los 10 candidatos son casi medio\n"
        "    corpus, así que el número se ve espectacular. En un corpus real\n"
        "    de cientos de miles, el reranker sigue viendo solo 10-50: por\n"
        "    eso el recall del paso anterior es el que manda.\n"
        "  · Y el reranker es la variante más lenta de la tabla. Si tu\n"
        "    producto tolera ese tiempo, entra; si no, el híbrido solo ya\n"
        "    resolvía el fallo grave (no perder la evidencia).\n\n"
        "Con esto cerramos el núcleo: diagnosticamos, medimos, aplicamos dos\n"
        "palancas y volvimos a medir. Lo demás son palancas para OTROS\n"
        "síntomas → script 04."
    )


if __name__ == "__main__":
    main()
