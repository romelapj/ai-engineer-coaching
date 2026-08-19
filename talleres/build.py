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
    """Markdown mínimo: **negrita**, *cursiva*, `código`, [texto](url).

    Los tramos de código se apartan ANTES de aplicar énfasis y vuelven al
    final. Sin eso, un `*` dentro de código se empareja con otro más adelante y
    pone en cursiva todo lo que hay en medio: es justo lo que pasaba al
    explicar qué significa el `*` de un patrón de archivos."""
    t = html.escape(texto).replace("\n", " ")

    apartados = []

    def guardar(m):
        apartados.append(f"<code>{m.group(1)}</code>")
        return f"\x00{len(apartados) - 1}\x00"

    t = re.sub(r"`([^`]+)`", guardar, t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?![*\w])", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    return re.sub(r"\x00(\d+)\x00", lambda m: apartados[int(m.group(1))], t)


# ---------------------------------------------------------------------------
# Videos
# ---------------------------------------------------------------------------

# Se carga una vez: el catálogo es del curso entero, no de un taller.
CATALOGO = {}
_cat = RAIZ / "videos.yaml"
if _cat.exists():
    CATALOGO = (yaml.safe_load(_cat.read_text(encoding="utf-8")) or {}).get("videos", {})

# Qué videos tienen contenido escrito y cuáles no. Lo llena render_video() y lo
# lee main() para poder listar los pendientes sin volver a recorrer nada.
PENDIENTES = {}
USADOS = {}

# Un video se considera escrito cuando tiene resumen. Los demás campos matizan,
# pero sin resumen la página no tiene nada que contar.
def tiene_contenido(v):
    return bool(v.get("resumen"))


def render_video(dia, id_taller, num_dia):
    """La tarjeta del video al cierre del día: miniatura, título y por qué."""
    ref = dia.get("video")
    if not ref:
        return ""
    vid = ref["id"] if isinstance(ref, dict) else ref
    v = CATALOGO.get(vid)
    if not v:
        raise ErrorTaller(
            f"día {num_dia}: el video {vid} no está en talleres/videos.yaml"
        )

    USADOS.setdefault(vid, []).append((id_taller, num_dia))
    if not tiene_contenido(v):
        PENDIENTES[vid] = v.get("titulo", vid)

    porque = ref.get("porque", "") if isinstance(ref, dict) else ""
    falta = (
        '<span class="vt-falta">resumen pendiente</span>'
        if not tiene_contenido(v)
        else ""
    )
    return f"""
      <a class="video-tarjeta" href="videos/{html.escape(vid)}.html"
         target="_blank" rel="noopener">
        <span class="vt-cab">Para ampliar</span>
        <span class="vt-mini">
          <img src="https://img.youtube.com/vi/{html.escape(vid)}/mqdefault.jpg"
               alt="" loading="lazy" width="320" height="180" />
          <span class="vt-play" aria-hidden="true"></span>
        </span>
        <span class="vt-texto">
          <span class="vt-titulo">{html.escape(v.get("titulo", vid))}</span>
          <span class="vt-meta">{html.escape(v.get("autor", ""))}
            · {html.escape(v.get("idioma", ""))}
            · {html.escape(v.get("duracion", ""))}{falta}</span>
          <span class="vt-porque">{marcado(porque)}</span>
        </span>
      </a>"""


