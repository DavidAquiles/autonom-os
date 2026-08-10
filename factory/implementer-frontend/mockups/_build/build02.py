#!/usr/bin/env python3
"""Generates the Run 02 Phase 1 static mockups into ../ .

Review artefacts, not application code. Every output file is self-contained:
inline CSS, inline SVG, no network request, no build step, opens straight from
the filesystem.

Placeholder data is shaped exactly like the Interface Contract's payloads —
`GET /api/expenses` items, `GET /api/expenses/{id}`, `GET /api/summary/month`.
`source` is absent everywhere, as it is on the wire (constraint 43).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from css02 import CSS, AUDIT_JS  # noqa: E402

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------- icons
def svg(inner, size=24, sw=1.9):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="{sw}" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{inner}</svg>')


I = {
    "mic28": svg('<rect x="8.6" y="3" width="6.8" height="11.4" rx="3.4"/>'
                 '<path d="M5 11a7 7 0 0 0 14 0"/><path d="M12 18v3"/>', 28),
    "plus18": svg('<path d="M12 5v14M5 12h14"/>', 18),
    "left": svg('<path d="M15 5l-7 7 7 7"/>'),
    "right": svg('<path d="M9 5l7 7-7 7"/>'),
    "chev": svg('<path d="M9 5l7 7-7 7"/>', 18, 2.1),
    "x": svg('<path d="M6 6l12 12M18 6L6 18"/>'),
    "x18": svg('<path d="M6 6l12 12M18 6L6 18"/>', 18, 2.1),
    "alert": svg('<circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.6"/>'
                 '<circle cx="12" cy="16.6" r=".95" fill="currentColor" stroke="none"/>'),
    "pencil": svg('<path d="M4.5 19.5h4L19 9l-4-4L4.5 15.5v4z"/>', 20),
}


# ---------------------------------------------------------------- shell
def page(fname, title, inner):
    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{CSS}</style>
</head>
<body>
{inner}
<script>{AUDIT_JS}</script>
</body>
</html>
"""
    with open(os.path.join(OUT, fname), "w", encoding="utf-8") as f:
        f.write(html)
    return fname


def phone(*parts):
    return '<div class="phone">' + "".join(parts) + "</div>"


def statusbar(t="19:47"):
    return (f'<div class="statusbar"><span>{t}</span>'
            '<span style="display:flex;gap:7px;align-items:center">'
            '<span class="sig"><i></i><i></i><i></i></span><span class="bat"></span>'
            '</span></div>')


def appbar(mod="Finanzas", act="Ajustes", href="#"):
    right = f'<a href="{href}" class="act">{act}</a>' if act else '<span></span>'
    return f'<div class="appbar"><span class="mod">{mod}</span>{right}</div>'


# The fourth tab (16.1, A23, constraint 29). Order is fixed by A23.
FIN_TABS = [
    ("Hoy", "#"),
    ("Este mes", "finanzas-mes.html"),
    ("Historial", "historial.html"),
    ("Análisis", "#"),
]


def tabs(active, cls=""):
    out = []
    for label, href in FIN_TABS:
        on = " is-on" if label == active else ""
        out.append(f'<a class="tab{on}" href="{href}">{label}</a>')
    return f'<div class="tabs {cls}">' + "".join(out) + "</div>"


def capture():
    return ('<div class="capture">'
            f'<a class="manual" href="#">{I["plus18"]}Anotar gasto</a>'
            f'<button class="mic" aria-label="Grabar con la voz">{I["mic28"]}</button>'
            '</div>')


def nav(active="Finanzas"):
    items = [("Finanzas", "historial.html"), ("Diario", "#"), ("Gimnasio", "#")]
    out = []
    for label, href in items:
        on = "is-on" if label == active else ""
        soon = "pronto" if label == "Gimnasio" else ""
        out.append(f'<a class="{on}" href="{href}"><span>{label}</span>'
                   f'<span class="soon">{soon}</span></a>')
    return '<nav class="nav">' + "".join(out) + "</nav>"


def formbar(title, back="historial.html"):
    return ('<div class="formbar">'
            f'<a href="{back}" class="close" aria-label="Cerrar">{I["x"]}</a>'
            f'<span class="ftitle">{title}</span></div>')


