# Run 02 mockup stylesheet DELTA.
#
# The base is imported verbatim from the Run 01 approved mockups
# (../../../../mockups/_build/css.py), which is also what the shipped
# stylesheets were carried from. Nothing below redefines a Run 01 selector —
# every rule here is a new class for a new surface, so a Run 02 mockup and a
# Run 01 mockup are literally the same stylesheet plus this file.
#
# No `var(--danger…)` appears anywhere in this delta: constraint 38 requires a
# neutral edited-since mark, and `estilos.test.ts:62-74` allows red in three
# named modules only.
import os
import sys

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "mockups", "_build")))

from css import CSS as BASE_CSS, AUDIT_JS  # noqa: E402

DELTA = r"""
/* ================= Run 02 — new surfaces only ================= */

/* ---------- form bar (constraint 36: the journal read screen's frame) ----------
   Mirrors Screen.module.css:67-100 exactly, so the detail screen and
   EntradaLeer are the same object. */
.formbar{flex:none;padding:2px var(--pad) 0;display:flex;align-items:center}
.formbar .close{
  width:44px;height:44px;display:inline-flex;align-items:center;justify-content:center;
  color:var(--violet);margin-left:-10px;flex:none;
}
.formbar .close:hover,.formbar .close.is-hover{color:var(--violet-deep)}
.formbar .close:focus-visible,.formbar .close.is-focus{
  outline:2.5px solid var(--violet);outline-offset:-2px;border-radius:999px;
}
.formbar .ftitle{
  flex:1;font-size:17px;font-weight:700;margin-left:4px;min-width:0;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
}

/* ---------- Historial: the ordering statement (16.6, constraint 31) ----------
   Same treatment as Hoy's `.hero .when` date line — it occupies the same slot,
   "what am I looking at", and is read before the first row. No count readout:
   "mostrando 50 de 431" is named on the Avoid list. */
.orden{padding:22px var(--pad) 17px}
.orden p{
  font-size:14px;font-weight:600;color:var(--ink-soft);letter-spacing:.01em;line-height:1.45;
  max-width:320px;
}

/* ---------- Historial: show more (16.7, constraint 32) ----------
   The existing quiet-action vocabulary (.btn--text) centred under the last
   rule. No border, no fill, no spinner: a page turn, not a call to action. */
.vermas{display:flex;justify-content:center;padding:12px var(--pad) 8px}
.vermas .btn{width:auto;padding:0 22px}
/* The Run 01 mockup stylesheet has no disabled rule for `.btn--text` at all,
   though the shipped Button.module.css:123-126 does. Mirrored here so the
   in-flight control is drawn as it would really render. */
.vermas .btn[disabled]{color:var(--ink-soft);cursor:not-allowed}
/* Must beat `.btn--text:hover` (0,2,0), which sets a background that the
   disabled rule does not reset — found by forcing :hover on the in-flight
   control and looking at the render, not by reading the CSS. The same omission
   is live in Button.module.css `.text:disabled`; see the design note,
   "What the renders found that reading the CSS did not". */
.vermas .btn[disabled]:hover,.vermas .btn[disabled].is-hover{background:none}

/* Constraint 29 remedy, drawn for the gate decision only — see the design note.
   Uniform across all four labels: same font size, same weight, same padding.
   Nothing here ships unless the human asks for it. */
.tabs--estrecho{gap:6px;padding:0 calc(var(--pad) - 7px)}
.tabs--estrecho .tab{padding:0 7px}

/* ---------- month: a category row you can open (18.1, constraint 39) ----------
   The app already distinguishes tappable from static by where the hairline
   runs: `.ledger .row` is full-bleed and washes on press, `.brk`/`.pm` are
   inset and inert. Category rows move to the full-bleed side of that existing
   grammar and gain the violet chevron; payment rows keep today's inset rule
   and gain nothing, so the difference is legible without touching either. */
.brk--tap{padding:0;border-top:1px solid var(--rule)}
.brk--tap li{padding:0;border-bottom:0}
.catrow{
  display:block;width:100%;text-align:left;
  padding:11px var(--pad) 13px;border-bottom:1px solid var(--rule);
}
.catrow .line{display:flex;align-items:baseline;gap:10px}
.catrow .name{flex:1;font-size:16px;font-weight:600;min-width:0}
.catrow .val{
  font-size:16px;font-weight:700;font-variant-numeric:tabular-nums lining-nums;
  font-feature-settings:"tnum" 1,"lnum" 1;
}
.catrow .pct{
  width:44px;text-align:right;font-size:14px;font-weight:700;color:var(--ink-soft);
  font-variant-numeric:tabular-nums;
}
.catrow .chev{flex:none;color:var(--violet);display:inline-flex;align-self:center;margin-left:-2px}
.catrow .track{margin-top:9px;height:7px;border-radius:4px;background:var(--paper-sunk)}
.catrow .fill{height:7px;border-radius:4px;background:var(--t2)}
.catrow:hover,.catrow.is-hover{background:var(--violet-wash)}
.catrow:active,.catrow.is-active-press{background:var(--violet-wash2)}
.catrow:focus-visible,.catrow.is-focus{
  outline:2.5px solid var(--violet);outline-offset:-2.5px;background:var(--violet-wash);
}

/* ---------- month: the opened category (18.3-18.5, constraints 40, 41) ----------
   One recessed full-bleed band — the lid lifted on a number already on screen.
   --paper-sunk is the app's existing "recessed surface" token (the bar track,
   the disabled fill); no new colour, no new shape language, and it cannot be
   read as a banner because it is square, full-bleed and carries no icon. */
.opened{
  background:var(--paper-sunk);
  border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);
  padding:15px var(--pad) 17px;
}
.opened .head{display:flex;align-items:center;gap:12px}
.opened .cname{flex:1;font-size:19px;font-weight:700;letter-spacing:-.01em;min-width:0}
.opened .cerrar{
  flex:none;display:inline-flex;align-items:center;gap:6px;
  min-height:44px;padding:0 4px;font-size:15px;font-weight:700;color:var(--violet);
}
.opened .cerrar:hover,.opened .cerrar.is-hover{
  color:var(--violet-deep);text-decoration:underline;text-underline-offset:3px;
}
.opened .cerrar:active,.opened .cerrar.is-active-press{color:var(--violet-deep)}
.opened .cerrar:focus-visible,.opened .cerrar.is-focus{
  outline:2.5px solid var(--violet);outline-offset:2px;border-radius:8px;
}
.opened .figs{margin-top:2px;display:flex;align-items:baseline;gap:12px}
.opened .ctotal{
  font-size:22px;font-weight:700;letter-spacing:-.012em;
  font-variant-numeric:tabular-nums lining-nums;font-feature-settings:"tnum" 1,"lnum" 1;
}
.opened .ccount{font-size:14px;font-weight:600;color:var(--ink-soft)}

/* ---------- the expense detail: a small receipt (17.2-17.6, constraints 35-38) ----------
   No uppercase label above a bordered box anywhere — that is what this app's
   forms look like, and constraint 35 says this must not look like a form. */
.receipt{padding:24px var(--pad) 0}
.receipt .ramt{
  font-size:46px;font-weight:300;letter-spacing:-.025em;line-height:1.05;
  font-variant-numeric:tabular-nums lining-nums;font-feature-settings:"tnum" 1,"lnum" 1;
}
.receipt .rcat{margin-top:9px;font-size:19px;font-weight:700;letter-spacing:-.01em}
/* 17.2 / constraint 37: shown whole. No clamp, no line limit, no control. */
.receipt .rdesc{
  margin-top:15px;font-size:16.5px;line-height:1.66;overflow-wrap:break-word;
}

.rfacts{margin-top:26px;border-top:1px solid var(--rule)}
.rfacts li{
  display:flex;gap:14px;align-items:baseline;padding:13px 0;
  border-bottom:1px solid var(--rule);
}
.rfacts .fn{flex:1;font-size:15px;font-weight:600;color:var(--ink-soft)}
.rfacts .fv{font-size:16px;font-weight:700;text-align:right}

/* 17.4 / constraint 37: the recorded moment is a footnote about the record and
   sits well away from the dated-for date, which is a fact about the money.
   17.5 / constraint 38: the edited line is the same ink, the same size and the
   same block — a fact, not a warning. No red, no icon, no badge. */
.stampnote{padding:19px var(--pad) 0}
.stampnote p{font-size:13.5px;line-height:1.6;color:var(--ink-soft)}
.stampnote p + p{margin-top:4px}

/* Pending, following the one in-repo pattern (Finanzas.module.css:198-202). */
.skel{padding:22px var(--pad);color:var(--ink-soft);font-size:15px}

/* ---------- index (review artefact, not app UI) ---------- */
.idx{max-width:860px;margin:0 auto;padding:30px 22px 70px}
.idx h1{font-size:26px;font-weight:700;letter-spacing:-.015em}
.idx .lede{margin-top:9px;font-size:15.5px;line-height:1.62;color:var(--ink-soft);max-width:620px}
.idx h2{margin-top:34px;font-size:12px;font-weight:700;letter-spacing:.15em;
  text-transform:uppercase;color:var(--ink-soft)}
.idx ul{margin-top:10px;background:var(--paper);border:1px solid var(--rule);border-radius:16px}
.idx li + li{border-top:1px solid var(--rule)}
.idx a{display:block;padding:14px 17px}
.idx a:hover{background:var(--violet-wash)}
.idx a:focus-visible{outline:2.5px solid var(--violet);outline-offset:-3px;border-radius:16px}
.idx .n{font-size:16px;font-weight:700}
.idx .d{margin-top:3px;font-size:13.5px;line-height:1.5;color:var(--ink-soft)}
.idx .c{margin-top:4px;font-size:12.5px;font-weight:700;color:var(--violet);letter-spacing:.02em}
"""

CSS = BASE_CSS + DELTA
