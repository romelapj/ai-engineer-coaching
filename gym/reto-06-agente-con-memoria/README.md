# 🏋️ Reto 06 — Agente con memoria

| Metadato                            | Valor                                                                                                                                                                   |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Fase**                            | Fase 2                                                                                                                                                                  |
| **Sesión en que se asigna**         | Sesión 7                                                                                                                                                                |
| **Tiempo estimado**                 | 12–16 horas (repartidas en 1 semana)                                                                                                                                    |
| **Skill de entrevista que entrena** | Arquitectura de agentes con estado: memoria persistente, delegación a subagentes (patrón orchestrator–workers) y optimización de costo/latencia demostrada con métricas |
| **Prerrequisitos**                  | Reto 05 completado (agente investigador con loop de tool use escrito a mano), Python 3.11+, API key de LLM                                                              |

---

## Contexto

Un agente sin memoria es un becario con amnesia: cada mañana reinvestiga lo que ya investigó ayer, gasta los mismos tokens y comete los mismos errores. El salto de "demo de agente" a "agente que una empresa pagaría por correr a diario" pasa exactamente por las dos piezas de este reto: **estado persistente entre ejecuciones** y **descomposición en subagentes** para que el contexto del orquestador no explote. No es casualidad que los sistemas de agentes serios (Claude Code, Deep Research, los agentes de soporte en producción) tengan ambas cosas; tampoco es casualidad que casi ningún tutorial las cubra, porque obligan a tomar decisiones de diseño incómodas: ¿qué se guarda?, ¿cuándo se recupera?, ¿cómo evitas que la memoria se llene de basura?, ¿qué ve y qué NO ve el orquestador del trabajo del subagente?

La segunda pieza —el subagente— ataca el problema más caro de los agentes de largo aliento: la **contaminación de contexto**. Si tu orquestador mete en su historia cada página web cruda que descarga, a la décima tool call estás pagando 80k tokens de entrada por turno y el modelo se distrae con ruido. La solución estándar es delegar la subtarea sucia a un worker con su propio contexto (y a menudo un modelo más barato), que devuelve solo un resultado estructurado y destilado. Eso es aislamiento de contexto, y es una palabra que en entrevista vale oro si puedes respaldarla con un sistema que construiste.

Las preguntas de entrevista que dominar esto te permite responder con autoridad: _"¿Cómo harías que un agente recuerde entre sesiones? ¿Qué guardarías, dónde, y cómo decides qué recuperar?"_ y _"¿Cuándo partirías un agente en varios? ¿Qué le pasa al contexto y al costo?"_. La respuesta floja es "le pasaría el historial completo" o "usaría un framework de memoria". La respuesta que vas a poder dar después de este reto incluye un esquema de datos concreto, una política de deduplicación y frescura, y una tabla con números reales: cuántos tokens y segundos te ahorró la memoria en la segunda corrida.

## Enunciado

Extiende el agente investigador del reto 5 (el que, dado un tema, usa tools de búsqueda/fetch y produce un reporte) con dos capacidades nuevas. **No reescribas el agente con un framework**: sigue siendo tu loop, tus tools, tu código.

### Parte A — Memoria persistente entre ejecuciones

El agente guarda **hallazgos** (findings destilados, NO transcripts crudos) en un almacenamiento local persistente: **SQLite** (recomendado, un solo `memory.db`) o archivos JSON/JSONL en `memory/`. Cada hallazgo tiene como mínimo:

```
id, topic, claim (el hallazgo en ≤ 500 caracteres), sources (lista de URLs/ids),
confidence ("high"|"medium"|"low"), created_at, run_id
```

La memoria se expone al agente como **dos tools**: `memory_search(query)` y `memory_save(hallazgo)`. El system prompt instruye al agente a consultar la memoria ANTES de usar tools caras (búsqueda web, fetch) y a guardar cada hallazgo verificado al producirlo. La política de frescura es una decisión tuya documentada por escrito (p. ej., "hallazgos con `created_at` > 14 días se reportan como posiblemente desactualizados").

### Parte B — Subagente especializado

El orquestador delega una subtarea a un **subagente con su propio contexto, su propio system prompt y un toolset restringido** (subconjunto de las tools del orquestador). Elige UNA de estas dos especialidades (u otra validada con el coach antes del miércoles):