def render_pagina_video(vid, v, destino_dir, contexto):
    """La página propia del video: ficha, embebido y el material del curso.

    Si el video todavía no tiene `resumen` en el catálogo, la página se genera
    igual (el alumno puede verlo) pero con un estado de pendiente explícito.
    Nunca se inventa el contenido: eso convertiría el material del curso en
    algo que no se puede citar.
    """
    plantilla = (RAIZ / "plantilla-video.html").read_text(encoding="utf-8")

    if tiene_contenido(v):
        piezas = [
            '<section class="bloque"><h2><span class="num">01</span>'
            "De qué va</h2>" + parrafos(v["resumen"]) + "</section>"
        ]
        if v.get("valioso"):
            puntos = "".join(f"<li>{marcado(x)}</li>" for x in v["valioso"])
            piezas.append(
                '<section class="bloque"><h2><span class="num">02</span>'
                f'Lo que de verdad vale</h2><ul class="valioso">{puntos}</ul></section>'
            )
        if v.get("conecta"):
            piezas.append(
                '<section class="bloque"><h2><span class="num">03</span>'
                "Cómo se enlaza con el taller</h2>"
                + parrafos(v["conecta"])
                + "</section>"
            )
        if v.get("reparos"):
            piezas.append(
                '<section class="bloque"><h2><span class="num">04</span>'
                "Dónde se queda corto</h2>" + parrafos(v["reparos"]) + "</section>"
            )
        contenido = "".join(piezas)
    else:
        contenido = (
            '<section class="bloque"><div class="pendiente">'
            '<div class="cab">⧗ Resumen pendiente</div>'
            "<p>El video ya está aquí y se puede ver. Lo que falta es la parte "
            "del curso: el resumen de lo que dice, lo que de verdad vale la "
            "pena y cómo se enlaza con este día del taller.</p>"
            "<p>No se rellena a ojo. Se escribe después de verlo, en "
            "<code>talleres/videos.yaml</code>, y aparece aquí con el "
            "siguiente <code>build.py</code>.</p>"
            '<div class="esqueleto" aria-hidden="true">'
            '<div class="linea"></div><div class="linea"></div>'
            '<div class="linea"></div><div class="linea"></div></div>'
            "</div></section>"
        )

    aparte = ""
    if not tiene_contenido(v):
        aparte = (
            '<div class="caja"><div class="cab">Mientras tanto</div>'
            "<p>Véelo con el día del taller al lado: lo que reconozcas del "
            "código es la señal de que el video te está sirviendo.</p></div>"
        )

    salida = (
        plantilla.replace("{{TITULO}}", html.escape(v.get("titulo", vid)))
        .replace("{{AUTOR}}", html.escape(v.get("autor", "")))
        .replace("{{IDIOMA}}", html.escape(v.get("idioma", "")))
        .replace("{{DURACION}}", html.escape(v.get("duracion", "")))
        .replace("{{VIDEO_ID}}", html.escape(vid))
        .replace("{{KICKER}}", html.escape(contexto["kicker"]))
        .replace("{{VOLVER_URL}}", html.escape(contexto["volver_url"]))
        .replace("{{VOLVER_TEXTO}}", html.escape(contexto["volver_texto"]))
        .replace("{{VOLVER_NOTA}}", html.escape(contexto["volver_nota"]))
        .replace("{{INICIO}}", html.escape(contexto["inicio"]))
        .replace("{{CONTENIDO}}", contenido)
        .replace("{{APARTE}}", aparte)
    )
    destino_dir.mkdir(parents=True, exist_ok=True)
    (destino_dir / f"{vid}.html").write_text(salida, encoding="utf-8")


def render_paso(paso, num_dia, num_paso, base, salidas, uso):
    pid = f"d{num_dia}p{num_paso}"
    ctx = f"día {num_dia} · paso {num_paso} ({paso.get('titulo', 'sin título')})"
    piezas = []

    # Definiciones de dominio: la PRIMERA pieza del paso, antes del objetivo y
    # del código. Un término que aparece en el código sin haberse definido
    # obliga a deducirlo, y quien no puede deducirlo se cae del resto del
    # taller. Estuvo ocho pasos saliendo detrás del código, al revés de lo que
    # decía este mismo comentario y docs/04.
    define = paso.get("define") or []
    if define:
        filas = "".join(
            f'<li><b>{marcado(x["termino"])}</b><span>{marcado(x["es"])}</span></li>'
            for x in define
        )
        piezas.append(
            '<div class="nota define"><div class="nota-cab">Antes de seguir</div>'
            f'<ul class="define-lista">{filas}</ul></div>'
        )

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

    # Sintaxis de Python. Va ANTES del "por qué" a propósito: primero entiendes
    # qué dice el código, después por qué está escrito así. Plegado, porque a
    # quien ya sabe Python le estorbaría en los 41 pasos.
    sintaxis = paso.get("python") or []
    if sintaxis:
        filas = "".join(
            f'<li><code>{html.escape(s["de"])}</code><span>{marcado(s["es"])}</span></li>'
            for s in sintaxis
        )
        piezas.append(
            '<details class="nota sintaxis"><summary>Sintaxis de Python '
            f'<span class="cuenta">{len(sintaxis)}</span></summary>'
            f'<ul class="sintaxis-lista">{filas}</ul></details>'
        )

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
        <button class="tick-fin" type="button" data-tick="{pid}">
          <span class="tick-fin-marca" aria-hidden="true"></span>
          <span class="tick-fin-texto">Marcar como hecho</span>
        </button>
      </div>
    </article>"""


def render_dia(dia, num_dia, base, salidas, uso, id_taller="", entregados=None):
    entregados = entregados if entregados is not None else set()
    pasos = "".join(
        render_paso(p, num_dia, i, base, salidas, uso)
        for i, p in enumerate(dia.get("pasos", []), start=1)
    )

    completos = ""
    for archivo in dia.get("archivo_completo", []):
        frag = leer_fragmento(base, {"archivo": archivo}, f"día {num_dia} (archivo completo)")
        # Mostrarlo entero cuenta como entregarlo, pero NO entra en `uso`: ese
        # controla el solapamiento línea a línea, y este panel repite a
        # propósito lo que los pasos ya enseñaron.
        entregados.add(archivo)
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

    # De dónde vienes: una o dos frases que enlazan con el día anterior. Va
    # ARRIBA del título, porque orienta antes de que empieces a leer.
    vienes = ""
    if dia.get("vienes_de"):
        vienes = f'<p class="dia-vienes">{marcado(dia["vienes_de"])}</p>'

    # Y qué queda abierto. Va al final del todo: es el gancho al día siguiente.
    deja = ""
    if dia.get("te_deja"):
        deja = (
            '<div class="dia-deja"><span class="dia-deja-cab">Lo que queda abierto</span>'
            + parrafos(dia["te_deja"])
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
          {vienes}
          <h2>{marcado(dia.get("titulo", ""))}</h2>
          {parrafos(dia.get("meta"))}
        </div>
      </header>
      {pasos}
      {completos}
      {cierre}
      {render_video(dia, id_taller, num_dia)}
      {deja}
    </section>"""


