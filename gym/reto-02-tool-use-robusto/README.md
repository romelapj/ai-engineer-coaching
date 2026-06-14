# 🏋️ Reto 02 — Tool use robusto

|                                     |                                                                                                                          |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **Fase**                            | Fase 1 — Fundamentos de LLM Engineering                                                                                  |
| **Sesión en que se asigna**         | Sesión 3 (se revisa en la Sesión 4)                                                                                      |
| **Tiempo estimado**                 | 6–8 horas, repartidas en la semana                                                                                       |
| **Skill de entrevista que entrena** | Tool use / function calling resiliente: retries, backoff, clasificación de errores y degradación elegante en agentes LLM |

---

## Contexto

Cualquier tutorial te enseña a conectar una función a un LLM con function calling. Lo que separa a un dev que "probó la API" de un AI engineer contratable es qué pasa cuando esa función falla — porque en producción **va a fallar**: la API de clima devuelve un 500 a las 3 a.m., el servicio de tasas de cambio tarda 30 segundos en responder, y el endpoint interno devuelve JSON truncado porque alguien deployó a mitad de un request. Un agente que crashea ante cualquiera de esos escenarios no es un producto, es una demo.

Este reto te obliga a tratar las tools como lo que son: **dependencias remotas no confiables**. Vas a construir la capa de ejecución que todo agente serio necesita — retries con backoff exponencial, timeouts agresivos, clasificación de errores reintetables vs. no reintetables, y mensajes honestos al usuario cuando todo falla. Y lo vas a demostrar contra un harness de caos que inyecta fallos de forma determinista, no contra el "happy path" de un notebook.

En entrevista, esto responde directamente a preguntas como: _"¿Qué pasa en tu agente cuando una tool falla?"_, _"¿Cómo decides si reintentar un error?"_ y _"¿Cómo testeas un sistema no determinista?"_. Si solo puedes responder "le pongo un try/except", la entrevista terminó. Si puedes describir tu política de retries, tu presupuesto de latencia por llamada y tu eval reproducible con seeds, estás hablando el idioma de un equipo de producción.

## Enunciado

Construye un **asistente conversacional por CLI** (Python) que use function calling con tu proveedor de LLM preferido (Anthropic, OpenAI o un modelo local con soporte de tools) y exponga exactamente **3 herramientas**:

1. **`get_weather(city: str)`** — devuelve clima sintético desde un dataset local `data/weather.json` con mínimo 20 ciudades. Ejemplo de entrada del dataset:
   ```json
   {
     "medellin": { "temp_c": 24, "condition": "lluvia ligera", "humidity": 78 },
     "bogota": { "temp_c": 14, "condition": "nublado", "humidity": 65 }
   }
   ```
2. **`convert_currency(amount: float, from_currency: str, to_currency: str)`** — usa una tabla fija de tasas en `data/rates.json` con mínimo 8 monedas (USD, EUR, COP, MXN, BRL, ARS, GBP, JPY). Las tasas no necesitan ser reales, pero sí consistentes (la conversión debe ser verificable por el eval).
3. **`search_db(query: str)`** — búsqueda por substring/keywords sobre una "DB" local: un JSON o SQLite con mínimo 30 registros de un catálogo de productos (`id`, `name`, `category`, `price_usd`, `stock`). Devuelve hasta 5 resultados.

Las tres tools son funciones locales puras y rápidas. **La falla no viene de las tools: viene del harness de caos**, que envuelve cada tool y, con probabilidad configurable y seed fijo, inyecta uno de tres modos de fallo: timeout (duerme 3 s antes de lanzar excepción), error de servidor (excepción tipo 500), o JSON malformado (devuelve el JSON del resultado truncado a la mitad). Usa **este harness tal cual** — cópialo a `chaos.py`. No lo modifiques: el eval depende de su determinismo.

```python
# chaos.py — provisto por el enunciado. NO MODIFICAR.
import json, random, time

class ToolTimeout(Exception): ...
class ToolServerError(Exception): ...

class ChaosMonkey:
    def __init__(self, seed: int, p_fail: float = 0.35):
        self.rng = random.Random(seed)
        self.p_fail = p_fail

    def wrap(self, tool_fn):
        """Envuelve una tool. El resultado 'bueno' siempre es un string JSON."""
        def chaotic(*args, **kwargs):
            if self.rng.random() < self.p_fail:
                mode = self.rng.choice(("timeout", "http_500", "bad_json"))
                if mode == "timeout":
                    time.sleep(3.0)               # tu cliente debe cortar ANTES
                    raise ToolTimeout("upstream timeout after 3000ms")
                if mode == "http_500":
                    raise ToolServerError("500 Internal Server Error")
                if mode == "bad_json":
                    good = json.dumps(tool_fn(*args, **kwargs))
                    return good[: len(good) // 2]  # JSON truncado
            return json.dumps(tool_fn(*args, **kwargs))
        return chaotic
```

