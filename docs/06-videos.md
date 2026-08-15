# 06 · Videos de los talleres

**Estado:** 3 de 24 con resumen escrito · actualizado el 15 de agosto de 2026

Cada día del taller cierra con la tarjeta de un video: miniatura, título y una
línea de por qué ese video en ese día. Al hacer clic se abre en una pestaña
nueva una página propia, con el video embebido y el material del curso alrededor.

## Por qué una página y no un enlace suelto

Un enlace a YouTube manda al alumno a un sitio diseñado para retenerlo, con
recomendaciones al lado. La página propia hace tres cosas que el enlace no:
sitúa el video en el día concreto del taller, dice qué mirar antes de darle a
reproducir, y deja por escrito dónde el video se queda corto. Esa última parte
es la que más valor tiene y la que ningún video trae.

## Cómo se añade un video

1. Se registra en `talleres/videos.yaml` con su id de YouTube, título, autor,
   idioma y duración.
2. El día del taller lo referencia y explica **por qué ahí**:

```yaml
video:
  id: 8OJC21T2SL4
  porque: >-
    Tu corte por títulos es uno de sus cinco niveles; el video te muestra
    los otros cuatro y cuándo cada uno paga su complejidad.
```

3. `build.py` genera `talleres/videos/<id>.html`. No hay paso manual: si un día
   referencia un video, su página existe.

## El contenido se escribe después de ver el video

Los campos `resumen`, `valioso`, `conecta` y `reparos` del catálogo son
opcionales. Mientras falten, la página se genera igual (el video se ve) pero
muestra un estado de **resumen pendiente** en vez de contenido inventado.

Esa es una decisión deliberada y del mismo tipo que la del código: igual que el
taller nunca muestra código que no corre, tampoco resume un video que nadie vio.
Un resumen inventado se lee perfecto y es exactamente lo que un alumno no puede
detectar.

Se intentó automatizar bajando las transcripciones de YouTube. No se puede: el
endpoint `timedtext` exige una sesión autenticada desde 2024 y devuelve vacío.
Los metadatos scrapeados tampoco son fiables (la página responde con un muro de
consentimiento), así que título, autor y duración salen del deck, revisados a
mano.

`build.py` lista al final de cada corrida los que faltan.

## Los videos, por día

