# Frontend — Phase 1 design note (Run 02, brownfield feature)

**Status: mockups ready for review. No application code was written.** Nothing
under `frontend/src/` was touched.

- Mockups: `factory/implementer-frontend/mockups/` — open `index.html`.
- Screenshots: `factory/implementer-frontend/mockups/shots/` — 49 PNGs.
- Builders (review artefacts, not app code): `mockups/_build/{css02.py,build02.py,shots02.mjs}`.

Every mockup is one self-contained HTML file: inline CSS, inline SVG, no
network request, no build step, no external font. `grep` for `http`, `<link>`
and `src=` across all 17 files returns nothing.

**On the `frontend-design` skill.** It was loaded into this turn as a command
(`<command-name>frontend-design:frontend-design</command-name>`), so per the
Skill tool's own instruction I followed it directly rather than calling it a
second time. Its two-pass method — plan the token system, critique the plan
against the generic default, then build — is what § Direction records. Where its
instincts and PM's brief could have diverged, the brief won: this run's whole
job is to be indistinguishable from a shipped product, and the brief says in as
many words "no new colour, no new typeface, no new icon family".

---

## Direction

There was no palette to choose. `mockups/_build/css.py` — the stylesheet the
Run 01 mockups were approved on, and the one `styles/tokens.css` was carried
from — is imported *verbatim* by `css02.py`, and every Run 02 rule is appended
as new classes that redefine nothing. A Run 02 mockup is literally the Run 01
stylesheet plus a delta. That is the strongest available guarantee that these
screens and the shipped ones are the same object.

So the craft went into four decisions, each derived from something the product
already says rather than from taste:

