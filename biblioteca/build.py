#!/usr/bin/env python3
"""
Generador de la biblioteca.

Dos puertas al mismo catálogo:

    biblioteca/index.html    artículos, noticias, videos y podcasts
    biblioteca/libros.html   el club de lectura

y una ficha por pieza en biblioteca/<slug>.html.

El formato de la ficha es el mismo que el de las páginas de video de los
talleres —qué dice, qué vale, cómo conecta, dónde se queda corto— porque el
trabajo del curso es el mismo lo leas o lo veas. Lo que cambia es el ritmo: un
artículo se cierra en una sentada y un libro dura semanas, tiene estado y tiene
tramos. Por eso son dos portadas y no una lista sola.

Uso:
    python biblioteca/build.py                # genera todo
    python biblioteca/build.py --pendientes   # solo lista lo que falta escribir

Entrada:  biblioteca/catalogo.yaml  (+ talleres/videos.yaml, solo para listarlos)
Salida:   biblioteca/index.html, biblioteca/libros.html, biblioteca/<slug>.html
"""

import html
import importlib.util
import re
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent
REPO = RAIZ.parent


# ---------------------------------------------------------------------------
# El markdown mínimo se toma prestado, no se copia
# ---------------------------------------------------------------------------
# `marcado()` y `parrafos()` ya existen en talleres/build.py y ya tienen dentro
# un fallo resuelto (el `*` dentro de código que ponía en cursiva media línea).
# Reimplementarlos aquí significaría volver a tropezar con eso el día que uno
# de los dos se toque. Se carga por ruta explícita y no con `import build`
# porque este archivo también se llama build.py: el import corriente es
# ambiguo según desde dónde se invoque.
def _prestado():
    ruta = REPO / "talleres" / "build.py"
    spec = importlib.util.spec_from_file_location("talleres_build", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


_T = _prestado()
marcado = _T.marcado
parrafos = _T.parrafos


# ---------------------------------------------------------------------------
# Catálogo
# ---------------------------------------------------------------------------

TIPOS = ("libro", "articulo", "noticia", "video", "podcast")

# Cómo se llama cada tipo en pantalla. En singular, porque etiqueta una pieza.
NOMBRE_TIPO = {
    "libro": "Libro",
    "articulo": "Artículo",
    "noticia": "Noticia",
    "video": "Video",
    "podcast": "Podcast",
}

ESTADOS = ("por-leer", "leyendo", "terminado", "abandonado")
NOMBRE_ESTADO = {
    "por-leer": "Por leer",
    "leyendo": "Leyendo",
    "terminado": "Terminado",
    "abandonado": "Abandonado",
}

CAMPOS = {
    "tipo", "titulo", "autor", "fuente", "fecha", "idioma", "extension",
    "url", "archivo", "video_id", "portada", "etiquetas", "sesiones",
    "engancho", "resumen", "valioso", "conecta", "reparos",
    # solo libros
    "isbn", "estado", "avance", "abandonado_porque", "subrayados", "plan",
}

SOLO_LIBRO = {"isbn", "estado", "avance", "abandonado_porque", "subrayados", "plan"}


def cargar():
    datos = yaml.safe_load((RAIZ / "catalogo.yaml").read_text(encoding="utf-8")) or {}
    piezas = datos.get("piezas") or {}
    inbox = datos.get("inbox") or []
    for slug, p in piezas.items():
        validar(slug, p)
    return piezas, inbox


def validar(slug, p):
    """Se falla aquí y no en la página. Un campo mal escrito en el YAML es
    invisible en el HTML generado: simplemente no sale, y eso se descubre
    semanas después leyendo una ficha a la que le falta la mitad."""
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
        raise SystemExit(f"✗ {slug}: el slug va en minúsculas y guiones (es el nombre del archivo)")
    sobran = set(p) - CAMPOS
    if sobran:
        raise SystemExit(f"✗ {slug}: campos que no existen: {', '.join(sorted(sobran))}")
    if p.get("tipo") not in TIPOS:
        raise SystemExit(f"✗ {slug}: tipo debe ser uno de {', '.join(TIPOS)}")
    if not p.get("titulo"):
        raise SystemExit(f"✗ {slug}: falta el título")
    if p["tipo"] != "libro":
        mal = set(p) & SOLO_LIBRO
        if mal:
            raise SystemExit(f"✗ {slug}: {', '.join(sorted(mal))} solo aplica a los libros")
    if p.get("estado") and p["estado"] not in ESTADOS:
        raise SystemExit(f"✗ {slug}: estado debe ser uno de {', '.join(ESTADOS)}")
    if p["tipo"] == "video" and not p.get("video_id") and not p.get("url"):
        raise SystemExit(f"✗ {slug}: un video necesita video_id (para embeberlo) o url")


def escrita(p):
    """Una pieza está escrita cuando tiene resumen. Los demás campos matizan;
    sin el resumen no hay ficha, solo un enlace con portada."""
    return bool(p.get("resumen"))


# ---------------------------------------------------------------------------
# Enlaces al programa
# ---------------------------------------------------------------------------

def resolver(ident):
    """`sesion-08` → la URL del deck y su nombre para mostrar.

    Los ids del campo `sesiones` son cortos a propósito (se escriben a mano en
    el YAML). Aquí se resuelven contra los archivos que existen de verdad, así
    que un id inventado rompe el build en vez de generar un enlace muerto."""
    m = re.fullmatch(r"(sesion|prefase|taller|reto|kata)-(\d{2})", ident or "")
    if not m:
        raise SystemExit(
            f"✗ '{ident}' no es un id del programa. Van así: sesion-08, prefase-03, "
            f"taller-04, reto-05, kata-02."
        )
    clase, num = m.group(1), m.group(2)

    if clase == "taller":
        destino = REPO / "talleres" / f"sesion-{num}.html"
        if not destino.exists():
            raise SystemExit(f"✗ {ident}: no existe talleres/sesion-{num}.html")
        return f"../talleres/sesion-{num}.html", f"Taller {num}"

    if clase in ("sesion", "prefase"):
        encontrados = sorted((REPO / "sesiones").glob(f"{clase}-{num}-*.html"))
        if not encontrados:
            raise SystemExit(f"✗ {ident}: no existe ningún sesiones/{clase}-{num}-*.html")
        f = encontrados[0]
        etiqueta = "Sesión" if clase == "sesion" else "Pre-fase"
        return f"../sesiones/{f.name}", f"{etiqueta} {num} · {bonito(f.stem, clase, num)}"

    encontrados = sorted(d for d in (REPO / "gym").glob(f"{clase}-{num}-*") if d.is_dir())
    if not encontrados:
        raise SystemExit(f"✗ {ident}: no existe ningún gym/{clase}-{num}-*/")
    d = encontrados[0]
    etiqueta = "Reto" if clase == "reto" else "Kata"
    return (
        f"../view.html?doc=gym/{d.name}/README.md",
        f"{etiqueta} {num} · {bonito(d.name, clase, num)}",
    )


def bonito(stem, clase, num):
    resto = stem[len(f"{clase}-{num}-"):].replace("-", " ")
    return resto[:1].upper() + resto[1:]


# ---------------------------------------------------------------------------
# Piezas de la portada
# ---------------------------------------------------------------------------

def e(t):
    return html.escape(str(t or ""))


def primera_frase(texto, tope=180):
    """El gancho de la tarjeta es una línea, no un párrafo.

    El `conecta` de los videos de los talleres es prosa larga escrita para
    leerse dentro de la página del video. Puesta entera en una tarjeta, la
    rejilla se convierte en un muro de texto."""
    texto = " ".join(str(texto or "").split())
    if not texto:
        return ""
    # Solo el punto cierra la frase. Cortar también en los dos puntos partía
    # justo donde la frase iba a decir lo interesante ("desarma la sigla:").
    corte = re.split(r"(?<=\.)\s", texto, maxsplit=1)[0]
    return corte if len(corte) <= tope else corte[:tope].rsplit(" ", 1)[0] + "…"


def imagen_de(p):
    """La portada descargada, o None si la pieza no tiene.

    Nunca se enlaza la imagen desde el servidor de otro: se descarga una vez a
    portadas/ y se versiona. Es la misma regla del código de los talleres —lo
    que se muestra es lo que hay— aplicada a que la página no dependa de que a
    nadie se le caiga un dominio."""
    ruta = p.get("portada")
    if not ruta:
        return None
    if not (RAIZ / ruta).exists():
        raise SystemExit(
            f"✗ {p.get('titulo')}: la portada '{ruta}' no está en biblioteca/. "
            f"Se descarga una vez y se versiona (ver portadas/README.md)."
        )
    return f'<img src="{e(ruta)}" alt="Portada de {e(p["titulo"])}" loading="lazy" />'


def portada_tipografica(p, clase="arte-tipo"):
    """Cuando no hay imagen, la portada la compone el título.

    Se usa SOLO en las rejillas. Es lo único que distingue una tarjeta de otra
    cuando ninguna trae imagen: sin texto, veinticinco degradados idénticos son
    el muro de tarjetas que el sistema visual lleva evitando desde el principio.
    En la ficha no se usa, porque allí el título ya está en el h1 y repetirlo en
    una placa de color sería decoración."""
    fuente = p.get("fuente") or p.get("autor") or NOMBRE_TIPO[p["tipo"]]
    return (
        f'<div class="{clase}"><div class="t">{e(p["titulo"])}</div>'
        f'<div class="f">{e(fuente)}</div></div>'
    )


def tarjeta(slug, p, href=None):
    """Una pieza en la rejilla. Lo único que se lee aquí es el `engancho`: es
    lo que decide si alguien abre la ficha, así que si falta se ve el hueco."""
    partes = [NOMBRE_TIPO[p["tipo"]]]
    if p.get("fuente"):
        partes.append(e(p["fuente"]))
    sellos = ""
    if p["tipo"] == "libro" and p.get("estado"):
        etiqueta = NOMBRE_ESTADO[p["estado"]]
        if p["estado"] == "leyendo" and p.get("avance"):
            etiqueta += f" · {e(p['avance'])}"
        sellos += f'<span class="sello {p["estado"]}">{etiqueta}</span>'
    if not escrita(p):
        sellos += '<span class="sello pendiente">⧗ Sin escribir</span>'

    # El título aparece UNA vez por tarjeta. Si la portada es tipográfica, ya lo
    # lleva ella; repetirlo debajo era leerlo dos veces seguidas.
    imagen = imagen_de(p)
    arte = imagen or portada_tipografica(p)
    titulo = f"<h3>{e(p['titulo'])}</h3>" if imagen else ""

    engancho = ""
    if p.get("engancho"):
        engancho = f'<div class="engancho">{marcado(p["engancho"])}</div>'
    elif escrita(p):
        # Sin escribir ya lo dice el sello; el hueco solo se señala cuando la
        # ficha existe y aun así nadie resumió por qué la pieza está aquí.
        engancho = (
            '<div class="engancho" style="color:var(--tenue)">'
            "Sin una línea que diga por qué está aquí.</div>"
        )

    return f"""
      <a class="pieza {e(p['tipo'])}" data-tipo="{e(p['tipo'])}" href="{href or f'{slug}.html'}">
        <div class="arte">{arte}</div>
        <div class="txt">
          <div class="meta">{' · '.join(partes)}{sellos}</div>
          {titulo}
          <div class="autor">{e(p.get('autor', ''))}</div>
          {engancho}
          <div class="pie">{e(p.get('_cta', 'Ver la ficha'))} →</div>
        </div>
      </a>"""


def filtros(piezas):
    """Un botón por tipo presente. No se pintan tipos vacíos: un filtro que
    devuelve cero resultados es una promesa rota."""
    cuenta = {}
    for p in piezas:
        cuenta[p["tipo"]] = cuenta.get(p["tipo"], 0) + 1
    if len(cuenta) < 2:
        return ""
    botones = [
        f'<button class="filtro" data-filtro="todo" aria-pressed="true">'
        f'Todo<span class="n">{len(piezas)}</span></button>'
    ]
    for t in TIPOS:
        if t in cuenta:
            botones.append(
                f'<button class="filtro" data-filtro="{t}" aria-pressed="false">'
                f'{NOMBRE_TIPO[t]}s<span class="n">{cuenta[t]}</span></button>'
            )
    return f'<div class="filtros">{"".join(botones)}</div>'


def rejilla(tarjetas, vacio):
    if not tarjetas:
        return f'<div class="vacio">{vacio}</div>'
    return f'<div class="rejilla">{"".join(tarjetas)}</div>'


# ---------------------------------------------------------------------------
# La ficha
# ---------------------------------------------------------------------------

def lista(items, clase):
    puntos = "".join(f"<li>{marcado(x)}</li>" for x in items)
    return f'<ul class="{clase}">{puntos}</ul>'


def bloque(n, titulo, cuerpo):
    return (
        f'<section class="bloque"><h2><span class="num">{n:02d}</span>'
        f"{titulo}</h2>{cuerpo}</section>"
    )


def render_ficha(slug, p):
    plantilla = (RAIZ / "plantilla-ficha.html").read_text(encoding="utf-8")
    es_libro = p["tipo"] == "libro"

    # ------------------------------------------------------------ ficha técnica
    campos = []
    if p.get("autor"):
        campos.append(f"<span><b>{e(p['autor'])}</b></span>")
    for c in ("fuente", "fecha", "idioma", "extension"):
        if p.get(c):
            campos.append(f"<span>{e(p[c])}</span>")
    if es_libro and p.get("estado"):
        etiqueta = NOMBRE_ESTADO[p["estado"]]
        if p["estado"] == "leyendo" and p.get("avance"):
            etiqueta += f" · {e(p['avance'])}"
        campos.append(f'<span class="estado {p["estado"]}">{etiqueta}</span>')
    ficha = '<span class="sep">·</span>'.join(campos)

    # ------------------------------------------------------------------- medio
    acciones = []
    if p.get("url"):
        texto = "Leer el original ↗" if not es_libro else "Ver el libro ↗"
        acciones.append(
            f'<a class="accion principal" href="{e(p["url"])}" target="_blank" '
            f'rel="noopener">{texto}</a>'
        )
    if p.get("archivo"):
        acciones.append(
            f'<a class="accion" href="{e(p["archivo"])}" target="_blank" '
            f'rel="noopener">Copia archivada ↗</a>'
        )
    caja_acciones = f'<div class="acciones">{"".join(acciones)}</div>' if acciones else ""

    etiquetas = ""
    if p.get("etiquetas"):
        marcas = "".join(f'<span class="etiqueta">{e(x)}</span>' for x in p["etiquetas"])
        etiquetas = f'<div class="etiquetas">{marcas}</div>'

    engancho = f'<p class="engancho">{marcado(p["engancho"])}</p>' if p.get("engancho") else ""

    if p["tipo"] == "video" and p.get("video_id"):
        vid = e(p["video_id"])
        medio = f"""<div class="medio">
        <div class="marco"><iframe
            src="https://www.youtube-nocookie.com/embed/{vid}" title="{e(p['titulo'])}"
            loading="lazy" allow="accelerometer; autoplay; clipboard-write;
            encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>
        <div>{engancho}<div class="acciones">
          <a class="accion principal" href="https://www.youtube.com/watch?v={vid}"
             target="_blank" rel="noopener">Ver en YouTube ↗</a></div>{etiquetas}</div>
      </div>"""
    else:
        # Con imagen, dos columnas. Sin ella, el ancho entero: el h1 de arriba ya
        # es la portada, y una placa de degradado repitiendo el título sería
        # decoración ocupando media pantalla.
        imagen = imagen_de(p)
        if imagen and es_libro:
            # La portada de un libro es vertical y se lee bien en una columna
            # estrecha, al lado de la entradilla.
            medio = f"""<div class="medio con-portada">
        <div class="portada">{imagen}</div>
        <div>{engancho}{caja_acciones}{etiquetas}</div>
      </div>"""
        elif imagen:
            # La de un artículo suele ser apaisada y muchas veces es un diagrama
            # con texto dentro. Metida en 240px no se lee, así que va a lo ancho
            # y la entradilla debajo.
            medio = f"""<div class="medio ancha">
        <div class="portada">{imagen}</div>
        {engancho}{caja_acciones}{etiquetas}
      </div>"""
        else:
            medio = f'<div class="medio simple">{engancho}{caja_acciones}{etiquetas}</div>'

    # ------------------------------------------------------------------ cuerpo
    if escrita(p):
        n = 0
        piezas_txt = []

        def add(titulo, cuerpo):
            nonlocal n
            n += 1
            piezas_txt.append(bloque(n, titulo, cuerpo))

        add("De qué va", parrafos(p["resumen"]))
        # El plan va arriba en un libro: mientras se lee, es lo que se consulta.
        if es_libro and p.get("plan"):
            add("El plan de lectura", render_plan(p["plan"]))
        if p.get("valioso"):
            add("Lo que de verdad vale", lista(p["valioso"], "valioso"))
        if p.get("conecta"):
            add("Cómo se enlaza con el programa", parrafos(p["conecta"]))
        if p.get("reparos"):
            add("Dónde se queda corto", lista(p["reparos"], "reparos"))
        if es_libro and p.get("subrayados"):
            add("Subrayados", render_subrayados(p["subrayados"]))
        if es_libro and p.get("abandonado_porque"):
            add("Por qué lo dejé", parrafos(p["abandonado_porque"]))
        contenido = "".join(piezas_txt)
    else:
        que_falta = (
            "el resumen de lo que dice, lo que de verdad vale la pena, cómo se "
            "enlaza con el programa y dónde se queda corto"
        )
        contenido = (
            '<section class="bloque"><div class="pendiente">'
            '<div class="cab">⧗ Ficha pendiente</div>'
            f"<p>La pieza ya está aquí y se puede abrir. Lo que falta es {que_falta}.</p>"
            "<p>No se rellena a ojo: se escribe después de leerla, en "
            "<code>biblioteca/catalogo.yaml</code>, y aparece aquí con el "
            "siguiente <code>build.py</code>.</p>"
            '<div class="esqueleto" aria-hidden="true">'
            '<div class="linea"></div><div class="linea"></div>'
            '<div class="linea"></div><div class="linea"></div></div>'
            "</div></section>"
        )

    # ------------------------------------------------------------------ aparte
    cajas = []
    if p.get("sesiones"):
        enlaces = "".join(
            f'<a class="vuelta" href="{url}">{texto}</a>'
            for url, texto in (resolver(i) for i in p["sesiones"])
        )
        cajas.append(f'<div class="caja"><div class="cab">Engancha con</div>{enlaces}</div>')
    vuelta = "libros.html" if es_libro else "index.html"
    nombre_vuelta = "Club de lectura" if es_libro else "Biblioteca"
    cajas.append(
        f'<div class="caja"><div class="cab">Volver</div>'
        f'<a class="vuelta" href="{vuelta}">{nombre_vuelta}'
        f"<small>Todo lo demás que hay leído</small></a></div>"
    )
    aparte = "".join(cajas)

    salida = (
        plantilla.replace("{{TITULO}}", e(p["titulo"]))
        .replace("{{KICKER}}", e("Club de lectura" if es_libro else NOMBRE_TIPO[p["tipo"]]))
        .replace("{{FICHA}}", ficha)
        .replace("{{MEDIO}}", medio)
        .replace("{{CONTENIDO}}", contenido)
        .replace("{{APARTE}}", aparte)
        .replace("{{VOLVER_URL}}", vuelta)
        .replace("{{VOLVER_TEXTO}}", nombre_vuelta)
        .replace(
            "{{PIE}}",
            "Página generada por <code>biblioteca/build.py</code> desde "
            "<code>biblioteca/catalogo.yaml</code>. La obra es de "
            f"{e(p.get('autor') or p.get('fuente') or 'su autor')}; el resumen y los "
            "comentarios son material del curso.",
        )
    )
    (RAIZ / f"{slug}.html").write_text(salida, encoding="utf-8")


def render_subrayados(subrayados):
    piezas_txt = []
    for s in subrayados:
        pagina = f'<span class="pagina">p. {e(s["pagina"])}</span>' if s.get("pagina") else ""
        comento = f'<div class="comento">{marcado(s["comento"])}</div>' if s.get("comento") else ""
        piezas_txt.append(
            f'<div class="subrayado"><blockquote>«{marcado(s["cita"])}»</blockquote>'
            f"{pagina}{comento}</div>"
        )
    return "".join(piezas_txt)


def render_plan(plan):
    piezas_txt = []
    for t in plan:
        semana = f'<span class="semana">Semana {e(t["semana"])}</span>' if t.get("semana") else ""
        preguntas = ""
        if t.get("preguntas"):
            preguntas = "<ul>" + "".join(f"<li>{marcado(q)}</li>" for q in t["preguntas"]) + "</ul>"
        piezas_txt.append(
            f'<div class="tramo"><div class="cab"><b>{e(t.get("tramo", ""))}</b>'
            f"{semana}</div>{preguntas}</div>"
        )
    return "".join(piezas_txt)


# ---------------------------------------------------------------------------
# Los videos de los talleres se listan, no se copian
# ---------------------------------------------------------------------------

def videos_del_taller():
    """El catálogo de los talleres ya existe y ya tiene sus 24 páginas. Aquí se
    leen para que aparezcan en el índice —si no, la mitad de la biblioteca
    seguiría escondida detrás de un día de taller— pero no se duplican: la
    tarjeta enlaza a la página que genera talleres/build.py."""
    ruta = REPO / "talleres" / "videos.yaml"
    if not ruta.exists():
        return []
    catalogo = (yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}).get("videos", {})
    fuera = []
    for vid, v in catalogo.items():
        fuera.append(
            (
                vid,
                {
                    "tipo": "video",
                    "titulo": v.get("titulo", vid),
                    "autor": v.get("autor", ""),
                    "fuente": "YouTube",
                    "idioma": v.get("idioma", ""),
                    "extension": v.get("duracion", ""),
                    # Del resumen y NO del `conecta`: el `conecta` está escrito
                    # para la página del video dentro del taller y habla desde
                    # ahí ("ya sabes que arranca donde termina el día de hoy").
                    # En la biblioteca no hay un "hoy", así que esa frase llega
                    # sin referente. El resumen describe el video y se sostiene
                    # solo en cualquier sitio.
                    "engancho": primera_frase(v.get("resumen") or ""),
                    "resumen": v.get("resumen"),
                    "_cta": "Ver el video",
                },
                f"../talleres/videos/{vid}.html",
            )
        )
    return fuera