def render_historia(taller):
    """El arco del taller, antes del primer día.

    Sin esto el alumno entra al día 1 sin saber a dónde va: el razonamiento
    existe, pero repartido en los `porque` de cada paso, y esos solo se leen
    cuando ya estás dentro del paso mirando el código."""
    h = taller.get("historia")
    if not h:
        return ""
    actos = "".join(
        f'<div class="acto"><span class="acto-num">{i}</span>'
        f'<h3>{marcado(a["titulo"])}</h3>{parrafos(a["texto"])}'
        f'<span class="acto-dias">{marcado(a.get("dias", ""))}</span></div>'
        for i, a in enumerate(h.get("actos", []), start=1)
    )
    return (
        '<section class="historia">'
        f'<div class="historia-cab">{html.escape(h.get("cab", "La historia de esta sesión"))}</div>'
        + parrafos(h.get("entrada", ""))
        + f'<div class="actos">{actos}</div>'
        + (f'<p class="historia-cierre">{marcado(h["cierre"])}</p>' if h.get("cierre") else "")
        + "</section>"
    )


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


def revisar_cobertura(uso, base, taller, entregados=frozenset()):
    """El chequeo que existe este generador: ¿queda código sin explicar?

    Si un archivo del taller tiene líneas que ningún paso muestra, el alumno
    no puede reconstruirlo copiando y pegando. Eso es exactamente el hueco que
    tenían los decks."""
    problemas = []
    omitir = {o["archivo"]: o.get("razon", "") for o in taller.get("omitir", [])}

    # Un archivo que NINGÚN paso nombra era invisible para este chequeo, porque
    # `uso` solo se llena con lo que algún paso referencia. Así el taller 05 se
    # publicó sin entregar su corpus: el alumno acababa con cero chunks y un RAG
    # que contestaba "no tengo evidencia" a todo, sin un solo error. Justo el
    # fallo silencioso que esa sesión enseña a detectar.
    ignorar = {"__pycache__", "rag_db", ".venv", ".DS_Store"}
    for ruta in sorted(base.rglob("*")):
        if not ruta.is_file():
            continue
        if any(parte in ignorar for parte in ruta.parts):
            continue
        rel = str(ruta.relative_to(base))
        if rel not in uso and rel not in entregados and rel not in omitir:
            problemas.append((rel, "existe en codigo/ pero ningún paso lo entrega"))

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
# Validación del guion
# ---------------------------------------------------------------------------

# build.py lee el YAML entero con .get(), así que una clave mal escrita no falla:
# desaparece. Renombrar `porque:` a `porqué:` (un error de tilde frecuente en
# español, y el bloque se rotula "Por qué") borra la clase de un taller entero y
# el build sigue diciendo "sin huecos". Estos conjuntos cierran esa puerta.

