#!/usr/bin/env python3
"""
generar_articulos_data.py — Escanea /articulos/*.html y genera
articulos-data.json automáticamente, leyendo título, resumen y categoría
directo del HTML de cada artículo. Nunca hay que mantenerlo a mano ni
volver a pedírselo a nadie — si el dato está en el artículo, aparece aquí.

Se corre solo vía GitHub Actions (mismo workflow que el sitemap), pero
también lo puedes correr manual:
    python3 generar_articulos_data.py
"""

import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).parent
ARTICULOS_DIR = ROOT / "articulos"
SALIDA = ROOT / "articulos-data.json"


def limpiar(txt: str) -> str:
    txt = txt.replace("&nbsp;", " ")
    txt = re.sub(r"<br\s*/?>", " ", txt)
    txt = re.sub(r"<[^>]+>", "", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def extraer_primero(patrones, html):
    for patron in patrones:
        m = re.search(patron, html, re.DOTALL)
        if m:
            return limpiar(m.group(1))
    return ""


def fecha_git(path: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cd", "--date=short", "--", str(path)],
            cwd=ROOT, capture_output=True, text=True, timeout=5
        )
        f = out.stdout.strip()
        if f:
            return f
    except Exception:
        pass
    return date.today().isoformat()


def main():
    if not ARTICULOS_DIR.exists():
        print("No existe la carpeta /articulos, no hay nada que generar.")
        return

    articulos = []

    for p in sorted(ARTICULOS_DIR.glob("*.html")):
        if p.name.startswith("_"):
            continue  # plantillas, no son artículos reales

        html = p.read_text(encoding="utf-8", errors="ignore")

        titulo = extraer_primero([
            r'<h1 class="article-title">(.*?)</h1>',
            r'<h1 class="hero-title">(.*?)</h1>',
            r'<h1[^>]*>(.*?)</h1>',
        ], html) or p.stem

        resumen = extraer_primero([
            r'<p class="article-dek">\s*(.*?)\s*</p>',
            r'<p class="hero-subtitle">\s*(.*?)\s*</p>',
        ], html)

        cat_m = re.search(r'articulos\.html\?cat=([^"]+)"', html)
        categoria = unquote(cat_m.group(1)) if cat_m else "General"

        articulos.append({
            "slug": p.stem,
            "titulo": titulo,
            "resumen": resumen[:220],
            "categoria": categoria,
            "fecha": fecha_git(p),
        })

    SALIDA.write_text(
        json.dumps(articulos, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    print(f"articulos-data.json generado con {len(articulos)} artículos.")


if __name__ == "__main__":
    sys.exit(main())
