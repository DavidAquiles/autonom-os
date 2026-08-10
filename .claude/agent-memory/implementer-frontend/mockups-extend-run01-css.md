---
name: mockups-extend-run01-css
description: Build any new run's mockups by importing mockups/_build/css.py verbatim and appending a delta — never re-author the stylesheet; plus the measured capacity of the Finanzas tab strip
metadata:
  type: project
---

New mockups for a brownfield run must **import the Run 01 stylesheet, not
recreate it**: `mockups/_build/css.py` exports `CSS` (and `AUDIT_JS`), it has no
import side effects, and it is the same file `styles/tokens.css` and the shipped
CSS modules were carried from. Run 02 did
`sys.path.insert(...); from css import CSS as BASE_CSS` and appended a delta of
**new class names only**. `mockups/_build/build.py` must **not** be imported —
it writes all the Run 01 pages at import time.

**Why:** it makes "indistinguishable from the shipped product" a property of the
build rather than a thing review has to check by eye, and it means a Run 01
declaration cannot be silently contradicted by a Run 02 one.

**How to apply:**
- Delta rules get new class names (`.rfacts`, not a second `.facts`). A
  redefinition would leak across every page that inlines the blob.
- `AUDIT_JS` (loaded by `page()`) is a free gate: `?audit=1` reports contrast,
  sub-44×44 targets and horizontal overflow through `document.title`, and
  `?scroll=N` gives deterministic scrolled shots. Assert `AUDIT h=0 t=0 c=0` at
  **390 and 320**.
- The base stylesheet mirrors every pseudo-class with an `.is-hover`-style
  helper. Ignore the helpers and force the real pseudo-class over CDP anyway —
  see [[verify-interactive-states]]. Run 02 found two bugs that way; the helpers
  would have hidden one, because the base sheet has **no** disabled rule for
  `.btn--text` even though shipped `Button.module.css` does.
- Chromium is `/usr/bin/chromium-browser` and writes nothing under `/tmp` —
  see [[env-chromium-sandbox]].

**The Finanzas tab strip's measured capacity, at 16px with the current metrics
(`.tabs` gap 10, `.tab` padding 9):** four labels — Hoy · Este mes · Historial ·
Análisis — total **278.7 px** of label boxes and end at **319.7 px** inside a
390 px viewport, so ~70 px of slack. The strip **wraps at 330 px and below**.
A fifth tab does not fit; the uniform remedy (gap 10→6, padding 9→7, no font
change, `Hoy` still exactly 44 px) buys ~35 px and is drawn in
`factory/implementer-frontend/mockups/historial-tira-estrecha.html`. Measure
with a `Range` over the label's text node and count `getClientRects().length` —
element height proves nothing, `.tab` has `min-height:46px`.

Related: [[autonomos-context]].
