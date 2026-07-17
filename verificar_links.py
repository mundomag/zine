#!/usr/bin/env python3
"""
verificar_links.py — Revisa TODOS los archivos .html del repo y valida que
cada link interno (href) y cada imagen (src) apunte a un archivo que
realmente existe. No usa internet — chequea contra el propio sistema de
archivos, así que detecta el problema en el mismo commit, sin esperar a
que el sitio esté desplegado ni a que Google lo rastree.

Habría detectado solo, sin revisión manual:
  - El nav viejo de tunguska apuntando a index-ed-3.html (ya no existe)
  - Los 31 artículos sin el link a Hitos Médicos (si esa página no
    existiera todavía)
  - Cualquier link relacionado que apunte a un slug mal escrito

Se corre semanalmente vía GitHub Actions, o manual:
    python3 verificar_links.py
Sale con código de error si encuentra algo roto, así el Action queda en
rojo ❌ y GitHub te avisa por correo — no hay que revisar nada a mano.
"""

import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent

EXCLUIR_DIRS = {".git", ".github", "node_modules", ".vscode"}

# No son links internos que debamos validar como archivos
ESQUEMAS_EXTERNOS = ("http://", "https://", "mailto:", "tel:", "javascript:", "data:")

REF_RE = re.compile(r'(?:href|src)="([^"]+)"')


def es_externo_o_ignorable(href: str) -> bool:
    if not href or href.startswith("#"):
        return True
    if href.startswith(ESQUEMAS_EXTERNOS):
        return True
    return False


def resolver_ruta(href: str, archivo_origen: Path) -> Path:
    """Convierte un href (absoluto '/x.html' o relativo '../x.html') en una
    ruta real del sistema de archivos, sin query string ni #fragmento."""
    limpio = href.split("?")[0].split("#")[0]
    if not limpio:
        return None

    if limpio.startswith("/"):
        destino = ROOT / limpio.lstrip("/")
    else:
        destino = (archivo_origen.parent / limpio).resolve()

    return destino


def main():
    htmls = [
        p for p in ROOT.rglob("*.html")
        if not any(part in EXCLUIR_DIRS for part in p.parts)
    ]

    rotos = []
    total_links = 0

    for archivo in sorted(htmls):
        html = archivo.read_text(encoding="utf-8", errors="ignore")
        for href in REF_RE.findall(html):
            if es_externo_o_ignorable(href):
                continue
            total_links += 1
            destino = resolver_ruta(href, archivo)
            if destino is None:
                continue
            if not destino.exists():
                rotos.append((archivo.relative_to(ROOT), href, destino))

    print(f"Revisados {total_links} links internos en {len(htmls)} archivos.\n")

    if not rotos:
        print("✅ Ningún link roto encontrado.")
        return 0

    print(f"❌ {len(rotos)} link(s) roto(s):\n")
    for origen, href, destino in rotos:
        print(f"  {origen}")
        print(f"    → href=\"{href}\"")
        print(f"    → no existe: {destino}\n")

    return 1


if __name__ == "__main__":
    sys.exit(main())
