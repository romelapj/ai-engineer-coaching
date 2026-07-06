# Tracker de Progreso — Programa de Coaching AI Engineer (16 semanas)

Este documento es el registro vivo del programa. **Se actualiza al final de cada sesión semanal**, entre el coach y el alumno:

1. Marcar el estado del reto de la semana en la tabla principal (⬜ → 🟡 → ✅).
2. Registrar el score de evals cuando el reto lo incluya.
3. Anotar feedback, bloqueos o acuerdos en la columna **Notas**.
4. Reemplazar las metas de la sección **Semana actual** con las de la próxima semana.
5. Si hubo mock interview, agregar fila en **Registro de mocks**.
6. Capturar decisiones técnicas o deuda pendiente en **Decisiones y deuda**.

**Leyenda de estado:** ⬜ no iniciado · 🟡 en progreso · ✅ completado

> **Bloque Pre-Fase 0.5 (condicional):** las filas `N00`–`N05` y la evaluación de fluidez solo aplican si el diagnóstico disparó la **regla #1** (Parte A ≤ 2). Es un curso de **fundamentos de Python** de cadencia **diaria** (no semanal); se completa antes de la Semana 1. La salida se mide por **fluidez** (capstone + checklist), no por re-tomar el examen; el gate de promoción del programa lo administra el coach aparte. Si no aplica, ignora ese bloque.

---

## Semana actual

> Actualizar al cierre de cada sesión. Las metas deben ser concretas y verificables.

**Semana:** _
**Sesión:** _

### Metas de la semana

- [ ] Meta 1: \_
- [ ] Meta 2: \_
- [ ] Meta 3: \_

---

## Tabla principal

| Semana        | Sesión                                                   | Reto asignado                                                         | Estado | Score de evals | Notas                                                                                                                       |
| ------------- | -------------------------------------------------------- | --------------------------------------------------------------------- | ------ | -------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Pre-Sem 1     | N00 — Python y su modelo mental                          | kata-00-smoke-test-entorno                                            | ⬜     | pytest ✓       | _Bloque condicional (regla #1): solo si Parte A ≤ 2. Cadencia diaria. Fundamentos de Python._                               |
| Pre-Sem 1     | N01 — Tipos, valores y operadores                        | kata-01-conversor-tipado                                              | ⬜     | pytest ✓       |                                                                                                                             |
| Pre-Sem 1     | N02 — Estructuras de datos                               | kata-02-frecuencia-de-palabras                                        | ⬜     | pytest ✓       |                                                                                                                             |
| Pre-Sem 2     | N03 — Control de flujo y funciones                       | kata-03-transformar-coleccion-funciones-puras                         | ⬜     | pytest ✓       |                                                                                                                             |
| Pre-Sem 2     | N04 — Strings, archivos y errores                        | kata-04-csv-a-json-pipeline + kata-05-errores-robustos                | ⬜     | pytest ✓       |                                                                                                                             |
| Pre-Sem 2     | N05 — Pythonic, organización y herramientas              | kata-06-dataclass-de-dominio + kata-07-capstone-a-eleccion            | ⬜     | pytest ✓       |                                                                                                                             |
| Pre-Sem 2     | **Evaluación de fluidez** (capstone + checklist)         | Capstone a elección + rúbrica de fluidez (`coach/rubrica-prefase.md`) | ⬜     | Fluidez 1–5    | _Salida = fluidez en Python, no re-tomar el examen. Gate del programa (re-toma Parte A) lo corre el coach aparte → Fase 1._ |
| Semana 1      | S00 — Kickoff y Diagnóstico                              | Completar el assessment de diagnóstico (ver coach/diagnostic)         | ⬜     | —              |                                                                                                                             |
| Semana 2      | S01 — Fundamentos de LLMs                                | Script que tokenice 10 textos y compare costos entre 3 modelos        | ⬜     | —              |                                                                                                                             |
| Semana 3      | S02 — APIs de LLM y Prompt Engineering                   | reto-01-extractor-estructurado                                        | ⬜     | —              |                                                                                                                             |
| Semana 4      | S03 — Tool Use, Structured Outputs y Robustez            | reto-02-tool-use-robusto                                              | ⬜     | —              |                                                                                                                             |
| Semana 5      | S04 — RAG I — Embeddings, Chunking y Vector Stores       | reto-03-rag-basico                                                    | ⬜     | —              |                                                                                                                             |
| Semana 6      | S05 — RAG II — Retrieval Híbrido, Reranking y Evaluación | reto-04-retrieval-tuning                                              | ⬜     | —              |                                                                                                                             |
| Semana 7      | S06 — Agentes I — El Loop Agéntico y Herramientas        | reto-05-agente-from-scratch                                           | ⬜     | —              |                                                                                                                             |
| Semana 8      | S07 — Agentes II — Memoria, Multi-agente y MCP           | reto-06-agente-con-memoria                                            | ⬜     | —              |                                                                                                                             |
| Semana 9      | S08 — Evals — Medir Sistemas con LLMs                    | reto-07-suite-de-evals                                                | ⬜     | —              |                                                                                                                             |
| Semana 10     | S09 — Producción I — Observabilidad, Costos y Latencia   | reto-08-hardening-produccion                                          | ⬜     | —              |                                                                                                                             |
| Semana 11     | S10 — Producción II — Guardrails, Seguridad y Fallbacks  | reto-08-hardening-produccion                                          | ⬜     | —              |                                                                                                                             |
| Semana 12     | S11 — Hardening Final y Demo Day                         | Demo de 15 min grabada + README final + lista de 5 preguntas          | ⬜     | —              |                                                                                                                             |
| Semanas 13-14 | S12 — System Design de Sistemas con LLMs                 | Resolver 2 system designs por escrito (45 min cada uno, con rúbrica)  | ⬜     | —              |                                                                                                                             |
| Semanas 15-16 | S13 — Mock Interviews, Portfolio y Estrategia            | Mock interview completa grabada (usar las rúbricas del coach)         | ⬜     | —              |                                                                                                                             |

---

## Registro de mocks

> Una fila por cada mock interview realizada. El puntaje por dimensión sigue la rúbrica del coach (p. ej. comunicación / diseño / profundidad técnica / trade-offs, 1-5 cada una).

| Fecha | Tipo | Caso | Puntaje por dimensión | Feedback clave |
| ----- | ---- | ---- | --------------------- | -------------- |
|       |      |      |                       |                |

---

## Decisiones y deuda

> Decisiones técnicas tomadas durante el programa (con su porqué) y deuda pendiente que no bloquea la semana pero hay que retomar.

- _(vacío por ahora — agregar como: `[Semana N] Decisión/Deuda — contexto y siguiente paso`)_
- _(plantilla Pre-Fase, si aplicó: `[Pre-Fase] Fluidez al cierre: nivel __/5 → decisión __ (promover a Fase 1 / extender 2 semanas). Capstone elegido: __. Fortalezas/huecos: __.`)_
