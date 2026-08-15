# 🏋️ Reto 07: Suite de evals

| Metadato                            | Valor                                                                                                                                              |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Fase**                            | Fase 2                                                                                                                                             |
| **Sesión en que se asigna**         | Sesión 8                                                                                                                                           |
| **Tiempo estimado**                 | 10–14 horas (repartidas en la semana)                                                                                                              |
| **Skill de entrevista que entrena** | Evaluación sistemática de sistemas LLM: responder con evidencia a "¿cómo sabes que tu sistema funciona y que no lo rompiste con el último cambio?" |

---

## Contexto

Cualquiera puede pegar un prompt en un script y hacer una demo que funciona una vez. Lo que separa a un dev que "juega con LLMs" de un AI engineer contratable es la capacidad de **medir** el comportamiento de un sistema no determinista y de defender cambios con números en lugar de con "se siente mejor". Las empresas que ya tienen LLMs en producción han aprendido (a golpes) que sin evals cada deploy es una apuesta: un cambio de prompt que arregla un caso rompe otros tres y nadie se entera hasta que un cliente se queja.

Este reto convierte el RAG (retos 3–4) o el agente (retos 5–6) que ya construiste en un sistema **medible**: una suite de 30+ casos de evaluación que corre en CI, produce un score reproducible y bloquea regresiones. Después construirás un cambio real al sistema y demostrarás, con el antes y el después del score, que mejoró. Ese ciclo, baseline → cambio → evidencia, es exactamente el flujo de trabajo diario de un AI engineer.

En entrevista, esto responde directamente preguntas como: _"How do you evaluate LLM outputs?"_, _"How do you prevent prompt regressions?"_, _"When do you use LLM-as-judge vs. programmatic checks, and how do you trust the judge?"_. La mayoría de candidatos balbucea generalidades sobre "human review" o "vibes". Tú vas a poder abrir un repo con un workflow de GitHub Actions, un reporte de score por PR y un experimento documentado. Por eso esta es la pieza más valiosa del portfolio del programa.

---

## Enunciado

Construye una **suite de evaluación automatizada** para el sistema que elijas (el RAG de los retos 3–4 o el agente de los retos 5–6) y conéctala a CI. La suite debe tener tres capas:

### 1. Dataset de evaluación (30+ casos)

Un archivo versionado en el repo (recomendado: `evals/dataset.jsonl`, un caso por línea) donde cada caso tiene como mínimo:

```json
{
  "id": "rag-013",
  "category": "factual_with_source",
  "input": "¿Cuál es el límite de reintentos que recomienda el documento de arquitectura?",
  "expected": {
    "must_contain": ["3 reintentos", "backoff exponencial"],
    "must_cite_doc": "architecture-retry-policy.md",
    "must_not_contain": ["no tengo información"]
  },
  "grader": "programmatic"
}
```

```json
{
  "id": "rag-027",
  "category": "out_of_scope",
  "input": "¿Quién va a ganar la liga este año?",
  "expected": {
    "behavior": "Rechaza educadamente y aclara que solo responde sobre la documentación indexada. No inventa una respuesta."
  },
  "grader": "llm_judge",
  "rubric": "abstencion"
}
```

Los 30+ casos deben cubrir, como mínimo, estas categorías (con la cantidad mínima indicada):

| Categoría                                                  | Mín. casos | Qué prueba                                                 |
| ---------------------------------------------------------- | ---------- | ---------------------------------------------------------- |
| `happy_path`                                               | 8          | Preguntas/tareas típicas que el sistema debe resolver bien |
| `factual_with_source` (RAG) o `tool_use_correcto` (agente) | 6          | La respuesta usa la fuente/herramienta correcta            |
| `out_of_scope` / abstención                                | 5          | El sistema rechaza lo que no sabe en vez de alucinar       |
| `adversarial`                                              | 4          | Prompt injection, preguntas capciosas, premisas falsas     |
| `edge_cases`                                               | 4          | Entradas vacías, larguísimas, en otro idioma, con typos    |
| `regression`                                               | 3          | Casos que fallaron en retos anteriores y ya arreglaste     |

**Datasets sugeridos como base** (elige según tu sistema): tus propios documentos del RAG del reto 3 (genera preguntas sintéticas con un LLM y **revísalas a mano**; las que no revisaste no cuentan); para abstención y adversarial, inspírate en los patrones de TruthfulQA y de los repos públicos de prompt-injection (p. ej. los payloads clásicos de "ignore previous instructions"). No copies datasets enteros: el valor está en que los casos sean de **tu** dominio.