# ---------------------------------------------------------------------------
# Las dos portadas
# ---------------------------------------------------------------------------

def render_indice(nombre, ctx):
    plantilla = (RAIZ / "plantilla-indice.html").read_text(encoding="utf-8")
    salida = plantilla
    for clave, valor in ctx.items():
        salida = salida.replace("{{" + clave + "}}", valor)
    (RAIZ / nombre).write_text(salida, encoding="utf-8")


def render_inbox(inbox):
    if not inbox:
        return ""
    filas = []
    for x in sorted(inbox, key=lambda i: str(i.get("fecha", "")), reverse=True):
        fecha = f'<span class="fecha">{e(x["fecha"])}</span>' if x.get("fecha") else ""
        texto = marcado(x.get("engancho") or x.get("url", ""))
        filas.append(
            f'<li>{fecha}<span class="q">{texto}</span>'
            f'<a href="{e(x.get("url", "#"))}" target="_blank" rel="noopener">Abrir ↗</a></li>'
        )
    return f"""<div class="seccion">
      <h2>Por leer</h2>
      <p class="sub">Captura rápida: entra aquí en diez segundos y sin compromiso.
      Solo sube a ficha lo que a los pocos días siga pareciendo importante.</p>
      <ul class="cola">{''.join(filas)}</ul>
    </div>"""


