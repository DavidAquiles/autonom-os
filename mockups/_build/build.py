#!/usr/bin/env python3
"""Generates the Autonom-OS Phase 1 static mockups into ../ (mockups/).

These are review artefacts, not application code. Every output file is a
self-contained HTML document: inline CSS, inline SVG, no network request,
no build step, opens straight from the filesystem.
"""
import os
from css import CSS, AUDIT_JS, TALLY_JS

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# ---------------------------------------------------------------- icons
def svg(inner, size=24, sw=1.9):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="{sw}" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{inner}</svg>')

I = {
 "mic":   svg('<rect x="8.6" y="3" width="6.8" height="11.4" rx="3.4"/><path d="M5 11a7 7 0 0 0 14 0"/><path d="M12 18v3"/>'),
 "mic28": svg('<rect x="8.6" y="3" width="6.8" height="11.4" rx="3.4"/><path d="M5 11a7 7 0 0 0 14 0"/><path d="M12 18v3"/>', 28),
 "mic44": svg('<rect x="8.6" y="3" width="6.8" height="11.4" rx="3.4"/><path d="M5 11a7 7 0 0 0 14 0"/><path d="M12 18v3"/>', 46, 1.5),
 "plus":  svg('<path d="M12 5v14M5 12h14"/>'),
 "plus18":svg('<path d="M12 5v14M5 12h14"/>', 18),
 "left":  svg('<path d="M15 5l-7 7 7 7"/>'),
 "right": svg('<path d="M9 5l7 7-7 7"/>'),
 "alert": svg('<circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.6"/><circle cx="12" cy="16.6" r=".95" fill="currentColor" stroke="none"/>'),
 "alert18": svg('<circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.6"/><circle cx="12" cy="16.6" r=".95" fill="currentColor" stroke="none"/>', 18),
 "stop":  svg('<rect x="7" y="7" width="10" height="10" rx="2.5"/>', 26),
 "x":     svg('<path d="M6 6l12 12M18 6L6 18"/>'),
 "check": svg('<path d="M5 12.5l4.5 4.5L19 7"/>'),
 "pencil":svg('<path d="M4.5 19.5h4L19 9l-4-4L4.5 15.5v4z"/>', 20),
 "trash": svg('<path d="M4.5 7h15M9.5 7V4.8h5V7M6.5 7l1 12.2h9L17.5 7"/>', 20),
 "down":  svg('<path d="M12 4v11M7.5 10.5L12 15l4.5-4.5M5 19h14"/>', 20),
 "cal":   svg('<rect x="3.5" y="5" width="17" height="15" rx="3"/><path d="M8 3v4M16 3v4M3.5 10.2h17"/>', 20),
 "clock": svg('<circle cx="12" cy="12" r="9"/><path d="M12 7v5.4l3.2 2"/>', 20),
}

# ---------------------------------------------------------------- data (Interface Contract shapes)
CATS = ["Comida","Transporte","Mercado","Servicios","Salud","Ocio","Hogar","Ropa","Educación","Otros"]
PAYS = ["Efectivo","Tarjeta de crédito","Tarjeta débito","Transferencia","Nequi","Daviplata"]

HOY = [  # GET /api/summary/day items — newest first
 ("19:40","Transporte","Tarjeta de crédito","Uber a la casa","$14.000"),
 ("13:05","Comida","Efectivo","Almuerzo con Ana","$23.500"),
 ("11:20","Servicios","Transferencia","Recarga de datos","$12.000"),
 ("08:12","Comida","Nequi","Café y pan","$6.200"),
]
HOY_TOTAL = "$55.700"

MES = [  # GET /api/summary/month by_category — desc, percents sum to 100
 ("Mercado","$412.000",32),("Comida","$298.500",23),("Transporte","$187.000",15),
 ("Servicios","$154.000",12),("Hogar","$96.000",7),("Ocio","$74.000",6),
 ("Salud","$38.000",3),("Ropa","$25.000",2),
]
MES_PM = [("Tarjeta de crédito","$498.000"),("Efectivo","$331.500"),
          ("Tarjeta débito","$264.000"),("Nequi","$121.000"),("Transferencia","$70.000")]
MES_TOTAL = "$1.284.500"

TINTS = ["var(--t1)","var(--t2)","var(--t3)","var(--t4)","var(--t5)",
         "var(--t6)","var(--t7)","var(--t8)","var(--t9)","var(--t10)"]

# ---------------------------------------------------------------- shell
def page(fname, title, inner, body_class="", extra_css="", tally=False):
    scripts = AUDIT_JS + (TALLY_JS if tally else "")
    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{CSS}{extra_css}</style>
</head>
<body class="{body_class}">
{inner}
<script>{scripts}</script>
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
            '<span class="sig"><i></i><i></i><i></i></span><span class="bat"></span></span></div>')


def appbar(mod, act=None, href="analisis.html", act_cls=""):
    right = f'<a href="{href}" class="act {act_cls}">{act}</a>' if act else '<span></span>'
    return f'<div class="appbar"><span class="mod">{mod}</span>{right}</div>'


def tabs(items, active):
    out = []
    for label, href in items:
        on = " is-on" if label == active else ""
        out.append(f'<a class="tab{on}" href="{href}">{label}</a>')
    return '<div class="tabs">' + "".join(out) + "</div>"


FIN_TABS = [("Hoy","finanzas-hoy.html"),("Este mes","finanzas-mes.html"),("Análisis","analisis.html")]
DIA_TABS = [("Todo","diario.html"),("Por fecha","diario-fecha-vacia.html")]


def capture(module="fin", mic_state="", manual_state="", mic_disabled=False):
    label = "Anotar gasto" if module == "fin" else "Escribir"
    href = "gasto-nuevo.html" if module == "fin" else "diario-escribir.html"
    voz = "voz-escuchando.html"
    dis = " disabled" if mic_disabled else ""
    return (f'<div class="capture">'
            f'<a class="manual {manual_state}" href="{href}">{I["plus18"]}{label}</a>'
            f'<button class="mic {mic_state}"{dis} aria-label="Grabar con la voz">{I["mic28"]}</button>'
            f'</div>')


def nav(active, state=""):
    items = [("Finanzas","finanzas-hoy.html"),("Diario","diario.html"),("Gimnasio","gimnasio.html")]
    out = []
    for label, href in items:
        on = " is-on" if label == active else ""
        cls = state if label == active or state == "" else ""
        extra = ('<span class="soon">pronto</span>' if label == "Gimnasio"
                 else '<span class="soon"></span>')
        out.append(f'<a class="{on.strip()} {cls}" href="{href}"><span>{label}</span>{extra}</a>')
    return '<nav class="nav">' + "".join(out) + "</nav>"


def formbar(title, back="finanzas-hoy.html"):
    return ('<div class="appbar" style="padding-top:2px;align-items:center">'
            f'<a href="{back}" class="act" aria-label="Cerrar" '
            'style="width:44px;height:44px;justify-content:center;padding:0;margin-left:-10px">'
            f'{I["x"]}</a>'
            f'<span style="flex:1;font-size:17px;font-weight:700;margin-left:4px">{title}</span></div>')


def chips(names, selected=None, new_label=None, missing=False, disabled=False, states=None):
    states = states or {}
    out = []
    for n in names:
        cls = "chip"
        if n == selected:
            cls += " is-on"
        if n in states:
            cls += " " + states[n]
        d = " disabled" if disabled else ""
        out.append(f'<button class="{cls}"{d}>{n}</button>')
    if new_label:
        out.append(f'<button class="chip chip--new">{I["plus18"]}{new_label}</button>')
    wrap = "chips is-missing" if missing else "chips"
    return f'<div class="{wrap}">' + "".join(out) + "</div>"


def err(msg):
    return f'<p class="err">{I["alert18"]}<span>{msg}</span></p>'


