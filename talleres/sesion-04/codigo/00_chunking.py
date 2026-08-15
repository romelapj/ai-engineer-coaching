"""
Explicación 1: Chunking por estructura, en 20 líneas

Del deck: antes de poder "buscar" en tus documentos, hay que partirlos en
pedazos (chunks). La estrategia más simple es por tamaño fijo, pero la más
útil en la práctica es POR ESTRUCTURA: cortar donde el documento ya tiene
cortes naturales (los títulos ## y ### de un Markdown). Así cada chunk
habla de UN solo tema y además sabemos de qué sección salió (metadata que
luego usaremos para citar fuentes).

Este archivo NO llama a ningún modelo ni necesita internet: solo lee los
.md de la carpeta docs/ y muestra los chunks que produce.

Cómo correrlo:
    python ejemplos/00_chunking.py
"""

import re  # "re" = expresiones regulares, el buscador de patrones de texto de Python.
from pathlib import Path  # Manejo de rutas de archivos multiplataforma.


def split_max_tokens(texto, max_tokens=800, overlap=100):
    # Un chunk no puede ser infinito: los modelos de embeddings tienen un
    # límite de tokens. Esta función parte un texto largo en pedazos de
    # máximo ~800 tokens, con un "overlap" (solape) de ~100 tokens entre
    # pedazos para no cortar una idea justo en la frontera.
    palabras = texto.split()
    # No tenemos el tokenizador exacto a la mano, así que aproximamos:
    # en español/inglés, 1 palabra ≈ 1.3 tokens. Dividimos para pasar
    # de "tokens" a "cantidad de palabras".
    tam = int(max_tokens / 1.3)  # Tamaño de cada pedazo, en palabras.
    paso = max(
        1, tam - int(overlap / 1.3)
    )  # Cuánto avanzamos entre pedazo y pedazo (menos que 'tam' = hay solape).
    partes = []
    for i in range(0, len(palabras), paso):  # i avanza de 'paso' en 'paso': 0, paso, 2*paso...
        partes.append(" ".join(palabras[i : i + tam]))
        # Tomamos 'tam' palabras desde la posición i y las unimos en un texto.
        if i + tam >= len(palabras):
            break
            # Si esta ventana ya llegó al final del texto, PARAMOS. Sin este
            # break, el range genera una ventana más: una "cola" de pocas
            # palabras que ya estaba contenida en el chunk anterior. Esos
            # fragmentos huérfanos embeben con mucho ruido y producen
            # falsos positivos en el retrieval.
    return partes or [texto]
    # El "or [texto]" cubre el caso borde de un texto vacío: devolvemos
    # al menos el texto original en lugar de una lista vacía.


def chunk_markdown(texto, fuente):
    # Corta un documento Markdown por sus títulos de nivel 2 y 3 (## y ###).
    # 'fuente' es el nombre del archivo, que guardamos como metadata.
    secciones = re.split(r"\n(?=#{2,3} )", texto)
    # El patrón se lee así: corta en cada salto de línea (\n) que esté
    # seguido de "## " o "### ". El "(?=...)" es un "lookahead": mira que
    # el título viene después, pero NO lo consume; así el título queda
    # DENTRO de su sección, no se pierde en el corte.
    chunks = []  # Aquí iremos acumulando los chunks terminados.
    for sec in secciones:
        titulo = sec.splitlines()[0].lstrip("# ")
        # La primera línea de cada sección es su título; le quitamos los
        # '#' y espacios del inicio para quedarnos con el texto limpio.
        for parte in split_max_tokens(sec, max_tokens=100, overlap=20):
            # Si una sección es muy larga, la volvemos a partir por tamaño.
            # (En nuestros docs de ejemplo cada sección cabe en un chunk.)
            chunks.append(
                {
                    "texto": parte,  # El contenido del chunk (lo que se va a embeber y buscar).
                    "fuente": fuente,  # De qué archivo salió, para poder citar [1] (api-pagos.md § ...).
                    "seccion": titulo,  # De qué sección salió, misma razón.
                }
            )
    return chunks


def main():
    # Carpeta docs/ relativa a ESTE archivo (funciona sin importar desde
    # dónde ejecutes el script).
    carpeta_docs = Path(__file__).parent / "docs"

    todos = []  # Lista con los chunks de TODOS los documentos.
    for archivo in sorted(carpeta_docs.glob("*.md")):
        # glob("*.md") encuentra todos los Markdown de la carpeta.
        texto = archivo.read_text(
            encoding="utf-8"
        )  # Leemos el contenido completo del archivo.
        todos.extend(
            chunk_markdown(texto, archivo.name)
        )  # Lo partimos y sumamos sus chunks a la lista.

    print(
        f"Se generaron {len(todos)} chunks a partir de {len(list(carpeta_docs.glob('*.md')))} documentos:\n"
    )
    for i, c in enumerate(todos, start=1):
        # Mostramos cada chunk con su metadata y solo los primeros 80
        # caracteres del texto, para que la salida sea legible.
        print(f"[{i}] {c['fuente']} § {c['seccion']}")
        print(f"    \"{c['texto'][:80]}...\"  ({len(c['texto'])} caracteres)\n")


if __name__ == "__main__":
    # "Si este archivo se ejecuta directamente, corre main()". Esto permite
    # que 01_ingesta.py IMPORTE chunk_markdown sin que se ejecute la demo.
    main()
