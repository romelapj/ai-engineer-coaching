# 🏋️ Reto 05 — Agente desde cero

|                         |                                                                                                                                           |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **Fase**                | Fase 2                                                                                                                                    |
| **Se asigna en**        | Sesión 6                                                                                                                                  |
| **Tiempo estimado**     | 6–8 horas (repartidas en la semana)                                                                                                       |
| **Skill de entrevista** | "Explícame cómo funciona un agente por dentro, sin decir 'LangChain'" — diseño del loop agéntico, tool use crudo, control de presupuestos |
| **Prerrequisitos**      | Reto 03 (tool calling básico) y Reto 04 (manejo de contexto) completados                                                                  |

---

## Contexto

Si en una entrevista de AI Engineer te preguntan _"¿cómo funciona un agente?"_ y tu respuesta empieza con el nombre de un framework, acabas de perder puntos. Los frameworks (LangChain, CrewAI, LlamaIndex, smolagents) son azúcar encima de una idea brutalmente simple: **un `while` loop donde el modelo decide la siguiente acción, tú la ejecutas, le devuelves el resultado, y se repite hasta que el modelo declara que terminó o se le acaba el presupuesto**. Quien no ha escrito ese loop a mano no entiende qué abstrae el framework — y por tanto no puede debuggearlo cuando se rompe, que es el 80 % del trabajo real.

Este reto te obliga a construir ese loop con las manos: solo el SDK oficial del proveedor del modelo (`anthropic`, `openai` o equivalente), la librería estándar y, como mucho, un cliente HTTP. Vas a tocar las tres decisiones que definen a cualquier agente en producción: **cómo se le presentan las tools al modelo**, **cómo se acumula la conversación entre pasos** (y cuánto crece), y **qué pasa cuando el agente quiere seguir pero ya no puede** (presupuesto de pasos y de tokens agotado). Ninguna de las tres la resuelve el modelo por ti.

Dominar esto responde directamente preguntas de entrevista como: _"¿Qué hay dentro de una llamada de tool use?"_, _"¿Cómo evitas que un agente entre en loop infinito o te queme la factura?"_ y _"¿Cuándo usarías un framework y cuándo no?"_. Después de este reto, las respondes con código tuyo como evidencia.

## Enunciado

Construye **un agente investigador de línea de comandos** que recibe una pregunta, investiga usando tools, y produce un informe en markdown con fuentes citadas.

**Restricción central: cero frameworks de agentes.** Permitido: el SDK del modelo (`anthropic` / `openai`), `httpx`/`requests`, `pathlib`, `json`, `argparse`. Prohibido: LangChain, LlamaIndex, CrewAI, smolagents, Haystack, o cualquier librería que implemente el loop por ti.

### El loop

El corazón del proyecto es un archivo `agent.py` cuyo loop hace exactamente esto:

1. Envía la conversación al modelo con las tools declaradas.
2. Si el modelo pide una tool → la ejecuta, agrega el resultado a la conversación, vuelve al paso 1.
3. Si el modelo responde texto final → termina y escribe el informe.
4. Si se agota el presupuesto (pasos o tokens) → **corta limpiamente** y fuerza una última llamada _sin tools_ pidiendo el mejor informe posible con lo recolectado hasta el momento.

### Las tools (elige UNA modalidad y hazla bien)

**Modalidad A — Investigador local (recomendada: determinista y evaluable):**

- `list_files()` → lista los archivos del corpus con su tamaño.
- `read_file(path)` → devuelve el contenido (truncado a un máximo que tú definas, p. ej. 8 000 caracteres, indicando que fue truncado).
- `search_corpus(query)` → grep simple (substring o regex) sobre el corpus, devuelve archivo + línea + contexto.
- **Corpus sugerido:** descarga 12–15 ensayos de Paul Graham en texto plano (paulgraham.com), o 10 RFCs cortos (p. ej. RFC 1945, 2616, 6455, 6749, 7519, 9110...), o los release notes de un proyecto open source que conozcas. Inclúyelo en `corpus/` con un script `download_corpus.sh` reproducible.

**Modalidad B — Investigador web:**

- `web_search(query)` → vía API de Brave Search, Tavily o la búsqueda de DuckDuckGo (sin scraping frágil). Devuelve título + URL + snippet de los top 5 resultados.
- `fetch_page(url)` → descarga la página y devuelve texto plano (truncado, p. ej. 10 000 caracteres).
- Esta modalidad es más vistosa pero menos reproducible; si la eliges, cachea las respuestas HTTP en disco para que el eval sea repetible.