- **Lector/extractor** (recomendado): recibe una URL, hace el fetch él mismo, y devuelve al orquestador SOLO una lista de hallazgos estructurados con citas. El orquestador nunca ve el HTML/markdown crudo de la página.
- **Verificador**: recibe un hallazgo y devuelve un veredicto estructurado (`confirmado`/`contradicho`/`sin evidencia`) contrastándolo con una segunda fuente que él mismo busca.

El subagente se invoca como una tool del orquestador (p. ej. `delegar_lectura(url, foco)`) y se implementa como una función con su propia lista de mensajes — un mini-loop dentro del loop. Usa un modelo más barato para el subagente si tu proveedor lo permite (p. ej. clase Haiku para el worker, clase Sonnet para el orquestador) y reporta el desglose de costo.

### Parte C — La demo que lo prueba todo

Sobre un tema de investigación concreto (sugeridos: _"Compara LanceDB, Chroma y Qdrant para un RAG local: rendimiento, persistencia y licencia"_, o _"Estado del arte de structured outputs en los SDKs de Anthropic y OpenAI"_), ejecutas **tres corridas en procesos separados**:

1. **Corrida fría** (`--reset-memory`): memoria vacía. El agente investiga desde cero.
2. **Corrida caliente** (mismo tema, mismo comando): el agente encuentra los hallazgos en memoria y produce un reporte equivalente con mucho menos trabajo.
3. **Corrida de control** (`--no-memory`): mismo tema con la memoria deshabilitada, para demostrar que el ahorro viene de TU memoria y no de otra cosa.

**Ejemplo de entrada/salida.** Entrada:

```
python agent.py "Compara LanceDB, Chroma y Qdrant para un RAG local: rendimiento, persistencia y licencia"
```

Cada corrida escribe `runs/<timestamp>/report.md` (el reporte con citas) y `runs/<timestamp>/metrics.json`:

```json
{
  "run_id": "2026-06-15T10-32-11",
  "topic": "Compara LanceDB, Chroma y Qdrant...",
  "wall_time_s": 148.2,
  "tokens_in": 51240,
  "tokens_out": 6890,
  "cost_usd": 0.34,
  "tool_calls": {
    "web_search": 8,
    "delegar_lectura": 11,
    "memory_search": 1,
    "memory_save": 9
  },
  "memory_hits": 0,
  "hallazgos_nuevos": 9
}
```

En la corrida caliente esperas algo como: `memory_hits: 8`, `web_search: 1`, `tokens_in` y `wall_time_s` reducidos drásticamente. Esa comparación, en tabla, es el corazón del entregable.

Además defines `eval/key_points.json`: **5 puntos clave** que un buen reporte sobre tu tema debe cubrir (los escribes a mano tras tu primera investigación). Sirven para verificar que la corrida caliente no es "más barata porque responde menos".

## Requisitos

1. La memoria persiste en disco (`memory.db` SQLite o `memory/*.jsonl`) y **sobrevive al reinicio del proceso**: las tres corridas de la demo son invocaciones separadas de `python agent.py`.
2. El esquema del hallazgo incluye como mínimo los 7 campos de la Parte A, validados con Pydantic al guardar y al leer.
3. `memory_search` y `memory_save` son tools que el agente decide invocar (aparecen en el transcript como tool calls); está prohibido inyectar silenciosamente toda la memoria en el prompt. Sí puedes (y deberías) inyectar al inicio un resumen corto de qué temas hay en memoria (≤ 300 tokens).
4. Deduplicación: guardar dos veces un hallazgo equivalente del mismo tema hace upsert, no inserta. Correr 3 veces el mismo tema deja la misma cantidad de hallazgos que correrlo 1 vez (±1).
5. El subagente tiene system prompt propio, toolset restringido (estrictamente menor que el del orquestador) y contexto propio; su transcript se guarda separado del transcript del orquestador.
6. **Aislamiento de contexto verificable**: ningún `tool_result` que reciba el orquestador supera 2.000 tokens. El contenido crudo de páginas solo existe en el contexto del subagente.
7. El resultado del subagente es JSON estructurado validado (Pydantic); si el subagente falla o devuelve basura, el orquestador recibe un error manejable y el run continúa (nunca crashea por culpa del worker).
8. CLI: `python agent.py "<tema>"` con flags `--reset-memory` (borra la memoria y corre) y `--no-memory` (corre sin leer ni escribir memoria). Cada corrida persiste `report.md`, `metrics.json` y `transcript.jsonl` (todas las tool calls con argumentos y tamaño de resultado) en `runs/<timestamp>/`.
9. `metrics.json` incluye: `wall_time_s`, `tokens_in`, `tokens_out`, `cost_usd` (estimado con la tabla de precios del proveedor), `tool_calls` por tool, `memory_hits`, `hallazgos_nuevos`, y el desglose orquestador vs. subagente.
10. Script `eval/run_demo.py` que ejecuta las tres corridas (fría → caliente → control), verifica los umbrales de los criterios de aceptación y emite la tabla comparativa final. Exit code 1 si algún umbral falla.
11. README propio del reto con: diagrama de arquitectura (ASCII o imagen), esquema de memoria, política de frescura y deduplicación, la tabla comparativa de las 3 corridas, y setup reproducible en ≤ 5 comandos.
12. API keys solo por variables de entorno; costo total de la demo completa (3 corridas + eval) ≤ 3 USD, reportado en el README.