def banner_unreachable():
    return ('<div class="banner">' + I["alert"] + '<div>'
            '<div class="b-t">No alcanzo tu servidor.</div>'
            '<div class="b-d">Lo que ves puede estar desactualizado y no se puede guardar '
            'nada nuevo hasta que vuelva. Se reconecta solo.</div>'
            '<a class="b-a" href="#">Ver qué hacer</a>'
            '</div></div>')


def empty(title, body):
    return ('<div class="empty"><div class="mark"></div>'
            f'<h2>{title}</h2><p>{body}</p></div>')


# ---------------------------------------------------------------- copy (new strings)
# Every one of these becomes an entry in copy/es.ts in Phase 2 (Deferred 6).
# Checked against es.test.ts:62-71 — no save|cancel|delete|loading|error|
# settings|today|month|search|submit appears in any of them.
C = {
    "tab_historial": "Historial",
    "orden": "En el orden en que los anotaste, no por su fecha.",
    "ver_mas": "Ver gastos más antiguos",
    "cargando": "Cargando…",
    "hist_vacio_t": "Todavía no has anotado ningún gasto.",
    "hist_vacio_c": ("Cuando anotes el primero, aquí van quedando todos, "
                     "del último al primero."),
    "detalle_titulo": "Gasto",
    "metodo": "Método de pago",
    "fecha_gasto": "Fecha del gasto",
    "editar": "Editar gasto",
    "no_existe_t": "Este gasto ya no existe.",
    "no_existe_c": ("Puede que lo hayas borrado desde otra pantalla. "
                    "En la lista está todo lo que sí tienes anotado."),
    "cerrar": "Cerrar",
    "cat_vacia_t": lambda mes_, cat: f"En {mes_} ya no queda nada en {cat}.",
    "cat_vacia_c": ("Puede que lo hayas borrado o que lo hayas pasado a otra categoría. "
                    "El resto del mes sigue completo."),
}


def anotado(cuando):
    return f"Anotado el {cuando}."


def editado(cuando):
    return f"Editado el {cuando}."


def gastos_contados(n):
    return "1 gasto" if n == 1 else f"{n} gastos"


# ---------------------------------------------------------------- data
# GET /api/expenses?order=registered — items in id DESC order. The dates
# deliberately do NOT descend: that is the whole point of 16.6 / constraint 31.
HISTORIAL = [
    # (spent_on rendered, category_name, payment_method_name, amount)
    ("5 de agosto", "Transporte", "Tarjeta de crédito", "$18.000"),
    ("2 de agosto", "Mercado", "Tarjeta débito", "$150.000"),
    ("5 de agosto", "Comida", "Efectivo", "$23.500"),
    ("4 de agosto", "Comida", "Nequi", "$9.000"),
    ("1 de agosto", "Servicios", "Transferencia", "$62.000"),
    ("5 de agosto", "Transporte", "Efectivo", "$12.000"),
    ("28 de julio", "Hogar", "Tarjeta de crédito", "$340.000"),
    ("3 de agosto", "Comida", "Efectivo", "$7.500"),
    ("30 de julio", "Salud", "Tarjeta débito", "$86.000"),
    ("2 de agosto", "Ocio", "Nequi", "$21.000"),
    ("3 de agosto", "Mercado", "Efectivo", "$15.400"),
    ("1 de agosto", "Comida", "Efectivo", "$4.800"),
    ("26 de julio", "Ropa", "Tarjeta de crédito", "$54.000"),
]

# GET /api/summary/month — carried unchanged from the Run 01 approved mockup.
MES = [
    ("Mercado", "$412.000", 32), ("Comida", "$298.500", 23),
    ("Transporte", "$187.000", 15), ("Servicios", "$154.000", 12),
    ("Hogar", "$96.000", 7), ("Ocio", "$74.000", 6),
    ("Salud", "$38.000", 3), ("Ropa", "$25.000", 2),
]
MES_PM = [("Tarjeta de crédito", "$498.000"), ("Efectivo", "$331.500"),
          ("Tarjeta débito", "$264.000"), ("Nequi", "$121.000"),
          ("Transferencia", "$70.000")]
MES_TOTAL = "$1.284.500"
TINTS = ["var(--t1)", "var(--t2)", "var(--t3)", "var(--t4)", "var(--t5)",
         "var(--t6)", "var(--t7)", "var(--t8)", "var(--t9)", "var(--t10)"]

