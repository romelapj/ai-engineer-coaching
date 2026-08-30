# AI Engineer Coaching

Programa de coaching 1:1 de **16 semanas** para transicionar de developer a **AI Engineer**: sesiones diarias de 30 min + un reto práctico semanal que termina siendo el portfolio para entrevistas.

## 🌐 Sitio del programa

**Las presentaciones se ven aquí:** https://romelapj.github.io/ai-engineer-coaching/

El portal enlaza las 14 sesiones, el AI Gym, la biblioteca y el tracker de progreso.

## Estructura

- **`index.html`**: portal de entrada del programa.
- **`sesiones/`**: 14 presentaciones HTML (una por sesión) + 6 de la Pre-Fase 0.5 (`prefase-0X`), navegables con las flechas ← →. Cuentan el **porqué**: comparaciones, trade-offs, idea fuerza.
- **`talleres/`**: los **builds**, en pasos de 30 minutos diarios, con el código completo copiable y su salida esperada. Se generan desde el código ejecutable que vive en `talleres/<sesion>/codigo/`, así que lo que se muestra siempre es lo que corre.
- **`gym/`**: el AI Gym, con 8 retos prácticos + 8 katas de nivelación (`kata-0X`), criterios de aceptación medibles, pistas escalonadas y harness de evaluación.
- **`biblioteca/`**: el **club de lectura** (libros, con su plan por tramos y sus
  subrayados) y la **biblioteca** de artículos, noticias, videos y podcasts. Cada
  pieza lleva de qué va, qué se rescata y dónde se queda corta. Se generan desde
  `biblioteca/catalogo.yaml`.
- **`docs/`**: la bitácora, con el análisis, las decisiones de formato y el historial de versiones del curso.
- **`progress.md`**: tracker semanal del alumno y el coach.

### Trabajar con los talleres

```bash
python talleres/build.py             # genera talleres/<sesion>.html desde el código real
python talleres/verificar.py         # comprueba que no queden huecos en ningún taller
python biblioteca/build.py           # genera la biblioteca y el club de lectura
python talleres/enlaces.py           # comprueba que ningún enlace relativo quedó roto
```

Cómo escribir uno: [`docs/04-como-crear-un-taller.md`](docs/04-como-crear-un-taller.md).

> Las presentaciones son HTML interactivo (se ven mejor en el sitio de Pages).
> Los enunciados del gym y el tracker son markdown (se ven mejor navegando este repo en GitHub, que los renderiza).

## Las 4 fases (+ nivelación opcional)

| Fase                 | Semanas       | Foco                                                                                  |
| -------------------- | ------------- | ------------------------------------------------------------------------------------- |
| Pre-Fase 0.5: Python | Pre-Sem A-B\* | Fundamentos de Python (modelo de datos, estructuras, funciones, errores, lo Pythonic) |
| 0: Diagnóstico       | 1             | Calibrar el punto de partida                                                          |
| 1: Fundamentos LLM   | 2-4           | Tokens, prompting, tool use, robustez                                                 |
| 2: Patrones          | 5-9           | RAG, agentes, evals                                                                   |
| 3: Producción        | 10-12         | Observabilidad, seguridad, hardening                                                  |
| 4: Entrevistas       | 13-16         | System design, mocks, portfolio                                                       |

\* **Pre-Fase 0.5 es condicional:** el programa abre con un diagnóstico (Fase 0) que, si la Parte A ≤ 2 (regla #1), activa 2 semanas de **fundamentos de Python** **antes** de Fase 1 (extendiendo el programa a ~18 semanas para ese coachee). Es un curso de Python para devs que vienen de otro lenguaje pero no dominan Python: 6 decks (`prefase-0X`) + 8 katas diarias y variadas (`kata-0X`) con harness `pytest`, que cierran con un capstone a elección y una rúbrica de fluidez. Enseña el lenguaje de verdad, no a aprobar el diagnóstico: aprobar el gate del programa sale como consecuencia de la fluidez. Si la Parte A ≥ 3, se ignora y se arranca directo en Fase 1.

## Metodología

Construir > consumir (máx. 20% en cursos/videos), evals-first (todo se mide), cadencia diaria de 30 minutos, y el portfolio sale del gym.

Una regla de formato, que está detrás de todo lo demás: **el código que ve el alumno es el código que corre**, nunca una copia. Por qué, en [`docs/`](docs/README.md).

---

El kit del coach (assessment de diagnóstico, rúbricas de mocks, guías) se mantiene en un repositorio **privado** aparte para no exponer las respuestas a los alumnos.