def construir():
    piezas, inbox = cargar()

    for slug, p in piezas.items():
        render_ficha(slug, p)

    libros = {s: p for s, p in piezas.items() if p["tipo"] == "libro"}
    otras = {s: p for s, p in piezas.items() if p["tipo"] != "libro"}

    # ------------------------------------------------------------- biblioteca
    propias = [(s, p, None) for s, p in otras.items()]
    tarjetas = [tarjeta(s, p, href) for s, p, href in propias + videos_del_taller()]
    todas = [p for _, p, _ in propias + videos_del_taller()]
    render_indice(
        "index.html",
        {
            "TITULO": "Biblioteca",
            "KICKER": "Lo que leo, veo y escucho",
            "TITULAR": "Biblioteca",
            "ENTRADA": (
                "Artículos, noticias, videos y podcasts que valen la pena, cada uno "
                "con lo que dice, lo que me llevo y —sobre todo— dónde se queda corto. "
                "Si una pieza no tiene ningún reparo, probablemente no se leyó con cuidado."
            ),
            "OTRA_URL": "libros.html",
            "OTRA_TEXTO": "Club de lectura",
            "FILTROS": filtros(todas),
            "REJILLA": rejilla(
                tarjetas,
                "<b>Todavía no hay ninguna ficha.</b>Se añaden en "
                "<code>biblioteca/catalogo.yaml</code> y aparecen aquí con "
                "<code>python biblioteca/build.py</code>.",
            ),
            "EXTRA": "",
            "INBOX": render_inbox(inbox),
            "PIE": (
                "Portada generada por <code>biblioteca/build.py</code> desde "
                "<code>biblioteca/catalogo.yaml</code>. Los videos de los talleres se "
                "listan desde <code>talleres/videos.yaml</code>, donde ya viven."
            ),
        },
    )

    # ---------------------------------------------------------- club de lectura
    orden = {"leyendo": 0, "por-leer": 1, "terminado": 2, "abandonado": 3}
    en_orden = sorted(libros.items(), key=lambda kv: orden.get(kv[1].get("estado", "por-leer"), 9))
    render_indice(
        "libros.html",
        {
            "TITULO": "Club de lectura",
            "KICKER": "Un libro a la vez, con preguntas",
            "TITULAR": "Club de lectura",
            "ENTRADA": (
                "Los libros del programa, con su plan por tramos, las preguntas de cada "
                "sesión y los subrayados que sobrevivieron. Un libro abandonado también "
                "cuenta: decir por qué se dejó suele valer más que terminarlo."
            ),
            "OTRA_URL": "index.html",
            "OTRA_TEXTO": "Biblioteca",
            "FILTROS": "",
            "REJILLA": rejilla(
                [tarjeta(s, p) for s, p in en_orden],
                "<b>Todavía no hay ningún libro.</b>Se añaden en "
                "<code>biblioteca/catalogo.yaml</code> con <code>tipo: libro</code> y "
                "aparecen aquí con <code>python biblioteca/build.py</code>.",
            ),
            "EXTRA": "",
            "INBOX": "",
            "PIE": (
                "Portada generada por <code>biblioteca/build.py</code> desde "
                "<code>biblioteca/catalogo.yaml</code>."
            ),
        },
    )

    return piezas


def main():
    solo_pendientes = "--pendientes" in sys.argv
    piezas = construir()

    faltan = {s: p for s, p in piezas.items() if not escrita(p)}
    if not solo_pendientes:
        libros = sum(1 for p in piezas.values() if p["tipo"] == "libro")
        print(
            f"✓ biblioteca: {len(piezas)} ficha(s) ({libros} libro(s)), "
            f"index.html y libros.html"
        )

    # Igual que con los videos: una pieza sin escribir no rompe el build, pero
    # se lista. Un pendiente que no se ve deja de ser un pendiente y pasa a ser
    # un hueco.
    if faltan:
        print(f"\n⧗ {len(faltan)} de {len(piezas)} piezas esperan su ficha:")
        for slug, p in faltan.items():
            print(f"    {NOMBRE_TIPO[p['tipo']]:9} {p['titulo'][:58]:58} → {slug}.html")
        print("  Se escriben en biblioteca/catalogo.yaml (resumen, valioso, conecta, reparos).")
    elif piezas:
        print("  Todas las piezas tienen su ficha escrita.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