### 2. Dos tipos de grader

- **Asserts programáticos** (mínimo 15 casos): checks deterministas en Python: `must_contain`, `must_not_contain`, regex, JSON schema válido, cita al documento correcto, latencia < N segundos, herramienta correcta invocada con argumentos correctos.
- **LLM-as-judge** (mínimo 10 casos): un modelo evaluador con **rúbrica explícita versionada en el repo** (`evals/rubrics/*.md`). Cada rúbrica define la escala (p. ej. 1–5 o PASS/FAIL), criterios por nivel, y 2 ejemplos calibrados (uno que pasa, uno que falla). El judge debe devolver JSON estructurado (`{"score": ..., "reasoning": ...}`), no prosa libre.

Además: debes **calibrar el judge** contra tu propio criterio. Etiqueta a mano 10 outputs, pásalos por el judge y reporta el % de acuerdo. Si el acuerdo es < 80 %, ajusta la rúbrica y repite.

### 3. Integración a CI

Un workflow de GitHub Actions (`.github/workflows/evals.yml`) que:

- Corre la suite completa en cada PR al branch principal.
- Publica el score como comentario en el PR (o como job summary): score global, score por categoría, y lista de casos que fallaron con su `id`.
- Falla el check si el score global cae por debajo de un umbral configurable (define el umbral a partir de tu baseline, p. ej. `baseline - 5 puntos`).
- Maneja el costo: cachea respuestas cuando el input no cambió, o corre el subset programático siempre y el subset judge solo con un label/comando.

### 4. El experimento (entregable estrella)

1. Corre la suite contra tu sistema actual → documenta el **score baseline** en `evals/BASELINE.md` (score global, por categoría, fecha, commit hash, modelo y versión usados).
2. Formula una hipótesis de mejora (p. ej. "reescribir el system prompt para forzar citación", "subir top-k de 3 a 5", "agregar un paso de reranking").
3. Implementa el cambio en un PR.
4. Demuestra con el reporte de CI que el score subió (y en qué categorías), y documenta el resultado en `evals/EXPERIMENT-01.md`: hipótesis, cambio, score antes/después, casos que pasaron a verde, casos que (si los hay) pasaron a rojo, y conclusión.

---

## Requisitos

1. Dataset versionado en el repo con **≥ 30 casos** en formato estructurado (JSONL o YAML), cada caso con `id` único, `category`, `input`, criterio de éxito y tipo de grader.
2. Las 6 categorías de la tabla del enunciado están presentes con su mínimo de casos.
3. **≥ 15 casos** evaluados con asserts programáticos puros (sin LLM en el grading).
4. **≥ 10 casos** evaluados con LLM-as-judge, con rúbrica explícita en archivos versionados y output JSON estructurado del judge.
5. Calibración del judge documentada: 10 outputs etiquetados a mano vs. veredicto del judge, con % de acuerdo reportado y **≥ 80 %** de acuerdo final.
6. Runner ejecutable con un solo comando (`make eval` o `python -m evals.run`) que imprime score global, score por categoría y casos fallidos, y escribe un reporte JSON (`evals/reports/<timestamp>.json`).
7. El runner es **determinista en su estructura**: `temperature=0` (o el equivalente) en el judge, seeds fijos donde aplique, y los casos programáticos producen el mismo resultado en dos corridas consecutivas.
8. Workflow de GitHub Actions que corre en cada PR, reporta el score en el PR y falla si el score cae bajo el umbral definido.
9. `evals/BASELINE.md` con el score baseline completo (global + por categoría + commit + modelo + fecha).
10. Un PR mergeado con un cambio al sistema cuyo reporte de CI demuestra mejora del score, documentado en `evals/EXPERIMENT-01.md`.
11. Control de costos documentado en el README de `evals/`: costo estimado por corrida completa en USD y la estrategia para no quemar presupuesto en CI (cache, subset, triggers).

---

## Criterios de aceptación