def tally_block(secs, phase, said, local, acts):
    return (f'<div class="tallywrap" data-tally="{secs}">'
            f'<div class="tally"></div>'
            f'<div class="secs"><span class="n">{secs}</span><span class="u">segundos</span></div>'
            f'</div>')


# ---------------------------------------------------------------- pages
P = []

# ---- 1. Finanzas / Hoy -------------------------------------------------
def ledger_rows(rows, hover_index=None, focus_index=None):
    out = ['<ul class="ledger">']
    for i, (t, cat, pay, desc, amt) in enumerate(rows):
        cls = ""
        if i == hover_index: cls = " is-hover"
        if i == focus_index: cls = " is-focus"
        out.append(
            f'<li><a class="row{cls}" href="gasto-editar.html">'
            f'<span class="what"><span class="cat">{cat}</span>'
            f'<span class="meta">{t} · {pay} · {desc}</span></span>'
            f'<span class="amt">{amt}</span></a></li>')
    out.append("</ul>")
    return "".join(out)


P.append(page("finanzas-hoy.html", "Finanzas · Hoy", phone(
    statusbar(),
    appbar("Finanzas", "Ajustes", "finanzas-ajustes.html"),
    tabs(FIN_TABS, "Hoy"),
    '<div class="scroll">'
    '<div class="hero"><div class="when">miércoles 5 de agosto</div>'
    f'<div class="sum">{HOY_TOTAL}</div>'
    '<div class="sub">4 gastos anotados hoy</div></div>'
    + ledger_rows(HOY) +
    '<div style="height:26px"></div>'
    '</div>',
    capture("fin"),
    nav("Finanzas"),
)))

P.append(page("finanzas-hoy-vacio.html", "Finanzas · Hoy sin gastos", phone(
    statusbar("08:03"),
    appbar("Finanzas", "Ajustes", "finanzas-ajustes.html"),
    tabs(FIN_TABS, "Hoy"),
    '<div class="scroll">'
    '<div class="hero"><div class="when">miércoles 5 de agosto</div>'
    '<div class="sum">$0</div></div>'
    '<div class="empty"><div class="mark"></div>'
    '<h2>Todavía no has anotado nada hoy.</h2>'
    '<p>Puedes escribirlo con el botón de abajo, o decirlo en voz alta mientras caminas.</p></div>'
    '</div>',
    capture("fin"),
    nav("Finanzas"),
)))

# ---- 2. Finanzas / Mes -------------------------------------------------
def month_body(month="agosto 2026", total=MES_TOTAL, count="43 gastos"):
    brk = ['<ul class="brk">']
    for i, (name, amt, pct) in enumerate(MES):
        brk.append(
            f'<li><div class="line"><span class="name">{name}</span>'
            f'<span class="val">{amt}</span><span class="pct">{pct} %</span></div>'
            f'<div class="track"><div class="fill" style="width:{pct}%;background:{TINTS[i]}"></div></div></li>')
    brk.append("</ul>")
    pm = ['<ul class="pm" style="padding:0 var(--pad)">']
    for name, amt in MES_PM:
        pm.append(f'<li><span class="name">{name}</span><span class="val">{amt}</span></li>')
    pm.append("</ul>")
    return (
        '<div class="hero hero--mes">'
        '<div class="monthnav">'
        f'<span class="mname">{month}</span>'
        f'<a class="arrow" href="#" aria-label="Mes anterior">{I["left"]}</a>'
        f'<a class="arrow is-disabled" href="#" aria-label="Mes siguiente">{I["right"]}</a></div>'
        f'<div class="sum" style="margin-top:10px">{total}</div>'
        f'<div class="sub">{count}</div></div>'
        '<div class="slabel">En qué se fue</div>' + "".join(brk) +
        '<div class="slabel">Cómo se pagó</div>' + "".join(pm) +
        '<div style="height:28px"></div>')


P.append(page("finanzas-mes.html", "Finanzas · Este mes", phone(
    statusbar(),
    appbar("Finanzas", "Ajustes", "finanzas-ajustes.html"),
    tabs(FIN_TABS, "Este mes"),
    '<div class="scroll">' + month_body() + "</div>",
    capture("fin"),
    nav("Finanzas"),
)))

P.append(page("finanzas-mes-vacio.html", "Finanzas · Mes sin gastos", phone(
    statusbar(),
    appbar("Finanzas", "Ajustes", "finanzas-ajustes.html"),
    tabs(FIN_TABS, "Este mes"),
    '<div class="scroll">'
    '<div class="hero hero--mes"><div class="monthnav">'
    '<span class="mname">febrero 2026</span>'
    f'<a class="arrow" href="#" aria-label="Mes anterior">{I["left"]}</a>'
    f'<a class="arrow" href="#" aria-label="Mes siguiente">{I["right"]}</a></div></div>'
    '<div class="empty"><div class="mark"></div>'
    '<h2>En febrero no hay gastos anotados.</h2>'
    '<p>Cuando anotes el primero, aquí verás en qué se fue el mes y cómo lo pagaste.</p></div>'
    '</div>',
    capture("fin"),
    nav("Finanzas"),
)))

# ---- 3. Ajustes --------------------------------------------------------
def setting_rows(names, counts):
    out = ['<ul class="ledger">']
    for n, c in zip(names, counts):
        out.append(
            f'<li><a class="row" href="finanzas-ajustes-quitar.html">'
            f'<span class="what"><span class="cat">{n}</span>'
            f'<span class="meta">{c}</span></span>'
            f'<span class="amt" style="color:var(--violet);font-size:15px">Editar</span></a></li>')
    out.append("</ul>")
    return "".join(out)


P.append(page("finanzas-ajustes.html", "Finanzas · Ajustes", phone(
    statusbar(),
    formbar("Ajustes"),
    '<div class="scroll">'
    '<div class="slabel">Categorías</div>'
    + setting_rows(CATS[:4], ["en 34 gastos","en 61 gastos","en 12 gastos","en 9 gastos"]) +
    '<div style="padding:14px var(--pad) 0">'
    f'<button class="chip chip--new">{I["plus18"]}Nueva categoría</button></div>'
    '<div class="slabel">Métodos de pago</div>'
    + setting_rows(PAYS[:3], ["en 88 gastos","en 40 gastos","en 25 gastos"]) +
    '<div style="padding:14px var(--pad) 0">'
    f'<button class="chip chip--new">{I["plus18"]}Nuevo método</button></div>'
    '<div class="slabel">Tu servidor</div>'
    '<ul class="pm" style="padding:0 var(--pad)">'
    '<li><span class="name">Transcripción</span><span class="val" style="font-size:15px">disponible</span></li>'
    '<li><span class="name">Modelo de texto</span><span class="val" style="font-size:15px">disponible</span></li>'
    '</ul>'
    '<div class="slabel">Copia de seguridad</div>'
    '<div style="padding:0 var(--pad) 30px">'
    f'<button class="btn btn--ghost">{I["down"]}Exportar todo</button>'
    '<p class="hint">Descarga un archivo con todo lo que tienes guardado: gastos, diario, '
    'categorías y métodos de pago. Se lee en cualquier editor de texto.</p></div>'
    '</div>',
    nav("Finanzas"),
)))

P.append(page("finanzas-ajustes-quitar.html", "Ajustes · Quitar categoría en uso", phone(
    statusbar(),
    formbar("Ajustes"),
    '<div class="scroll">'
    '<div class="field"><span class="flabel">Nombre</span>'
    '<input class="input" value="Comida"></div>'
    '<div style="padding:22px var(--pad) 0">'
    f'<button class="btn btn--ghost" style="color:var(--danger);border-color:#F0C3C8">{I["trash"]}Quitar de la lista</button>'
    '</div></div>',
    nav("Finanzas"),
    '<div class="veil"><div class="sheet"><div class="grab"></div>'
    '<h2>“Comida” está en 34 gastos.</h2>'
    '<p>Esos 34 gastos se quedan como están y siguen contando en los totales, con el nombre '
    '“Comida”. Lo único que cambia es que ya no vas a poder elegirla al anotar.</p>'
    '<div class="acts">'
    '<button class="btn btn--danger">Quitar de la lista</button>'
    '<button class="btn btn--text">Cancelar</button>'
    '</div></div></div>',
)))

