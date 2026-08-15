# Código de la sesión 04: RAG desde cero

Estos son los archivos que construyes en el
[Taller 04](https://romelapj.github.io/ai-engineer-coaching/talleres/sesion-04.html).
Están aquí completos para que puedas compararlos con los tuyos o desatascarte si
un día no te cuadra algo, pero **el orden de aprendizaje es el del taller**, no
el de leer estos archivos de corrido.

Cada uno corre solo y está comentado línea por línea.

```
Ingesta → Chunking → Embeddings → Vector Store → Retrieval → Generación
```

## Cómo correrlos

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."   # solo hace falta para 03 y 04

python 00_chunking.py
```

**Córrelos en orden la primera vez.** `01_ingesta.py` crea la base vectorial en
`rag_db/` que los scripts 02, 03 y 04 necesitan.

| Archivo              | Día del taller                        | ¿Llama al modelo?                  |
| -------------------- | ------------------------------------- | ---------------------------------- |
| `00_chunking.py`     | 1: Chunking por estructura            | No                                 |
| `01_ingesta.py`      | 2: Chunks → embeddings → vector store | No (embeddings locales)            |
| `02_retrieval.py`    | 3: Top-k y umbral de similitud        | No                                 |
| `03_rag_completo.py` | 4: Pipeline v0.3 con citas            | Sí (1 llamada por pregunta)        |
| `04_rag_v04.py`      | 5: Pipeline v0.4, expansión + rerank  | Sí (3 llamadas por pregunta)       |
| `docs/*.md`          | -                                     | La base de conocimiento de ejemplo |

`01_ingesta.py` descarga un modelo de embeddings local (~80 MB) la primera vez;
después todo es instantáneo.

## Una diferencia deliberada con el deck

El deck usa `UMBRAL = 0.7`, pensando en embeddings comerciales (voyage-3.5-lite,
text-embedding-3-small). Aquí el umbral es `0.40`, porque el modelo local de
Chroma (MiniLM) produce similitudes más bajas.

Esa es justamente la lección del día 3: **el umbral no se copia de un tutorial,
se calibra mirando las similitudes de tu propio modelo de embeddings**.
`02_retrieval.py` te imprime esos números precisamente para eso.

## Si cambias algo aquí

Las salidas que muestra el taller están capturadas en `../salidas/`. Si tocas un
script, vuelve a capturarlas y regenera la página:

```bash
cd talleres/sesion-04/codigo
for f in 0*.py; do python "$f" > "../salidas/${f%.py}.txt" 2>&1; done
cd ../../..
python talleres/build.py sesion-04 && python talleres/verificar.py sesion-04
```
