#!/usr/bin/env python3
"""Builds mockups/matriz.html — the screenshot matrix — and rewrites index.html
with thumbnails. Run after shoot.sh."""
import os
from css import CSS, AUDIT_JS
from build import page, GROUPS, OUT

SHOTS = os.path.join(OUT, "shots")

ROWS = [
 ("Por defecto", "El estado base de cada pantalla, a 390×844.",
  [(f.replace(".html", ""), t) for _, items in GROUPS for f, t, _ in items
   if f not in ("estados-interactivos.html", "analisis-errores.html")]),

 ("Hover · foco · pulsado · deshabilitado",
  "Los cuatro estados que ninguna captura estática enseña, forzados con la misma regla CSS "
  "que la pseudoclase real. Aquí es donde se escondió el único fallo que se escapó en el "
  "piloto anterior, y aquí es donde se revisa.",
  [("estados-interactivos", "Los diez controles × cinco estados")]),

 ("Vacío", "Todo lo que puede estar vacío tiene pantalla propia. Ninguna es una pantalla en blanco.",
  [("finanzas-hoy-vacio", "Hoy sin gastos"),
   ("finanzas-mes-vacio", "Un mes sin gastos"),
   ("diario-vacio", "Diario sin ninguna entrada"),
   ("diario-fecha-vacia", "Un día concreto sin nada escrito"),
   ("analisis-sin-resumen", "Nunca se ha producido un resumen"),
   ("analisis-periodo-vacio", "El mes cerró sin datos")]),

 ("Esperando", "La misma espera en dos momentos distintos: la marca de conteo crece, así que "
  "lo que se ve cambia por sí solo. No hay barra que prometa un final.",
  [("voz-transcribiendo--3s", "Transcripción a los 3 s"),
   ("voz-transcribiendo--14s", "La misma, a los 14 s"),
   ("analisis-esperando--12s", "Pregunta a los 12 s"),
   ("analisis-esperando--68s", "La misma, a los 68 s — dos filas de marcas"),
   ("analisis-generando", "El resumen del mes, escribiéndose en segundo plano"),
   ("gasto-guardando", "Guardando un gasto")]),

 ("Error", "Sólo estados que el contrato puede producir de verdad.",
  [("gasto-nuevo-error", "Validación en el cliente: los tres campos a la vez"),
   ("diario-escribir-error", "Entrada de diario en blanco"),
   ("voz-fallo", "No se entendió el audio"),
   ("voz-sin-permiso", "Micrófono bloqueado"),
   ("gasto-guardar-fallo", "No se pudo guardar; el texto sigue en pantalla"),
   ("sin-servidor", "Apertura en frío sin servidor"),
   ("sin-servidor-banner", "Aviso con la app ya abierta"),
   ("analisis-resumen-fallo", "El resumen del mes falló"),
   ("analisis-ocupado", "409 busy: ya hay una pregunta en curso"),
   ("analisis-ia-no-disponible", "El modelo no responde; el resto sigue funcionando"),
   ("analisis-errores", "Los cinco finales fallidos de una pregunta")]),

 ("Desplazado", "Las pantallas más altas que el teléfono, con el contenido de abajo.",
  [("gasto-nuevo--desplazado", "Formulario: fecha y descripción"),
   ("gasto-nuevo-error--desplazado", "Los errores de más abajo"),
   ("gasto-voz-revision--desplazado", "Revisión por voz: el campo que falta"),
   ("finanzas-mes--desplazado", "Cómo se pagó el mes"),
   ("diario--desplazado", "Entrada larga con “Seguir leyendo”"),
   ("analisis-respuesta--desplazado", "Respuesta sin periodo nombrado")]),

 ("Otros anchos", "El objetivo es el teléfono. 320 px es el Android estrecho; 900 px demuestra "
  "que no hay maquetación de escritorio, sólo la misma columna centrada.",
  [("finanzas-hoy--360", "Hoy a 360 px"),
   ("gasto-nuevo--360", "Formulario a 360 px"),
   ("finanzas-mes--320", "Mes a 320 px"),
   ("gasto-nuevo--320", "Formulario a 320 px — diez categorías en cinco filas"),
   ("diario--320", "Diario a 320 px"),
   ("finanzas-hoy--900", "Hoy a 900 px"),
   ("diario--900", "Diario a 900 px")]),
]