Tu asistente debe **sobrevivir siempre**: reintentar fallos transitorios con backoff exponencial, cortar timeouts antes de los 3 s del harness, detectar JSON truncado, y — cuando se agote el presupuesto de reintentos — responder al usuario con un mensaje útil en lugar de crashear o alucinar datos.

**Ejemplo de interacción esperada** (con caos activo):

```
Usuario: ¿Cuánto son 150 USD en COP y qué clima hace en Medellín?

[log] tool=convert_currency intento=1 → ToolServerError (500) | retry en 0.52s
[log] tool=convert_currency intento=2 → ok
[log] tool=get_weather      intento=1 → bad_json (parse error) | retry en 0.48s
[log] tool=get_weather      intento=2 → ToolTimeout (cortado a 2.0s) | retry en 1.04s
[log] tool=get_weather      intento=3 → ok

Asistente: 150 USD equivalen a 612,000 COP. En Medellín hay lluvia ligera,
24 °C y 78 % de humedad.
```

**Ejemplo de degradación elegante** (tool agotó sus 3 reintentos):

```
Asistente: 150 USD equivalen a 612,000 COP. Sin embargo, no pude consultar
el clima de Medellín: el servicio de clima falló repetidamente (timeouts).
¿Quieres que lo intente de nuevo?
```

Fíjate en lo que NO hace: no inventa el clima, no muestra un stacktrace, no se queda callado sobre la parte que sí funcionó.

Además, distingue **errores de dominio** de errores de infraestructura: si el usuario pide el clima de una ciudad que no existe en el dataset, la tool devuelve `{"error": "city_not_found"}` — eso **no se reintenta** (reintentar no lo va a arreglar); se le comunica al modelo para que responda con naturalidad.

## Requisitos

1. Asistente CLI multiturno (mínimo 2 turnos por conversación) con las 3 tools registradas vía function calling nativo del proveedor.
2. Las 3 tools leen de datasets locales versionados en el repo (`data/`); cero llamadas a APIs externas de datos.
3. Toda ejecución de tool pasa por una función `execute_with_retry()` propia que implementa: máximo **3 reintentos** (4 intentos totales), backoff exponencial con base **0.5 s**, factor **2** y jitter **±20 %** (0.5 → 1 → 2 s), y timeout duro de **2 s por intento** (debe cortar el `sleep(3.0)` del harness).
4. Clasificación de errores: `ToolTimeout`, `ToolServerError` y JSON no parseable → **reintetables**; errores de dominio devueltos por la tool (p. ej. `city_not_found`, moneda desconocida) → **no reintetables**, se pasan al modelo como resultado.
5. Cuando una tool agota sus reintentos, el agente devuelve al modelo un resultado de error estructurado (p. ej. `{"error": "tool_unavailable", "tool": "get_weather", "attempts": 4}`) y el modelo produce un mensaje al usuario que: (a) menciona qué no se pudo hacer, (b) entrega las partes de la respuesta que sí se obtuvieron, (c) no inventa datos.
6. Logging estructurado a stderr o archivo: una línea por intento con `tool`, `intento`, `resultado` (`ok`/tipo de fallo) y `delay` del próximo retry. Los delays reales deben ser medibles desde los logs.
7. Ninguna excepción no capturada llega al loop principal: el proceso jamás termina con stacktrace por culpa de una tool.
8. El programa acepta `--seed` y `--p-fail` por CLI para reproducir cualquier corrida exactamente.
9. Repo con `README` propio (cómo correr), `requirements.txt` o `pyproject.toml`, y el eval ejecutable con un solo comando (`python -m eval.run_eval`).

## Criterios de aceptación