# GET /api/expenses?month=2026-08&category_id=2 — spent_on DESC (18.13).
# The twelve amounts sum to exactly $298.500, the figure in by_category.
COMIDA = [
    ("5 de agosto", "Efectivo · Almuerzo con Ana", "$23.500"),
    ("5 de agosto", "Nequi · Café y pan", "$6.200"),
    ("4 de agosto", "Tarjeta débito · Domicilio de la noche", "$38.400"),
    ("4 de agosto", "Efectivo", "$9.000"),
    ("3 de agosto", "Efectivo · Pan y café", "$7.500"),
    ("2 de agosto", "Tarjeta de crédito · Almuerzo con el equipo", "$64.000"),
    ("2 de agosto", "Nequi · Empanadas", "$5.000"),
    ("1 de agosto", "Tarjeta de crédito · Cena del viernes", "$66.500"),
    ("1 de agosto", "Tarjeta débito · Cena en casa de Sofía", "$52.000"),
    ("1 de agosto", "Nequi · Almuerzo", "$18.000"),
    ("1 de agosto", "Efectivo", "$4.800"),
    ("1 de agosto", "Efectivo · Jugo", "$3.600"),
]

LARGA = (
    "Mercado grande del mes en la plaza de Paloquemao, con Ana. Fuimos temprano "
    "porque después se llena y los precios de la fruta suben. Llevamos la papa "
    "criolla, la yuca, el plátano, tres kilos de naranja para el jugo de la "
    "semana, el tomate de árbol, cilantro, cebolla larga y una libra de queso "
    "campesino del puesto del fondo, que es el que sirve. También pagamos el "
    "domicilio hasta la casa porque no cabía en el carro y salía más caro pedir "
    "un taxi. Anoto todo junto en un solo gasto porque fue un solo pago con la "
    "tarjeta; si lo separo después no me acuerdo de qué era cada cosa."
)


# ---------------------------------------------------------------- pieces
def hist_rows(rows):
    """Constraint 30: byte-for-byte Hoy's `.row`. Only the facts differ.
    16.5: amount, category, payment method, and the date it is dated for."""
    out = ['<ul class="ledger">']
    for fecha, cat, pago, amt in rows:
        out.append(
            '<li><a class="row" href="gasto-detalle.html">'
            f'<span class="what"><span class="cat">{cat}</span>'
            f'<span class="meta">{fecha} · {pago}</span></span>'
            f'<span class="amt">{amt}</span></a></li>')
    out.append("</ul>")
    return "".join(out)


def cat_rows(rows):
    """18.12: amount, payment method, dated-for date, description when present.
    Same `.row`; the primary line carries the date because this list is
    date-ordered (18.13) and every row is the same category."""
    out = ['<ul class="ledger">']
    for fecha, meta, amt in rows:
        out.append(
            '<li><a class="row" href="gasto-detalle.html">'
            f'<span class="what"><span class="cat">{fecha}</span>'
            f'<span class="meta">{meta}</span></span>'
            f'<span class="amt">{amt}</span></a></li>')
    out.append("</ul>")
    return "".join(out)


def historial_screen(rows, ver_mas=None, banner=False, tabcls=""):
    """ver_mas: None → absent (constraint 32, nothing implying more exists);
    'on' → the control; 'busy' → the same control, in flight, in place."""
    body = [banner_unreachable() if banner else ""]
    body.append(f'<div class="orden"><p>{C["orden"]}</p></div>')
    body.append(hist_rows(rows))
    if ver_mas == "on":
        body.append('<div class="vermas">'
                    f'<button class="btn btn--text">{C["ver_mas"]}</button></div>')
    elif ver_mas == "busy":
        body.append('<div class="vermas">'
                    f'<button class="btn btn--text" disabled>{C["cargando"]}</button></div>')
    body.append('<div style="height:26px"></div>')
    return phone(
        statusbar(), appbar(), tabs("Historial", tabcls),
        '<div class="scroll">' + "".join(body) + "</div>",
        capture(), nav(),
    )