# ---- 4. Manual expense form -------------------------------------------
def form_body(amount_html, cat_sel=None, pay_sel=None, cat_err=None, pay_err=None,
              amt_err=None, date_err=None, desc_value="", extra_cat="", missing_pay=False,
              cat_tag="", new_cat_field=False, desc_note="", transcript=None,
              date_line="Hoy, miércoles 5 de agosto"):
    out = []
    if transcript:
        out.append(
            '<div style="padding:16px var(--pad) 0">'
            '<div class="slabel" style="padding:0 0 8px">Esto fue lo que escuché</div>'
            f'<p style="font-size:17px;line-height:1.6">“{transcript}”</p>'
            '<a class="btn btn--text" href="voz-escuchando.html" '
            'style="justify-content:flex-start;padding-left:0">Grabar otra vez</a>'
            '<div style="height:6px"></div>'
            '<div style="height:1px;background:var(--rule)"></div></div>')
    out.append(f'<div class="field"><span class="flabel">Monto</span>{amount_html}'
               + (err(amt_err) if amt_err else "") + "</div>")
    out.append('<div class="field"><span class="flabel">Categoría' + cat_tag + '</span>'
               + chips(CATS, cat_sel, "Nueva") + extra_cat
               + (err(cat_err) if cat_err else "") + "</div>")
    if new_cat_field:
        out.append('<div class="field" style="padding-top:12px">'
                   '<input class="input is-focus" value="Cafetería" '
                   'placeholder="Nombre de la categoría">'
                   '<div class="btnrow" style="margin-top:10px">'
                   '<button class="btn btn--primary" style="min-height:48px;font-size:16px">Crear y elegir</button>'
                   '<button class="btn btn--text" style="width:auto;padding:0 18px">Cancelar</button></div>'
                   '<p class="hint">Lo que ya escribiste se queda como está.</p></div>')
    pay_label = "Método de pago"
    if missing_pay:
        pay_label += ' <span class="tag tag--need">Falta elegirlo</span>'
    out.append('<div class="field"><span class="flabel">' + pay_label + '</span>'
               + chips(PAYS, pay_sel, "Nuevo", missing=missing_pay)
               + (err(pay_err) if pay_err else "") + "</div>")
    out.append('<div class="field"><span class="flabel">Fecha</span>'
               '<div style="display:flex;align-items:center;gap:10px">'
               f'<span style="flex:1;font-size:16.5px;font-weight:600">{date_line}</span>'
               f'<button class="btn btn--text" style="width:auto;padding:0 14px">{I["cal"]}Cambiar</button></div>'
               + (err(date_err) if date_err else "") + "</div>")
    out.append('<div class="field"><span class="flabel">Descripción <span class="opt">(opcional)</span></span>'
               f'<input class="input" value="{desc_value}" placeholder="Para acordarte después">'
               + (f'<div class="note">{desc_note}</div>' if desc_note else "") + "</div>")
    return "".join(out)


AMOUNT_EMPTY = ('<div class="amountbox is-focus"><span class="cur">$</span>'
                '<span class="val" style="flex:none">14.000</span><span class="caret"></span>'
                '<span style="flex:1"></span></div>')
AMOUNT_BLANK = ('<div class="amountbox is-err"><span class="cur">$</span>'
                '<input class="val" value="" placeholder="0" aria-label="Monto"></div>')

P.append(page("gasto-nuevo.html", "Nuevo gasto", phone(
    statusbar(),
    formbar("Nuevo gasto"),
    '<div class="scroll">' + form_body(AMOUNT_EMPTY, "Transporte", "Tarjeta de crédito") +
    '<div class="formfoot"><button class="btn btn--primary">Guardar gasto</button></div></div>',
    nav("Finanzas"),
)))

P.append(page("gasto-nuevo-error.html", "Nuevo gasto · errores", phone(
    statusbar(),
    formbar("Nuevo gasto"),
    '<div class="scroll">' + form_body(
        AMOUNT_BLANK, None, None,
        amt_err="Escribe un monto mayor que cero.",
        cat_err="Elige una categoría.",
        pay_err="Elige un método de pago.") +
    '<div class="formfoot"><button class="btn btn--primary">Guardar gasto</button></div></div>',
    nav("Finanzas"),
)))

P.append(page("gasto-nuevo-nueva-categoria.html", "Nuevo gasto · crear categoría", phone(
    statusbar(),
    formbar("Nuevo gasto"),
    '<div class="scroll">' + form_body(AMOUNT_EMPTY, None, "Nequi", new_cat_field=True) +
    '<div class="formfoot"><button class="btn btn--primary">Guardar gasto</button></div></div>',
    nav("Finanzas"),
)))

P.append(page("gasto-guardando.html", "Nuevo gasto · guardando", phone(
    statusbar(),
    formbar("Nuevo gasto"),
    '<div class="scroll">' + form_body(AMOUNT_EMPTY, "Transporte", "Tarjeta de crédito") +
    '<div class="formfoot"><button class="btn btn--primary is-disabled" disabled>Guardando…</button>'
    '<p class="hint" style="text-align:center">Se guarda en tu computador.</p></div></div>',
    nav("Finanzas"),
)))

P.append(page("gasto-guardar-fallo.html", "Nuevo gasto · no se pudo guardar", phone(
    statusbar(),
    formbar("Nuevo gasto"),
    '<div class="scroll">'
    '<div class="banner" style="background:var(--danger-wash);border-color:#F0C3C8">'
    f'<span style="color:var(--danger)">{I["alert"]}</span>'
    '<div><div class="b-t">No pude guardar: no alcanzo tu servidor.</div>'
    '<div class="b-d">Nada se perdió. El gasto sigue aquí tal como lo escribiste; '
    'vuelve a intentarlo cuando el computador esté despierto.</div>'
    '<a class="b-a" href="sin-servidor.html">Ver qué hacer</a></div></div>'
    + form_body(AMOUNT_EMPTY, "Transporte", "Tarjeta de crédito", desc_value="Uber a la casa") +
    '<div class="formfoot"><button class="btn btn--primary">Reintentar</button></div></div>',
    nav("Finanzas"),
)))

P.append(page("gasto-editar.html", "Editar gasto", phone(
    statusbar(),
    formbar("Editar gasto"),
    '<div class="scroll">' + form_body(
        '<div class="amountbox"><span class="cur">$</span>'
        '<input class="val" value="14.000" aria-label="Monto"></div>',
        "Transporte", "Tarjeta de crédito", desc_value="Uber a la casa") +
    '<div class="formfoot"><button class="btn btn--primary">Guardar cambios</button>'
    '<div style="height:10px"></div>'
    f'<a class="btn btn--ghost" href="gasto-eliminar.html" '
    f'style="color:var(--danger);border-color:#F0C3C8">{I["trash"]}Eliminar gasto</a></div></div>',
    nav("Finanzas"),
)))

P.append(page("gasto-eliminar.html", "Eliminar gasto · confirmación", phone(
    statusbar(),
    formbar("Editar gasto"),
    '<div class="scroll">' + form_body(
        '<div class="amountbox"><span class="cur">$</span>'
        '<input class="val" value="14.000" aria-label="Monto"></div>',
        "Transporte", "Tarjeta de crédito", desc_value="Uber a la casa") + "</div>",
    nav("Finanzas"),
    '<div class="veil"><div class="sheet"><div class="grab"></div>'
    '<h2>¿Eliminar este gasto?</h2>'
    '<p>Deja de contar en el total de hoy y en el del mes. No se puede deshacer.</p>'
    '<div class="subject">$14.000 · Transporte · Tarjeta de crédito<br>'
    '<span style="font-weight:400;color:var(--ink-soft);font-size:14px">'
    'miércoles 5 de agosto · Uber a la casa</span></div>'
    '<div class="acts"><button class="btn btn--danger">Eliminar</button>'
    '<button class="btn btn--text">Cancelar</button></div></div></div>',
)))

