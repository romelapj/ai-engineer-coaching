#!/usr/bin/env python3
"""
Generador de talleres.

Un taller es una página HTML de pasos donde el código cuenta la historia.
El código NO se escribe en la página: se LEE de los archivos ejecutables que
viven en talleres/<id>/codigo/. La página es una vista de ese código, nunca
una copia. Esa es toda la idea: si el archivo corre, la página corre.

Uso:
    python talleres/build.py              # genera todos los talleres
    python talleres/build.py sesion-04    # genera uno
    python talleres/build.py --estricto   # falla si algún archivo tiene huecos

Entrada:  talleres/<id>/taller.yaml  +  talleres/<id>/codigo/**  +  salidas/**
Salida:   talleres/<id>.html
"""

import html
import re
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent
REPO = RAIZ.parent

# ---------------------------------------------------------------------------
# Resaltado de sintaxis
# ---------------------------------------------------------------------------
# Produce las mismas clases que ya usan los decks (.c .k .s .f) para que el
# taller y el deck se vean como la misma plataforma.

PALABRAS_CLAVE = (
    "False None True and as assert async await break class continue def del "
    "elif else except finally for from global if import in is lambda nonlocal "
    "not or pass raise return try while with yield"
).split()

_TOKENS = re.compile(
    r"""
      (?P<comentario>\#[^\n]*)
    | (?P<texto>(?:[fFrRbBuU]{0,2})(?:\"\"\"[\s\S]*?\"\"\"|'''[\s\S]*?'''|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'))
    | (?P<clave>\b(?:%s)\b)
    | (?P<funcion>\b[A-Za-z_]\w*(?=\s*\())
    """
    % "|".join(PALABRAS_CLAVE),
    re.VERBOSE,
)


def envolver(clase, texto):
    """Un span por línea: ningún resaltado puede cruzar un salto de línea.

    Importa porque después partimos el HTML por líneas para darle a cada una su
    propio bloque (y su sangría colgante al ajustar). Un docstring de varias
    líneas rompería ese corte si viviera dentro de un solo <span>."""
    return "\n".join(
        f'<span class="{clase}">{html.escape(p)}</span>' if p else ""
        for p in texto.split("\n")
    )


def resaltar_python(codigo):
    partes, ultimo = [], 0
    for m in _TOKENS.finditer(codigo):
        partes.append(html.escape(codigo[ultimo : m.start()]))
        clase = {"comentario": "c", "texto": "s", "clave": "k", "funcion": "f"}[
            m.lastgroup
        ]
        partes.append(envolver(clase, m.group()))
        ultimo = m.end()
    partes.append(html.escape(codigo[ultimo:]))
    return "".join(partes)


def por_lineas(resaltado):
    """Cada línea del fuente pasa a ser un bloque propio.

    Sin saltos de línea entre ellos: el salto lo da el `display: block`. Así el
    navegador puede darle sangría colgante a cada línea cuando el alumno activa
    "Ajustar líneas", y una línea envuelta no se confunde con una sentencia
    nueva."""
    return "".join(f'<span class="l">{l}</span>' for l in resaltado.split("\n"))


_MD = re.compile(r"^(#{1,6} .*)$|(`[^`\n]+`)", re.MULTILINE)


def resaltar_markdown(texto):
    def sub(m):
        if m.group(1):
            return envolver("k", m.group(1))
        return envolver("s", m.group(2))

    partes, ultimo = [], 0
    for m in _MD.finditer(texto):
        partes.append(html.escape(texto[ultimo : m.start()]))
        partes.append(sub(m))
        ultimo = m.end()
    partes.append(html.escape(texto[ultimo:]))
    return "".join(partes)


_SHELL = re.compile(r"(?P<comentario>\#[^\n]*)|(?P<clave>^\s*(?:cd|source|python|pip|export|mkdir|git)\b)", re.MULTILINE)


def resaltar_shell(texto):
    partes, ultimo = [], 0
    for m in _SHELL.finditer(texto):
        partes.append(html.escape(texto[ultimo : m.start()]))
        clase = "c" if m.lastgroup == "comentario" else "k"
        partes.append(envolver(clase, m.group()))
        ultimo = m.end()
    partes.append(html.escape(texto[ultimo:]))
    return "".join(partes)


def resaltar(texto, lenguaje):
    if lenguaje == "python":
        return resaltar_python(texto)
    if lenguaje in ("markdown", "md"):
        return resaltar_markdown(texto)
    if lenguaje in ("bash", "shell", "sh"):
        return resaltar_shell(texto)
    return html.escape(texto)