def month_hero(month="agosto 2026", total=MES_TOTAL, count="43 gastos"):
    return ('<div class="hero hero--mes">'
            '<div class="monthnav">'
            f'<span class="mname">{month}</span>'
            f'<a class="arrow" href="#" aria-label="Mes anterior">{I["left"]}</a>'
            f'<a class="arrow is-disabled" href="#" aria-label="Mes siguiente">{I["right"]}</a>'
            '</div>'
            f'<div class="sum" style="margin-top:10px">{total}</div>'
            f'<div class="sub">{count}</div></div>')


def breakdown():
    """Category rows are tappable (18.1); payment rows below are not (39)."""
    out = ['<ul class="brk brk--tap">']
    for i, (name, amt, pct) in enumerate(MES):
        href = "finanzas-mes-categoria.html" if name == "Comida" else "#"
        out.append(
            f'<li><a class="catrow" href="{href}">'
            f'<span class="line"><span class="name">{name}</span>'
            f'<span class="val">{amt}</span><span class="pct">{pct} %</span>'
            f'<span class="chev">{I["chev"]}</span></span>'
            f'<span class="track"><span class="fill" style="display:block;width:{pct}%;'
            f'background:{TINTS[i]}"></span></span></a></li>')
    out.append("</ul>")
    pm = ['<ul class="pm" style="padding:0 var(--pad)">']
    for name, amt in MES_PM:
        pm.append(f'<li><span class="name">{name}</span><span class="val">{amt}</span></li>')
    pm.append("</ul>")
    return ('<div class="slabel">En qué se fue</div>' + "".join(out) +
            '<div class="slabel">Cómo se pagó</div>' + "".join(pm) +
            '<div style="height:28px"></div>')


def opened(cat, total=None, count=None):
    figs = ""
    if total is not None:
        figs = ('<div class="figs">'
                f'<span class="ctotal">{total}</span>'
                f'<span class="ccount">{gastos_contados(count)}</span></div>')
    return ('<div class="opened"><div class="head">'
            f'<span class="cname">{cat}</span>'
            f'<a class="cerrar" href="finanzas-mes.html">{I["x18"]}{C["cerrar"]}</a>'
            f'</div>{figs}</div>')


def detalle(amount, cat, desc, metodo, fecha, anotado_txt, editado_txt=None):
    d = f'<div class="rdesc">{desc}</div>' if desc else ""
    notes = f"<p>{anotado_txt}</p>"
    if editado_txt:
        notes += f"<p>{editado_txt}</p>"
    return phone(
        statusbar(),
        formbar(C["detalle_titulo"]),
        '<div class="scroll">'
        '<div class="receipt">'
        f'<div class="ramt">{amount}</div>'
        f'<div class="rcat">{cat}</div>'
        f'{d}'
        '<ul class="rfacts">'
        f'<li><span class="fn">{C["metodo"]}</span><span class="fv">{metodo}</span></li>'
        f'<li><span class="fn">{C["fecha_gasto"]}</span><span class="fv">{fecha}</span></li>'
        '</ul></div>'
        f'<div class="stampnote">{notes}</div>'
        '<div class="formfoot" style="padding-top:26px">'
        f'<button class="btn btn--ghost">{I["pencil"]}{C["editar"]}</button></div>'
        '</div>',
        nav(),
    )


# ---------------------------------------------------------------- pages
P = []

# ---- Historial ---------------------------------------------------------
P.append(page("historial.html", "Finanzas · Historial",
              historial_screen(HISTORIAL, ver_mas="on")))

P.append(page("historial-completo.html", "Finanzas · Historial (última página)",
              historial_screen(HISTORIAL[:9], ver_mas=None)))

P.append(page("historial-ver-mas-en-curso.html", "Finanzas · Historial (trayendo más)",
              historial_screen(HISTORIAL, ver_mas="busy")))

P.append(page("historial-vacio.html", "Finanzas · Historial sin gastos", phone(
    statusbar("08:03"), appbar(), tabs("Historial"),
    '<div class="scroll">' + empty(C["hist_vacio_t"], C["hist_vacio_c"]) + '</div>',
    capture(), nav(),
)))

P.append(page("historial-cargando.html", "Finanzas · Historial esperando", phone(
    statusbar(), appbar(), tabs("Historial"),
    f'<div class="scroll"><p class="skel">{C["cargando"]}</p></div>',
    capture(), nav(),
)))

