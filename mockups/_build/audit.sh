#!/usr/bin/env bash
# Reads back the in-page audit (horizontal scroll, <44px targets, AA contrast)
# for every mockup at the design viewport.
set -u
CHROME=/usr/bin/chromium-browser
ROOT=/home/david/Proyectos/Autonom-OS/mockups
PROFILE=$ROOT/_build/.chrome
W=${1:-390}; H=${2:-844}
for f in "$ROOT"/*.html; do
  b=$(basename "$f")
  case "$b" in index.html|matriz.html) continue;; esac
  t=$("$CHROME" --headless --disable-gpu --no-first-run --user-data-dir="$PROFILE" \
      --virtual-time-budget=1500 --window-size="$W,$H" --hide-scrollbars \
      --dump-dom "file://$ROOT/$b?audit=1" 2>/dev/null \
      | grep -o '<title>[^<]*</title>' | head -1 | sed 's|</\?title>||g')
  echo "$b :: $t"
done
