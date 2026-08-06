#!/usr/bin/env bash
# Renders the screenshot matrix. Chromium here is sandboxed and writes nothing
# under /tmp, so every path (profile, HTML, PNG) stays inside the project or $HOME.
set -u
CHROME=/usr/bin/chromium-browser
ROOT=/home/david/Proyectos/Autonom-OS/mockups
SHOTS=$ROOT/shots
PROFILE=/home/david/Proyectos/Autonom-OS/mockups/_build/.chrome
mkdir -p "$SHOTS" "$PROFILE"

shoot () {  # shoot <outname> <file+query> <w> <h>
  local out="$SHOTS/$1.png"
  local url="file://$ROOT/$2"
  local w="$3"
  local h="$4"
  "$CHROME" --headless --disable-gpu --no-first-run --no-default-browser-check \
    --hide-scrollbars --force-device-scale-factor=2 \
    --user-data-dir="$PROFILE" --virtual-time-budget=1800 \
    --window-size="$w,$h" --screenshot="$out" "$url" >/dev/null 2>&1
  if [ -s "$out" ]; then echo "ok   $1 ($w x $h)"; else echo "FAIL $1"; fi
}

# --- every screen at the design target -------------------------------------
for f in "$ROOT"/*.html; do
  b=$(basename "$f" .html)
  case "$b" in index|matriz|estados-interactivos|analisis-errores) continue;; esac
  shoot "$b" "$b.html" 390 844
done

# --- catalogue pages (wider, they are review artefacts) --------------------
shoot estados-interactivos "estados-interactivos.html" 1160 2000
shoot analisis-errores     "analisis-errores.html"     1160 1200

# --- scrolled views of the screens that are taller than the phone ----------
shoot gasto-nuevo--desplazado          "gasto-nuevo.html?scroll=330"          390 844
shoot gasto-nuevo-error--desplazado    "gasto-nuevo-error.html?scroll=300"    390 844
shoot gasto-voz-revision--desplazado   "gasto-voz-revision.html?scroll=420"   390 844
shoot finanzas-mes--desplazado         "finanzas-mes.html?scroll=430"         390 844
shoot diario--desplazado               "diario.html?scroll=520"               390 844
shoot analisis-respuesta--desplazado   "analisis-respuesta.html?scroll=340"   390 844

# --- the same wait, two moments apart: proof it changes --------------------
shoot voz-transcribiendo--3s   "voz-transcribiendo.html?freeze=3"    390 844
shoot voz-transcribiendo--14s  "voz-transcribiendo.html?freeze=14"   390 844
shoot analisis-esperando--12s  "analisis-esperando.html?freeze=12"   390 844
shoot analisis-esperando--68s  "analisis-esperando.html?freeze=68"   390 844

# --- narrower and wider viewports -----------------------------------------
shoot finanzas-hoy--360   "finanzas-hoy.html"   360 780
shoot gasto-nuevo--360    "gasto-nuevo.html"    360 780
shoot finanzas-mes--320   "finanzas-mes.html"   320 700
shoot gasto-nuevo--320    "gasto-nuevo.html"    320 700
shoot diario--320         "diario.html"         320 700
shoot finanzas-hoy--900   "finanzas-hoy.html"   900 900
shoot diario--900         "diario.html"         900 900

echo "listo"
