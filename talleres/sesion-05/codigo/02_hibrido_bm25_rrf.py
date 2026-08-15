"""
Paso 4. Primera mejora: búsqueda híbrida (BM25 + vectores con RRF)

Cubre la slide "Búsqueda híbrida: BM25 + vectores con RRF". Es la pieza
central de la sesión porque es la continuación DIRECTA de la sesión 04: el
diagnóstico del script 01 dijo "fallo de recuperación por términos
literales", y BM25 es exactamente la herramienta para eso.

    · La búsqueda vectorial conserva el SIGNIFICADO (paráfrasis, sinónimos).
    · BM25 conserva las PALABRAS EXACTAS (códigos, siglas, identificadores).
    · RRF combina las dos listas sin tener que calibrar sus scores.

La regla de la sesión: no asumimos que esto mejora. Lo medimos contra el
mismo golden set y comparamos con el baseline.

Este script también mide "solo BM25", y esa fila es la más instructiva de
todas: BM25 gana en varias queries pero PIERDE una que el vector sí
encontraba ("¿cómo firmo mis webhooks?": el documento dice "firma", no
"firmo", y BM25 no sabe de morfología). Por eso el patrón es HÍBRIDO y no
"reemplazar el vector por BM25": cada uno cubre el punto ciego del otro.

No llama a la API de Anthropic: BM25 y RRF son puro cálculo local.

Cómo correrlo:
    python ejemplos/02_hibrido_bm25_rrf.py
"""

import base
import metricas
import retrieval


def main():
    chunks = base.todos_los_chunks()
    collection = base.crear_coleccion("docs", chunks)
    golden = base.cargar_golden()
    buscadores = retrieval.construir_buscadores(chunks, collection)

    # Las tres variantes SIN modelo: baseline, léxico puro y la fusión.
    # (El reranker queda para el script 03: es el único que cuesta dinero
    # y latencia, y todavía no sabemos si hace falta.)
    variantes = ["vectorial (sesión 04)", "solo BM25", "híbrido RRF"]

    print(f"Golden set: {len(golden)} queries · {len(variantes)} variantes\n")
    print(metricas.encabezado())
    resultados = {}
    for nombre in variantes:
        resultados[nombre] = metricas.evaluar(golden, buscadores[nombre])
        print(metricas.fila(nombre, golden, resultados[nombre]))

    vec = resultados["vectorial (sesión 04)"]
    bm = resultados["solo BM25"]
    hib = resultados["híbrido RRF"]

    # 1. Qué rescató el híbrido: las queries cuyo chunk correcto NO llegaba
    #    al generador (fuera del top-4, la ventana real de rag.py).
    print("\n=== Queries que el baseline no le entregaba al modelo ===")
    for q in golden:
        if metricas.sintoma(golden, vec, q) == "recuperacion":
            pos_v = metricas.posicion(golden, vec, q)
            pos_h = metricas.posicion(golden, hib, q)
            estado = "sigue sin llegar" if metricas.sintoma(golden, hib, q) == "recuperacion" else "AHORA LLEGA"
            print(f"  vec pos={pos_v or '-'} → híbrido pos={pos_h or '-'}  [{estado}]  {q}")
    print(
        "  → Donde entra BM25, entra porque la query comparte términos\n"
        "    LITERALES con el chunk correcto. Lo exacto es su especialidad."
    )

    # 2. El contraejemplo: dónde BM25 solo se rompe y el vector lo salva.
    print("\n=== Queries que BM25 pierde del todo y el vector sí encuentra ===")
    for q in golden:
        if metricas.posicion(golden, bm, q) is None:
            pos_v = metricas.posicion(golden, vec, q)
            print(f"  BM25: fuera del top-10 · vectorial: pos={pos_v}   {q}")
    print(
        "  → El documento dice 'firma' y la query dice 'firmo'. Para BM25 son\n"
        "    dos tokens distintos; para el embedding, la misma idea.\n"
        "    Esto es lo que decide la sesión: NO se trata de reemplazar el\n"
        "    vector por BM25, sino de sumarlos. Cada uno cubre el punto ciego\n"
        "    del otro."
    )

    # 3. El nuevo diagnóstico, que es el puente al script 03.
    print("\n=== Diagnóstico después del híbrido ===")
    for nombre in variantes:
        c = metricas.diagnostico(golden, resultados[nombre])
        print(
            f"  {nombre:<24} ok={c['ok']:<3} orden={c['orden']:<3} "
            f"recuperación={c['recuperacion']}"
        )

    print(
        "\nLee la tabla completa, no solo la fila que te gusta:\n\n"
        "  · Contra el baseline, ganamos: recall@1 sube de 0.60 a 0.73 y el MRR\n"
        "    de 0.71 a 0.82. El diagnóstico acertó y la palanca funcionó.\n\n"
        "  · Pero 'solo BM25' EMPATA al híbrido en recall@1, y en este corpus\n"
        "    cargado de jerga hasta le gana en recall@5. Si te quedaras en esa\n"
        "    fila concluirías que el vector search sobra. Sería un error, y la\n"
        "    columna que lo delata es recall@10: BM25 pierde una query POR\n"
        "    COMPLETO ('¿cómo firmo mis webhooks?'), y lo que no está entre los\n"
        "    candidatos ya no lo rescata nadie. El híbrido es la única variante\n"
        "    con recall@10 = 1.00: siempre trae el chunk correcto a la mesa.\n\n"
        "  · Ese es su verdadero valor, y es una decisión de ingeniería, no de\n"
        "    métrica: prefiero la variante que nunca pierde la evidencia, aunque\n"
        "    hoy empate en recall@1, porque es la única sobre la que un paso de\n"
        "    reordenamiento puede llegar a 1.00.\n\n"
        "  · Y una honestidad más: el híbrido dejó 2 queries fuera del top-4,\n"
        "    una más que BM25 solo. RRF con k=60 amortigua mucho un #1 fuerte de\n"
        "    un solo ranker. Ese k es una perilla: cámbiala y vuelve a medir.\n\n"
        "Con el chunk correcto ya siempre entre los candidatos, el problema que\n"
        "queda es de ORDEN. Esa es la condición exacta que el deck pone para el\n"
        "reranker → script 03."
    )


if __name__ == "__main__":
    main()
