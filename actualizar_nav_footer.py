#!/usr/bin/env python3
"""
actualizar_nav_footer.py — Aplica el nav y footer compartidos a todos los
artículos en /articulos/, leyendo las plantillas en /_partials/.

QUÉ HACE
--------
1. NAV: reemplaza el <nav class="site-nav">...</nav> completo de cada
   artículo por el contenido de _partials/nav.html. Como es un reemplazo
   total, agregar una sección nueva al nav (como pasó con Hitos Médicos)
   se hace UNA vez en _partials/nav.html y se propaga sola a todos los
   artículos la próxima vez que corra este script.

2. FOOTER — social: si el artículo todavía no tiene el bloque de redes
   sociales, lo inserta (desde _partials/footer-social.html) justo
   después de la tarjeta de marca (.footer-brand), dentro de
   .footer-nav-grid. También inserta el CSS necesario
   (_partials/footer-social.css) una sola vez, si no está ya presente.

3. FOOTER — línea final: cambia el texto de <p class="footer-copy"> por
   COPY_LINE (abajo). Ojo: solo la línea corta del final, NO toca el
   footer-signal (que identifica el artículo) ni el resto del footer.

NO TOCA el contenido del artículo, ni la columna "// Artículos"
(relacionados) que cada página ya trae curada a mano.

Se corre solo vía GitHub Actions, o manual:
    python3 actualizar_nav_footer.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
ARTICULOS_DIR = ROOT / "articulos"
PARTIALS_DIR = ROOT / "_partials"

COPY_LINE = "Mundo Maravilloso · Hecho en El Salvador · 2026"

NAV_RE = re.compile(r'<nav class="site-nav">.*?</nav>', re.DOTALL)
FOOTER_BRAND_CLOSE_RE = re.compile(
    r'(<div class="footer-brand">.*?</div>\s*)(<div class="footer-nav-grid">)',
    re.DOTALL
)
FOOTER_COPY_RE = re.compile(r'(<p class="footer-copy">)[^<]*(</p>)')


def cargar_partial(nombre: str) -> str:
    p = PARTIALS_DIR / nombre
    if not p.exists():
        print(f"❌ Falta la plantilla {nombre} en /_partials — abortando.")
        sys.exit(1)
    return p.read_text(encoding="utf-8").strip()


def main():
    if not ARTICULOS_DIR.exists():
        print("No existe /articulos — nada que hacer.")
        return

    nav_nuevo = cargar_partial("nav.html")
    social_html = cargar_partial("footer-social.html")
    social_css = cargar_partial("footer-social.css")

    tocados = 0

    for p in sorted(ARTICULOS_DIR.glob("*.html")):
        if p.name.startswith("_"):
            continue

        html = p.read_text(encoding="utf-8")
        original = html

        # 1. NAV — reemplazo total
        if NAV_RE.search(html):
            html = NAV_RE.sub(lambda m: nav_nuevo, html, count=1)
        else:
            print(f"  ⚠️  {p.name}: no encontré <nav class=\"site-nav\"> — nav no tocado.")

        # 2. FOOTER — insertar bloque social si no existe todavía
        if "footer-social-links" not in html:
            html, n = FOOTER_BRAND_CLOSE_RE.subn(
                lambda m: m.group(1) + social_html + "\n      " + m.group(2),
                html, count=1
            )
            if n == 0:
                print(f"  ⚠️  {p.name}: no encontré dónde insertar el bloque social.")

        # 2b. CSS del bloque social, una sola vez
        if 'id="footer-social-css"' not in html:
            html = html.replace("</head>", social_css + "\n</head>", 1)

        # 3. FOOTER — línea final
        html, n = FOOTER_COPY_RE.subn(r'\g<1>' + COPY_LINE + r'\g<2>', html, count=1)

        if html != original:
            p.write_text(html, encoding="utf-8")
            tocados += 1
            print(f"  ✓ {p.name}: actualizado.")

    print(f"\n{tocados} artículo(s) actualizados de {len(list(ARTICULOS_DIR.glob('*.html')))}.")


if __name__ == "__main__":
    sys.exit(main())