**1. The grammar of "you can tap this" was already in the product; I used it
instead of inventing one.** Finanzas today draws tappable rows full-bleed with
the hairline running edge to edge (`.ledger .row`), and static rows inset with
the hairline stopping at the gutter (`.brk`, `.pm`). Nobody wrote that down, but
it is true of every screen. Making the category rows tappable therefore meant
moving them to the full-bleed side of a distinction the user has already learnt,
and leaving the payment-method rows exactly as they are. Put
`shots/finanzas-mes--frontera.png` in front of someone and the boundary between
the two kinds of row is visible before a word is read — which is what
constraint 39 asks for and what a hover state alone could never deliver. A
violet chevron (the app's existing `RightIcon`, at 18 px) is the second,
non-structural cue, so tappability is never carried by shape alone or colour
alone.

**2. Historial opens with one sentence and no number.** The obvious move is an
`<h1>Historial</h1>` and a count. Both were cut. The tab strip already says
Historial two centimetres above — repeating it is the app "explaining itself
twice", which the brief's tone note forbids. And `total_count` is on the wire,
so "431 gastos" was free to render; the Avoid list names exactly that
("mostrando 50 de 431 rendered as a status readout"), so it stays off the
screen. What is left is a single line in the same 14 px/600/`--ink-soft`
treatment Hoy uses for its date — the "what am I looking at" slot, reused:
*"En el orden en que los anotaste, no por su fecha."* One sentence, stating the
order and pre-empting the "these dates are broken" reading in the same breath.

**3. The detail is a receipt, and the two timestamps live in different
neighbourhoods.** The amount takes Hoy's hero treatment (46 px/300, tabular),
the category sits under it at 19 px/700, the description is prose at
16.5 px/1.66 with no clamp. The record's facts — method, dated-for date — are a
hairline-ruled label/value run, the pattern Análisis already uses (`.facts`) at
a roomier rhythm. *Below that rule*, in 13.5 px `--ink-soft` footnote text, sit
"Anotado el…" and, when it applies, "Editado el…". That separation is
deliberate: constraint 37 forbids the two dates reading as one value or a range,
and stacking them as adjacent rows in one list is the arrangement that would
invite it. It also delivers the Feel note's "when it was typed in is a
footnote-weight fact" literally. There is no uppercase label above a bordered
box anywhere — that is what this app's forms look like, and constraint 35 says
this must not look like one.

**4. The one bold move: the opened category is a recessed full-bleed band.**
When a category is open, the breakdown gives way to a single band on
`--paper-sunk` — the app's existing "recessed surface" token, used today for the
bar track and disabled fills — carrying the category name, its total, its count
and the way to close it. It is square, full-bleed and carries no icon, so it
cannot be confused with the rounded `.banner`. Nothing else on the screen has a
fill behind a heading, which is what makes "the lid is open on this one" legible
at a glance. The month name and the month total stay above it, untouched, so the
month is never lost.

I considered expanding the selected row in place instead. It is a truer
"accordion", and it fails: if the user opens the eighth category, the category
total and the close control are both below the fold, and constraints 40 and 41
are both graded on a 390×844 screenshot taken from the top.

**Removed on the last pass (Chanel's rule):** an end-of-list mark for Historial
("ya viste todo"). It was the fifth idea and it was the one to cut — see Open
Question 4.

---

## Constraints Conformance

### The new constraints, 29–43

**29 — four tabs, all legible at 390×844.** Measured, not eyeballed
(`shots02.mjs § measureTabs`, run against the real render):

| viewport | strip content | last tab's right edge | slack | any label wrapped | any label clipped | sizes |
| --- | --- | --- | --- | --- | --- | --- |
| **390** | 390 px | 319.7 px | **70.3 px** | no (all `lineBoxes=1`) | no (`textOverflow: clip`, `scrollWidth == clientWidth`) | all four 16 px; 700 active, 600 inactive |
| 360 | 360 px | 319.7 px | 40.3 px | no | no | same |
| 330 and below | — | — | — | **"Este mes" wraps to 2 lines** | no | same |

Touch targets: `Hoy` 47.3×46, `Este mes` 81.1×46, `Historial` 78.5×46,
`Análisis` 71.8×46 — every one clears 44×44 (constraint 10). No horizontal
overflow at 390 or 320 (`AUDIT h=0` on every page at both widths). R2's estimate
of "roughly 360 px with under 30 px of margin" was pessimistic; the real figure
is 278.7 px of labels and 70.3 px of slack. **Constraint 29 passes as
specified.** The sub-331 px wrap is outside constraint 29's stated viewport but
is a real regression caused by the fourth tab, and it is Open Question 2 with a
drawn remedy.

**30 — Historial's rows are Hoy's rows.** Same `.row` / `.what` / `.cat` /
`.meta` / `.amt` markup, same stylesheet rules, no Historial-specific override
exists. Compare `shots/historial.png` with Run 01's `mockups/shots/finanzas-hoy*`:
structure identical, facts different. Historial's secondary line is
`5 de agosto · Tarjeta de crédito` where Hoy's is `19:40 · Tarjeta · Uber a la
casa` — the dated-for date leads, because it is the fact that makes the
non-descending order legible and it must never be the thing the ellipsis eats.

**31 — the ordering statement.** `shots/historial.png`, one line above the first
rule, read before any row. Also present with the unreachable banner above it
(`shots/historial--sin-servidor.png`) — the banner does not displace it.

**32 — show-more present and absent, distinguishable on sight.** Both
photographed at the bottom of the list, which is the only place the difference
lives: `shots/historial--abajo.png` (a centred violet "Ver gastos más antiguos")
against `shots/historial--sin-control.png` (the list ends at the last hairline
and nothing follows). No spinner, no trailing affordance, no label in the absent
state. The in-flight case keeps the control in place and greys it —
`shots/historial--ver-mas-en-curso.png` — rather than growing a bottom spinner.

**33 — flat.** No date heading, day separator, month band or sticky header
exists in the markup. `shots/historial--abajo.png` is the scrolled shot where
one would show up if it crept in.

**34 — nothing else operable.** The screen is a title area, rows and the
show-more control. The five operables Historial inherits from the shell are
frame, not screen, exactly as the design's ratified reading enumerates: the
four-tab strip, the AppBar's "Ajustes" link, the `ReachabilityBanner` (only when
unreachable — `shots/historial--sin-servidor.png`), the capture bar and the
bottom nav. All five are visible in the shots and all five are inherited by Hoy
and Mes today on identical terms. No search field, no filter row, no sort
control, no chip bar.

**35 — a reading surface.** No `<input>`, no `<textarea>`, no chip, no select
appears in any `gasto-detalle*.html`. Exactly one control that touches the
expense: "Editar gasto". The FormBar's ✕ is navigation, the same one
`EntradaLeer` carries. Nothing is drawn as a greyed-out field.

**36 — the journal read screen's frame.** `.formbar` in `css02.py` mirrors
`Screen.module.css:67-100` declaration for declaration (padding `2px var(--pad)
0`, a 44×44 violet close at `margin-left:-10px`, a 17 px/700 title). Capture bar
absent, bottom nav present — the `capture={null}` frame `Entrada.tsx:34` uses.

**37 — two labelled dates, never one value; description unclamped.**
"Fecha del gasto" is inside the ruled facts block; "Anotado el…" is outside it,
below a hairline, in footnote type. `shots/gasto-detalle.png`. The description
is shown whole at ~600 characters —
`shots/gasto-detalle--descripcion-larga.png` plus a scrolled companion — with no
`line-clamp` and no "seguir leyendo" anywhere in the CSS or the markup.

**38 — the edited mark is neutral.** `shots/gasto-detalle--editado.png`:
"Editado el 7 de agosto a las 09:20." is the same colour, the same size and the
same block as "Anotado el…". No red, no icon, no badge, no border. `grep` for
elements carrying a red class across all 17 mockups returns none. (The
`var(--danger…)` declarations that exist in the inlined base stylesheet are
never reached by any element on these screens.)

**39 — tappable versus not, apparent without touching.** `shots/finanzas-mes--frontera.png`
shows the boundary in one frame: category rows run to the bleed, carry a violet
chevron and rule edge to edge; payment rows keep today's inset rule and gain
nothing. Hover, focus-visible and active are captured separately.

**40 — two totals, never ambiguous.** `shots/finanzas-mes--categoria.png`:
month total `$1.284.500` at 40 px/300 in the hero, labelled by "agosto 2026";
category total `$298.500` at 22 px/700 in the band, labelled by "Comida". They
differ in position, label, weight *and* size — four axes where the constraint
asks for three.

**41 — clear the selection without scrolling.** "✕ Cerrar" sits in the band at
roughly 322 px from the top of an 844 px viewport, on screen in the default
shot with no scrolling.

**42 — both new empty states are designed.** `shots/historial--vacio.png` and
`shots/finanzas-mes--categoria-vacia.png`. Both use the app's `EmptyState`
vocabulary (violet mark, 21 px title, body). Neither is a blank area, a zero row,
an error or a bare frame. The empty-category state deliberately shows **no**
`$0` figure — 18.10 names "a zero row" as the thing to avoid (see Open
Question 3).

**43 — nothing reveals voice versus typed.** No badge, icon, tint, label or
field on any of the three surfaces. The placeholder payloads carry no `source`
key, matching the wire. The only string containing "voz" anywhere is
`aria-label="Grabar con la voz"` on the capture bar's mic — the shell's capture
control, present on Hoy and Este mes today, which says nothing about how any
listed expense was captured.

### The Run 01 constraints most at risk

- **2, 3 (one hue; red reserved).** No new colour token. No element on any new
  screen uses a red class. Nothing in `css02.py`'s delta references
  `var(--danger…)`, so `estilos.test.ts:62-74` cannot be provoked.
- **6 (no information by colour alone).** The breakdown rows still carry name,
  amount and percentage adjacent to every bar. Tappability is carried by the
  full-bleed rule *and* the chevron *and* the wash — never by tint alone.
- **7, 8, 10.** `AUDIT h=0 t=0 c=0` on all 13 substantive pages at **both** 390
  and 320 px: no horizontal overflow, no control under 44×44, no text below its
  AA ratio.
- **5 (AA contrast).** Included in the audit above, computed against each
  element's real composited background. The one new grey-on-white pairing is the
  in-flight show-more label, `--ink-soft` at 6.83:1.
- **12 (one typeface).** Lato only; the delta sets no `font-family`.
- **15.** Two new designed empty states, above.
- **16 (in-progress and error states).** Pending follows the one in-repo pattern
  (`shots/historial--cargando.png`, `shots/gasto-detalle--cargando.png`);
  unreachable is the inherited banner (`shots/historial--sin-servidor.png`).
- **21 (peso convention).** `$298.500`, `$1.284.500`, `$18.000` — dot thousands,
  no cents, no space.
- **22 (light only).** No `prefers-color-scheme` rule anywhere in the delta.
- **23, 24 (Spanish, accents intact).** Every string is Spanish. Accents and ñ
  render clean at every size used — verify in the shots: "Análisis",
  "miércoles", "ningún", "sábado", "Categoría", "Tarjeta de crédito", "débito".
  No new string contains any of `save|cancel|delete|loading|error|settings|
  today|month|search|submit` (`es.test.ts:62-71`).

**Nothing was silently ignored.** Where a constraint could not be met exactly as
written, it is an Open Question below, not a quiet bend.

---

## Screens

| file | what it shows | criteria |
| --- | --- | --- |
| `historial.html` | The fourth tab: flat registration-ordered list, the ordering statement, show-more present | 16.1 16.2 16.5 16.6 16.7 16.12 |
| `historial-completo.html` | The last page — no control, no affordance | 16.9 |
| `historial-ver-mas-en-curso.html` | "Ver más" in flight, in place | 16.7 |
| `historial-vacio.html` | Nothing ever recorded | 16.10 |
| `historial-cargando.html` | Pending | — |
| `historial-sin-servidor.html` | The inherited unreachable banner | — |
| `gasto-detalle.html` | Read-only detail, one edit action | 17.1 17.2 17.4 17.6 17.10 |
| `gasto-detalle-sin-descripcion.html` | Description omitted entirely | 17.3 |
| `gasto-detalle-descripcion-larga.html` | ~600 characters, unclamped | 17.2 |
| `gasto-detalle-editado.html` | Edited since recorded, neutrally | 17.5 |
| `gasto-detalle-no-existe.html` | Plain Spanish, no such expense | 17.11 |
| `gasto-detalle-cargando.html` | Pending | — |
| `finanzas-mes.html` | Tappable category rows against inert payment rows | 18.1 |
| `finanzas-mes-categoria.html` | Comida open: both totals, count, close, filtered list | 18.2 18.3 18.4 18.5 18.8 18.12 18.13 |
| `finanzas-mes-categoria-vacia.html` | An ordinary category with nothing left that month | 18.10 |
| `historial-tira-estrecha.html` | **Not a screen** — the 320 px remedy, for Open Question 2 | — |

**Criteria in my scope that these mockups do not depict, and why.** 16.3, 16.4,
16.8, 16.11, 17.7, 17.8, 17.9, 18.6, 18.7, 18.9 are all *behaviour over time* —
where a row lands after a save, what survives a round trip, what a repeated tap
eventually reaches. A static mockup cannot show any of them and pretending
otherwise would be the dishonest kind of picture. They are Phase 2 work against
the design's push/pop table. 18.11 (an empty month offers no selection) is the
Run 01 empty-month screen unchanged — no new drawing.

**Placeholder data is contract-shaped.** Historial's rows are
`GET /api/expenses?order=registered` items in id-descending order with dates
that deliberately do *not* descend. The filtered list is
`?month=2026-08&category_id=…` in `spent_on DESC` order, and its twelve amounts
sum to exactly `$298.500`, the figure `by_category` shows for Comida — so a
reviewer who adds them up gets the right answer. No payload carries `source`.

---

## States Covered

49 PNGs, all rendered at 390×844 (or 320×844 where noted) at 2× with headless
Chromium, all verified non-empty. Interactive states are forced with CDP
`CSS.forcePseudoState` on the **real element** — not with mirrored `.is-hover`
helper classes, which are a second source of truth that can drift from the rule
they claim to prove. Every forced shot is md5'd against its own default; a
byte-identical result is reported as `ESTADO-PERDIDO` and fails the run.

| matrix row | captured | where |
| --- | --- | --- |
| default | yes | every screen |
| **hover** | yes | `historial--fila-hover`, `historial--ver-mas-hover`, `historial--pestana-hover`, `gasto-detalle--editar-hover`, `gasto-detalle--cerrar-hover`, `finanzas-mes--categoria-hover`, `finanzas-mes--cerrar-hover` |
| **focus-visible** | yes | `historial--fila-foco`, `historial--ver-mas-foco`, `historial--pestana-foco`, `gasto-detalle--editar-foco`, `gasto-detalle--cerrar-foco`, `finanzas-mes--categoria-foco`, `finanzas-mes--cerrar-foco` |
| **active / pressed** | yes | `historial--fila-pulsada`, `historial--ver-mas-pulsado`, `historial--pestana-pulsada`, `gasto-detalle--editar-pulsado`, `finanzas-mes--categoria-pulsada`, `finanzas-mes--cerrar-pulsado` |
| **disabled** | yes | `historial--ver-mas-en-curso` (+ `…-hover`, asserted to *not* light up); `finanzas-mes--mes-siguiente-inerte` (next-month arrow, asserted inert under hover) |
| empty | yes | `historial--vacio`, `historial--vacio-320`, `finanzas-mes--categoria-vacia` |
| loading | yes | `historial--cargando`, `gasto-detalle--cargando`, `historial--ver-mas-en-curso` |
| error | yes | `historial--sin-servidor` (unreachable), `gasto-detalle--no-existe` (17.11) |
| scrolled | yes | `historial--abajo`, `historial--sin-control`, `finanzas-mes--frontera`, `finanzas-mes--categoria-abajo`, `gasto-detalle--descripcion-larga-abajo` |
| narrow viewport | yes | `historial--320`, `historial--vacio-320`, `gasto-detalle--320`, `gasto-detalle--larga-320`, `finanzas-mes--320`, `finanzas-mes--categoria-320` |
| dark mode | **not applicable** | constraint 22 — light mode only, no `prefers-color-scheme` rule exists |

**Not captured, and why.** Only one: a **multi-error** case. The contract cannot
produce one on any of these three screens — Historial and the filtered list have
no validation surface, and the detail's only failure is the single `not_found`
from `useExpense`. Drawing a stacked-error state would be a picture of something
the API cannot return. Every other state in the matrix was captured; none is
recorded as "not screenshotable".

`state.environment_verified.visual_capable` is **true** here: Chromium 150 is
present, renders these files, and produced every PNG listed.

---

## What the renders found that reading the CSS did not

Two defects, both invisible in a static render and in a code read, both fixed
before this note was written. Recording them because one of them is in shipped
code.

1. **The in-flight show-more lit up violet on hover.** `.btn--text:hover` sets a
   background that the disabled rule never resets, so a disabled text button
   still washes under the pointer. **The same omission is live in
   `frontend/src/components/ui/Button.module.css:123-126`** — `.text:disabled`
   sets `color` and `cursor` but not `background`. It has never bitten because
   no shipped screen disables a `kind="text"` button; the in-flight show-more
   would be the first. The mockup carries the fix
   (`.vermas .btn[disabled]:hover{background:none}`, declared after the rule it
   must beat, with a comment naming that rule). **Phase 2 should add
   `background: none` to `Button.module.css`'s `.text:disabled`** — a one-line
   change to a file outside this feature's stated change list, so flagging it
   rather than assuming it.
2. **The in-flight label rendered violet instead of grey.** The Run 01 mockup
   stylesheet has no disabled rule for `.btn--text` at all, though the shipped
   `Button.module.css` does — so the mockup would have depicted a state the real
   app renders differently. Mirrored into the delta.

Both were caught by forcing the state and looking at the image. Neither would
have appeared in any default screenshot, and I did not see either while reading
the CSS.

---

## Open Questions for the Human

**1. Is the show-more control too loud?** It uses the app's existing quiet-action
vocabulary (`Button kind="text"`: violet, no border, no fill — the same control
as "Grabar otra vez"), centred under the last rule. Constraint 32 requires "a
visible control", and the Feel note asks for "unremarkable, low contrast, easy
to ignore until wanted. Not a call to action." I chose visible over quiet where
the two pulled apart. If it reads as a call to action to you, the cheap move is
15 px/600 instead of 16 px/700; the expensive move is `--ink-soft`, which I'd
argue against because it stops looking tappable. See
`shots/historial--abajo.png`.

**2. Should the tab strip tighten for narrow phones?** At 390 px the four tabs
fit with 70 px to spare and need no change. At **330 px and below, "Este mes"
wraps to two lines** — a real regression from the fourth tab, measured, and
visible in `shots/historial--320.png`. Constraint 29 is specified at 390×844, so
this is out of its literal scope, and I did not unilaterally change the shared
shell metrics that Run 01 approved. The remedy is drawn so you can decide from a
picture: `historial-tira-estrecha.html` reduces the strip gap 10→6 px and the
tab padding 9→7 px, **uniformly across all four labels** — no font size changes,
so constraint 29's "no label smaller than its neighbours" is untouched, and
`Hoy` still measures exactly 44 px wide. Compare
`shots/historial--tira-estrecha-390.png` against `shots/historial.png` to see
what 390 px loses, and `shots/historial--tira-estrecha-320.png` against
`shots/historial--320.png` to see what 320 px gains. My recommendation: ship as
drawn unless you use a phone narrower than 331 px.

**3. The opened band shows no total when the category is empty — 18.3 versus
18.10.** 18.3 says a selected category shows "the category's name, that
category's total, and how many expenses it contains". 18.10 says the empty case
must not be "a blank area or a zero row". Those pull in opposite directions when
the total is zero, and I resolved it toward 18.10: the band keeps the name and
the close control, drops the figures entirely, and the designed empty state
carries the meaning. `shots/finanzas-mes--categoria-vacia.png`. If you'd rather
see `$0 · sin gastos` in the band, say so — it is a two-line change, but I read
it as exactly the zero row 18.10 forbids.

**4. Historial's end shows nothing rather than saying "that's everything".** A
line like "Ya viste todo lo que has anotado" would be warmer and would make the
last page positively legible rather than merely blank. I cut it because
constraint 32 reads "no control, **label**, spinner, or trailing affordance
implying more exist is present", and although such a label implies the opposite,
a QA pass reading that sentence literally would flag it. If you want it, it
needs a word from you so it isn't a defect later.

**5. "Cerrar" or "Cerrar Comida"?** The band's control reads `✕ Cerrar`,
adjacent to the category name on the same line. It is unambiguous in context and
uses the design's requested "opening/closing a category" vocabulary rather than
filter vocabulary. `✕ Cerrar Comida` is more explicit but repeats the name on
one line. Low stakes; happy either way.

**6. The edited footnote shows *when*, and that amplifies R3.** The design's R3
records that saving the form without changing anything still marks an expense
edited, and flags it as still open at Approve Plan. My mockup shows the edit
*timestamp* ("Editado el 7 de agosto a las 09:20."), not just the fact. I think
that helps — it lets you reconcile a surprising mark against "oh, that was when
I opened it yesterday" — but it does make R3 more visible than a bare "editado"
would. If you decide R3 should be tightened, this line is where it shows.

**7. One data dependency the design's data flow does not list.** When a category
has no expenses in the viewed month it is absent from `by_category`, so the
month summary cannot supply its name for the band. The name comes from
`useCategories()` (`api/queries.ts:78`), which already exists. Two residual
cases have no name available anywhere — an **unknown** `categoria` id, and an
**archived** category that has nothing in the viewed month (the default
`GET /api/categories` excludes archived). For those the copy falls back to
*"En agosto ya no queda nada en esa categoría."* rather than inventing a name.
Flagging for Architect/Reviewer as a small addition to Mes's stated data flow.

*(Noted, not a question: the coordinator's mid-flight correction on archived
categories landed after the mockup set was planned and changed nothing in it.
Mockup 9 was already an ordinary category — Ropa — whose expenses left the
month, never an archived one. `finanzas-mes-categoria.html` correctly depicts an
archived category's behaviour too, since an archived category lists its expenses
exactly like any other.)*