def lenguaje_de(nombre):
    sufijo = Path(nombre).suffix
    return {".py": "python", ".md": "markdown", ".txt": "texto", ".sh": "bash"}.get(
        sufijo, "texto"
    )


# ---------------------------------------------------------------------------
# Lectura de fragmentos
# ---------------------------------------------------------------------------


class ErrorTaller(Exception):
    pass


def parsear_rango(spec, total, contexto):
    """'22-48' -> (22, 48). Sin spec -> archivo completo. Valida los bordes."""
    if spec is None:
        return 1, total
    m = re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*", str(spec))
    if not m:
        raise ErrorTaller(
            f"{contexto}: rango '{spec}' inválido. Usa 'inicio-fin' (un solo "
            f"rango contiguo; si necesitas dos, son dos pasos)."
        )
    ini, fin = int(m.group(1)), int(m.group(2))
    if ini < 1 or fin > total or ini > fin:
        raise ErrorTaller(
            f"{contexto}: el rango {ini}-{fin} se sale del archivo (tiene {total} líneas)."
        )
    return ini, fin


def leer_fragmento(base, spec, contexto):
    """spec: {archivo, lineas?} -> dict con texto, rango y metadatos."""
    ruta = base / spec["archivo"]
    if not ruta.exists():
        raise ErrorTaller(f"{contexto}: no existe {ruta.relative_to(REPO)}")
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    ini, fin = parsear_rango(spec.get("lineas"), len(lineas), contexto)
    return {
        "archivo": spec["archivo"],
        "texto": "\n".join(lineas[ini - 1 : fin]),
        "ini": ini,
        "fin": fin,
        "total": len(lineas),
        "lenguaje": spec.get("lenguaje") or lenguaje_de(spec["archivo"]),
        "completo": (ini, fin) == (1, len(lineas)),
    }


def limpiar_salida(texto):
    """Las salidas capturadas traen rutas absolutas de la máquina del coach."""
    return texto.replace(str(REPO), "…").replace(str(Path.home()), "~")


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def bloque_codigo(frag, etiqueta_extra=""):
    if frag["completo"]:
        ubicacion = f"{frag['archivo']} · archivo completo ({frag['total']} líneas)"
    else:
        ubicacion = f"{frag['archivo']} · líneas {frag['ini']}–{frag['fin']}"
    return envoltorio(ubicacion, frag["texto"], frag["lenguaje"], etiqueta_extra)


def bloque_inline(bloque):
    lenguaje = bloque.get("lenguaje", "bash")
    titulo = bloque.get("titulo", "terminal" if lenguaje == "bash" else lenguaje)
    return envoltorio(titulo, bloque["texto"].rstrip(), lenguaje)


def envoltorio(titulo, texto, lenguaje, etiqueta_extra=""):
    # data-codigo lleva el fuente EXACTO. El botón de copiar lee de ahí, no del
    # DOM: así lo que se copia no depende de si el bloque está envuelto, o
    # plegado dentro de un <details>.
    return (
        f'<div class="bloque" data-codigo="{html.escape(texto, quote=True)}">'
        f'<div class="bloque-cab"><span class="ruta">{html.escape(titulo)}</span>{etiqueta_extra}</div>'
        f"<pre><code>{por_lineas(resaltar(texto, lenguaje))}</code></pre>"
        "</div>"
    )


def bloque_salida(texto, titulo="lo que deberías ver"):
    limpio = limpiar_salida(texto).rstrip()
    return (
        f'<div class="bloque salida" data-codigo="{html.escape(limpio, quote=True)}">'
        f'<div class="bloque-cab"><span class="ruta">▸ {html.escape(titulo)}</span></div>'
        f"<pre><code>{por_lineas(html.escape(limpio))}</code></pre>"
        "</div>"
    )


def parrafos(texto):
    if not texto:
        return ""
    bloques = [b.strip() for b in str(texto).strip().split("\n\n") if b.strip()]
    return "".join(f"<p>{marcado(b)}</p>" for b in bloques)


def marcado(texto):
    """Markdown mínimo: **negrita**, *cursiva*, `código`, [texto](url)."""
    t = html.escape(texto).replace("\n", " ")
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?![*\w])", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    return t


