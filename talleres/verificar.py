#!/usr/bin/env python3
"""
Verifica que un taller generado no tenga huecos.

La prueba es la que importa pedagógicamente: si el alumno copia los bloques de
código de la página EN ORDEN y los pega en un archivo, ¿le queda exactamente el
archivo que corre? Si la respuesta es no, hay un hueco, y ese es el defecto que
tenían los decks.

Se comprueban las dos caras del bloque por separado:

  * lo que se VE:    el HTML renderizado, línea por línea
  * lo que se COPIA: el atributo data-codigo, que es lo que lee el botón

Tienen que coincidir entre sí y con el archivo fuente.

Uso:
    python talleres/verificar.py              # verifica todos
    python talleres/verificar.py sesion-04    # verifica uno

Devuelve 1 si algo no cuadra. Sirve en CI.
"""

import html
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

BLOQUE = re.compile(
    r'<div class="bloque[^"]*" data-codigo="(?P<fuente>[^"]*)">'
    r'.*?<span class="ruta">(?P<ruta>[^<]+)</span>'
    r".*?<pre><code>(?P<render>.*?)</code></pre>",
    re.S,
)
RANGO = re.compile(r"(\S+) · líneas (\d+)–(\d+)")
LINEA = '<span class="l">'


def sin_etiquetas(fragmento):
    return html.unescape(re.sub(r"<[^>]+>", "", fragmento))


def lineas_renderizadas(render):
    """Reconstruye el texto visible. Cada línea es un <span class="l">."""
    trozos = render.split(LINEA)[1:]
    return "\n".join(sin_etiquetas(t.rsplit("</span>", 1)[0]) for t in trozos)


def verificar(nombre):
    pagina_ruta = RAIZ / f"{nombre}.html"
    base = RAIZ / nombre / "codigo"
    if not pagina_ruta.exists():
        print(f"  ✗ falta {pagina_ruta.name}. Corre primero build.py")
        return 1

    pagina = pagina_ruta.read_text(encoding="utf-8")
    partes, fallos = {}, 0

    for m in BLOQUE.finditer(pagina):
        ruta = html.unescape(m.group("ruta"))
        fuente = html.unescape(m.group("fuente"))
        visible = lineas_renderizadas(m.group("render"))

        # 1. Lo que se ve tiene que ser lo que se copia.
        if visible != fuente:
            fallos += 1
            print(f"  ✗ {ruta}: lo que se muestra no es lo que copia el botón")

        r = RANGO.match(ruta)
        if r:
            partes.setdefault(r.group(1), []).append((int(r.group(2)), fuente))

    if not partes:
        print("  ✗ la página no tiene bloques de código con rango de líneas")
        return 1

    # 2. Los bloques de un archivo, pegados en orden, tienen que dar el archivo.
    for archivo, trozos in sorted(partes.items()):
        trozos.sort()
        reconstruido = "\n".join(t for _, t in trozos)
        original = (base / archivo).read_text(encoding="utf-8").rstrip("\n")
        if reconstruido == original:
            print(f"  ✓ {archivo}: {len(trozos)} bloques reconstruyen el fuente")
            continue
        fallos += 1
        print(f"  ✗ {archivo}: lo que se copia de la página NO es el archivo")
        esperado, obtenido = original.splitlines(), reconstruido.splitlines()
        for i, (a, b) in enumerate(zip(esperado, obtenido), start=1):
            if a != b:
                print(f"      primera diferencia en la línea {i}:")
                print(f"        archivo: {a!r}")
                print(f"        página : {b!r}")
                break
        else:
            print(f"      largos distintos: {len(esperado)} vs {len(obtenido)} líneas")
    return fallos


def main():
    nombres = [a for a in sys.argv[1:] if not a.startswith("-")] or [
        d.name for d in sorted(RAIZ.iterdir()) if (d / "taller.yaml").exists()
    ]
    total = 0
    for n in nombres:
        print(f"{n}:")
        total += verificar(n)
    print(
        "\n✓ Sin huecos: lo que se ve, lo que se copia y el archivo fuente coinciden."
        if not total
        else f"\n✗ {total} problema(s)."
    )
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