P.append(page("historial-sin-servidor.html", "Finanzas · Historial sin servidor",
              historial_screen(HISTORIAL, ver_mas="on", banner=True)))

# Drawn only so the human can decide the 320px question at the gate with a
# picture instead of a paragraph. Not a screen; not part of the product.
P.append(page("historial-tira-estrecha.html", "Variante · tira de pestañas más apretada",
              historial_screen(HISTORIAL, ver_mas="on", tabcls="tabs--estrecho")))

# ---- The expense detail -------------------------------------------------
P.append(page("gasto-detalle.html", "Gasto", detalle(
    "$23.500", "Comida", "Almuerzo con Ana en el italiano de la 85",
    "Efectivo", "miércoles 5 de agosto",
    anotado("5 de agosto a las 13:05"),
)))

P.append(page("gasto-detalle-sin-descripcion.html", "Gasto sin descripción", detalle(
    "$12.000", "Transporte", None,
    "Efectivo", "miércoles 5 de agosto",
    anotado("5 de agosto a las 19:41"),
)))

P.append(page("gasto-detalle-descripcion-larga.html", "Gasto con descripción larga", detalle(
    "$150.000", "Mercado", LARGA,
    "Tarjeta débito", "domingo 2 de agosto",
    anotado("2 de agosto a las 11:26"),
)))

P.append(page("gasto-detalle-editado.html", "Gasto editado", detalle(
    "$62.000", "Servicios", "Internet de agosto",
    "Transferencia", "sábado 1 de agosto",
    anotado("1 de agosto a las 08:14"),
    editado("7 de agosto a las 09:20"),
)))

P.append(page("gasto-detalle-no-existe.html", "Gasto que ya no existe", phone(
    statusbar(),
    formbar(C["detalle_titulo"]),
    '<div class="scroll">' + empty(C["no_existe_t"], C["no_existe_c"]) + '</div>',
    nav(),
)))

P.append(page("gasto-detalle-cargando.html", "Gasto esperando", phone(
    statusbar(),
    formbar(C["detalle_titulo"]),
    f'<div class="scroll"><p class="skel">{C["cargando"]}</p></div>',
    nav(),
)))

# ---- The month and its category ----------------------------------------
P.append(page("finanzas-mes.html", "Finanzas · Este mes", phone(
    statusbar(), appbar(), tabs("Este mes"),
    '<div class="scroll">' + month_hero() + breakdown() + '</div>',
    capture(), nav(),
)))

P.append(page("finanzas-mes-categoria.html", "Finanzas · Este mes · Comida", phone(
    statusbar(), appbar(), tabs("Este mes"),
    '<div class="scroll">' + month_hero() +
    opened("Comida", "$298.500", 12) +
    cat_rows(COMIDA) +
    '<div style="height:28px"></div></div>',
    capture(), nav(),
)))

P.append(page("finanzas-mes-categoria-vacia.html", "Finanzas · Este mes · Ropa sin gastos", phone(
    statusbar(), appbar(), tabs("Este mes"),
    '<div class="scroll">' + month_hero() +
    opened("Ropa") +
    empty(C["cat_vacia_t"]("agosto", "Ropa"), C["cat_vacia_c"]) +
    '</div>',
    capture(), nav(),
)))

