#!/usr/bin/env python3
"""
generar_articulos_data.py — Escanea /articulos/*.html y genera
articulos-data.json automáticamente, leyendo título, resumen y categoría
directo del bloque <!-- MM-META --> de cada artículo.

Si un artículo NO trae el bloque MM-META, o le falta alguno de los campos
obligatorios (titulo, categoria, blurb), se omite del JSON — no se rellena
adivinando datos desde el HTML (h1, meta description, deks, etc).

Se corre solo vía GitHub Actions (mismo workflow que el sitemap), pero
también lo puedes correr manual:
    python3 generar_articulos_data.py
"""
import html as html_lib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
ARTICULOS_DIR = ROOT / "articulos"
SALIDA = ROOT / "articulos-data.json"

RESUMEN_MAX = 220

# Campos que el bloque MM-META debe traer, sí o sí, para que el artículo
# se incluya en el JSON.
CAMPOS_REQUERIDOS = ("titulo", "categoria", "blurb")


def limpiar(txt: str) -> str:
    txt = html_lib.unescape(txt)
    txt = txt.replace("&nbsp;", " ")
    txt = re.sub(r"<br\s*/?>", " ", txt)
    txt = re.sub(r"<[^>]+>", "", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def extraer_mm_meta(html: str) -> dict:
    """
    Cada plantilla de artículo trae un bloque de comentario al inicio del
    archivo con los metadatos "de verdad" (slug, titulo, categoria, blurb,
    fecha, formato), por ejemplo:

        <!-- MM-META
        slug: el-fenomeno-fantasma
        titulo: The Phantom Phenomenon: ...
        categoria: mitologia-moderna
        blurb: Un diagrama casero de 1979 ...
        fecha: 2026-07-22
        formato: hero-documental-v1
        -->

    Esta es la ÚNICA fuente de metadatos: no depende de qué clase CSS use
    la plantilla para la etiqueta visual, y evita el bug anterior (regex
    buscando un link "articulos.html?cat=X" que nunca existió). Se parsea
    línea por línea dentro del comentario.
    """
    datos = {}
    m = re.search(r"<!--\s*MM-META\s*(.*?)-->", html, re.DOTALL)
    if not m:
        return datos
    bloque = m.group(1)
    for linea in bloque.splitlines():
        lm = re.match(r"\s*([a-zA-Z_]+)\s*:\s*(.*?)\s*$", linea)
        if lm:
            clave, valor = lm.group(1), lm.group(2)
            if valor:
                datos[clave] = limpiar(valor)
    return datos


def truncar(txt: str, maximo: int = RESUMEN_MAX) -> str:
    """Corta en el límite de palabra más cercano y agrega '…' si truncó,
    en vez de cortar a la mitad de una palabra sin avisar."""
    if len(txt) <= maximo:
        return txt
    recorte = txt[:maximo]
    ultimo_espacio = recorte.rfind(" ")
    if ultimo_espacio > 0:
        recorte = recorte[:ultimo_espacio]
    return recorte.rstrip(",.;: ") + "…"


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
    omitidos = 0

    for p in sorted(ARTICULOS_DIR.glob("*.html")):
        if p.name.startswith("_"):
            continue  # plantillas, no son artículos reales

        html = p.read_text(encoding="utf-8", errors="ignore")
        mm_meta = extraer_mm_meta(html)

        # Si falta el bloque MM-META, o le falta algún campo obligatorio,
        # el artículo se omite por completo del JSON.
        faltantes = [c for c in CAMPOS_REQUERIDOS if not mm_meta.get(c)]
        if faltantes:
            omitidos += 1
            motivo = ", ".join(faltantes) if mm_meta else "sin bloque MM-META"
            print(f"  omitido {p.name}: falta {motivo}")
            continue

        articulos.append({
            "slug": p.stem,
            "titulo": mm_meta["titulo"],
            "resumen": truncar(mm_meta["blurb"]),
            "categoria": mm_meta["categoria"],
            "fecha": mm_meta.get("fecha") or fecha_git(p),
        })

    SALIDA.write_text(
        json.dumps(articulos, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    print(f"articulos-data.json generado con {len(articulos)} artículos "
          f"({omitidos} omitidos por falta de MM-META).")


if __name__ == "__main__":
    sys.exit(main())
