#!/usr/bin/env python3
"""
generar_fixed_cards.py — Lee un pequeño bloque de datos en cada página de
/seguimientos/ y actualiza las tarjetas de "Secciones fijas" en index.html
automáticamente. Así nunca más se desactualiza un número a mano.

CÓMO FUNCIONA
-------------
Cada archivo en /seguimientos/*.html debe tener, en cualquier parte del
<head> o el <body>, un bloque como este:

    <script type="application/json" id="fixed-card-data">
    {"update_label": "10 jul 2026", "stat_strong": "334", "stat_label": "documentos publicados"}
    </script>

- update_label: el texto que aparece junto al punto verde ("Act. X" o
  "N° tanda · fecha")
- stat_strong: el número/dato en negrita de la línea inferior
- stat_label: el texto que acompaña a ese número

Cuando actualices una página de seguimiento, solo edita esas 3 líneas del
bloque JSON — el resto de la tarjeta en index.html se actualiza solo la
próxima vez que corra este script (automático, vía GitHub Actions).

Se corre solo, pero también puedes correrlo manual:
    python3 generar_fixed_cards.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SEGUIMIENTOS_DIR = ROOT / "seguimientos"
INDEX_FILE = ROOT / "index.html"

DATA_BLOCK_RE = re.compile(
    r'<script type="application/json" id="fixed-card-data">\s*(\{.*?\})\s*</script>',
    re.DOTALL
)


def leer_datos_seguimiento(path: Path):
    html = path.read_text(encoding="utf-8", errors="ignore")
    m = DATA_BLOCK_RE.search(html)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError as e:
        print(f"  ⚠️  JSON inválido en {path.name}: {e}")
        return None


def actualizar_tarjeta(index_html: str, slug: str, datos: dict) -> str:
    # Aísla el bloque <a href="seguimientos/{slug}.html" class="fixed-card ...">...</a>
    patron_card = re.compile(
        r'(<a href="seguimientos/' + re.escape(slug) + r'\.html" class="fixed-card[^"]*">.*?</a>)',
        re.DOTALL
    )
    m = patron_card.search(index_html)
    if not m:
        print(f"  ⚠️  No encontré la tarjeta de '{slug}' en index.html — la omito.")
        return index_html

    bloque = m.group(1)
    nuevo_bloque = bloque

    if "update_label" in datos:
        nuevo_bloque = re.sub(
            r'(<span class="fixed-card-update">)[^<]*(</span>)',
            r'\g<1>' + datos["update_label"] + r'\g<2>',
            nuevo_bloque
        )

    if "stat_strong" in datos and "stat_label" in datos:
        nuevo_bloque = re.sub(
            r'(<span class="fixed-card-stat"><strong>)[^<]*(</strong>)[^<]*(</span>)',
            r'\g<1>' + datos["stat_strong"] + r'\g<2> ' + datos["stat_label"] + r'\g<3>',
            nuevo_bloque
        )

    return index_html[:m.start()] + nuevo_bloque + index_html[m.end():]


def main():
    if not SEGUIMIENTOS_DIR.exists() or not INDEX_FILE.exists():
        print("No encuentro /seguimientos o index.html — nada que hacer.")
        return

    index_html = INDEX_FILE.read_text(encoding="utf-8")
    cambios = 0

    for p in sorted(SEGUIMIENTOS_DIR.glob("*.html")):
        slug = p.stem
        datos = leer_datos_seguimiento(p)
        if datos is None:
            print(f"  — {slug}: sin bloque de datos, se deja como está.")
            continue

        antes = index_html
        index_html = actualizar_tarjeta(index_html, slug, datos)
        if index_html != antes:
            cambios += 1
            print(f"  ✓ {slug}: tarjeta actualizada.")

    if cambios:
        INDEX_FILE.write_text(index_html, encoding="utf-8")
        print(f"\nindex.html actualizado — {cambios} tarjeta(s) con cambios.")
    else:
        print("\nSin cambios en ninguna tarjeta.")


if __name__ == "__main__":
    sys.exit(main())