def render_paso(paso, num_dia, num_paso, base, salidas, uso):
    pid = f"d{num_dia}p{num_paso}"
    ctx = f"día {num_dia} · paso {num_paso} ({paso.get('titulo', 'sin título')})"
    piezas = []

    piezas.append(parrafos(paso.get("objetivo")))

    if "codigo" in paso:
        frag = leer_fragmento(base, paso["codigo"], ctx)
        uso.setdefault(frag["archivo"], []).append((frag["ini"], frag["fin"], pid))
        etiqueta = ""
        if paso["codigo"].get("nuevo"):
            n = frag["fin"] - frag["ini"] + 1
            etiqueta = f'<span class="pill nuevo">+{n} líneas nuevas</span>'
        piezas.append(bloque_codigo(frag, etiqueta))

    for b in paso.get("bloques", []):
        piezas.append(bloque_inline(b))

    if paso.get("corre"):
        piezas.append(
            bloque_inline({"texto": paso["corre"], "lenguaje": "bash", "titulo": "córrelo"})
        )

    salida = paso.get("salida")
    if salida:
        if isinstance(salida, str):
            salida = {"archivo": salida}
        ruta = salidas / salida["archivo"]
        if not ruta.exists():
            raise ErrorTaller(f"{ctx}: falta la salida capturada {ruta.relative_to(REPO)}")
        lineas = ruta.read_text(encoding="utf-8").splitlines()
        ini, fin = parsear_rango(salida.get("lineas"), len(lineas), ctx + " (salida)")
        recorte = "\n".join(lineas[ini - 1 : fin])
        if fin < len(lineas):
            recorte += "\n…"
        piezas.append(bloque_salida(recorte))
    elif paso.get("salida_texto"):
        piezas.append(bloque_salida(paso["salida_texto"]))

    if paso.get("porque"):
        piezas.append(
            '<div class="nota porque"><div class="nota-cab">Por qué</div>'
            + parrafos(paso["porque"])
            + "</div>"
        )

    fallas = paso.get("si_falla") or []
    if fallas:
        filas = "".join(
            f'<li><code>{html.escape(f["error"])}</code><span>{marcado(f["arreglo"])}</span></li>'
            for f in fallas
        )
        piezas.append(
            '<details class="nota falla"><summary>Si te falla</summary>'
            f'<ul class="fallas">{filas}</ul></details>'
        )

    if paso.get("nota_coach"):
        piezas.append(
            '<div class="nota coach"><div class="nota-cab">Nota del coach</div>'
            + parrafos(paso["nota_coach"])
            + "</div>"
        )

    minutos = (
        f'<span class="paso-min">{paso["minutos"]} min</span>'
        if paso.get("minutos")
        else ""
    )
    # Estructura editorial: la cifra del paso vive en el margen izquierdo, fuera
    # de la columna de texto. Rompe la monotonía de "tarjeta tras tarjeta" y le
    # devuelve el ancho completo al código, que es el protagonista.
    return f"""
    <article class="paso" id="{pid}" data-paso="{pid}">
      <div class="paso-margen">
        <span class="paso-cifra" aria-hidden="true">{num_dia}.{num_paso}</span>
        <button class="tick" type="button" data-tick="{pid}"
                aria-label="Marcar el paso {num_dia}.{num_paso} como hecho"
                aria-pressed="false"></button>
      </div>
      <div class="paso-cuerpo">
        <header class="paso-cab">
          <h3>{marcado(paso.get("titulo", ""))}</h3>
          {minutos}
        </header>
        {"".join(piezas)}
      </div>
    </article>"""


def render_dia(dia, num_dia, base, salidas, uso):
    pasos = "".join(
        render_paso(p, num_dia, i, base, salidas, uso)
        for i, p in enumerate(dia.get("pasos", []), start=1)
    )

    completos = ""
    for archivo in dia.get("archivo_completo", []):
        frag = leer_fragmento(base, {"archivo": archivo}, f"día {num_dia} (archivo completo)")
        completos += (
            f"<details class='completo'><summary>Ver <code>{html.escape(archivo)}</code> "
            f"completo ({frag['total']} líneas), para comparar con el tuyo</summary>"
            f"{bloque_codigo(frag)}</details>"
        )

    cierre = ""
    if dia.get("checkpoint"):
        cierre = (
            '<div class="checkpoint"><div class="nota-cab">✓ Checkpoint del día</div>'
            + parrafos(dia["checkpoint"])
            + "</div>"
        )

    etiqueta = dia.get("etiqueta", f"Día {num_dia}")
    # La cifra grande sale de la etiqueta ("Día 0 · Antes de empezar" → 0), no
    # del índice: el guion manda sobre la numeración.
    m = re.search(r"\d+", etiqueta)
    cifra = m.group() if m else str(num_dia)

    return f"""
    <section class="dia" id="dia-{num_dia}">
      <header class="dia-cab">
        <span class="dia-cifra" aria-hidden="true">{cifra}</span>
        <div class="dia-texto">
          <div class="dia-etiqueta">{html.escape(etiqueta)}
            <span class="dia-min">{dia.get("minutos", 30)} min</span></div>
          <h2>{marcado(dia.get("titulo", ""))}</h2>
          {parrafos(dia.get("meta"))}
        </div>
      </header>
      {pasos}
      {completos}
      {cierre}
    </section>"""