- [ ] `evals/dataset.jsonl` existe con ≥ 30 casos, todos con `id` único y `category` válida (verificable con un script de validación de schema incluido en el repo).
- [ ] Las 6 categorías cumplen su mínimo: 8 happy path, 6 factual/tool-use, 5 abstención, 4 adversarial, 4 edge cases, 3 regression.
- [ ] ≥ 15 casos con grader programático y ≥ 10 con LLM-as-judge.
- [ ] Existen ≥ 2 rúbricas en `evals/rubrics/`, cada una con escala definida, criterios por nivel y ≥ 2 ejemplos calibrados.
- [ ] Tabla de calibración del judge con 10 filas (output, etiqueta humana, veredicto judge) y acuerdo ≥ 80 %.
- [ ] `make eval` (o equivalente de un solo comando) corre de punta a punta en < 10 minutos y escribe el reporte JSON.
- [ ] Dos corridas consecutivas del subset programático dan exactamente el mismo resultado.
- [ ] El workflow de GitHub Actions corrió en ≥ 2 PRs reales (visible en la pestaña Actions) y el comentario/summary de score es legible: global, por categoría, fallidos.
- [ ] Existe al menos 1 PR donde el check de evals **falló** por regresión (real o provocada a propósito para probar el gate): captura o link en el entregable.
- [ ] `evals/BASELINE.md` documenta el baseline con commit hash, modelo, fecha y score por categoría.
- [ ] `evals/EXPERIMENT-01.md` documenta un cambio con mejora medida de **≥ 5 puntos porcentuales** en el score global o **≥ 15 puntos** en una categoría, con links a los dos reportes de CI (antes/después).
- [ ] El costo por corrida completa está documentado y es < 1 USD (si supera eso, documenta la estrategia de subset/cache que lo baja).

---

## Cómo se evalúa

El coach clonará tu repo, correrá `make eval` y revisará la pestaña Actions. La revisión sigue este orden: (1) ¿el runner corre con un comando?, (2) ¿el dataset cubre las categorías y los casos son de verdad de tu dominio?, (3) ¿las rúbricas del judge son específicas o genéricas tipo "evalúa si la respuesta es buena"?, (4) ¿la calibración del judge es honesta?, (5) ¿el experimento demuestra causalidad (mismo dataset, solo cambió el sistema)?

La estructura esperada del harness es aproximadamente esta (estructura, no solución):

```python
# evals/run.py: esqueleto del runner
import json
from dataclasses import dataclass
from pathlib import Path

@dataclass
class EvalCase:
    id: str
    category: str
    input: str
    expected: dict
    grader: str          # "programmatic" | "llm_judge"
    rubric: str | None = None

@dataclass
class CaseResult:
    case_id: str
    category: str
    passed: bool
    score: float         # 0.0–1.0 (binario en programmatic, normalizado en judge)
    details: str         # qué assert falló / reasoning del judge

def load_dataset(path: Path) -> list[EvalCase]:
    return [EvalCase(**json.loads(line)) for line in path.read_text().splitlines() if line.strip()]

def grade_programmatic(case: EvalCase, output: str, meta: dict) -> CaseResult:
    # asserts deterministas: must_contain, must_not_contain, cita correcta,
    # JSON schema, herramienta invocada, latencia...
    ...

def grade_with_judge(case: EvalCase, output: str, rubric_text: str) -> CaseResult:
    # llamada al modelo judge con temperature=0, rúbrica + ejemplos calibrados,
    # respuesta forzada a JSON: {"score": int, "reasoning": str}
    ...

def run_suite(dataset: Path, report_dir: Path) -> dict:
    results: list[CaseResult] = []
    for case in load_dataset(dataset):
        output, meta = call_system_under_test(case.input)   # tu RAG o agente
        results.append(dispatch_grader(case, output, meta))
    report = aggregate(results)   # score global, por categoría, lista de fallidos
    (report_dir / "latest.json").write_text(json.dumps(report, indent=2))
    return report

if __name__ == "__main__":
    report = run_suite(Path("evals/dataset.jsonl"), Path("evals/reports"))
    print(format_summary(report))
    raise SystemExit(0 if report["global_score"] >= report["threshold"] else 1)
```

El exit code distinto de cero es lo que hace que GitHub Actions marque el check en rojo; no necesitas nada más sofisticado para el gate.

---

## Pistas

<details><summary>Pista 1</summary>

No empieces por el código del runner: empieza por escribir 10 casos a mano contra tu sistema actual y córrelos manualmente. Vas a descubrir que la mitad de tus "criterios de éxito" son ambiguos ("la respuesta debe ser buena") y que necesitas reescribirlos como algo verificable ("debe mencionar X y citar el doc Y"). Escribir buenos casos ES el reto; el runner es plomería. Para generar volumen, usa un LLM para proponer preguntas a partir de tus documentos, pero etiqueta tú la respuesta esperada; un dataset sintético sin revisión humana se nota a kilómetros y el coach lo va a detectar.

</details>

<details><summary>Pista 2</summary>

