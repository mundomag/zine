#!/usr/bin/env python3
"""
generar_sitemap.py — Escanea el repo de mundomag.fyi y genera sitemap.xml
automáticamente. Detecta artículos y páginas nuevas sin que tengas que
tocar nada a mano.
"""

import subprocess
import sys
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

SITE_URL = "https://mundomag.fyi"
ROOT = Path(__file__).parent

EXCLUIR_DIRS = {".git", ".github", "node_modules", ".vscode"}
EXCLUIR_ARCHIVOS = {"404.html"}
EXCLUIR_PREFIJOS = ("_",)

REGLAS = [
    (lambda rel: rel == "index.html",                    1.0, "weekly"),
    (lambda rel: rel == "articulos.html",                 0.9, "weekly"),
    (lambda rel: rel.startswith("articulos/"),            0.8, "monthly"),
    (lambda rel: rel in ("seguimientos/3i-atlas.html",
                          "seguimientos/uap-watch.html"),  0.9, "daily"),
    (lambda rel: rel.startswith("seguimientos/"),          0.8, "weekly"),
    (lambda rel: rel == "glosario.html",                  0.4, "monthly"),
    (lambda rel: rel == "acerca-de.html",                 0.5, "yearly"),
    (lambda rel: rel == "contacto.html",                  0.4, "yearly"),
    (lambda rel: rel in ("privacidad.html", "terminos.html"), 0.3, "yearly"),
]
DEFAULT_PRIORIDAD, DEFAULT_FREQ = 0.6, "monthly"


def reglas_para(rel: str):
    for match, prioridad, freq in REGLAS:
        if match(rel):
            return prioridad, freq
    return DEFAULT_PRIORIDAD, DEFAULT_FREQ


def lastmod_git(path: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cd", "--date=short", "--", str(path)],
            cwd=ROOT, capture_output=True, text=True, timeout=5
        )
        fecha = out.stdout.strip()
        if fecha:
            return fecha
    except Exception:
        pass
    return date.today().isoformat()


def main():
    htmls = sorted(ROOT.rglob("*.html"))
    entradas = []

    for p in htmls:
        rel = p.relative_to(ROOT).as_posix()

        if any(part in EXCLUIR_DIRS for part in p.parts):
            continue
        if p.name in EXCLUIR_ARCHIVOS:
            continue
        if p.name.startswith(EXCLUIR_PREFIJOS):
            continue

        prioridad, freq = reglas_para(rel)
        lastmod = lastmod_git(p)
        loc = f"{SITE_URL}/{rel}" if rel != "index.html" else f"{SITE_URL}/"

        entradas.append((loc, lastmod, freq, prioridad))

    lineas = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod, freq, prioridad in entradas:
        lineas.append("  <url>")
        lineas.append(f"    <loc>{escape(loc)}</loc>")
        lineas.append(f"    <lastmod>{lastmod}</lastmod>")
        lineas.append(f"    <changefreq>{freq}</changefreq>")
        lineas.append(f"    <priority>{prioridad}</priority>")
        lineas.append("  </url>")
    lineas.append("</urlset>")

    salida = ROOT / "sitemap.xml"
    salida.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"sitemap.xml generado con {len(entradas)} URLs.")


if __name__ == "__main__":
    sys.exit(main())