CLAVES_TALLER = {
    "id", "titulo", "kicker", "subtitulo", "codigo", "salidas", "enlaces",
    "como_funciona", "historia", "cierre", "dias", "inicio", "omitir",
}
CLAVES_DIA = {
    "etiqueta", "titulo", "minutos", "meta", "vienes_de", "te_deja",
    "archivo_completo", "checkpoint", "video", "pasos",
}
CLAVES_PASO = {
    "titulo", "minutos", "objetivo", "define", "codigo", "bloques", "python",
    "corre", "salida", "salida_texto", "porque", "si_falla", "nota_coach",
}


def validar_esquema(taller, nombre):
    """Cada clave del guion tiene que existir en el vocabulario del generador.

    Sin esto, un typo es indistinguible de una omisión deliberada."""
    import difflib

    errores = []

    def revisar(d, permitidas, donde):
        for clave in d:
            if clave in permitidas:
                continue
            cerca = difflib.get_close_matches(str(clave), permitidas, n=1, cutoff=0.6)
            pista = f" ¿querías decir `{cerca[0]}`?" if cerca else ""
            errores.append(f"{donde}: clave desconocida `{clave}`.{pista}")

    revisar(taller, CLAVES_TALLER, "raíz")
    for i, dia in enumerate(taller.get("dias", []), start=1):
        revisar(dia, CLAVES_DIA, f"día {i}")
        for j, paso in enumerate(dia.get("pasos", []), start=1):
            revisar(paso, CLAVES_PASO, f"día {i} · paso {j}")

    if errores:
        raise ErrorTaller(
            f"{nombre}: el guion usa claves que el generador no conoce.\n    "
            + "\n    ".join(errores)
        )


# ---------------------------------------------------------------------------
# Construcción
# ---------------------------------------------------------------------------


def construir(dir_taller, estricto=False):
    taller = yaml.safe_load((dir_taller / "taller.yaml").read_text(encoding="utf-8"))
    validar_esquema(taller, dir_taller.name)
    base = dir_taller / taller.get("codigo", "codigo")
    salidas = dir_taller / taller.get("salidas", "salidas")

    uso = {}
    entregados = set()
    dias = taller["dias"]
    cuerpo = "".join(
        render_dia(d, i, base, salidas, uso, taller["id"], entregados)
        for i, d in enumerate(dias, start=1)
    )

    # Una página por cada video referenciado, en talleres/videos/. Se escribe
    # aquí y no en un script aparte para que un video nuevo no pueda quedarse
    # sin su página: si el día lo referencia, la página existe.
    n_videos = 0
    for i, d in enumerate(dias, start=1):
        ref = d.get("video")
        if not ref:
            continue
        vid = ref["id"] if isinstance(ref, dict) else ref
        render_pagina_video(
            vid,
            CATALOGO[vid],
            dir_taller.parent / "videos",
            {
                "kicker": f"{taller.get('kicker', '')} · {d.get('etiqueta', '')}",
                "volver_url": f"../{taller['id']}.html#dia-{i}",
                "volver_texto": d.get("etiqueta", f"Día {i}"),
                "volver_nota": d.get("titulo", ""),
                # Las páginas de video viven un nivel más abajo (talleres/videos/), así
                # que el destino sube un nivel más. Con lstrip("./") se comía los
                # dos puntos y las 24 páginas apuntaban a talleres/index.html.
                "inicio": "../" + taller.get("inicio", "../index.html"),
            },
        )
        n_videos += 1

    problemas = revisar_cobertura(uso, base, taller, entregados)
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
        .replace("{{HISTORIA}}", render_historia(taller))
    )

    destino = dir_taller.parent / f"{dir_taller.name}.html"
    destino.write_text(salida, encoding="utf-8")
    print(
        f"✓ {destino.relative_to(REPO)}: {len(dias)} días, {total_pasos} pasos, "
        f"{len(uso)} archivo(s) de código"
        f"{f', {n_videos} video(s)' if n_videos else ''}"
        f"{' · sin huecos' if not problemas else ''}"
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

    # Los videos sin resumen no rompen el build: la página se genera con su
    # estado de pendiente. Pero se listan, porque un pendiente que no se ve
    # deja de ser un pendiente y pasa a ser un hueco.
    if PENDIENTES:
        print(
            f"\n⧗ {len(PENDIENTES)} de {len(USADOS)} videos esperan su resumen "
            f"(la página se generó igual, con el estado de pendiente):"
        )
        for vid, titulo in PENDIENTES.items():
            donde = ", ".join(f"{t} día {n}" for t, n in USADOS[vid])
            print(f"    {vid}  {titulo[:56]:56} → {donde}")
        print("  Se escriben en talleres/videos.yaml (resumen, valioso, conecta, reparos).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
