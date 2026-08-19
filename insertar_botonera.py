#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
insertar_botonera.py
=====================
Inserta la botonera de compartir (X / Facebook / WhatsApp / Copiar enlace)
en artículos HTML ya existentes de STEMS / Mundo Maravilloso.

USO BÁSICO
----------
    python3 insertar_botonera.py articulo.html
    python3 insertar_botonera.py articulos/*.html
    python3 insertar_botonera.py --dry-run articulos/*.html

QUÉ HACE
--------
1. Se asegura de que las reglas CSS de .share-bar existan en tu hoja de
   estilos compartida (por defecto: css-articulos.css, en la misma carpeta
   que el primer archivo HTML que le pases, o la ruta que le indiques con
   --css-file). Solo las agrega una vez.

2. Por cada archivo HTML:
     - Si ya tiene la botonera (detecta el atributo data-share-bar), lo
       salta y no duplica nada. Podés correr el script las veces que quieras.
     - Inserta la barra "de arriba" justo antes de la primera sección de
       contenido (busca <div class="section-head" por defecto).
     - Inserta la barra "de abajo" justo antes de </main>, o antes de
       <div class="related-articles" o <footer si existen.
     - Inserta el <script> que arma los enlaces de compartir en tiempo de
       carga (usa el <title> y el <link rel="canonical"> de cada página,
       así que NO hace falta decirle la URL de cada artículo).

3. Si no encuentra dónde insertar automáticamente en algún archivo, no
   improvisa: te avisa por consola cuáles archivos necesitan que le pases
   --top-anchor / --bottom-anchor personalizados, o que los coloques a mano.

MARCADORES MANUALES (opcional, más seguro en páginas con estructura rara)
---------------------------------------------------------------------
Si preferís elegir vos exactamente dónde va cada barra, poné estos
comentarios en el HTML donde quieras que aparezcan, y el script los
reemplaza directamente:

    <!-- SHARE_BAR_TOP -->
    <!-- SHARE_BAR_BOTTOM -->

OPCIONES
--------
    --dry-run             No escribe nada, solo dice qué haría en cada archivo.
    --css-file RUTA        Ruta a la hoja de estilos compartida (default: busca
                           css-articulos.css en la carpeta del primer HTML).
    --top-anchor TEXTO     Cadena literal antes de la cual insertar la barra
                           superior (default: prueba '<div class="section-head"',
                           luego '<div class="article-body"', luego '<div class="intro"',
                           en ese orden, hasta encontrar una que exista en el archivo).
    --bottom-anchor TEXTO  Cadena literal antes de la cual insertar la barra
                           inferior (default: intenta 'related-articles',
                           luego '</main>', luego '<footer').
    --no-footer-bar        Solo inserta la barra de arriba.
    --no-top-bar           Solo inserta la barra de abajo.

EJEMPLOS
--------
    # Probar en todo articulos/ sin escribir nada todavía
    python3 insertar_botonera.py --dry-run articulos/*.html

    # Aplicar de verdad
    python3 insertar_botonera.py articulos/*.html

    # Un artículo con estructura distinta (ancla personalizada)
    python3 insertar_botonera.py --top-anchor '<div class="intro-body"' articulos/especial.html
"""

import argparse
import pathlib
import sys

SHARE_CSS_MARK = "BOTONERA DE COMPARTIR"

SHARE_CSS = f"""
/* ==== {SHARE_CSS_MARK} (bloque compartido \u2014 no borrar) ==== */
.share-bar{{ max-width:760px; margin:2.5rem auto; display:flex; align-items:center; gap:1.25rem; flex-wrap:wrap; }}
.share-bar-label{{ font-family:"JetBrains Mono",monospace; font-size:0.58rem; letter-spacing:0.2em; text-transform:uppercase; color:var(--muted, #7a7368); white-space:nowrap; }}
.share-buttons{{ display:flex; gap:0.6rem; flex-wrap:wrap; }}
.share-btn{{
  display:inline-flex; align-items:center; justify-content:center;
  width:2.25rem; height:2.25rem; border:1px solid var(--border, rgba(201,168,76,0.16)); border-radius:2px;
  color:rgba(241,235,224,0.7); background:var(--ink-mid, #100e0c); cursor:pointer;
  transition:border-color 0.2s, color 0.2s; padding:0; text-decoration:none;
}}
.share-btn svg{{ width:16px; height:16px; fill:currentColor; }}
.share-btn:hover{{ border-color:var(--accent-light, #e8c96a); color:var(--accent-light, #e8c96a); }}
.share-btn.copied{{ border-color:var(--gold, #c9a84c); color:var(--gold, #c9a84c); }}
.share-bar.is-footer{{ margin-top:4rem; }}
/* ==== FIN {SHARE_CSS_MARK} ==== */
""".strip("\n") + "\n"

ICON_X = '<svg viewBox="0 0 24 24"><path d="M18.9 2H22l-7.6 8.7L23.3 22H16.9l-5-6.5L6.1 22H3l8.1-9.3L2.7 2h6.5l4.5 6ZM17.7 20h1.7L7.4 4H5.5Z"/></svg>'
ICON_FB = '<svg viewBox="0 0 16 16"><path d="M16 8a8 8 0 1 0-9.25 7.9v-5.6H4.9V8h1.85V6.4c0-1.83 1.09-2.84 2.76-2.84.8 0 1.64.14 1.64.14v1.8h-.92c-.91 0-1.19.56-1.19 1.14V8h2.03l-.32 2.3H9.04v5.6A8 8 0 0 0 16 8z"/></svg>'
ICON_WA = '<svg viewBox="0 0 24 24"><path d="M17.5 14.4c-.3-.1-1.7-.9-2-.9-.3-.1-.5-.1-.7.1-.2.3-.8.9-.9 1.1-.2.2-.3.2-.6.1-.3-.1-1.2-.5-2.4-1.5-.9-.8-1.5-1.8-1.6-2.1-.2-.3 0-.5.1-.6.1-.1.3-.3.4-.5.1-.2.2-.3.3-.5.1-.2 0-.4 0-.5C10 9 9.4 7.6 9.2 7c-.2-.5-.4-.5-.6-.5h-.5c-.2 0-.5.1-.7.3-.2.3-.9.9-.9 2.1 0 1.2.9 2.4 1 2.6.1.2 1.8 2.8 4.4 3.9.6.3 1.1.4 1.5.6.6.2 1.2.2 1.6.1.5-.1 1.7-.7 1.9-1.3.2-.6.2-1.1.2-1.3-.1-.1-.3-.2-.6-.3ZM12 2a10 10 0 0 0-8.5 15.2L2 22l4.9-1.3A10 10 0 1 0 12 2Zm0 18.2a8.2 8.2 0 0 1-4.2-1.1l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Z"/></svg>'
ICON_LINK = '<svg viewBox="0 0 24 24" class="icon-link"><path d="M10.6 13.4a1 1 0 0 1 0-1.4l3-3a1 1 0 1 1 1.4 1.4l-3 3a1 1 0 0 1-1.4 0Zm-1.4 4.2-2.1 2.1a3 3 0 0 1-4.2-4.2l3.5-3.5a3 3 0 0 1 4.2 0 1 1 0 0 1-1.4 1.4 1 1 0 0 0-1.4 0l-3.5 3.5a1 1 0 0 0 1.4 1.4l2.1-2.1a1 1 0 0 1 1.4 1.4Zm10.2-10.2-3.5 3.5a3 3 0 0 1-4.2 0 1 1 0 0 1 1.4-1.4 1 1 0 0 0 1.4 0l3.5-3.5a1 1 0 0 0-1.4-1.4l-2.1 2.1a1 1 0 0 1-1.4-1.4l2.1-2.1a3 3 0 0 1 4.2 4.2Z"/></svg>'
ICON_CHECK = '<svg viewBox="0 0 24 24" class="icon-check" style="display:none"><path d="M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2Z"/></svg>'

SHARE_BAR_MARK = "data-share-bar"

# Anclas superiores que se prueban en orden cuando no se pasa --top-anchor.
# '<div class="section-head"' cubre la plantilla Antártida/Bestiario/Mitología.
# '<div class="article-body"' cubre la plantilla Ed.04 (grusch, hollywood-et-*,
# roswell-*, fable5-mythos5-*, loeb-galileo, seti-ia, torio, tunguska,
# uap-actualidad-2026, umbra-*, observador-*, dow-uap-*, pursue*,
# resquebrajamiento*), que no tiene section-head: la barra queda entre el
# bloque de stats (.article-hero-visual) y el cuerpo del artículo.
# '<div class="intro"' cubre alguna variante suelta que no tenga ninguna de
# las dos anteriores.
DEFAULT_TOP_ANCHORS = [
    '<div class="section-head"',
    '<div class="article-body"',
    '<div class="intro"',
]


def share_bar_html(footer: bool = False) -> str:
    extra = " is-footer" if footer else ""
    label = "// Compartir este art\u00edculo" if footer else "// Compartir"
    return f'''
  <div class="share-bar{extra}" data-share-bar>
    <span class="share-bar-label">{label}</span>
    <div class="share-buttons">
      <a class="share-btn" data-share="x" href="#" target="_blank" rel="noopener" aria-label="Compartir en X">{ICON_X}</a>
      <a class="share-btn" data-share="fb" href="#" target="_blank" rel="noopener" aria-label="Compartir en Facebook">{ICON_FB}</a>
      <a class="share-btn" data-share="wa" href="#" target="_blank" rel="noopener" aria-label="Compartir en WhatsApp">{ICON_WA}</a>
      <button class="share-btn" data-share="copy" type="button" aria-label="Copiar enlace">{ICON_LINK}{ICON_CHECK}</button>
    </div>
  </div>
'''


SHARE_JS = '''
<script>
(function(){
  var canonical = document.querySelector('link[rel="canonical"]');
  var url = canonical ? canonical.href : window.location.href;
  var title = document.title;
  document.querySelectorAll('[data-share="x"]').forEach(function(a){
    a.href = 'https://twitter.com/intent/tweet?url=' + encodeURIComponent(url) + '&text=' + encodeURIComponent(title);
  });
  document.querySelectorAll('[data-share="fb"]').forEach(function(a){
    a.href = 'https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(url);
  });
  document.querySelectorAll('[data-share="wa"]').forEach(function(a){
    a.href = 'https://api.whatsapp.com/send?text=' + encodeURIComponent(title + ' ' + url);
  });
  document.querySelectorAll('[data-share="copy"]').forEach(function(btn){
    btn.addEventListener('click', function(){
      var finish = function(){
        btn.classList.add('copied');
        btn.querySelector('.icon-link').style.display = 'none';
        btn.querySelector('.icon-check').style.display = 'block';
        setTimeout(function(){
          btn.classList.remove('copied');
          btn.querySelector('.icon-link').style.display = 'block';
          btn.querySelector('.icon-check').style.display = 'none';
        }, 1800);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(finish).catch(function(){ window.prompt('Copia el enlace:', url); });
      } else {
        window.prompt('Copia el enlace:', url);
      }
    });
  });
})();
</script>
'''

SHARE_JS_MARK = 'data-share="copy"'  # para detectar si el JS ya está insertado


def ensure_css(css_path: pathlib.Path, dry_run: bool) -> None:
    if not css_path.exists():
        print(f"[AVISO] No encontré {css_path}; no se agregó el CSS de la botonera ah\u00ed. "
              f"Pod\u00e9s pasar --css-file para indicar la ruta correcta, o pegar el bloque a mano.")
        return
    content = css_path.read_text(encoding="utf-8")
    if SHARE_CSS_MARK in content:
        print(f"[OK] {css_path.name} ya tiene el CSS de la botonera, no se toca.")
        return
    if dry_run:
        print(f"[DRY-RUN] Agregar\u00eda el bloque CSS de la botonera al final de {css_path.name}.")
        return
    new_content = content.rstrip("\n") + "\n\n" + SHARE_CSS
    css_path.write_text(new_content, encoding="utf-8")
    print(f"[HECHO] CSS de la botonera agregado a {css_path.name}.")


def insert_before(content: str, anchor: str, snippet: str) -> "tuple[str, bool]":
    idx = content.find(anchor)
    if idx == -1:
        return content, False
    return content[:idx] + snippet + "\n  " + content[idx:], True


def process_file(path: pathlib.Path, args) -> None:
    content = path.read_text(encoding="utf-8")

    if SHARE_BAR_MARK in content:
        print(f"[OK] {path.name} ya tiene la botonera, no se toca.")
        return

    changed = False
    warnings = []

    # --- Barra superior ---
    if not args.no_top_bar:
        if "<!-- SHARE_BAR_TOP -->" in content:
            content = content.replace("<!-- SHARE_BAR_TOP -->", share_bar_html(footer=False), 1)
            changed = True
        else:
            top_anchors = [args.top_anchor] if args.top_anchor else DEFAULT_TOP_ANCHORS
            done = False
            for anchor in top_anchors:
                content2, ok = insert_before(content, anchor, share_bar_html(footer=False))
                if ok:
                    content = content2
                    changed = True
                    done = True
                    break
            if not done:
                tried = ", ".join(repr(a) for a in top_anchors)
                warnings.append(f"no encontr\u00e9 ancla superior para insertar la barra de arriba (probu00e9: {tried})")

    # --- Barra inferior ---
    if not args.no_footer_bar:
        if "<!-- SHARE_BAR_BOTTOM -->" in content:
            content = content.replace("<!-- SHARE_BAR_BOTTOM -->", share_bar_html(footer=True), 1)
            changed = True
        else:
            bottom_anchors = [args.bottom_anchor] if args.bottom_anchor else [
                '<div class="related-articles"',
                "</main>",
                "<footer",
            ]
            done = False
            for anchor in bottom_anchors:
                content2, ok = insert_before(content, anchor, share_bar_html(footer=True))
                if ok:
                    content = content2
                    changed = True
                    done = True
                    break
            if not done:
                warnings.append("no encontr\u00e9 d\u00f3nde insertar la barra de abajo "
                                 "(probu00e9 related-articles, </main> y <footer)")

    # --- Script de enlaces (una sola vez) ---
    if changed and SHARE_JS_MARK not in content:
        if "</body>" in content:
            content = content.replace("</body>", SHARE_JS + "\n</body>", 1)
        else:
            content += SHARE_JS
            warnings.append("no encontr\u00e9 </body>; el script qued\u00f3 pegado al final del archivo, revisalo")

    if not changed:
        print(f"[SALTADO] {path.name}: {'; '.join(warnings) if warnings else 'no se hizo ning\u00fan cambio'}.")
        return

    if args.dry_run:
        print(f"[DRY-RUN] {path.name}: se insertar\u00eda la botonera correctamente.")
        for w in warnings:
            print(f"          \u26a0 {w}")
        return

    path.write_text(content, encoding="utf-8")
    print(f"[HECHO] {path.name}: botonera insertada.")
    for w in warnings:
        print(f"         \u26a0 {w}")


def main():
    parser = argparse.ArgumentParser(description="Inserta la botonera de compartir en art\u00edculos HTML existentes.")
    parser.add_argument("files", nargs="+", help="Archivos HTML a procesar (acepta comodines del shell, ej. articulos/*.html)")
    parser.add_argument("--dry-run", action="store_true", help="No escribe nada, solo muestra qu\u00e9 har\u00eda.")
    parser.add_argument("--css-file", default=None, help="Ruta a css-articulos.css (default: la busca junto al primer HTML).")
    parser.add_argument("--top-anchor", default=None,
                         help='Texto antes del cual insertar la barra superior (default: prueba varias '
                              'opciones: <div class="section-head", luego <div class="article-body", '
                              'luego <div class="intro").')
    parser.add_argument("--bottom-anchor", default=None,
                         help="Texto antes del cual insertar la barra inferior (default: prueba varias opciones).")
    parser.add_argument("--no-top-bar", action="store_true", help="No insertar la barra de arriba.")
    parser.add_argument("--no-footer-bar", action="store_true", help="No insertar la barra de abajo.")
    args = parser.parse_args()

    paths = [pathlib.Path(f) for f in args.files]
    paths = [p for p in paths if p.suffix.lower() in (".html", ".htm")]
    if not paths:
        print("No se encontraron archivos .html entre los argumentos dados.")
        sys.exit(1)

    css_path = pathlib.Path(args.css_file) if args.css_file else (paths[0].parent / "css-articulos.css")
    ensure_css(css_path, args.dry_run)

    print()
    for p in paths:
        if not p.exists():
            print(f"[AVISO] {p} no existe, se salta.")
            continue
        process_file(p, args)

    print("\nListo. Correlo con --dry-run primero si quer\u00e9s revisar antes de escribir de verdad.")


if __name__ == "__main__":
    main()
