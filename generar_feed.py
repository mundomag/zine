#!/usr/bin/env python3
"""
generar_feed.py — Genera feed.xml (RSS 2.0) a partir de articulos-data.json.

Se corre DESPUÉS de generar_articulos_data.py en el mismo workflow, para
que siempre lea los datos más recientes.

No hay que mantenerlo a mano nunca — cada artículo nuevo que entre a
articulos-data.json aparece solo en el feed la próxima vez que corra.

    python3 generar_feed.py
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "articulos-data.json"
SALIDA = ROOT / "feed.xml"

SITE_URL = "https://mundomag.fyi"
SITE_TITLE = "Mundo Maravilloso"
SITE_DESC = "Ciencia, misterio, fenómenos y futuro — revista digital independiente."
MAX_ITEMS = 30  # no hace falta meter los 100+ artículos que tendrás algún día


def rfc822(fecha_iso: str) -> str:
    """'2026-07-10' -> 'Fri, 10 Jul 2026 00:00:00 +0000' (formato que pide RSS)."""
    try:
        dt = datetime.strptime(fecha_iso, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        dt = datetime.now(timezone.utc)
    return dt.strftime("%a, %d %b %Y %H:%M:%S %z")


def main():
    if not DATA_FILE.exists():
        print("No existe articulos-data.json todavía — nada que hacer.")
        return

    articulos = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    articulos = sorted(articulos, key=lambda a: a.get("fecha", ""), reverse=True)[:MAX_ITEMS]

    ahora = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")

    items = []
    for a in articulos:
        loc = f"{SITE_URL}/articulos/{a['slug']}.html"
        items.append(f"""    <item>
      <title>{escape(a['titulo'])}</title>
      <link>{escape(loc)}</link>
      <guid isPermaLink="true">{escape(loc)}</guid>
      <description>{escape(a.get('resumen', ''))}</description>
      <category>{escape(a.get('categoria', 'General'))}</category>
      <pubDate>{rfc822(a.get('fecha', ''))}</pubDate>
    </item>""")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{escape(SITE_TITLE)}</title>
    <link>{SITE_URL}/</link>
    <description>{escape(SITE_DESC)}</description>
    <language>es</language>
    <lastBuildDate>{ahora}</lastBuildDate>
    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
{chr(10).join(items)}
  </channel>
</rss>
"""

    SALIDA.write_text(xml, encoding="utf-8")
    print(f"feed.xml generado con {len(articulos)} artículos.")


if __name__ == "__main__":
    sys.exit(main())