def render_cierre(taller, dir_taller):
    """El cierre del taller: qué sigue cuando el alumno terminó el último día."""
    cierre = taller.get("cierre")
    if not cierre:
        return ""

    piezas = []
    sig = cierre.get("siguiente")
    if sig:
        # ¿Ya existe el taller siguiente? No se pregunta al guion: se mira el
        # disco. Así el enlace se activa solo el día que se publique, sin que
        # nadie tenga que acordarse de volver aquí.
        destino = dir_taller.parent / f"{sig['id']}.html"
        cuerpo = (
            f'<span class="siguiente-titulo">{marcado(sig["titulo"])}</span>'
            f'<span class="siguiente-resumen">{marcado(sig.get("resumen", ""))}</span>'
        )
        if destino.exists():
            piezas.append(
                f'<a class="siguiente" href="{html.escape(sig["id"])}.html">'
                '<span class="siguiente-etiqueta">Siguiente taller</span>'
                f'{cuerpo}<span class="siguiente-flecha">→</span></a>'
            )
        else:
            alterno = ""
            if sig.get("deck"):
                alterno = (
                    f'<a class="siguiente-alterno" href="{html.escape(sig["deck"])}">'
                    "Mientras tanto, el deck de la sesión →</a>"
                )
            piezas.append(
                '<div class="siguiente pendiente">'
                '<span class="siguiente-etiqueta">Siguiente taller · aún no publicado</span>'
                f"{cuerpo}{alterno}</div>"
            )

    acciones = cierre.get("acciones") or []
    if acciones:
        piezas.append(
            '<div class="cierre-acciones">'
            + "".join(
                f'<a href="{html.escape(a["url"])}">{html.escape(a["texto"])}</a>'
                for a in acciones
            )
            + "</div>"
        )

    return f"""
    <section class="cierre" id="cierre">
      <div class="marca-cierre">✓ Taller terminado</div>
      <h2>{marcado(cierre.get("titulo", ""))}</h2>
      {parrafos(cierre.get("texto"))}
      {"".join(piezas)}
    </section>"""


def render_nav(dias, con_cierre=False):
    filas = []
    for i, dia in enumerate(dias, start=1):
        pasos = "".join(
            f'<li><a href="#d{i}p{j}" data-nav="d{i}p{j}">'
            f'<span class="dot"></span>{html.escape(p.get("titulo", ""))}</a></li>'
            for j, p in enumerate(dia.get("pasos", []), start=1)
        )
        filas.append(
            f'<li class="nav-dia"><a href="#dia-{i}"><span class="nav-dia-etiqueta">'
            f'{html.escape(dia.get("etiqueta", f"Día {i}"))}</span>'
            f'<span class="nav-dia-titulo">{html.escape(dia.get("titulo", ""))}</span></a>'
            f"<ul>{pasos}</ul></li>"
        )
    if con_cierre:
        filas.append(
            '<li class="nav-dia"><a href="#cierre">'
            '<span class="nav-dia-etiqueta">Al terminar</span>'
            '<span class="nav-dia-titulo">Qué sigue</span></a></li>'
        )
    return "".join(filas)


# ---------------------------------------------------------------------------
# Verificación de huecos
# ---------------------------------------------------------------------------