- [ ] **20/20** conversaciones del eval terminan sin excepción no capturada (exit code 0), con `p_fail=0.35` y seeds 1–20.
- [ ] **≥ 16/20** conversaciones terminan con respuesta final **correcta**, verificada programáticamente contra los datasets (montos de conversión exactos, clima de la ciudad correcta, resultados de búsqueda que existen en la DB).
- [ ] En las conversaciones restantes (donde el caos ganó), el mensaje final menciona explícitamente la tool que falló y **no contiene datos inventados** (el eval verifica que ningún valor numérico del mensaje contradiga los datasets).
- [ ] Ningún intento de tool excede **2.1 s** de duración (verificable en logs) — es decir, el timeout corta el modo `timeout` del harness.
- [ ] Los delays entre reintentos siguen la secuencia 0.5 / 1 / 2 s con ±20 % de tolerancia, medidos desde los timestamps de los logs.
- [ ] Ninguna llamada de tool registra más de **4 intentos**.
- [ ] Un error de dominio (`city_not_found` con una ciudad inventada en la conversación de prueba) genera **exactamente 1 intento** — cero reintentos.
- [ ] Dos corridas del eval con el mismo seed producen los mismos modos de fallo inyectados (determinismo del harness intacto).
- [ ] `json.loads` sobre un resultado truncado nunca propaga `JSONDecodeError` fuera de `execute_with_retry()`.
- [ ] El eval completo corre con un solo comando y termina en < 10 minutos.

## Cómo se evalúa

El coach correrá tu eval tal cual está en el repo. La estructura esperada: un archivo `eval/conversations.json` con 20 casos (cada uno con sus turnos de usuario, el seed, y el resultado esperado verificable) y un runner que produce un reporte agregado. Esqueleto sugerido — esto es la **estructura del eval, no la solución**:

```python
# eval/run_eval.py — estructura sugerida
import json
from chaos import ChaosMonkey
from agent import Agent  # tu implementación

CASES = json.load(open("eval/conversations.json"))  # 20 casos, seeds 1-20

def run_case(case: dict) -> dict:
    chaos = ChaosMonkey(seed=case["seed"], p_fail=0.35)
    agent = Agent(chaos=chaos)
    try:
        transcript = agent.run(case["turns"])   # turnos de usuario scripteados
    except Exception as exc:                     # esto NO debería pasar nunca
        return {"id": case["id"], "crashed": True, "error": repr(exc)}
    return {
        "id": case["id"],
        "crashed": False,
        "answer_ok": check_answer(case["expected"], transcript.final_message),
        "graceful": check_no_hallucinated_numbers(transcript.final_message),
        "max_attempts": max(transcript.metrics["attempts_per_call"]),
        "backoff_ok": check_backoff_timing(transcript.metrics["retry_delays"]),
        "timeout_ok": max(transcript.metrics["attempt_durations"]) <= 2.1,
    }

def main():
    results = [run_case(c) for c in CASES]
    crashed = sum(r["crashed"] for r in results)
    correct = sum(r.get("answer_ok", False) for r in results)
    print(f"crashes: {crashed}/20 (objetivo: 0)")
    print(f"respuestas correctas: {correct}/20 (objetivo: >= 16)")
    json.dump(results, open("eval/report.json", "w"), indent=2)

if __name__ == "__main__":
    main()
```

`check_answer` debe ser programático (comparar contra el dataset), no un LLM-judge: los datos son sintéticos y conocidos, así que la verificación es exacta. Diseña los 20 casos para cubrir: las 3 tools individualmente, combinaciones de 2–3 tools en un turno, multiturno con contexto ("¿y en EUR?"), errores de dominio, y al menos 2 casos con `p_fail=0.6` para forzar agotamiento de reintentos.

## Pistas

<details>
<summary>Pista 1</summary>

Separa dos capas que los principiantes mezclan: la **capa de decisión** (el LLM decide qué tool llamar y con qué argumentos) y la **capa de ejecución** (tu código Python ejecuta la tool). Los retries, timeouts y parseo de JSON viven 100 % en la capa de ejecución — el modelo nunca debería "ver" un timeout transitorio que se resolvió al segundo intento. Si tu primer instinto fue pedirle al modelo en el system prompt que "reintente si falla", estás resolviendo el problema en la capa equivocada.

</details>

<details>
<summary>Pista 2</summary>

Estructura de `execute_with_retry`: clasifica primero, reintenta después.