# ---- index -------------------------------------------------------------
GROUPS = [
    ("Historial — la cuarta pestaña", [
        ("historial.html", "Historial",
         "La lista plana en orden de registro, la frase que dice en qué orden va, "
         "y el control para ver más. Las fechas no van en orden descendente: eso es "
         "lo que 16.6 existe para explicar.",
         "16.1 16.2 16.5 16.6 16.7 16.12 · 29 30 31 33 34 43"),
        ("historial-completo.html", "Historial — última página",
         "Lo mismo sin nada más que traer. No hay control, ni etiqueta, ni indicio "
         "de que quede algo debajo.",
         "16.9 · 32"),
        ("historial-ver-mas-en-curso.html", "Historial — trayendo más",
         "El control se queda en su sitio y lleva él mismo el estado. No hay una "
         "rueda infinita al final de la lista.",
         "16.7 · 32"),
        ("historial-vacio.html", "Historial — sin gastos",
         "Nunca se ha anotado nada. Un estado diseñado, no un marco vacío.",
         "16.10 · 15 42"),
        ("historial-cargando.html", "Historial — esperando",
         "El patrón de espera que ya usan Hoy y Este mes, sin inventar nada.",
         "16"),
        ("historial-sin-servidor.html", "Historial — sin servidor",
         "El aviso que Historial hereda del marco de Finanzas, no algo suyo.",
         "13.2 · 18"),
    ]),
    ("Un gasto, antes de cambiarlo", [
        ("gasto-detalle.html", "Detalle del gasto",
         "Una superficie de lectura: el monto es el titular, la descripción es "
         "texto y hay una sola acción. El marco es el de leer una entrada del diario.",
         "17.1 17.2 17.4 17.6 17.10 · 35 36 37 43"),
        ("gasto-detalle-sin-descripcion.html", "Detalle — sin descripción",
         "La descripción no está: no hay guion, ni campo vacío, ni palabra que "
         "haga las veces de “nada”.",
         "17.3"),
        ("gasto-detalle-descripcion-larga.html", "Detalle — descripción larga",
         "Casi 600 caracteres, completos. Sin recorte y sin “seguir leyendo”.",
         "17.2 · 37"),
        ("gasto-detalle-editado.html", "Detalle — editado después",
         "La marca de editado es del mismo color y del mismo tamaño que la de "
         "anotado. Un dato del registro, no un problema con él.",
         "17.5 · 38"),
        ("gasto-detalle-no-existe.html", "Detalle — el gasto ya no existe",
         "En español llano, con el marco intacto. No es una pantalla en blanco, "
         "ni una rueda eterna, ni un mensaje técnico.",
         "17.11"),
        ("gasto-detalle-cargando.html", "Detalle — esperando",
         "El mismo patrón de espera del resto de Finanzas.",
         "16"),
    ]),
    ("El mes, una categoría a la vez", [
        ("finanzas-mes.html", "Este mes",
         "Las filas de categoría se pueden abrir y se ve que se pueden abrir: "
         "van a sangre, con galón violeta. Las de método de pago siguen "
         "exactamente como estaban.",
         "18.1 · 39"),
        ("finanzas-mes-categoria.html", "Este mes — Comida abierta",
         "El total del mes sigue arriba; el de la categoría vive en la banda, con "
         "otro peso y otra posición. Cerrar está a la vista sin bajar.",
         "18.2 18.3 18.4 18.5 18.8 18.12 18.13 · 40 41 43"),
        ("finanzas-mes-categoria-vacia.html", "Este mes — una categoría sin nada",
         "La última compra de esa categoría en ese mes se fue. Un estado dicho en "
         "español, no un área en blanco ni una fila en cero.",
         "18.10 · 42"),
    ]),
    ("Una decisión para el gate — no es una pantalla", [
        ("historial-tira-estrecha.html", "Variante: la tira de pestañas más apretada",
         "A 390 px las cuatro pestañas caben con 70 px de sobra y esta variante no "
         "hace falta. A 320 px, “Este mes” se parte en dos líneas. Esta variante "
         "junta las cuatro por igual —mismo tamaño, mismo peso, menos aire— y deja "
         "de partirse. Ábrela junto a Historial para ver qué se pierde a 390.",
         "29 · decide tú"),
    ]),
]


def build_index():
    parts = ['<div class="idx">',
             '<h1>Autonom-OS · maquetas de la segunda entrega</h1>',
             '<p class="lede">Historial, el detalle de un gasto y el mes abierto por '
             'categoría. Son archivos estáticos: se abren directamente en el navegador, '
             'no piden nada a la red y no hay nada que compilar. Cada pantalla está '
             'dibujada a 390×844 con la misma hoja de estilos que la aplicación ya usa. '
             'Los números y los textos son de mentira, pero tienen la forma exacta de lo '
             'que devuelve el servidor.</p>']
    for title, items in GROUPS:
        parts.append(f"<h2>{title}</h2><ul>")
        for href, name, desc, crit in items:
            parts.append(f'<li><a href="{href}"><span class="n">{name}</span>'
                         f'<span class="d">{desc}</span>'
                         f'<span class="c">{crit}</span></a></li>')
        parts.append("</ul>")
    parts.append("</div>")
    return "".join(parts)


P.append(page("index.html", "Autonom-OS · maquetas (entrega 2)", build_index()))

print("\n".join(sorted(P)))