# ---- 5. Voice to expense ----------------------------------------------
P.append(page("gasto-voz-revision.html", "Gasto por voz · revisar", phone(
    statusbar(),
    formbar("Revisar gasto"),
    '<div class="scroll">' + form_body(
        '<div class="amountbox"><span class="cur">$</span>'
        '<input class="val" value="14.000" aria-label="Monto"></div>',
        "Transporte", None,
        cat_tag=' <span class="tag">sugerido</span>',
        missing_pay=True,
        desc_value="Uber a la casa desde el trabajo",
        transcript="Gasté catorce mil pesos en un Uber a la casa desde el trabajo") +
    '<div class="formfoot"><button class="btn btn--primary">Guardar gasto</button>'
    '<p class="hint" style="text-align:center">Nada se guarda hasta que toques Guardar.</p></div></div>',
    nav("Finanzas"),
)))

LONG_T = ("Gasté ciento ochenta mil pesos en el mercado de la semana, compré fruta, verdura, "
          "carne para tres días, leche, café, jabón y cosas de aseo, todo en el supermercado "
          "de la esquina, pagué con la tarjeta débito porque la de crédito ya la tengo bastante "
          "cargada este mes y quiero bajarle un poco antes del corte, además aproveché y llevé "
          "algo para el almuerzo del sábado que viene Ana con los niños…")

P.append(page("gasto-voz-largo.html", "Gasto por voz · descripción recortada", phone(
    statusbar(),
    formbar("Revisar gasto"),
    '<div class="scroll">' + form_body(
        '<div class="amountbox"><span class="cur">$</span>'
        '<input class="val" value="180.000" aria-label="Monto"></div>',
        "Mercado", "Tarjeta débito",
        cat_tag=' <span class="tag">sugerido</span>',
        desc_value="Mercado de la semana, fruta, verdura, carne para tres días…",
        desc_note="La descripción guarda <b>1.000 caracteres</b> y lo que dijiste es más largo. "
                  "Se recortó al final de una palabra. Arriba está completo si quieres reescribirlo.",
        transcript=LONG_T) +
    '<div class="formfoot"><button class="btn btn--primary">Guardar gasto</button></div></div>',
    nav("Finanzas"),
)))

# ---- 6. Voice capture --------------------------------------------------
P.append(page("voz-escuchando.html", "Voz · escuchando", phone(
    statusbar(),
    formbar("Gasto por voz"),
    '<div class="listen">'
    f'<div class="pulse">{I["mic44"]}</div>'
    '<h2>Te estoy escuchando</h2>'
    '<div class="clock">0:07</div>'
    '<div class="cap"><div class="captrack"><div class="capfill" style="width:23%"></div></div>'
    '<div class="caplbl">máximo 30 segundos</div></div>'
    '<div class="acts">'
    f'<button class="btn btn--primary">{I["stop"]}Listo</button>'
    '<button class="btn btn--text">Cancelar</button>'
    '</div></div>',
    nav("Finanzas"),
)))

P.append(page("voz-transcribiendo.html", "Voz · transcribiendo", phone(
    statusbar(),
    formbar("Gasto por voz"),
    '<div class="scroll"><div class="wait">'
    '<h2>Pasando tu voz a texto</h2>'
    '<div class="phase">Transcribiendo en tu computador</div>'
    + tally_block(9, "", "", "", "") +
    '<p class="local">Esto ocurre en tu propio computador, no en internet. '
    'Con un mensaje corto suele tardar entre 7 y 15 segundos.</p>'
    '<div class="acts">'
    '<a class="btn btn--ghost" href="gasto-nuevo.html">Escribir a mano</a>'
    '<button class="btn btn--text">Cancelar</button>'
    '</div></div></div>',
    nav("Finanzas"),
), tally=True))

P.append(page("voz-fallo.html", "Voz · no se entendió", phone(
    statusbar(),
    formbar("Gasto por voz"),
    '<div class="scroll"><div class="wait">'
    '<h2>No entendí lo que dijiste.</h2>'
    '<p class="local" style="margin-top:12px">El audio llegó, pero salió vacío. '
    'Suele pasar cuando hay mucho ruido alrededor o el micrófono quedó tapado. '
    'No se guardó nada.</p>'
    '<div class="acts">'
    f'<a class="btn btn--primary" href="voz-escuchando.html">{I["mic"]}Grabar otra vez</a>'
    '<a class="btn btn--ghost" href="gasto-nuevo.html">Escribir a mano</a>'
    '</div>'
    '<div class="note" style="margin-top:28px">Si pasa siempre: la transcripción corre en tu '
    'computador y puede estar apagada. Lo ves en <b>Ajustes → Tu servidor</b>.</div>'
    '</div></div>',
    nav("Finanzas"),
)))

P.append(page("voz-sin-permiso.html", "Voz · sin micrófono", phone(
    statusbar(),
    formbar("Gasto por voz"),
    '<div class="scroll"><div class="wait">'
    '<h2>El navegador no me deja usar el micrófono.</h2>'
    '<p class="local" style="margin-top:12px">El permiso está bloqueado para esta dirección. '
    'Puedes cambiarlo en los ajustes del navegador, en Permisos del sitio.</p>'
    '<p class="local">Mientras tanto, anotar a mano funciona igual que siempre.</p>'
    '<div class="acts">'
    '<a class="btn btn--primary" href="gasto-nuevo.html">Escribir el gasto a mano</a>'
    '</div></div></div>',
    nav("Finanzas"),
)))

# ---- 7. Diario ---------------------------------------------------------
E1 = ("Hoy fue un día raro. Empecé con la sensación de que no iba a rendir nada y terminé "
      "sacando adelante todo lo que tenía pendiente. ¿Por qué me cuesta tanto confiar en las "
      "mañanas?\n\nMañana quiero levantarme sin revisar el teléfono. A ver cuánto dura.")
E2 = "Dormí mal. Volví a soñar con la mudanza, otra vez con las cajas sin marcar."
E3 = ("Llamé a mi mamá. Está bien, el jardín le está quedando lindo y el limonero por fin dio "
      "algo. Me contó lo del vecino con el perro y me reí como no me reía hace rato.")
E4 = ("Estuve pensando en por qué me pongo tan tenso los domingos por la tarde. Creo que es la "
      "sensación de que la semana ya empezó aunque todavía no, y me la paso adelantándome a cosas "
      "que ni siquiera han pasado. Hoy intenté quedarme quieto un rato, sin teléfono, sin lista de "
      "pendientes, solo mirando por la ventana, y a los diez minutos ya estaba buscando algo que "
      "hacer. No sé si eso se entrena. Ana dice que sí, que es cuestión de aburrirse más seguido, "
      "y que el aburrimiento es un músculo que uno deja de usar. Puede ser. Lo que sí sé es que "
      "los domingos que salgo a caminar sin destino terminan mejor que los que me quedo en la casa "
      "organizando cosas que no hacía falta organizar.")


def entry(t, body, clamp=False, more=False, cls=""):
    b = '<div class="body' + (" clamp" if clamp else "") + '">' + body + "</div>"
    m = '<span class="more">Seguir leyendo</span>' if more else ""
    return (f'<a class="entry {cls}" href="diario-entrada.html">'
            f'<div class="t">{t}</div>{b}{m}</a>')


P.append(page("diario.html", "Diario", phone(
    statusbar("21:18"),
    appbar("Diario", "Análisis"),
    tabs(DIA_TABS, "Todo"),
    '<div class="scroll">'
    '<div class="daylabel">miércoles 5 de agosto</div>'
    + entry("21:14", E1)
    + entry("08:02", E2)
    + '<div class="daysep"></div>'
    + '<div class="daylabel">martes 4 de agosto</div>'
    + entry("22:30", E3)
    + '<div class="daysep"></div>'
    + '<div class="daylabel">domingo 2 de agosto</div>'
    + entry("19:05", E4, clamp=True, more=True)
    + '<div style="height:20px"></div>'
    '</div>',
    capture("dia"),
    nav("Diario"),
), body_class="diario"))