DARK = ("Modo oscuro", "No aplica: la restricción 22 pide sólo modo claro y ningún selector de "
        "tema. La hoja de estilos no contiene ninguna regla <code>prefers-color-scheme</code> y "
        "declara <code>color-scheme: light</code>, así que no hay variante oscura que capturar.")


def build_matrix():
    out = []
    for title, why, items in ROWS:
        cells = []
        for name, cap in items:
            png = f"shots/{name}.png"
            if not os.path.exists(os.path.join(OUT, png)):
                continue
            wide = name in ("estados-interactivos", "analisis-errores")
            w = 480 if wide else 232
            cells.append(
                f'<figure style="width:{w}px;margin:0">'
                f'<a href="{png}"><img src="{png}" alt="" style="width:100%;display:block;'
                f'border:1px solid var(--rule);border-radius:12px;background:#fff"></a>'
                f'<figcaption style="font-size:13px;line-height:1.4;margin-top:8px;'
                f'color:var(--ink-soft)">{cap}</figcaption></figure>')
        out.append(
            f'<section style="margin-top:44px"><h2 style="font-size:20px;font-weight:700;'
            f'letter-spacing:-.01em">{title}</h2>'
            f'<p class="lede" style="margin-top:6px">{why}</p>'
            f'<div style="display:flex;flex-wrap:wrap;gap:22px;margin-top:18px;'
            f'align-items:flex-start">' + "".join(cells) + "</div></section>")
    out.append(f'<section style="margin-top:44px"><h2 style="font-size:20px;font-weight:700">'
               f'{DARK[0]}</h2><p class="lede" style="margin-top:6px">{DARK[1]}</p></section>')
    return page("matriz.html", "Autonom-OS · matriz de capturas",
        '<div class="cat-wrap" style="max-width:1120px">'
        '<h1>Matriz de capturas</h1>'
        '<p class="lede">Todas las pantallas y todos los estados, renderizados con Chromium a '
        '390×844 salvo donde se indique otro ancho. Cada imagen se abre a tamaño completo.</p>'
        '<p class="lede" style="margin-top:8px"><a href="index.html" style="color:var(--violet);'
        'font-weight:700">Volver al índice</a></p>'
        + "".join(out) + "</div>",
        extra_css="body{background:var(--paper-sunk)}")


def build_index():
    rows = []
    for gname, items in GROUPS:
        cells = []
        for f, title, req in items:
            png = f"shots/{f.replace('.html','')}.png"
            thumb = (f'<img src="{png}" alt="" style="width:100%;display:block;border-radius:10px;'
                     f'border:1px solid var(--rule);background:#fff">'
                     if os.path.exists(os.path.join(OUT, png)) else
                     '<div style="height:120px;background:var(--rule);border-radius:10px"></div>')
            cells.append(
                f'<a href="{f}" style="width:206px;display:block">{thumb}'
                f'<div style="font-size:14.5px;font-weight:700;margin-top:9px;line-height:1.35">{title}</div>'
                f'<div style="font-size:12px;color:var(--ink-soft);margin-top:3px">{req}</div></a>')
        rows.append(f'<h2 style="font-size:13px;font-weight:700;letter-spacing:.14em;'
                    f'text-transform:uppercase;color:var(--ink-soft);margin:38px 0 16px">{gname}</h2>'
                    '<div style="display:flex;flex-wrap:wrap;gap:22px">' + "".join(cells) + "</div>")
    return page("index.html", "Autonom-OS · mockups",
        '<div class="cat-wrap" style="max-width:1120px">'
        '<h1>Autonom-OS — mockups para revisar</h1>'
        '<p class="lede">Pantallas estáticas, en español, pensadas para un teléfono de 390×844. '
        'Cada archivo se abre solo, sin servidor y sin conexión. Los datos son de ejemplo pero '
        'tienen exactamente la forma que devuelve el contrato del backend.</p>'
        '<p class="lede" style="margin-top:10px"><a href="matriz.html" '
        'style="color:var(--violet);font-weight:700">Ver la matriz de capturas →</a> '
        'Todas las pantallas y estados renderizados, incluidos hover, foco, pulsado y '
        'deshabilitado, las esperas en dos momentos distintos y tres anchos de pantalla.</p>'
        + "".join(rows) + "</div>",
        extra_css="body{background:var(--paper-sunk)}")


if __name__ == "__main__":
    print(build_matrix(), build_index())