def revisar_cobertura(uso, base, taller):
    """El chequeo que existe este generador: ¿queda código sin explicar?

    Si un archivo del taller tiene líneas que ningún paso muestra, el alumno
    no puede reconstruirlo copiando y pegando. Eso es exactamente el hueco que
    tenían los decks."""
    problemas = []
    omitir = {o["archivo"]: o.get("razon", "") for o in taller.get("omitir", [])}
    for archivo, rangos in sorted(uso.items()):
        total = len((base / archivo).read_text(encoding="utf-8").splitlines())
        cubierto = set()
        for ini, fin, _ in rangos:
            cubierto |= set(range(ini, fin + 1))
        faltan = sorted(set(range(1, total + 1)) - cubierto)
        if faltan and archivo not in omitir:
            problemas.append((archivo, comprimir(faltan)))

        solapes = []
        vistos = {}
        for ini, fin, pid in rangos:
            for n in range(ini, fin + 1):
                if n in vistos:
                    solapes.append((n, vistos[n], pid))
                    break
                vistos[n] = pid
        for n, a, b in solapes:
            problemas.append((archivo, f"línea {n} mostrada dos veces ({a} y {b})"))
    return problemas


def comprimir(numeros):
    rangos, ini, prev = [], numeros[0], numeros[0]
    for n in numeros[1:]:
        if n == prev + 1:
            prev = n
            continue
        rangos.append((ini, prev))
        ini = prev = n
    rangos.append((ini, prev))
    return ", ".join(f"{a}" if a == b else f"{a}–{b}" for a, b in rangos)


# ---------------------------------------------------------------------------
# Construcción
# ---------------------------------------------------------------------------


def construir(dir_taller, estricto=False):
    taller = yaml.safe_load((dir_taller / "taller.yaml").read_text(encoding="utf-8"))
    base = dir_taller / taller.get("codigo", "codigo")
    salidas = dir_taller / taller.get("salidas", "salidas")

    uso = {}
    dias = taller["dias"]
    cuerpo = "".join(
        render_dia(d, i, base, salidas, uso) for i, d in enumerate(dias, start=1)
    )

    problemas = revisar_cobertura(uso, base, taller)
    for archivo, detalle in problemas:
        print(f"  ⚠ hueco en {archivo}: {detalle}")
    if problemas and estricto:
        raise ErrorTaller(f"{len(problemas)} hueco(s) sin explicar. Corrige taller.yaml.")

    total_pasos = sum(len(d.get("pasos", [])) for d in dias)
    total_min = sum(d.get("minutos", 30) for d in dias)

    enlaces = "".join(
        f'<a class="enlace" href="{html.escape(e["url"])}">{html.escape(e["texto"])}</a>'
        for e in taller.get("enlaces", [])
    )

    plantilla = (RAIZ / "plantilla.html").read_text(encoding="utf-8")
    salida = (
        plantilla.replace("{{TITULO}}", html.escape(taller["titulo"]))
        .replace("{{KICKER}}", html.escape(taller.get("kicker", "")))
        .replace("{{SUBTITULO}}", marcado(taller.get("subtitulo", "")))
        .replace("{{ID}}", html.escape(taller["id"]))
        .replace("{{INICIO}}", html.escape(taller.get("inicio", "../index.html")))
        .replace("{{NAV}}", render_nav(dias, con_cierre=bool(taller.get("cierre"))))
        .replace("{{CUERPO}}", cuerpo)
        .replace("{{CIERRE}}", render_cierre(taller, dir_taller))
        .replace("{{ENLACES}}", enlaces)
        .replace("{{TOTAL_PASOS}}", str(total_pasos))
        .replace("{{TOTAL_DIAS}}", str(len(dias)))
        .replace("{{TOTAL_MIN}}", str(total_min))
        .replace("{{COMO_FUNCIONA}}", parrafos(taller.get("como_funciona", "")))
    )

    destino = dir_taller.parent / f"{dir_taller.name}.html"
    destino.write_text(salida, encoding="utf-8")
    print(
        f"✓ {destino.relative_to(REPO)}: {len(dias)} días, {total_pasos} pasos, "
        f"{len(uso)} archivo(s) de código{' · sin huecos' if not problemas else ''}"
    )
    return destino


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    estricto = "--estricto" in sys.argv
    dirs = (
        [RAIZ / a for a in args]
        if args
        else sorted(d for d in RAIZ.iterdir() if (d / "taller.yaml").exists())
    )
    if not dirs:
        print("No encontré ningún taller.yaml en talleres/")
        return 1
    for d in dirs:
        if not (d / "taller.yaml").exists():
            print(f"✗ {d.name}: no tiene taller.yaml")
            return 1
        try:
            construir(d, estricto)
        except ErrorTaller as e:
            print(f"✗ {d.name}: {e}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