### Presupuestos (no negociables)

- **Máximo de pasos:** configurable, default **10** iteraciones del loop.
- **Máximo de tokens:** configurable, default **50 000 tokens totales** (input + output acumulados, leídos del campo `usage` de cada respuesta del API — no estimados).
- Ambos por flag de CLI: `--max-steps`, `--max-tokens`.

### Interfaz

```bash
python agent.py "¿Qué dice Paul Graham sobre cómo elegir en qué trabajar?" \
  --max-steps 10 --max-tokens 50000 \
  --out informes/pg-trabajo.md
```

### Ejemplo de entrada/salida

**Entrada:** `"Según el corpus, ¿cuáles son las diferencias clave entre OAuth 2.0 y JWT, y cuándo se usa cada uno?"`

**Salida (`informes/oauth-vs-jwt.md`):**

```markdown
# OAuth 2.0 vs JWT

## Respuesta

OAuth 2.0 es un framework de autorización [1], mientras que JWT es un
formato de token [2]. Se complementan: OAuth define el flujo, JWT puede
ser el formato del access token [1][2]...

## Fuentes

1. corpus/rfc6749.txt — sección 1.4, líneas 210–245
2. corpus/rfc7519.txt — sección 3, líneas 88–120

## Metadatos de la corrida

- Pasos usados: 6/10
- Tokens usados: 31 204/50 000
- Tool calls: search_corpus ×3, read_file ×3
```

La sección **Metadatos de la corrida** es obligatoria: es tu evidencia de que el presupuesto se respetó.

Además del informe, cada corrida debe escribir un **trace JSONL** (`traces/<timestamp>.jsonl`): una línea por paso con `{step, tool_name, tool_input, tokens_in, tokens_out, tokens_acumulados}`. El eval lee este archivo.

## Requisitos

1. `agent.py` implementa el loop completo (decisión → ejecución → observación → repetición) en **menos de 200 líneas** contadas con `cloc` o equivalente (sin contar comentarios ni líneas en blanco). Las tools pueden vivir en `tools.py` aparte y no cuentan para el límite.
2. Usa **únicamente** el SDK del modelo + librería estándar + cliente HTTP. `pip freeze` / `uv.lock` lo demuestra.
3. Implementa **mínimo 2 tools, máximo 4**, con schema JSON declarado al modelo (no parsing de texto libre con regex sobre la respuesta).
4. Respeta `--max-steps` (default 10): al alcanzarlo, ejecuta el cierre forzado (llamada final sin tools) en lugar de cortar con excepción o informe vacío.
5. Respeta `--max-tokens` (default 50 000): el conteo sale del campo `usage` real de cada respuesta del API y se verifica **antes** de cada nueva llamada.
6. Toda corrida produce: (a) el informe markdown con secciones `Respuesta`, `Fuentes` y `Metadatos de la corrida`, y (b) el trace JSONL.
7. Cada afirmación sustantiva del informe cita su fuente con referencia verificable: archivo + líneas (Modalidad A) o URL (Modalidad B). Mínimo **2 fuentes distintas** por informe.
8. Manejo de errores de tool: si una tool falla (archivo inexistente, HTTP 4xx/5xx), el error se devuelve **al modelo** como resultado de la tool (para que se recupere), no revienta el proceso.
9. El agente termina por sí mismo (el modelo decide responder) en al menos una de las preguntas del eval — es decir, no siempre muere por presupuesto.
10. `README.md` propio del proyecto con: cómo instalar, cómo correr, una corrida de ejemplo pegada, y 3–5 líneas sobre la decisión de diseño más difícil que tomaste.

## Criterios de aceptación