```
para intento en 1..4:
    resultado = correr tool_fn con deadline de 2s   # ThreadPoolExecutor + future.result(timeout=2.0)
    si lanzó ToolTimeout o ToolServerError → fallo reintetable
    si retornó string → intenta json.loads:
        si parsea y trae {"error": ...} de dominio → retornar tal cual (NO reintentar)
        si parsea ok → retornar
        si no parsea (JSONDecodeError) → fallo reintetable
    si fue el intento 4 → retornar {"error": "tool_unavailable", ...}
    dormir base * 2**(intento-1) * uniform(0.8, 1.2)
```

Ojo con el timeout: `time.sleep(3.0)` del harness no es interrumpible con `signal` de forma portable; correr la tool en un `ThreadPoolExecutor` y usar `future.result(timeout=2.0)` es el camino simple.

</details>

<details>
<summary>Pista 3</summary>

Para la degradación elegante: cuando `execute_with_retry` agota intentos, **no lances excepción** — devuelve al modelo, como contenido del tool result, algo como `{"error": "tool_unavailable", "tool": "get_weather", "attempts": 4, "last_error": "timeout"}`, y agrega en el system prompt una regla explícita: _"si una tool devuelve error: tool_unavailable, informa al usuario qué no pudiste consultar, entrega lo que sí obtuviste y nunca estimes ni inventes el dato faltante"_. Para el determinismo del eval: el `ChaosMonkey` consume su RNG una vez por llamada de tool, así que la secuencia de fallos depende solo del seed y del **orden de llamadas** — scriptea los turnos de usuario (nada de input interactivo en el eval) y fija `temperature=0` para minimizar variación en el orden de tool calls. Acepta que 2–3 casos puedan variar entre corridas por no determinismo del modelo: por eso el umbral es 16/20 y no 20/20.

</details>

## Bonus

1. **Circuit breaker**: si una tool acumula 5 fallos consecutivos a lo largo de la conversación, "abre el circuito" 30 s — las llamadas siguientes fallan rápido con `circuit_open` sin gastar reintentos ni latencia, y el modelo informa que el servicio está caído. Demuéstralo con un caso de eval con `p_fail=0.9`.
2. **Métricas agregadas**: al final de cada corrida del eval, imprime por tool: tasa de éxito al primer intento, distribución de intentos (histograma 1/2/3/4), latencia p50/p95 por llamada, y porcentaje de conversaciones degradadas. Es exactamente el dashboard que pedirías en producción.

## Qué demuestra en entrevista

- _"Construí un agente con function calling y lo endurecí contra un harness de caos que inyectaba timeouts, 500s y JSON corrupto de forma determinista. Implementé retries con backoff exponencial y jitter, timeouts duros por intento, y clasificación de errores reintetables vs. de dominio — la política de resiliencia vive en la capa de ejecución, no en el prompt."_
- _"Lo evalué con 20 conversaciones scripteadas con seeds fijos y verificación programática contra los datasets: 0 crashes, ≥80 % de respuestas correctas bajo 35 % de fallo inyectado, y verificación de los tiempos de backoff desde los logs."_ — esto demuestra que sabes testear sistemas no deterministas, una pregunta casi garantizada.
- _"La parte más difícil fue la degradación elegante: lograr que el modelo reporte honestamente qué tool falló sin alucinar el dato faltante — lo resolví devolviendo errores estructurados como tool results más una regla explícita de system prompt, y lo verifico en el eval chequeando que ningún número de la respuesta contradiga el dataset."_

## Entregable

**En el repo** (carpeta `reto-02-tool-use-robusto/` en tu repo del gym, o repo propio enlazado):

- `agent.py` (o paquete equivalente) con el loop del asistente y `execute_with_retry()`.
- `chaos.py` sin modificar, `data/` con los 3 datasets, `eval/conversations.json` con los 20 casos y `eval/run_eval.py`.
- `eval/report.json` generado por tu última corrida completa.
- `README.md` propio: comando para chatear, comando para correr el eval, y una sección "Decisiones" (máx. 15 líneas) justificando tu política de retries y timeouts.

**En la sesión de revisión (Sesión 4)**: demo en vivo de 5 minutos — una conversación con `p_fail=0.6` mostrando los logs de retries en tiempo real, seguida de la corrida del eval delante del coach. Trae preparada la respuesta a: _"¿por qué 3 reintentos y no 5, y por qué 2 s de timeout y no 500 ms?"_ — no hay respuesta única correcta, pero sí tiene que haber un razonamiento de presupuesto de latencia end-to-end.