## Criterios de aceptación

- [ ] La corrida caliente consume **≤ 60 % de los tokens totales** (`tokens_in + tokens_out`) de la corrida fría.
- [ ] La corrida caliente tarda **≤ 70 % del wall time** de la corrida fría.
- [ ] La corrida caliente hace **≤ 50 % de las llamadas a tools de investigación** (`web_search` + `delegar_lectura`/fetch) que la fría, y registra `memory_hits ≥ 3`.
- [ ] La corrida de control (`--no-memory`) queda dentro de **±25 % de los tokens de la corrida fría** — prueba de que el ahorro viene de la memoria y no de caching accidental.
- [ ] Calidad sin degradación: tanto el reporte frío como el caliente cubren **≥ 4 de los 5** puntos de `eval/key_points.json` (juzgado por LLM-as-judge a temperatura 0).
- [ ] Persistencia real: entre corrida fría y caliente el proceso muere (invocaciones separadas); ningún estado en variables de proceso.
- [ ] Deduplicación: tras correr el mismo tema 3 veces, `COUNT(*)` de hallazgos del tema difiere en ≤ 1 respecto a una sola corrida.
- [ ] Aislamiento: en `transcript.jsonl` del orquestador, **0 tool results > 2.000 tokens**; el transcript del subagente existe como archivo separado y SÍ contiene el contenido crudo.
- [ ] El subagente devuelve JSON que valida contra su schema en **el 100 % de sus invocaciones** del run final (con 1 reintento permitido por invocación).
- [ ] Una cuarta corrida sobre un **tema relacionado pero distinto** (p. ej. "¿Qué vector store usarías para 10 M de documentos?") reutiliza ≥ 1 hallazgo de memoria (`memory_hits ≥ 1`), demostrando que la memoria no es un cache por string exacto del tema.
- [ ] `eval/run_demo.py` corre de punta a punta sin intervención manual y el coach puede reproducirlo con ≤ 5 comandos.

## Cómo se evalúa

El harness ejecuta las corridas como subprocesos (eso garantiza la persistencia real), lee los `metrics.json` y verifica los umbrales de forma determinista; solo la cobertura de puntos clave usa LLM-as-judge. El coach correrá tu `eval/run_demo.py` tal cual; estructura sugerida:

```python
# eval/run_demo.py — estructura del harness (no la solución)
import json, sqlite3, subprocess
from pathlib import Path

TOPIC = "Compara LanceDB, Chroma y Qdrant para un RAG local..."
TOPIC_RELACIONADO = "¿Qué vector store usarías para 10M de documentos?"

def run_agent(topic: str, *flags: str) -> dict:
    """Lanza `python agent.py <topic> *flags` como subproceso
    y devuelve el metrics.json del run recién creado."""
    subprocess.run(["python", "agent.py", topic, *flags], check=True)
    last_run = sorted(Path("runs").iterdir())[-1]
    return json.loads((last_run / "metrics.json").read_text())

def judge_key_points(report_path: Path, key_points: list[str]) -> int:
    """LLM-as-judge a temperatura 0: ¿cuántos de los 5 puntos
    clave cubre el reporte? Devuelve el conteo (0-5)."""
    ...

fria     = run_agent(TOPIC, "--reset-memory")
caliente = run_agent(TOPIC)
control  = run_agent(TOPIC, "--no-memory")
relacionada = run_agent(TOPIC_RELACIONADO)

t = lambda m: m["tokens_in"] + m["tokens_out"]
investigacion = lambda m: m["tool_calls"].get("web_search", 0) \
                        + m["tool_calls"].get("delegar_lectura", 0)

assert t(caliente) <= 0.60 * t(fria),                "tokens: memoria no ahorra lo suficiente"
assert caliente["wall_time_s"] <= 0.70 * fria["wall_time_s"], "latencia"
assert investigacion(caliente) <= 0.50 * investigacion(fria), "tools de investigación"
assert caliente["memory_hits"] >= 3
assert abs(t(control) - t(fria)) <= 0.25 * t(fria),  "el control debe parecerse a la fría"
assert relacionada["memory_hits"] >= 1,              "memoria no generaliza a temas relacionados"

# deduplicación: 3 corridas del mismo tema no inflan la memoria
n1 = sqlite3.connect("memory.db").execute(
    "SELECT COUNT(*) FROM hallazgos WHERE topic = ?", (TOPIC,)).fetchone()[0]
run_agent(TOPIC); run_agent(TOPIC)
n3 = ...  # mismo COUNT
assert abs(n3 - n1) <= 1, f"memoria duplicada: {n1} -> {n3}"

# calidad: imprimir tabla final fría vs caliente vs control + cobertura 4/5
...
```