P.append(page("diario-vacio.html", "Diario vacío", phone(
    statusbar("21:18"),
    appbar("Diario", "Análisis"),
    tabs(DIA_TABS, "Todo"),
    '<div class="scroll"><div class="empty"><div class="mark"></div>'
    '<h2>El diario está vacío.</h2>'
    '<p>Escribe lo que estés pensando. No hace falta título, ni categoría, ni ánimo del día: '
    'solo el texto.</p></div></div>',
    capture("dia"),
    nav("Diario"),
), body_class="diario"))

P.append(page("diario-fecha-vacia.html", "Diario · día sin entradas", phone(
    statusbar("21:18"),
    appbar("Diario", "Análisis"),
    tabs(DIA_TABS, "Por fecha"),
    '<div class="scroll">'
    '<div class="hero" style="padding-bottom:6px"><div class="monthnav">'
    '<span class="mname" style="font-size:19px">domingo 12 de julio</span>'
    f'<a class="arrow" href="#" aria-label="Día anterior">{I["left"]}</a>'
    f'<a class="arrow" href="#" aria-label="Día siguiente">{I["right"]}</a></div></div>'
    '<div class="empty" style="padding-top:26px"><div class="mark"></div>'
    '<h2>No escribiste nada el 12 de julio.</h2>'
    '<p>Puedes moverte a otro día con las flechas, o volver a todas las entradas.</p></div>'
    '</div>',
    capture("dia"),
    nav("Diario"),
), body_class="diario"))

P.append(page("diario-entrada.html", "Diario · entrada", phone(
    statusbar("21:20"),
    formbar("miércoles 5 de agosto, 21:14", back="diario.html"),
    '<div class="scroll">'
    f'<div style="padding:10px var(--pad-diario) 0"><div class="body" style="font-size:17.5px;'
    f'line-height:1.72;white-space:pre-wrap">{E1}</div></div>'
    '<div class="formfoot">'
    f'<a class="btn btn--ghost" href="diario-escribir.html">{I["pencil"]}Editar</a>'
    '<div style="height:10px"></div>'
    f'<button class="btn btn--text" style="color:var(--danger)">{I["trash"]}Eliminar entrada</button>'
    '</div></div>',
    nav("Diario"),
), body_class="diario"))

P.append(page("diario-escribir.html", "Diario · escribir", phone(
    statusbar("21:22"),
    formbar("Escribir", back="diario.html"),
    '<div class="scroll">'
    '<div class="field" style="padding-top:10px">'
    '<textarea class="textarea is-focus" style="min-height:320px" '
    'placeholder="Lo que estés pensando…"></textarea>'
    '<p class="hint">Se guarda con la fecha y la hora de ahora. Los saltos de línea se '
    'respetan tal cual.</p></div>'
    '<div class="formfoot"><button class="btn btn--primary">Guardar</button></div></div>',
    nav("Diario"),
), body_class="diario"))

P.append(page("diario-escribir-error.html", "Diario · texto vacío", phone(
    statusbar("21:22"),
    formbar("Escribir", back="diario.html"),
    '<div class="scroll">'
    '<div class="field" style="padding-top:10px">'
    '<textarea class="textarea is-err" style="min-height:320px" '
    'placeholder="Lo que estés pensando…">   </textarea>'
    + err("Escribe algo antes de guardar.") + "</div>"
    '<div class="formfoot"><button class="btn btn--primary">Guardar</button></div></div>',
    nav("Diario"),
), body_class="diario"))

P.append(page("diario-voz-revision.html", "Diario por voz · revisar", phone(
    statusbar("21:24"),
    formbar("Revisar entrada", back="diario.html"),
    '<div class="scroll">'
    '<div style="padding:14px var(--pad-diario) 0">'
    '<div class="slabel" style="padding:0 0 8px">Esto fue lo que escuché</div>'
    '<p class="hint" style="margin-top:0">Son tus palabras, sin corregir ni resumir. '
    'Puedes editarlas antes de guardar.</p></div>'
    '<div class="field" style="padding-top:12px">'
    '<textarea class="textarea" style="min-height:260px">Hoy fue un día raro. '
    'Empecé con la sensación de que no iba a rendir nada y terminé sacando adelante todo lo que '
    'tenía pendiente. ¿Por qué me cuesta tanto confiar en las mañanas?</textarea></div>'
    '<div class="formfoot"><button class="btn btn--primary">Guardar</button>'
    '<div style="height:10px"></div>'
    f'<a class="btn btn--text" href="voz-escuchando.html">{I["mic"]}Grabar otra vez</a></div></div>',
    nav("Diario"),
), body_class="diario"))

# ---- 8. Análisis -------------------------------------------------------
SUMMARY = ("<p>En julio anotaste 84 gastos por $2.418.000. Mercado y Comida se llevaron poco "
           "más de la mitad del mes; el resto se reparte entre Transporte y Servicios.</p>"
           "<p>En el diario escribiste 26 veces. La mudanza aparece en nueve de esas entradas, "
           "casi siempre de noche, y a partir del 18 deja de aparecer.</p>")


def ask_block(disabled=False, value="", placeholder="¿En qué gasté más en julio?"):
    d = " is-disabled" if disabled else ""
    dis = " disabled" if disabled else ""
    return ('<div class="ask"><div class="slabel" style="padding:0">Haz una pregunta</div>'
            '<div class="askrow">'
            f'<input class="input{d}" value="{value}" placeholder="{placeholder}"{dis}>'
            f'<button class="askmic{d}"{dis} aria-label="Preguntar con la voz">{I["mic"]}</button>'
            "</div>"
            '<p class="hint">Responde solo con lo que tú has anotado. La respuesta la escribe '
            'tu computador y suele tardar cerca de un minuto.</p></div>')


P.append(page("analisis.html", "Análisis", phone(
    statusbar(),
    appbar("Finanzas", "Ajustes", "finanzas-ajustes.html"),
    tabs(FIN_TABS, "Análisis"),
    '<div class="scroll">'
    '<div class="card"><h2>Resumen de julio</h2>'
    '<div class="stamp">Escrito el 1 de agosto a las 03:12</div>'
    f'<div class="prose">{SUMMARY}</div></div>'
    + ask_block() +
    '</div>',
    capture("fin"),
    nav("Finanzas"),
)))

P.append(page("analisis-sin-resumen.html", "Análisis · sin resumen todavía", phone(
    statusbar(),
    appbar("Finanzas", "Ajustes", "finanzas-ajustes.html"),
    tabs(FIN_TABS, "Análisis"),
    '<div class="scroll">'
    '<div class="card"><h2>Todavía no hay ningún resumen.</h2>'
    '<div class="prose"><p>El primero se escribe solo cuando termine agosto. No tienes que '
    'pedirlo ni esperarlo aquí.</p></div></div>'
    + ask_block() +
    '</div>',
    capture("fin"),
    nav("Finanzas"),
)))

P.append(page("analisis-generando.html", "Análisis · resumen escribiéndose", phone(
    statusbar("03:14"),
    appbar("Finanzas", "Ajustes", "finanzas-ajustes.html"),
    tabs(FIN_TABS, "Análisis"),
    '<div class="scroll">'
    '<div class="card"><h2>Escribiendo el resumen de julio</h2>'
    '<div class="stamp">Empezó a las 03:12</div>'
    '<div class="wait" style="padding:18px 0 0">'
    + tally_block(96, "", "", "", "") +
    '<p class="local" style="margin-top:16px">Lo está escribiendo tu computador, sin que tengas '
    'que esperar aquí. Puedes cerrar la app: cuando vuelvas, estará listo.</p></div></div>'
    + ask_block() +
    '</div>',
    capture("fin"),
    nav("Finanzas"),
), tally=True))