| Taller | Día | Video | Autor | Duración | Resumen |
| ------ | --- | ----- | ----- | -------- | ------- |
| 01 | D1 | [But what is a GPT? Visual intro to transformers](https://youtu.be/wjZofJX0v4M) | 3Blue1Brown | ~27 min | ⧗ pendiente |
| 01 | D2 | [¿Qué es un LLM? Enormes Modelos del Lenguaje](https://youtu.be/Sz4qacFBHLk) | Dot CSV | ~15 min | ⧗ pendiente |
| 01 | D3 | [Attention in transformers, step-by-step](https://youtu.be/eMlx5fFNoYc) | 3Blue1Brown | ~26 min | ⧗ pendiente |
| 01 | D4 | [Deep Dive into LLMs like ChatGPT](https://youtu.be/7xTGNNLPyMI) | Andrej Karpathy | 3 h 31 min | ⧗ pendiente |
| 01 | D5 | [What are Word Embeddings?](https://youtu.be/wgfSDrqYMJ4) | IBM Technology | corto | ⧗ pendiente |
| 02 | D1 | [Prompt Engineering Tutorial: Master ChatGPT and LLM ](https://youtu.be/_ZvnD73m40o) | freeCodeCamp.org | ~1 h | ⧗ pendiente |
| 02 | D3 | [Prompting 101 | Code w/ Claude](https://youtu.be/ysPbXH0LpIE) | Anthropic | ~24 min | ⧗ pendiente |
| 02 | D4 | [Cómo usar (BIEN) ChatGPT y cualquier Inteligencia Ar](https://youtu.be/7f5xF-I-S3c) | Dot CSV | ~20 min | ⧗ pendiente |
| 02 | D5 | [AI prompt engineering: A deep dive](https://youtu.be/T9aRN5JkmL8) | Anthropic | ~1 h 30 min | ⧗ pendiente |
| 02 | D6 | [IBM AI Experts Reveal Prompt Engineering Secrets](https://youtu.be/7zczUN30wSw) | IBM Technology | corto | ⧗ pendiente |
| 03 | D1 | [Build AI Function Calling with LangChain & Advanced ](https://youtu.be/cjCYcTPryw8) | IBM Technology | corto | ⧗ pendiente |
| 03 | D2 | [How to Connect an LLM to Python Functions (Tool Call](https://youtu.be/liV0bfZ5Wu0) | Dataquest | medio | ⧗ pendiente |
| 03 | D3 | [Tutorial Assistants API de OpenAI · Parte 2: Functio](https://youtu.be/-3-wq_kvc3A) | LLM Master | medio | ⧗ pendiente |
| 03 | D4 | [Pydantic is all you need · Jason Liu](https://youtu.be/yj-wSRJwrrc) | AI Engineer | ~20 min | ⧗ pendiente |
| 03 | D5 | [Pydantic is STILL all you need · Jason Liu](https://youtu.be/pZ4DIH2BVqg) | AI Engineer | ~20 min | ⧗ pendiente |
| 04 | D1 | [The 5 Levels Of Text Splitting For Retrieval](https://youtu.be/8OJC21T2SL4) | Greg Kamradt | ~1 h 10 min | ✅ |
| 04 | D2 | [Vector Databases simply explained! (Embeddings & Ind](https://youtu.be/dN0lsF2cvm4) | Python Engineer | ~4 min | ✅ |
| 04 | D3 | [What is Retrieval-Augmented Generation (RAG)?](https://youtu.be/T-D1OfcDW1M) | IBM Technology | ~6 min | ✅ |
| 04 | D4 | [¿Qué es RAG? Clase con código y ejemplo](https://youtu.be/uAsd9pOIcLg) | EvoAcademy | medio | ⧗ pendiente |
| 04 | D5 | [Learn RAG From Scratch: Python AI Tutorial](https://youtu.be/sVcwVQRHIc8) | freeCodeCamp.org | ~2 h 30 min | ⧗ pendiente |
| 05 | D6 | [Top 3 RAG Retrieval Strategies: Sparse, Dense & Hybr](https://youtu.be/r0Dciuq0knU) | IBM Technology | corto | ⧗ pendiente |
| 05 | D7 | [Mastering Retrieval for LLMs: BM25, Fine-tuned Embed](https://youtu.be/9QJXvNiJIG8) | Trelis Research | largo | ⧗ pendiente |
| 05 | D8 | [Advanced RAG 04: Reranking with Cross Encoders and C](https://youtu.be/ZFbaA9eM0uo) | Sam Witteveen | medio | ⧗ pendiente |
| 05 | D9 | [The Best RAG Technique Yet? Anthropic's Contextual R](https://youtu.be/tmiBae2goJM) | Prompt Engineering | medio | ⧗ pendiente |

## Días sin video

No todos los días tienen uno, y no se rellena por rellenar. Los que hoy no
tienen candidato:

- **Taller 02, día 2** (streaming): ninguno de los cinco videos de la sesión
  habla de streaming.
- **Taller 03, día 6** (timeouts, idempotencia y logs): es el día más de oficio
  y el menos cubierto por el material divulgativo.
- **Taller 05, días 1 a 5 y 10**: la sesión tiene 10 días y solo 4 videos. Los
  días de medición (golden set, recall@k, MRR, diagnóstico) son justamente los
  que menos material bueno tienen en video, que es parte de por qué existe
  este taller.

Antes de buscar relleno conviene aceptar que un día sin video está bien: la
tarjeta es para ampliar, no un requisito de formato.