- [ ] `agent.py` tiene **< 200 líneas** de código efectivo (verificado con `cloc agent.py`).
- [ ] `grep -riE "langchain|llamaindex|crewai|smolagents|haystack" requirements.txt uv.lock pyproject.toml` no devuelve nada.
- [ ] Con `--max-steps 3` sobre una pregunta que requiere más investigación, el trace muestra **exactamente ≤ 3 pasos** y el informe existe igualmente (cierre forzado funcionó).
- [ ] Con `--max-tokens 15000`, el trace muestra `tokens_acumulados ≤ 15 000` en el momento del corte, y nunca se hizo una llamada habiendo ya superado el límite.
- [ ] Las **5 preguntas del eval** (ver abajo) producen informe con ≥ 2 fuentes citadas cada uno.
- [ ] En ≥ 4 de las 5 preguntas, las citas son verificables: el archivo/URL citado existe y contiene el contenido referenciado.
- [ ] En ≥ 3 de las 5 preguntas, el juez LLM del eval califica la respuesta como "responde la pregunta" (score ≥ 4/5).
- [ ] Una tool forzada a fallar (p. ej. pedirle al agente que lea `corpus/no-existe.txt` vía la pregunta) no tumba el proceso: el trace muestra el error devuelto al modelo y el agente continúa.
- [ ] `python eval/run_eval.py` corre de punta a punta sin intervención manual y exit code 0 cuando todo pasa.

## Cómo se evalúa

El reto incluye su propio harness en `eval/`. Define **5 preguntas fijas** sobre tu corpus en `eval/questions.json` (3 que el corpus responde bien, 1 que requiere sintetizar de ≥ 2 documentos, 1 que el corpus NO responde — el informe debe decirlo honestamente, no alucinar). El harness corre el agente sobre cada una y aplica checks deterministas + un juez LLM.

Estructura sugerida (esqueleto, no la solución):

```python
# eval/run_eval.py
import json, subprocess, sys
from pathlib import Path

QUESTIONS = json.loads(Path("eval/questions.json").read_text())
MAX_STEPS, MAX_TOKENS = 10, 50_000

def run_agent(question: str, out: Path) -> Path:
    """Corre agent.py como subproceso; devuelve la ruta del trace JSONL."""
    subprocess.run([sys.executable, "agent.py", question,
                    "--max-steps", str(MAX_STEPS),
                    "--max-tokens", str(MAX_TOKENS),
                    "--out", str(out)], check=True, timeout=300)
    return newest_trace()  # el trace más reciente en traces/

def check_budget(trace: Path) -> dict:
    steps = [json.loads(l) for l in trace.read_text().splitlines()]
    return {
        "steps_ok": len(steps) <= MAX_STEPS,
        "tokens_ok": all(s["tokens_acumulados"] <= MAX_TOKENS for s in steps),
    }

def check_report(report: Path) -> dict:
    text = report.read_text()
    return {
        "has_sources": text.count("corpus/") >= 2 or text.count("http") >= 2,
        "has_metadata": "Metadatos de la corrida" in text,
        "sources_exist": verify_citations(text),  # abre cada archivo/URL citado
    }

def judge_answer(question: str, report: Path) -> int:
    """Juez LLM: ¿el informe responde la pregunta usando solo lo citado?
    Devuelve score 1-5. Rubrica fija en eval/judge_prompt.txt."""
    ...

def check_line_count() -> bool:
    # cloc --json agent.py → code < 200
    ...

if __name__ == "__main__":
    results = []
    for q in QUESTIONS:
        report = Path(f"eval/out/{q['id']}.md")
        trace = run_agent(q["question"], report)
        results.append({**check_budget(trace), **check_report(report),
                        "judge": judge_answer(q["question"], report)})
    # criterio global: budgets 5/5, fuentes 5/5, citas verificables ≥4/5,
    # juez ≥4 en ≥3/5, y check_line_count() == True
    ...
```

En la sesión de revisión, el coach correrá `python eval/run_eval.py` en frío y además leerá `agent.py` en voz alta contigo: tendrás que justificar cada bloque del loop en menos de una frase. Si un bloque necesita un párrafo de explicación, probablemente sobra.

## Pistas

<details>
<summary>Pista 1 — La forma del loop</summary>

El loop entero cabe en esta silueta: una lista `messages`, un `for step in range(max_steps)`, una llamada al API con `tools=[...]`, y un `if` sobre la razón de parada de la respuesta (`stop_reason` / `finish_reason`). Si el modelo paró por tool use, iteras sobre los tool calls, ejecutas cada uno con un `dict` que mapea nombre → función, y agregas a `messages` tanto la respuesta del assistant como los resultados de las tools en el formato que el SDK exige. Si paró por fin de turno, ese texto es tu informe. No necesitas clases, ni "AgentExecutor", ni grafos: necesitas una lista y un `for`.

