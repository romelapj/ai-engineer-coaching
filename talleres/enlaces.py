#!/usr/bin/env python3
"""Comprueba que ningún enlace relativo del sitio apunte a un archivo que no existe.

Nace de un fallo real: las 24 páginas de video tuvieron el enlace de marca roto
desde que se generaron, porque un `lstrip("./")` se comía los dos puntos del
`../`. Nadie lo vio porque nada lo miraba.

No toca la red: los enlaces externos (http, mailto) se ignoran a propósito.
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENLACE = re.compile(r'(?:href|src)="([^"#][^"]*)"')


def main():
    rotos = []
    revisados = 0
    for pagina in sorted(REPO.rglob("*.html")):
        # .diseno guarda los archivos de trabajo del canvas de diseño, que no
        # forman parte del sitio: sus "enlaces" son placeholders del editor.
        if any(p in {".git", "node_modules", ".diseno"} for p in pagina.parts):
            continue
        # Las plantillas no son páginas: sus enlaces son placeholders {{...}}
        # que build.py rellena al generar.
        if pagina.name.startswith("plantilla"):
            continue
        texto = pagina.read_text(encoding="utf-8", errors="replace")
        for destino in ENLACE.findall(texto):
            if re.match(r"^(https?:|mailto:|data:|//)", destino):
                continue
            revisados += 1
            ruta = (pagina.parent / destino.split("?")[0].split("#")[0]).resolve()
            if not ruta.exists():
                rotos.append((pagina.relative_to(REPO), destino))

    for pagina, destino in rotos:
        print(f"  ✗ {pagina} → {destino}")
    print(
        f"{'✗' if rotos else '✓'} {revisados} enlaces relativos revisados, "
        f"{len(rotos)} rotos"
    )
    return 1 if rotos else 0


if __name__ == "__main__":
    sys.exit(main())
