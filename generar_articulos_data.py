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


def limpiar(txt: str) -> str:
    txt = html_lib.unescape(txt)
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

    Esta es la fuente más confiable para categoria: no depende de qué
    clase CSS use la plantilla para la etiqueta visual, y evita el bug
    anterior (regex buscando un link "articulos.html?cat=X" que nunca
    existió). Se parsea línea por línea dentro del comentario.
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


def extraer_meta_description(html: str) -> str:
    """
    Busca <meta name="description" content="..."> sin importar el orden
    de los atributos ni las comillas usadas. Es la fuente más confiable:
    está presente en el 100% de los artículos (incluyendo herramientas
    interactivas sin dek propio, como los mapas) y suele ser más completa
    que los deks cortos del cuerpo del artículo.
    """
    for m in re.finditer(r"<meta\s+[^>]*>", html, re.IGNORECASE):
        tag = m.group(0)
        if re.search(r'name=["\']description["\']', tag, re.IGNORECASE):
            # \1 fuerza a que la comilla de cierre sea del MISMO tipo que la
            # de apertura. Sin esto, una descripción con comillas simples
            # adentro (p.ej. 'The Phantom Phenomenon') corta ahí por error,
            # porque .*? con ["\'] como clase de caracteres para el cierre
            # se detiene en la PRIMERA comilla de cualquier tipo que encuentra.
            cm = re.search(r'content=(["\'])(.*?)\1', tag, re.DOTALL)
            if cm:
                return limpiar(cm.group(2))
    return ""


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
    for p in sorted(ARTICULOS_DIR.glob("*.html")):
        if p.name.startswith("_"):
            continue  # plantillas, no son artículos reales
        html = p.read_text(encoding="utf-8", errors="ignore")

        mm_meta = extraer_mm_meta(html)

        # PRIORIDAD 1: bloque <!-- MM-META --> al inicio del archivo.
        # PRIORIDAD 2 (respaldo, artículos viejos sin el bloque): buscar
        # el <h1> según la plantilla que use.
        titulo = mm_meta.get("titulo") or extraer_primero([
            r'<h1 class="article-title">(.*?)</h1>',
            r'<h1 class="hero-title">(.*?)</h1>',
            r'<h1 class="hero-doc-title">(.*?)</h1>',
            r'<h1 class="tool-title">(.*?)</h1>',
            r'<h1[^>]*>(.*?)</h1>',
        ], html) or p.stem

        # PRIORIDAD 1: "blurb" del bloque MM-META.
        # PRIORIDAD 2: meta description — está en el 100% de los artículos.
        # PRIORIDAD 3: deks visibles en el cuerpo, según la plantilla.
        resumen = (
            mm_meta.get("blurb")
            or extraer_meta_description(html)
            or extraer_primero([
                r'<p class="hero-doc-subtitle">\s*(.*?)\s*</p>',
                r'<p class="article-dek">\s*(.*?)\s*</p>',
                r'<p class="hero-subtitle">\s*(.*?)\s*</p>',
            ], html)
        )

        # Categoría: se lee de "categoria" en el bloque MM-META. No se
        # adivina desde las etiquetas visuales (hero-eyebrow, hero-doc-
        # eyebrow, article-section-label, hero-kicker...) porque su texto
        # no es un slug limpio (ej. "PURSUE · Fact-Check"). Si un artículo
        # viejo no trae el bloque MM-META, cae en "General".
        categoria = mm_meta.get("categoria") or "General"

        articulos.append({
            "slug": p.stem,
            "titulo": titulo,
            "resumen": truncar(resumen),
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