</details>

<details>
<summary>Pista 2 — Presupuesto de tokens sin estimar</summary>

No uses tiktoken ni heurísticas de caracteres/4. Cada respuesta del API trae `usage` con tokens de input y output exactos. Acumula `total += usage.input_tokens + usage.output_tokens` después de cada llamada, y chequea `total >= max_tokens` **al inicio** de la siguiente iteración, no al final. Detalle que separa juniors de seniors: como el historial completo se reenvía en cada paso, el input crece cuadráticamente con los pasos — por eso truncar los resultados de tools (8–10k chars) no es cosmético, es lo que hace viable el presupuesto. Loguea el acumulado en el trace en cada paso y verás la curva.

</details>

<details>
<summary>Pista 3 — El cierre forzado (casi spoiler)</summary>

Cuando se agota el presupuesto a mitad de investigación, NO devuelvas el último texto parcial ni lances excepción. Haz una última llamada extra (fuera del loop, presupuestada aparte, ~2 000 tokens de margen) con el historial completo, `tools` vacío o `tool_choice` deshabilitado, y un mensaje final tipo: _"Se agotó el presupuesto de investigación. Escribe el mejor informe posible SOLO con la información ya recolectada arriba. Cita únicamente fuentes que efectivamente leíste. Si la pregunta no quedó respondida, dilo explícitamente en la primera línea de la sección Respuesta."_ Eso convierte un corte abrupto en una degradación elegante — y es exactamente la frase "graceful degradation under budget" que quieres poder decir en entrevista con código que la respalde.

</details>

## Bonus

1. **Context compaction:** cuando el historial supere un umbral (p. ej. 30 000 tokens), reemplaza los tool results más viejos por un resumen de una línea generado por el propio modelo ("Leí X, lo relevante fue Y") y mide en el trace cuántos tokens ahorraste por corrida. Compara informes con y sin compaction sobre las mismas 5 preguntas del eval.
2. **Modo comparativo:** implementa las dos modalidades (A y B) detrás de la misma interfaz de tools y corre el eval contra ambas. Una tabla de 5 filas (pregunta) × 4 columnas (pasos, tokens, score del juez, citas verificables) por modalidad es oro puro para el portafolio.

## Qué demuestra en entrevista

- _"Implementé el loop agéntico desde cero con el SDK crudo: el modelo decide la tool por `stop_reason`, yo ejecuto y devuelvo el resultado como tool result, y todo el agente son ~150 líneas. Por eso sé exactamente qué me abstrae un framework — y qué me esconde cuando algo falla."_
- _"El problema real no es que el agente funcione, es que pare: implementé presupuesto dual de pasos y tokens medidos del `usage` real del API, con cierre forzado que produce un informe parcial honesto en lugar de una excepción. Graceful degradation under budget."_
- _"Cada corrida emite un trace JSONL por paso, y el eval combina checks deterministas (presupuestos, citas verificables contra el corpus) con un juez LLM con rúbrica fija — incluyendo una pregunta-trampa que el corpus no responde, para medir que el agente no alucine."_

## Entregable

**En el repo** (`gym/reto-05-agente-from-scratch/` de tu repo de retos, o repo propio enlazado):

```
agent.py              # el loop, < 200 líneas efectivas
tools.py              # implementación de las tools
corpus/               # o download_corpus.sh reproducible
eval/
  questions.json      # las 5 preguntas fijas
  judge_prompt.txt    # rúbrica del juez
  run_eval.py         # harness completo
  out/                # los 5 informes de la última corrida del eval
traces/               # al menos 3 traces JSONL de corridas reales
informes/             # 2+ informes de corridas manuales
README.md             # setup, uso, corrida de ejemplo, decisión de diseño
```

**En la sesión de revisión (15 min):**

1. Demo en vivo (5 min): una pregunta nueva que el coach trae, corrida en frío.
2. Walkthrough de `agent.py` (5 min): explicas el loop línea por línea; el coach interrumpe con "¿y si...?" (tool falla, modelo pide tool inexistente, presupuesto a la mitad de un paso).
3. El eval (5 min): corres `eval/run_eval.py` y defiendes los resultados, incluyendo qué hizo el agente con la pregunta que el corpus no responde.

No se acepta el reto sin el harness de eval funcionando: un agente sin eval es una demo, no ingeniería.