P.append(page("analisis-periodo-vacio.html", "Análisis · mes sin datos", phone(
    statusbar(),
    appbar("Finanzas", "Ajustes", "finanzas-ajustes.html"),
    tabs(FIN_TABS, "Análisis"),
    '<div class="scroll">'
    '<div class="card"><h2>Julio no tiene nada anotado.</h2>'
    '<div class="prose"><p>Sin gastos y sin entradas de diario no hay resumen que escribir. '
    'El de agosto se intentará cuando termine el mes.</p></div></div>'
    + ask_block() +
    '</div>',
    capture("fin"),
    nav("Finanzas"),
)))

P.append(page("analisis-resumen-fallo.html", "Análisis · resumen falló", phone(
    statusbar(),
    appbar("Finanzas", "Ajustes", "finanzas-ajustes.html"),
    tabs(FIN_TABS, "Análisis"),
    '<div class="scroll">'
    '<div class="card"><h2>El resumen de julio no se pudo escribir.</h2>'
    '<div class="stamp">Último intento: 1 de agosto, 03:12</div>'
    '<div class="prose"><p>El modelo de texto de tu computador no respondió. Tus gastos y tu '
    'diario de julio están completos; lo único que falta es el texto del resumen.</p></div>'
    '<div class="note">Puedes revisar si el modelo está encendido en '
    '<b>Ajustes → Tu servidor</b>.</div></div>'
    + ask_block() +
    '</div>',
    capture("fin"),
    nav("Finanzas"),
)))

P.append(page("analisis-esperando.html", "Análisis · pensando la respuesta", phone(
    statusbar(),
    appbar("Finanzas", "Ajustes", "finanzas-ajustes.html"),
    tabs(FIN_TABS, "Análisis"),
    '<div class="scroll">'
    '<div class="card"><div class="qhead">“¿En qué gasté más en julio?”</div>'
    '<div class="wait" style="padding:20px 0 0">'
    '<div class="phase" style="margin-top:0">Pensándolo en tu computador</div>'
    + tally_block(41, "", "", "", "") +
    '<p class="local">Suele tardar alrededor de un minuto. Puedes irte de esta pantalla; '
    'cancelar no borra nada de lo que tienes guardado.</p>'
    '<div class="note" style="margin-top:22px">Lleva escrito hasta ahora:<br>'
    '<span style="color:var(--ink)">“En julio gastaste $2.418.000 en total. Lo más grande fue '
    'Mercado, con…”</span></div>'
    '<div class="acts"><button class="btn btn--ghost">Cancelar la pregunta</button></div>'
    '</div></div>'
    '</div>',
    capture("fin"),
    nav("Finanzas"),
), tally=True))

P.append(page("analisis-respuesta.html", "Análisis · respuesta", phone(
    statusbar(),
    appbar("Finanzas", "Ajustes", "finanzas-ajustes.html"),
    tabs(FIN_TABS, "Análisis"),
    '<div class="scroll">'
    '<div class="card"><div class="qhead">“¿Qué me preocupaba en julio?”</div>'
    '<div class="prose"><p>En julio la mudanza aparece en nueve entradas, casi todas escritas '
    'de noche. También vuelve el sueño con las cajas sin marcar. A partir del 18 deja de '
    'aparecer y lo que escribes cambia hacia el trabajo.</p></div>'
    '<div class="note"><b>Leí 40 de las 112 entradas de julio.</b> No cupieron todas, así que '
    'esta respuesta no cubre el mes completo.</div>'
    '<ul class="facts">'
    '<li><span class="fn">Periodo</span><span class="fv">julio de 2026</span></li>'
    '<li><span class="fn">Entradas leídas</span><span class="fv">40 de 112</span></li>'
    '<li><span class="fn">Tardó</span><span class="fv">1 min 12 s</span></li>'
    '</ul></div>'
    '<div class="statecap">Otra pregunta, sin periodo nombrado</div>'
    '<div class="card"><div class="qhead">“¿Cuánto llevo en comida?”</div>'
    '<div class="prose"><p>Llevas $298.500 en Comida este mes, repartidos en 21 gastos.</p></div>'
    '<div class="note">No dijiste de qué periodo, así que respondí sobre <b>agosto de 2026</b>, '
    'el mes en curso.</div></div>'
    + ask_block() +
    '</div>',
    capture("fin"),
    nav("Finanzas"),
)))

P.append(page("analisis-ocupado.html", "Análisis · ya hay una pregunta en curso", phone(
    statusbar(),
    appbar("Finanzas", "Ajustes", "finanzas-ajustes.html"),
    tabs(FIN_TABS, "Análisis"),
    '<div class="scroll">'
    '<div class="card"><div class="qhead">“¿Cuánto gasté en transporte?”</div>'
    '<div class="prose"><p style="color:var(--ink-soft)">Sin responder todavía.</p></div></div>'
    + ask_block(value="¿Cuánto gasté en transporte?") +
    '</div>',
    nav("Finanzas"),
    '<div class="veil"><div class="sheet"><div class="grab"></div>'
    '<h2>Ya hay una pregunta en curso.</h2>'
    '<p>Tu computador está respondiendo “¿En qué gasté más en julio?”. Puede con una a la vez.</p>'
    '<div class="acts">'
    '<button class="btn btn--primary">Cancelar esa y hacer la mía</button>'
    '<button class="btn btn--text">Esperar a que termine</button>'
    '</div></div></div>',
)))

P.append(page("analisis-ia-no-disponible.html", "Análisis · modelo no disponible", phone(
    statusbar(),
    appbar("Finanzas", "Ajustes", "finanzas-ajustes.html"),
    tabs(FIN_TABS, "Análisis"),
    '<div class="scroll">'
    '<div class="banner banner--flat">'
    f'{I["alert"]}'
    '<div><div class="b-t">El modelo de texto de tu computador no responde.</div>'
    '<div class="b-d">No se pueden hacer preguntas ni escribir resúmenes ahora mismo. '
    'Anotar gastos, escribir en el diario y ver tus totales funciona igual que siempre.</div>'
    '<a class="b-a" href="finanzas-ajustes.html">Ver el estado del servidor</a></div></div>'
    '<div class="card" style="border-top:1px solid var(--rule);margin-top:16px">'
    '<h2>Resumen de julio</h2>'
    '<div class="stamp">Escrito el 1 de agosto a las 03:12</div>'
    f'<div class="prose">{SUMMARY}</div></div>'
    + ask_block(disabled=True, placeholder="No disponible ahora mismo") +
    '</div>',
    capture("fin"),
    nav("Finanzas"),
)))

# ---- 9. Gimnasio -------------------------------------------------------
P.append(page("gimnasio.html", "Gimnasio", phone(
    statusbar(),
    appbar("Gimnasio", None),
    '<div class="gym"><div class="mark"></div>'
    '<h1>Todavía no está disponible.</h1>'
    '<p>Este espacio queda reservado para el gimnasio. Por ahora no hay nada que anotar aquí.</p>'
    '</div>',
    nav("Gimnasio"),
)))

# ---- 10. Sin servidor --------------------------------------------------
P.append(page("sin-servidor.html", "No puedo alcanzar tu servidor", phone(
    statusbar("07:41"),
    '<div class="offline"><div class="mark"></div>'
    '<h1>No puedo alcanzar tu servidor.</h1>'
    '<p>Tu teléfono no encuentra el computador donde vive Autonom-OS. Casi siempre es que el '
    'computador está suspendido o apagado.</p>'
    '<p>Lo que ya guardaste está a salvo allá. No se pierde nada por esperar.</p>'
    '<div class="acts">'
    '<button class="btn btn--primary">Reintentar</button>'
    '<a class="btn btn--ghost" href="finanzas-hoy.html">Abrir la versión de casa</a></div>'
    '<p class="addr">La versión de casa funciona cuando el teléfono y el computador están en '
    'el mismo wifi, aunque no haya internet.<b>https://192.168.1.24:8443</b></p>'
    '</div>',
    nav("Finanzas"),
)))