Para el judge: el error clásico es darle una instrucción genérica ("¿es correcta esta respuesta? 1-5"). Eso produce scores inflados y ruidosos. Estructura el prompt del judge así: (1) rol y tarea, (2) la rúbrica completa con descripción de cada nivel, (3) 1 ejemplo de output que merece score alto y 1 que merece score bajo, con su justificación, (4) el caso a evaluar, (5) instrucción de responder SOLO JSON. Usa `temperature=0` y un modelo distinto (o al menos una llamada separada sin contexto compartido) al que genera las respuestas. Para la calibración: si tu acuerdo humano-judge da bajo, casi siempre el problema es que la rúbrica no distingue el nivel 3 del 4; colapsa a PASS/FAIL antes que inventar granularidad que ni tú puedes juzgar.

</details>

<details><summary>Pista 3</summary>

Para CI sin quemar dinero: separa el workflow en dos jobs. Job 1 (`evals-fast`): corre siempre, solo casos programáticos contra respuestas del sistema. Necesitas la API key del modelo del sistema pero no del judge; típicamente < 0.10 USD. Job 2 (`evals-judge`): corre solo cuando el PR tiene el label `run-full-evals` (condición `if: contains(github.event.pull_request.labels.*.name, 'run-full-evals')`). Guarda la API key como secret del repo, pásala por `env:`, y publica el resumen con `$GITHUB_STEP_SUMMARY` (más simple que un bot de comentarios: `python -m evals.run --format md >> "$GITHUB_STEP_SUMMARY"`). Para el experimento, la mejora más fácil de demostrar en un RAG suele ser atacar la categoría de abstención: agrega al system prompt una instrucción explícita de rechazar cuando los chunks recuperados no contienen la respuesta, con umbral de similitud: casi siempre mueve 3-5 casos de rojo a verde sin tocar el retrieval.

</details>

---

## Bonus

1. **Eval de regresión histórica con tracking de tendencia**: persiste los reportes de cada corrida en el repo (o en una rama `eval-reports`) y genera una gráfica de score vs. tiempo (un script con matplotlib basta). Poder mostrar "así evolucionó el score del sistema durante 3 semanas" en una entrevista es oro.
2. **Pairwise comparison para el judge**: en lugar de score absoluto, implementa un modo donde el judge compara la respuesta del sistema actual vs. la del candidato (A/B, con posiciones aleatorizadas para evitar position bias) y reporta win-rate. Documenta cuándo preferirías pairwise sobre score absoluto.

---

## Qué demuestra en entrevista

- _"I built an eval suite with 30+ cases: programmatic asserts for deterministic checks and an LLM judge with an explicit, versioned rubric for subjective ones. I calibrated the judge against my own labels and got 85% agreement before trusting it."_. Demuestra que sabes que un judge sin calibrar es ruido, algo que la mayoría de candidatos ignora.
- _"Evals run on every PR in GitHub Actions; the check fails if the score drops below baseline minus five points. I caught a real regression when a prompt change improved citations but broke out-of-scope refusals."_. Demuestra mentalidad de ingeniería: los LLMs se testean como cualquier otro sistema, con gates en CI.
- _"My baseline was 71% global; I hypothesized that explicit abstention instructions would fix the hallucination category, shipped it, and the suite confirmed +12 points in that category with no regressions elsewhere."_. Demuestra el ciclo hipótesis → cambio → evidencia, que es la habilidad central del rol.

---

## Entregable

**En el repo** (el mismo del RAG o del agente, en una carpeta `evals/`):

- `evals/dataset.jsonl`: los 30+ casos.
- `evals/rubrics/`: rúbricas del judge con ejemplos calibrados.
- `evals/run.py` (o módulo equivalente) + `Makefile` con target `eval`.
- `evals/reports/`: al menos el reporte baseline y el del experimento.
- `evals/BASELINE.md` y `evals/EXPERIMENT-01.md`.
- `evals/README.md`: cómo correr la suite, costo por corrida, estrategia de CI, tabla de calibración del judge.
- `.github/workflows/evals.yml`: con historial visible de ≥ 2 corridas en PRs y ≥ 1 corrida fallida por el gate.

**En la sesión de revisión** (15 minutos):

1. Demo en vivo: `make eval` corriendo de punta a punta (puedes usar el subset programático si la corrida completa tarda).
2. Abre el PR del experimento y recorre la evidencia: score antes/después en los checks de CI.
3. Trae preparada la respuesta a estas tres preguntas, que el coach va a hacer sí o sí: _¿qué caso te costó más definir y por qué?_, _¿en qué casos NO confiarías en tu judge?_, y _¿qué medirías distinto si este sistema estuviera en producción con usuarios reales?_
