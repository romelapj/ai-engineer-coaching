"""
Paso 3. Antes de arreglar: medir. Golden set, recall@k, MRR y diagnóstico

Cubre las slides "Dónde se rompe el vector search puro" y "Golden set:
recall@k y MRR".

En el script 00 vimos dos fallos. Dos fallos elegidos a mano son una
anécdota: no sabemos si el RAG falla el 10% o el 40% de las veces, ni si
fallan siempre por lo mismo. Necesitamos preguntas reales y, para cada una,
el chunk que ESPERAMOS recuperar. Ese conjunto es el golden set, y con él
el baseline deja de ser una impresión y pasa a ser un número.

Pero el número global tampoco basta. "recall@5 = 0.87" no dice qué hacer.
Por eso este script termina clasificando cada query fallida por SÍNTOMA:

    · fallo de RECUPERACIÓN → el chunk correcto no aparece ni en el top-10.
      El buscador literalmente no lo ve. Cambiar el ORDEN no lo arregla.

    · fallo de ORDEN → aparece en el top-10, pero abajo. El buscador sí lo
      encuentra; lo pone en mal lugar.

Esa es la pregunta que faltaba entre "medir" y "BM25": ahora que medimos,
¿QUÉ TIPO de error estamos observando? La respuesta decide la palanca.

No llama a la API de Anthropic: solo la base vectorial local.

Cómo correrlo:
    python ejemplos/01_medir_el_baseline.py
"""

import base
import metricas
import retrieval

ETIQUETA = {
    "ok": "✓ ok        ",
    "orden": "~ ORDEN     ",
    "recuperacion": "✗ NO LLEGA  ",
}


def main():
    chunks = base.todos_los_chunks()
    collection = base.crear_coleccion("docs", chunks)

    # El golden set: queries reales mapeadas a su chunk esperado. Vive en
    # golden.json y no en el código porque es un ARTEFACTO del proyecto: se
    # construye a mano, se versiona y se discute en PRs como cualquier otro
    # activo. El deck recomienda 20-50 queries para un corpus real; aquí 15
    # alcanzan para ver el patrón.
    golden = base.cargar_golden()
    print(f"Corpus: {len(chunks)} chunks · Golden set: {len(golden)} queries\n")

    # El baseline es EXACTAMENTE el buscador de la sesión 04.
    baseline = lambda q: retrieval.buscar_vectores(collection, q)
    results = metricas.evaluar(golden, baseline)

    print("=== Baseline: solo vectores (el RAG de la sesión 04) ===")
    print(metricas.encabezado())
    print(metricas.fila("vectorial (sesión 04)", golden, results))

    # El detalle por query, que es donde está el aprendizaje.
    print(
        f"\n=== Detalle por query, con su síntoma ==="
        f"\n(el RAG entrega {metricas.K_UTIL} chunks: de la posición "
        f"{metricas.K_UTIL + 1} en adelante, el modelo nunca lo ve)"
    )
    for q in golden:
        s = metricas.sintoma(golden, results, q)
        pos = metricas.posicion(golden, results, q)
        lugar = f"pos={pos}" if pos else "fuera del top-10"
        print(f"  {ETIQUETA[s]} {lugar:<16} {q}")
        if s != "ok":
            print(f"{'':>16}esperado: {golden[q]}")
            print(f"{'':>16}salió #1: {results[q][0]}")

    # Y el diagnóstico agregado: el conteo que decide qué hacer después.
    conteo = metricas.diagnostico(golden, results)
    print(f"\n=== Diagnóstico: ¿qué TIPO de error tenemos? ===")
    print(f"  (ventana: los {metricas.K_UTIL} chunks que rag.py entrega al generador)")
    print(f"  correctas de primeras : {conteo['ok']}")
    print(f"  fallo de ORDEN        : {conteo['orden']}   (llega, pero enterrado)")
    print(f"  fallo de RECUPERACIÓN : {conteo['recuperacion']}   (no llega al modelo)")

    print(
        "\nDos lecturas, en este orden:\n\n"
        "1. Las queries que fallan comparten un patrón. Todas se apoyan en un\n"
        "   término LITERAL del documento ('cobros duplicados', 'sk_test_',\n"
        "   'firma') y el embedding lo suaviza hacia el tema general: por eso\n"
        "   gana el chunk introductorio genérico ('Guía de Webhooks') sobre la\n"
        "   sección específica. Es exactamente la slide 'dónde se rompe el\n"
        "   vector search puro': brilla en paráfrasis, falla en lo exacto.\n\n"
        "2. Tenemos los DOS síntomas, y eso fija el orden de trabajo. El\n"
        "   reranking solo puede arreglar los fallos de orden: reordenar no\n"
        "   rescata un chunk que nunca se recuperó. Así que primero atacamos\n"
        "   recuperación (cambiando CÓMO se busca) y recién después decidimos\n"
        "   si el orden sigue siendo un problema.\n\n"
        "Fallo de recuperación por términos literales tiene una palanca con\n"
        "nombre propio: búsqueda léxica → script 02."
    )


if __name__ == "__main__":
    main()