P.append(page("sin-servidor-banner.html", "Sin servidor · aviso sobre Hoy", phone(
    statusbar("07:42"),
    appbar("Finanzas", "Ajustes", "finanzas-ajustes.html"),
    tabs(FIN_TABS, "Hoy"),
    '<div class="scroll">'
    '<div class="banner">'
    f'{I["alert"]}'
    '<div><div class="b-t">No alcanzo tu servidor.</div>'
    '<div class="b-d">Lo que ves puede estar desactualizado y no se puede guardar nada nuevo '
    'hasta que vuelva. Se reconecta solo.</div>'
    '<a class="b-a" href="sin-servidor.html">Ver qué hacer</a></div></div>'
    '<div class="hero" style="padding-top:18px"><div class="when">miércoles 5 de agosto</div>'
    f'<div class="sum">{HOY_TOTAL}</div>'
    '<div class="sub">4 gastos anotados hoy</div></div>'
    + ledger_rows(HOY) +
    '</div>',
    capture("fin"),
    nav("Finanzas"),
)))

# ---- 11. Catálogo: estados de interacción ------------------------------
def cell(title, why, demo):
    return (f'<div class="cat-cell"><h3>{title}</h3><p class="why">{why}</p>'
            f'<div class="demo">{demo}</div></div>')


STATES = [("Normal", ""), ("Hover", "is-hover"), ("Foco (teclado)", "is-focus"),
          ("Pulsado", "is-active-press"), ("Deshabilitado", "is-disabled")]


def control_row(name, note, render, disable_ok=True):
    """One control across the five states. A state that cannot occur says so."""
    cells = []
    for label, cls in STATES:
        if cls == "is-disabled" and not disable_ok:
            body = ('<div style="min-height:58px;display:flex;align-items:center;'
                    'font-size:13.5px;color:var(--ink-soft)">No existe deshabilitado '
                    'para este control.</div>')
        else:
            body = render(cls, " disabled" if cls == "is-disabled" else "")
        cells.append(
            '<div style="width:188px">'
            f'<div style="font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;'
            f'color:var(--ink-soft);margin-bottom:9px">{label}</div>{body}</div>')
    return ('<div style="background:var(--paper);border:1px solid var(--rule);border-radius:18px;'
            'padding:18px;margin-bottom:18px">'
            f'<h3 style="font-size:16px;font-weight:700">{name}</h3>'
            f'<p class="why" style="margin-top:4px;max-width:640px">{note}</p>'
            '<div style="display:flex;flex-wrap:wrap;gap:18px;margin-top:16px">'
            + "".join(cells) + "</div></div>")


CONTROLS = [
 ("Botón principal — Guardar gasto",
  "Violeta lleno. Al pulsar oscurece; nunca cambia de color. Deshabilitado sólo mientras se guarda.",
  lambda c, d: f'<button class="btn btn--primary {c}"{d}>Guardar gasto</button>', True),
 ("Botón secundario — Escribir a mano",
  "Contorno violeta sobre blanco. El hover es un tinte violeta claro, no un gris ni otro tono.",
  lambda c, d: f'<button class="btn btn--ghost {c}"{d}>Escribir a mano</button>', True),
 ("Chip elegido / sin elegir / crear",
  "El control que sostiene el presupuesto de cuatro toques. 44 px de alto en todos los estados.",
  lambda c, d: (f'<div class="chips"><button class="chip is-on {c}"{d}>Transporte</button>'
                f'<button class="chip {c}"{d}>Comida</button>'
                f'<button class="chip chip--new {c}"{d}>Nueva</button></div>'), True),
 ("Botón de voz",
  "Deshabilitado sólo cuando la transcripción del servidor no responde.",
  lambda c, d: (f'<button class="mic {c}"{d} aria-label="Grabar">{I["mic28"]}</button>'), True),
 ("Pestaña de módulo",
  "Hoy · Este mes · Análisis. La activa lleva subrayado violeta; no hay pestaña deshabilitada.",
  lambda c, d: (f'<div class="tabs" style="border:0;padding:0">'
                f'<a class="tab is-on {c}" href="#">Hoy</a>'
                f'<a class="tab {c}" href="#">Este mes</a></div>'), False),
 ("Flecha de mes",
  "El mes siguiente sí se deshabilita: no hay futuro que mirar.",
  lambda c, d: (f'<div style="display:flex;gap:6px"><a class="arrow {c}" href="#">{I["left"]}</a>'
                f'<a class="arrow {c}" href="#">{I["right"]}</a></div>'), True),
 ("Fila del libro de gastos",
  "Toda la fila se toca para editar. El pulsado usa el tinte violeta más profundo — ahí el texto "
  "secundario sigue por encima de 4,5:1.",
  lambda c, d: (f'<div style="border:1px solid var(--rule);border-radius:14px;overflow:hidden">'
                f'<a class="row {c}" href="#" style="border-bottom:0;padding:13px 14px">'
                f'<span class="what"><span class="cat">Transporte</span>'
                f'<span class="meta">19:40 · Tarjeta de crédito</span></span>'
                f'<span class="amt">$14.000</span></a></div>'), False),
 ("Navegación de abajo",
  "Siempre visible, siempre con los tres destinos. Ninguno se deshabilita: Gimnasio se abre y "
  "explica que todavía no está.",
  lambda c, d: (f'<div style="border:1px solid var(--rule);border-radius:14px;overflow:hidden">'
                f'<nav class="nav" style="border-top:0;padding-bottom:0">'
                f'<a class="is-on {c}" href="#"><span>Finanzas</span><span class="soon"></span></a>'
                f'<a class="{c}" href="#"><span>Diario</span><span class="soon"></span></a>'
                f'</nav></div>'), False),
 ("Campo de texto",
  "El foco engorda el borde y añade contorno; el error lo pinta de rojo, el único uso del rojo "
  "junto con eliminar.",
  lambda c, d: f'<input class="input {c}"{d} value="¿Qué gasté en julio?">', True),
 ("Botón destructivo",
  "El rojo aparece aquí y en los errores de validación, en ningún otro sitio. Nunca se "
  "deshabilita: si se puede eliminar, se puede pulsar.",
  lambda c, d: f'<button class="btn btn--danger {c}"{d}>Eliminar</button>', False),
]

P.append(page("estados-interactivos.html", "Estados de interacción",
    '<div class="cat-wrap" style="max-width:1120px"><h1>Estados de interacción</h1>'
    '<p class="lede">Cada control en los cinco estados. Están forzados con una clase que comparte '
    'exactamente la misma regla CSS que la pseudoclase real '
    '(<code>.btn:hover, .btn.is-hover { … }</code>), así que lo que se ve aquí no puede '
    'separarse de lo que ocurre al tocar. Es la fila de la matriz que una captura estática '
    'nunca muestra, y donde se escondió el único fallo que se escapó en el piloto anterior.</p>'
    + "".join(control_row(*c) for c in CONTROLS) + "</div>",
    extra_css="body{background:var(--paper-sunk)}"))

# ---- 12. Catálogo: estados terminales de una pregunta ------------------
def ans_cell(code, title, body, action=None):
    a = (f'<div style="margin-top:14px"><button class="btn btn--ghost" '
         f'style="min-height:48px;font-size:16px">{action}</button></div>') if action else ""
    return cell(f'error_code: {code}',
                "Estado terminal que el contrato puede devolver de verdad.",
                f'<div class="card" style="border:0;padding:0">'
                f'<div class="qhead">“{title}”</div>'
                f'<div class="prose" style="font-size:16px">{body}</div>{a}</div>')