En la sesión de revisión el coach abrirá tu `transcript.jsonl` del orquestador y buscará dos cosas a mano: (a) el momento en que el agente consulta memoria antes de buscar en la web, y (b) que ningún tool result supere los 2.000 tokens. También te pedirá `memory.db` para inspeccionar 3 hallazgos al azar y preguntarte por qué ese `confidence` y esas `sources`.

## Pistas

<details><summary>Pista 1 — Por dónde empezar (empujón suave)</summary>

Empieza por la instrumentación, no por la memoria: si no puedes medir tokens, costo y tiempo por corrida, no puedes demostrar nada de lo que pide el reto. Envuelve tu cliente de LLM en una clase que acumule `usage` de cada respuesta y los conteos de tool calls, y haz que `metrics.json` salga de ahí. Con eso funcionando, corre tu agente del reto 5 dos veces sobre el mismo tema y guarda esa tabla: esa es tu línea base "sin memoria" y te va a decir exactamente cuánto margen tienes que recortar. Después diseña el esquema del hallazgo en papel ANTES de escribir código — la pregunta clave es: "¿qué necesita leer el agente en la corrida 2 para no repetir el trabajo de la corrida 1?". La respuesta nunca es "el transcript completo".

</details>

<details><summary>Pista 2 — Memoria que funciona (dirección concreta)</summary>

Tres decisiones que separan una memoria útil de un log glorificado: (1) **Guarda destilado, no crudo** — el hallazgo es la conclusión con sus fuentes, en ≤ 500 caracteres; si guardas páginas enteras, la corrida 2 paga casi los mismos tokens por leerlas de la memoria que de la web. (2) **Búsqueda mejor que igualdad exacta**: SQLite con FTS5 (`CREATE VIRTUAL TABLE ... USING fts5`) te da búsqueda por términos en 10 líneas y resuelve el criterio del tema relacionado sin necesidad de embeddings; normaliza el `query` antes de buscar. (3) **Upsert por clave semántica**: calcula un hash de `(topic_normalizado, claim_normalizado)` o pide al modelo un `slug` estable del hallazgo, y haz `INSERT ... ON CONFLICT DO UPDATE`. Para que el agente realmente consulte la memoria primero, no confíes solo en el system prompt: inyecta al inicio una línea tipo `"Memoria disponible: 9 hallazgos sobre 'vector stores' (última actualización: hace 2 días)"` — con ese señuelo, el modelo llama a `memory_search` solo casi siempre.

</details>

<details><summary>Pista 3 — Subagente y corrida caliente (casi spoiler)</summary>

El subagente es literalmente una función: `def delegar_lectura(url: str, foco: str) -> list[Hallazgo]` que crea su PROPIA lista `messages` con su system prompt ("Eres un lector: haz fetch de la URL, extrae hallazgos relevantes al foco, devuelve SOLO este JSON..."), corre un mini-loop de máximo 5 turnos con solo la tool `fetch_url`, y devuelve la lista validada. El orquestador registra esa función como una tool más; el `tool_result` que recibe es el JSON compacto — el aislamiento de contexto sale gratis por construcción, porque el HTML crudo solo vivió en `messages` del worker. Usa el modelo barato para el worker y loguea `usage` por separado. Para clavar los umbrales de la corrida caliente, añade al system prompt del orquestador una regla explícita de política: _"Antes de cualquier `web_search`, llama a `memory_search`. Si la memoria cubre un punto del reporte con `confidence: high` y `created_at` < 14 días, úsala como fuente y NO investigues ese punto de nuevo; cita el hallazgo. Investiga solo los huecos."_ Si aun así re-investiga, revisa qué devuelve tu `memory_search`: si devuelve los hallazgos sin `claim` legible o sin fuentes, el modelo desconfía y vuelve a la web — el formato del resultado de la tool ES parte del prompt engineering.

