"""
base.py: utilidades compartidas por los 3 ejemplos de la sesión 05

Los tres scripts de esta sesión (00, 01 y 02) trabajan sobre el MISMO
corpus y el MISMO golden set, así que lo común vive aquí una sola vez:
leer los documentos, partirlos en chunks, ingestar en Chroma y cargar el
golden set. La lógica que cada slide explica vive en su propio script.

Este archivo no se ejecuta directamente: los otros lo importan.
"""

import json  # Para leer el golden set (golden.json).
import re  # Expresiones regulares: para el chunking y el tokenizador.
from pathlib import Path  # Rutas de archivos multiplataforma.

import chromadb  # El vector store, igual que en la sesión 04.

CARPETA = Path(__file__).parent  # La carpeta ejemplos/, relativa a este archivo.

# Metadata de cada documento. En un sistema real esto vendría de tu CMS o
# de convenciones de carpetas; aquí lo declaramos a mano. La usaremos en el
# script 02 para el metadata filtering (filtrar ANTES de buscar).
# Nota: usamos "anio" sin ñ porque será una clave de filtro en Chroma y
# los nombres ASCII evitan sorpresas de codificación.
METADATA_DOCS = {
    "api-pagos.md": {"tipo": "referencia", "anio": 2026},
    "errores.md": {"tipo": "referencia", "anio": 2026},
    "webhooks.md": {"tipo": "guia", "anio": 2026},
    "changelog-2025.md": {"tipo": "changelog", "anio": 2025},
    "changelog-2026.md": {"tipo": "changelog", "anio": 2026},
}


def cargar_documentos():
    # Lee todos los .md de docs/ y devuelve una lista de (texto, fuente).
    docs = []
    for archivo in sorted((CARPETA / "docs").glob("*.md")):
        docs.append((archivo.read_text(encoding="utf-8"), archivo.name))
    return docs


def chunk_markdown(texto, fuente):
    # El mismo chunking por estructura de la sesión 04: cortar en cada
    # título ## o ### (el lookahead (?=...) deja el título DENTRO del chunk).
    secciones = re.split(r"\n(?=#{2,3} )", texto)
    chunks = []
    for sec in secciones:
        titulo = sec.splitlines()[0].lstrip("# ")  # Primera línea = título limpio.
        chunks.append(
            {
                # El id del chunk es "archivo § sección": estable y legible.
                # El golden set apunta a estos ids, así que si cambias el
                # chunking, el golden set se revisa, y esa es la gracia.
                "id": f"{fuente} § {titulo}",
                "texto": sec,
                "fuente": fuente,
                "seccion": titulo,
                # Cada chunk hereda la metadata de su documento.
                **METADATA_DOCS[fuente],
            }
        )
    return chunks


def todos_los_chunks():
    # Chunking de todo el corpus, en una lista plana.
    chunks = []
    for texto, fuente in cargar_documentos():
        chunks.extend(chunk_markdown(texto, fuente))
    return chunks


def crear_coleccion(nombre, chunks, textos=None):
    # Crea una colección de Chroma desde cero, con las DOS lecciones que
    # nos dejó la sesión 04:
    #   1. Borrar antes de crear → la ingesta es idempotente (collection.add
    #      NO sobreescribe ids existentes, los salta en silencio).
    #   2. metadata={"hnsw:space": "cosine"} → así "similitud = 1 - distancia".
    # El parámetro 'textos' permite indexar una versión ALTERADA del texto
    # (lo usaremos en el 02 para contextual retrieval) manteniendo los
    # mismos ids y metadata.
    chroma = chromadb.PersistentClient(str(CARPETA / "rag_db"))
    try:
        chroma.delete_collection(nombre)
    except Exception:
        pass  # La primera vez no existe: no pasa nada.
    col = chroma.get_or_create_collection(nombre, metadata={"hnsw:space": "cosine"})
    col.add(
        ids=[c["id"] for c in chunks],
        documents=textos if textos is not None else [c["texto"] for c in chunks],
        metadatas=[
            {"fuente": c["fuente"], "seccion": c["seccion"],
             "tipo": c["tipo"], "anio": c["anio"]}
            for c in chunks
        ],
    )
    return col


def cargar_golden():
    # El golden set: {query real → id del chunk que DEBERÍA salir}.
    # Está en un .json aparte porque es un ARTEFACTO del proyecto, no
    # código: se construye a mano, se versiona y se discute en PRs.
    return json.loads((CARPETA / "golden.json").read_text(encoding="utf-8"))


def tokenizar(texto):
    # Tokenizador simple para BM25. El deck usa texto.split(), pero eso
    # rompe justo el caso que nos importa: en "¿qué es el error E-4012?"
    # el token quedaría "E-4012?" (con el signo pegado) y NUNCA igualaría
    # al "E-4012" del documento. Bajamos a minúsculas y extraemos solo
    # secuencias de letras/números/guiones: "e-4012" queda como UN token.
    return re.findall(r"[a-z0-9áéíóúüñ_-]+", texto.lower())
