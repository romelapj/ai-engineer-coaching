"""
metricas.py: el instrumento (recall@k, MRR y el DIAGNÓSTICO por síntoma)

Cubre la slide "Golden set: recall@k y MRR", más una pieza que el deck no
tiene explícita y que es la bisagra de esta sesión: además del número
global, clasificar CADA query fallida por su síntoma.

Un recall@5 de 0.87 no te dice qué hacer. Saber que 2 queries no aparecen
ni en el top-10 y otras 4 aparecen pero no de primeras, sí:

    · fallo de RECUPERACIÓN (el chunk correcto no llega al generador)
      → el buscador no lo trae: hay que cambiar CÓMO se busca.

    · fallo de ORDEN (llega, pero enterrado bajo chunks irrelevantes)
      → sí lo encuentra, lo pone en mal lugar: hay que REORDENAR.

Y el orden en que se atacan no es negociable: reordenar no puede rescatar
un chunk que nunca se recuperó. Primero recuperación, después orden.

Esa distinción es la que decide la siguiente palanca, y por eso el script
01 termina en un diagnóstico y no solo en tres decimales.

Este archivo no se ejecuta directamente: los scripts numerados lo importan.
"""

# Convención de esta sesión, para que todo sea comparable:
#   golden  = {query: id_del_chunk_correcto}          ← construido a mano
#   results = {query: [ids ordenados por el buscador]} ← lo que salió


def recall_at_k(golden, results, k=5):
    # ¿En qué fracción de las queries el chunk correcto apareció en el
    # top-k? Es LA métrica principal de retrieval: si el chunk correcto no
    # llega al contexto, el generador no puede responder bien, punto.
    hits = sum(1 for q in golden if golden[q] in results[q][:k])
    return hits / len(golden)


def mrr(golden, results):
    # Mean Reciprocal Rank: promedio de 1/posición del primer acierto.
    # Premia que lo correcto salga ARRIBA: de primero vale 1.0, de segundo
    # 0.5, de quinto 0.2... y no salir vale 0. Por eso recall y MRR se leen
    # juntos: recall dice "¿está?", MRR dice "¿está arriba?".
    total = 0.0
    for q in golden:
        if golden[q] in results[q]:
            total += 1 / (results[q].index(golden[q]) + 1)
    return total / len(golden)


def posicion(golden, results, q):
    # Posición 1-indexada del chunk correcto, o None si no está en la lista.
    return results[q].index(golden[q]) + 1 if golden[q] in results[q] else None


# La ventana que importa para el diagnóstico: cuántos chunks le entrega tu
# RAG al generador. En rag.py son 4, así que un chunk que quedó de quinto
# NUNCA llega al modelo, y para el sistema real es idéntico a no haberlo
# encontrado. Diagnosticar en top-10 cuando entregas 4 te haría creer que
# tienes un problema de orden donde en realidad tienes uno de recuperación.
K_UTIL = 4


def sintoma(golden, results, q, k=K_UTIL):
    # El diagnóstico de UNA query. Tres estados, tres decisiones distintas.
    pos = posicion(golden, results, q)
    if pos is None or pos > k:
        return "recuperacion"  # No llega al generador: es como si no existiera.
    if pos == 1:
        return "ok"  # Correcto y de primero: nada que arreglar aquí.
    return "orden"  # Llega al contexto, pero enterrado bajo ruido.


def diagnostico(golden, results, k=K_UTIL):
    # El conteo de síntomas del sistema completo. Este dict es el que
    # responde la pregunta que faltaba entre "medir" y "BM25":
    # ¿qué TIPO de error estamos observando?
    conteo = {"ok": 0, "orden": 0, "recuperacion": 0}
    for q in golden:
        conteo[sintoma(golden, results, q, k)] += 1
    return conteo


def evaluar(golden, buscar):
    # Corre las N queries del golden set contra un buscador cualquiera.
    # `buscar` es una función query → lista de ids ordenada. Toda variante
    # de esta sesión respeta esa firma, así que todas se miden igual: esa
    # es la única forma de que la comparación sea justa.
    return {q: buscar(q) for q in golden}


def fila(nombre, golden, results):
    # Una línea de la tabla antes/después. Incluimos recall@10 además de
    # @1 y @5 porque el deck lo usa para decidir el reranker: recall alto a
    # k grande + recall bajo a k=1 es exactamente el caso donde reordenar
    # paga su latencia.
    return (
        f"{nombre:<26}"
        f" {recall_at_k(golden, results, k=1):>8.2f}"
        f" {recall_at_k(golden, results, k=5):>8.2f}"
        f" {recall_at_k(golden, results, k=10):>9.2f}"
        f" {mrr(golden, results):>6.2f}"
    )


def encabezado():
    return (
        f"{'variante':<26} {'recall@1':>8} {'recall@5':>8} {'recall@10':>9} {'MRR':>6}\n"
        + "-" * 61
    )