</details>

## Bonus

1. **Tools como MCP server**: expón `memory_search`, `memory_save` y `delegar_lectura` como un servidor MCP (SDK oficial `mcp`, transporte stdio) y demuestra que un cliente genérico (Claude Code, el MCP Inspector, o un segundo script tuyo) puede usar tu memoria sin tocar tu código del agente. Esto convierte tu memoria en infraestructura reutilizable y te da la frase "construí un MCP server" con sustancia detrás.
2. **Consolidación de memoria**: un job `consolidate.py` que periódicamente fusiona hallazgos redundantes del mismo tema (con un LLM barato), resuelve contradicciones marcando el más reciente/confiable, y reporta cuánto se compactó. Corre tu demo antes y después de consolidar y muestra el efecto en `memory_hits` y tokens — es la versión embrionaria de la "reflexión" de los papers de agentes, con números tuyos.

## Qué demuestra en entrevista

- _"Le di memoria persistente a un agente investigador: hallazgos destilados en SQLite con FTS5, expuestos como tools, con upsert por clave semántica y política de frescura de 14 días. La segunda corrida sobre el mismo tema bajó de ~58k a ~21k tokens y de 148 a 95 segundos, con la misma cobertura de puntos clave verificada por un juez — y tengo la corrida de control sin memoria que prueba que el ahorro es de la memoria, no de un cache accidental."_
- _"Apliqué el patrón orchestrator–workers para el aislamiento de contexto: el orquestador delega la lectura de páginas a un subagente con modelo más barato y contexto propio, y solo recibe JSON validado de vuelta. En el transcript del orquestador no hay ningún tool result mayor a 2.000 tokens — el HTML crudo nunca toca su contexto, por construcción."_
- _"Todo está instrumentado: tokens, costo y tool calls por corrida y por agente, con un harness que falla en CI si la memoria deja de ahorrar el 40 % de tokens. Puedo decirte exactamente qué cuesta cada corrida y qué parte del costo es del worker — porque un agente sin métricas de costo no es un sistema, es una demo."_

## Entregable

**En el repo** (carpeta `gym/reto-06-agente-con-memoria/` de tu repo de soluciones, antes del domingo 23:59):

- `agent.py` (orquestador + CLI con `--reset-memory` / `--no-memory`), `subagent.py` (o módulo equivalente), `memory.py` (esquema + tools), `requirements.txt`/`pyproject.toml`.
- `eval/key_points.json` (los 5 puntos clave de tu tema) y `eval/run_demo.py`.
- `runs/` con las 4 corridas de la demo final (fría, caliente, control, tema relacionado): `report.md`, `metrics.json` y `transcript.jsonl` de cada una. NO subas `memory.db` si pesa > 5 MB (gitignore + se regenera con la corrida fría).
- README del reto con: diagrama de arquitectura, esquema de memoria, políticas de deduplicación y frescura, tabla comparativa de las 4 corridas, desglose de costo orquestador/subagente y setup en ≤ 5 comandos.

**En la sesión de revisión** (15 min, comparte pantalla):

1. Corre `eval/run_demo.py` en vivo, o muestra la corrida del día con timestamp si el presupuesto no da (2–4 min).
2. Recorre la tabla comparativa: fría vs. caliente vs. control vs. tema relacionado, explicando de dónde sale cada ahorro (3 min).
3. Abre `memory.db`/`memory/` y defiende 3 hallazgos que el coach elija al azar: por qué ese `confidence`, esas `sources` y esa granularidad (3 min).
4. Abre los dos transcripts (orquestador y subagente) y señala el aislamiento de contexto en los datos (2 min).
5. La pregunta del coach que debes poder responder: _"Tu memoria tiene un hallazgo de hace 3 meses que ya es falso y el agente lo acaba de citar en un reporte. ¿Qué falló en tu diseño y qué cambiarías primero?"_