P.append(page("analisis-errores.html", "Análisis · respuestas que no llegan",
    '<div class="cat-wrap"><h1>Cuando la pregunta no se puede responder</h1>'
    '<p class="lede">Los cinco finales que <code>GET /api/insights/questions/{job_id}</code> '
    'puede devolver con <code>status: failed</code>, tal como se leen dentro de la tarjeta de la '
    'pregunta. Ninguno inventa una cifra y ninguno pide disculpas.</p>'
    '<div class="cat-grid">'
    + ans_cell("insufficient_data", "¿Cómo me fue con la comida en 2024?",
               "<p>Todavía hay muy poco anotado de ese periodo para decir algo que sirva.</p>")
    + ans_cell("period_unrecognised", "¿Cuánto gasté en la temporada pasada?",
               "<p>No entendí de qué periodo hablas. Prueba nombrando un mes, “este mes” o "
               "“el mes pasado”.</p>", "Preguntar de otra forma")
    + ans_cell("unverifiable_figures", "¿Cuánto me ahorré en julio?",
               "<p>No puedo responder eso con lo que tienes anotado. Prefiero no darte una cifra "
               "antes que darte una inventada.</p>")
    + ans_cell("llm_timeout", "¿Qué cambió entre mayo y julio?",
               "<p>Pasaron dos minutos y tu computador seguía escribiendo, así que lo detuve. "
               "Una pregunta más corta suele salir.</p>", "Preguntar otra vez")
    + ans_cell("preempted", "¿En qué gasté más en julio?",
               "<p>La respuesta se detuvo porque empezaste a grabar y la voz va primero. "
               "Nada se perdió.</p>", "Volver a preguntar")
    + '</div></div>',
    extra_css="body{background:var(--paper-sunk)}"))

# ---------------------------------------------------------------- index
GROUPS = [
 ("Finanzas", [
   ("finanzas-hoy.html", "Hoy — pantalla de inicio", "1.1 1.2 1.4 4.1 2.5"),
   ("finanzas-hoy-vacio.html", "Hoy sin gastos", "4.5 · constraint 15"),
   ("finanzas-mes.html", "Este mes — en qué se fue", "4.2 4.3 4.4 4.7"),
   ("finanzas-mes-vacio.html", "Mes sin gastos", "4.5 · constraint 15"),
   ("finanzas-ajustes.html", "Ajustes: categorías, servidor, exportar", "3.2 3.3 14.2"),
   ("finanzas-ajustes-quitar.html", "Quitar una categoría en uso", "3.4 · constraint 19"),
 ]),
 ("Anotar un gasto", [
   ("gasto-nuevo.html", "Formulario manual — las cuatro interacciones", "2.1 2.8"),
   ("gasto-nuevo-error.html", "Validación: monto, categoría y método", "2.2 2.3"),
   ("gasto-nuevo-nueva-categoria.html", "Crear categoría sin salir del gasto", "3.2"),
   ("gasto-guardando.html", "Guardando", "constraint 16"),
   ("gasto-guardar-fallo.html", "No se pudo guardar — el texto se queda", "13.5"),
   ("gasto-editar.html", "Editar un gasto", "5.1"),
   ("gasto-eliminar.html", "Confirmar antes de eliminar", "5.2 · constraint 19"),
 ]),
 ("Voz", [
   ("voz-escuchando.html", "Escuchando", "8.1 · constraint 17"),
   ("voz-transcribiendo.html", "Transcribiendo (contador vivo)", "8.8 · constraints 25 26 28"),
   ("gasto-voz-revision.html", "Revisar el gasto dictado", "9.1 9.2 8.2 8.6"),
   ("gasto-voz-largo.html", "Descripción recortada a 1.000", "contrato: description_truncated"),
   ("voz-fallo.html", "No se entendió el audio", "8.4"),
   ("voz-sin-permiso.html", "Sin permiso de micrófono", "8.5"),
   ("diario-voz-revision.html", "Revisar la entrada dictada", "10.1 10.2 10.3"),
 ]),
 ("Diario", [
   ("diario.html", "Entradas por día", "7.1 6.4"),
   ("diario-vacio.html", "Diario vacío", "7.3"),
   ("diario-fecha-vacia.html", "Un día sin nada escrito", "7.2"),
   ("diario-entrada.html", "Una entrada completa", "6.4 6.5 5.3"),
   ("diario-escribir.html", "Escribir", "6.1 6.6"),
   ("diario-escribir-error.html", "Texto en blanco", "6.2"),
 ]),
 ("Análisis (dentro de Finanzas)", [
   ("analisis.html", "Resumen listo + preguntar", "11.14 11.15 11.18"),
   ("analisis-sin-resumen.html", "Nunca se ha hecho un resumen", "11.16 · constraint 27"),
   ("analisis-generando.html", "Resumen escribiéndose", "constraint 27"),
   ("analisis-periodo-vacio.html", "El periodo no tiene datos", "11.16"),
   ("analisis-resumen-fallo.html", "El resumen falló", "constraint 27"),
   ("analisis-esperando.html", "Pensando la respuesta", "11.5 11.12 11.13 · constraints 25 26"),
   ("analisis-respuesta.html", "Respuesta, con lo que no cupo", "11.8 11.9 11.11"),
   ("analisis-ocupado.html", "Ya hay una pregunta en curso (409)", "contrato: busy"),
   ("analisis-ia-no-disponible.html", "El modelo no responde", "11.4"),
   ("analisis-errores.html", "Los cinco finales fallidos", "11.3 11.11"),
 ]),
 ("Sistema", [
   ("gimnasio.html", "Gimnasio — sin captura, sin lista, sin error", "1.3 · constraint 20"),
   ("sin-servidor.html", "No puedo alcanzar tu servidor (apertura en frío)", "13.2 13.8 · constraint 18"),
   ("sin-servidor-banner.html", "Aviso con la app ya abierta", "13.2 13.3"),
   ("estados-interactivos.html", "Estados de interacción de cada control", "constraints 5 10"),
 ]),
]


def build_index(shots_exist):
    rows = []
    for gname, items in GROUPS:
        cells = []
        for f, title, req in items:
            shot = f"shots/{f.replace('.html','')}.png"
            thumb = (f'<img src="{shot}" alt="" style="width:100%;display:block;border-radius:10px;'
                     f'border:1px solid var(--rule)">' if shots_exist and
                     os.path.exists(os.path.join(OUT, shot)) else
                     '<div style="height:120px;background:var(--paper-sunk);border-radius:10px"></div>')
            cells.append(
                f'<a href="{f}" style="width:212px;display:block">{thumb}'
                f'<div style="font-size:14.5px;font-weight:700;margin-top:9px;line-height:1.35">{title}</div>'
                f'<div style="font-size:12px;color:var(--ink-soft);margin-top:3px">{req}</div></a>')
        rows.append(f'<h2 style="font-size:13px;font-weight:700;letter-spacing:.14em;'
                    f'text-transform:uppercase;color:var(--ink-soft);margin:34px 0 14px">{gname}</h2>'
                    '<div style="display:flex;flex-wrap:wrap;gap:20px">' + "".join(cells) + "</div>")
    return page("index.html", "Autonom-OS · mockups",
        '<div class="cat-wrap" style="max-width:1080px">'
        '<h1>Autonom-OS — mockups para revisar</h1>'
        '<p class="lede">Pantallas estáticas, en español, a 390×844. Cada archivo se abre solo, '
        'sin servidor ni conexión. Los datos son de ejemplo pero tienen exactamente la forma que '
        'devuelve el contrato del backend.</p>'
        '<p class="lede" style="margin-top:10px"><a href="matriz.html" '
        'style="color:var(--violet);font-weight:700">Ver la matriz de capturas</a> — '
        'todas las pantallas y estados renderizados, incluidos hover, foco, pulsado y '
        'deshabilitado.</p>'
        + "".join(rows) + "</div>",
        extra_css="body{background:var(--paper-sunk)}")


build_index(False)

print("\n".join(sorted(set(P))))
print(f"{len(set(P))} páginas en {OUT}")
