# Autonom-OS — Phase 1 mockups (design note)

**Status: mockups only. No application code written. `frontend/` does not exist.**

- Entry point: `/home/david/Proyectos/Autonom-OS/mockups/index.html`
- Screenshot matrix: `/home/david/Proyectos/Autonom-OS/mockups/matriz.html`
- Renders: `/home/david/Proyectos/Autonom-OS/mockups/shots/` (57 PNGs)
- Generator (mockup tooling, not app code): `/home/david/Proyectos/Autonom-OS/mockups/_build/`

40 self-contained HTML files. Inline CSS, inline SVG, no network request, no build
step, no CDN. Each opens straight from the filesystem.

Visual verification was possible on this machine (Chromium 150). Every Design
Constraint below was checked against a real render, not against intent.

---

## Direction

PM's brief fixed the palette (mostly white, violet, one red), the device, the two
moods, and light-mode-only. What it left to craft was *which* violet, which
typeface, how the month reads, and — the part that actually shapes this app — what
waiting looks like. Those are the four choices below.

**Violet `#5A2FCE`, pulled toward ink rather than toward neon.** 7.69:1 on white,
so the same value works as body text, as white-on-violet, and as a fill; there is
no "accessible variant" of the brand colour to keep in sync. It reads as fountain
pen violet, not as a fintech gradient. `--ink #221B33` is a near-black carrying the
same hue family, so the page has one temperature without introducing a second hue.
Red `#C0182B` appears in exactly two places in the whole set: destructive
confirmation and validation errors.

**Lato (SIL OFL), one family, weights 300/400/600/700.** Humanist, warm, unhurried
in paragraphs, and its diacritics — á é í ó ú ü ñ ¿ ¡ — are properly drawn rather
than bolted on, which matters when every string on every screen carries them.
Light 300 at 46 px carries the day's total; 600/700 does the work that boxes and
shadows would otherwise do. Amounts are `tabular-nums` and right-aligned in a
column, so `$6.200` and `$1.284.500` line up down the page.

**Finanzas is ruled; Diario is not.** The two moods the brief asks for are encoded
in a structural device rather than in decoration. Finanzas rows sit on hairline
rules with 20 px gutters and a scannable two-line row — a ledger. Diario has no
rules, no cards, no borders at all: 24 px gutters, 17.5 px text on 1.72 line
height, entries separated only by space. Put the two screenshots side by side and
the difference in tempo is visible before a word is read.

**The month breakdown is a ranked list, not a chart.** Name, amount and percentage
on one line, a proportional bar underneath tinted by rank within the violet family.
It answers "where did it go" in reading order, and every segment carries its label
and its number adjacent — so nothing depends on telling `--t4` from `--t5`.

### The signature: waiting is drawn as a tally

This is the one deliberate risk, and it is the piece I most want a decision on.

The constraints leave exactly one honest shape for an inference wait. A determinate
bar is forbidden (28: nothing may imply a completion time nobody knows). A static
spinner is forbidden (25: progress must visibly change). What is left is *elapsed
time* — and a bare digit readout is unreadable at arm's length while walking.

So elapsed seconds are drawn as tally marks: one stroke per second, grouped in
fives with the fifth crossing the group, wrapping onto a second row past a minute.
Older strokes are faded, the newest is full violet, so the direction of travel is
visible in a still frame. It comes from the notebook the brief names as the
reference, it cannot imply an end because there is no track to fill, and at a
glance you can see "about a minute" without reading a number. The numeral is
printed beside it so it is unambiguously a clock, not a score.

Compare `shots/analisis-esperando--12s.png` with `--68s.png`, and
`voz-transcribiendo--3s.png` with `--14s.png`: same screen, two moments, visibly
different.

The counterpart is that **recording** — the one wait with a known bound — uses a
determinate meter filling toward 30 s. Bounded work gets a bar; unbounded work gets
a count. That distinction is the thesis.

---

## Constraints Conformance

Each numbered Design Constraint from `factory/pm/visual-direction.md`.

**Colour**

1. **Met.** Every screen is white. Violet appears as fills on controls, never as a
   page background. The largest violet area in the set is a 58 px mic button.
2. **Met.** One brand hue. The tint ramp `--t1…--t10` is the same hue at different
   lightness; there is no second accent anywhere.
3. **Met.** `--danger #C0182B` appears in: the delete/remove confirmation buttons,
   the "Eliminar gasto"/"Quitar de la lista" triggers, and validation error text
   and field borders. Nowhere else — `grep` the stylesheet and there are no other
   uses.
4. **Met.** The breakdown uses ten steps of one violet. No unrelated hues.
5. **Met, and verified by measurement, not by eye.** Every mockup carries an audit
   that walks every text-bearing element, resolves its actual painted background,
   computes the WCAG 2.1 ratio and compares it against 4.5 (or 3.0 for large text).
   `_build/audit.sh` runs it headless on all 40 files. **Result: zero failures.**
   It found one real violation on the way — secondary text at 4.23:1 on the
   *pressed* tint, invisible in every static render — and `--ink-soft` was darkened
   to `#5E5770` to fix it.
6. **Met.** Every breakdown row and every payment-method row prints name, amount
   and (for categories) percentage adjacent to the bar. Colour carries nothing.

**Layout and device**

7. **Met, verified.** The audit also reports `scrollWidth > innerWidth` per page.
   Zero horizontal overflow at 390, 360 and 320 px. No zoom needed: smallest text
   in the app is 13.5 px, and the only 11.5 px text is uppercase letterspaced
   section labels.
8. **Met.** The layout is fluid (`width: min(390px, 100vw)`). At 900 px it is the
   same column centred — see `finanzas-hoy--900.png`. No sidebar, no table, no
   desktop variant.
9. **Met.** Both capture actions sit in a bar immediately above the navigation, in
   the bottom ~135 px: "Anotar gasto" (52 px pill) and the voice button (58 px
   circle).
10. **Met, verified.** The audit measures every interactive element's rendered box
    and flags anything under 44×44. Zero flags. It caught three real ones on the
    way: the "Hoy" tab at 31 px wide, the amount input at 43 px tall, and the mic
    button outside the capture bar.
11. **Met.** The three-destination navigation is on every screen including the
    unreachable-server screen and the Gym placeholder. Modal confirmations sit over
    it, which is the one place it is temporarily covered.
12. **Met.** One family. `font-variant-numeric: tabular-nums lining-nums` plus
    right alignment on every amount, total and percentage.
13. **Met.** Journal body: 17.5 px / 1.72, ~38 characters per line at 390 px, 24 px
    gutters, paragraph breaks preserved. Finanzas rows are 17/13.5 px and scan.
14. **Met.** Lato is SIL OFL 1.1. All icons are hand-drawn inline SVG paths in this
    repo — no icon set, free or paid, is used.

**Required states**

15. **Met.** Designed empty states for: today with no expenses, a month with no
    expenses, an empty journal, a selected date with nothing written, no summary
    ever produced, and a period that closed with no data. None is blank, an error,
    or a zeroed chart. See the "Vacío" row of the matrix.
16. **Met.** In-progress *and* error states exist for transcription, insight
    generation, and saving. See the "Esperando" and "Error" rows.
17. **Met.** `voz-escuchando.html` is a full-screen takeover with a pulsing violet
    ring, a running clock, "Te estoy escuchando", and both "Listo" (stop) and
    "Cancelar". It cannot be mistaken for idle.
18. **Met.** `sin-servidor.html` — "No puedo alcanzar tu servidor", plain language,
    designed for a cold open. Plus `sin-servidor-banner.html` for the app-already-
    open case.
19. **Met.** Both destructive paths confirm: deleting an expense or journal entry,
    and removing a category that is in use (which also states the count).
20. **Met.** Gimnasio is in the navigation, marked `pronto`, and its screen says
    "Todavía no está disponible." No data-entry control, no empty list, no error,
    **and no capture bar** (KD-16).

**Content and mode**

21. **Met.** `$55.700`, `$1.284.500`, `$6.200`, `$0`. Dot thousands, no cents,
    everywhere.
22. **Met.** The stylesheet contains no `prefers-color-scheme` rule at all and
    declares `color-scheme: light`. There is no theme control in any screen.
23. **Met.** Every string is Spanish, including errors, empty states, placeholders
    and the "pronto" marker. Route names in the mockup filenames are Spanish too.
24. **Met.** Accents, ñ, ¿ and ¡ render correctly at every size and weight used —
    check `analisis-errores.png` (¿…? at 16 px), `diario.png` (mañanas, día,
    ¿Por qué at 17.5 px) and `gimnasio.png` ("Todavía" at 27/700). Long Spanish
    labels are the reason the chips wrap rather than sit in a fixed grid:
    "Tarjeta de crédito" is 18 characters and still fits at 320 px.

**Waiting and long-running work**

25. **Met.** The tally adds a stroke per second and the numeral increments; both
    are live in the mockup (open `voz-transcribiendo.html` and watch it). Frozen
    pairs are in the matrix so a still reviewer can see it changes. No spinner
    exists anywhere in the set.
26. **Met, and deliberately over-satisfied for transcription.** The transcription
    wait offers "Escribir a mano" (abandon to the manual form, 8.9) and "Cancelar"
    **from second zero**, not from second ten — it is the wait the user meets
    several times a day, and a control that appears late is a control he learns not
    to look for. The copy says outright: "Esto ocurre en tu propio computador, no
    en internet." The insight wait offers "Cancelar la pregunta" with "Puedes irte
    de esta pantalla; cancelar no borra nada de lo que tienes guardado."
27. **Met.** Four distinguishable surfaces, one file each: `analisis.html` (ready,
    with period and production time), `analisis-generando.html` (being produced,
    with a live tally and its start time), `analisis-sin-resumen.html` (none ever
    produced), `analisis-periodo-vacio.html` (period closed with no data), plus
    `analisis-resumen-fallo.html` (failed). None is an empty area.
28. **Met.** No copy promises speed. The transcription screen says "Con un mensaje
    corto suele tardar entre 7 y 15 segundos" — the measured floor, stated as a
    typical range rather than a promise. The question screen says "Suele tardar
    alrededor de un minuto". No progress bar, no percentage, no ETA countdown, no
    animation that implies imminent completion.

---

## The four-interaction budget (criterion 2.8)

From `/finanzas` (the default screen), a complete expense:

| # | Interaction | Screen |
|---|---|---|
| 1 | Tap **Anotar gasto** | `finanzas-hoy.html` → `gasto-nuevo.html` |
| — | *type the amount* (field is focused on open, keyboard already up) | not counted per 2.8 |
| 2 | Tap a category chip | inline, wrapping row |
| 3 | Tap a payment-method chip | inline, wrapping row |
| 4 | Tap **Guardar gasto** | — |

Exactly four, with zero slack, which is why the control pattern is not left open:
**every category and every payment method is a single-tap chip already on screen.**
No `<select>`, no modal, no bottom sheet — each of those costs two interactions and
puts the total at six.

Verified in the renders: ten categories and six payment methods, all ≥44 px tall,
wrap into 4 and 3 rows at 390 px (`gasto-nuevo.png`) and into 5 and 3 rows at
320 px (`gasto-nuevo--320.png`), with no horizontal scrolling at either width. The
form scrolls vertically; scrolling is not an interaction in 2.8's sense, and the
amount field plus the first category row are above the keyboard on open.

Outside the four, deliberately: **"+ Nueva"** opens an inline field inside the form
and does not disturb the draft (`gasto-nuevo-nueva-categoria.png`, criterion 3.2),
and the date defaults to today with a "Cambiar" control for the exceptional case.

If slack is ever needed, the one interaction available to reclaim is #1 — putting
the amount field directly on `/finanzas`. I have **not** done that: it would put a
form on the screen whose job is to be a calm ledger, and the budget is met without
it.

---

## Waiting states, one by one

| Wait | Measured | What is shown | Escape |
|---|---|---|---|
| Recording | bounded, 30 s | Pulsing violet ring, `0:07` clock, determinate meter toward the 30 s cap | **Listo** (stop) and **Cancelar** |
| Transcription | ~6.4 s floor, up to ~28 s end-to-end | Phase label ("Transcribiendo en tu computador") + tally + seconds; "no en internet"; honest 7–15 s range | **Escribir a mano** and **Cancelar**, both from t=0 |
| Question | 55–76 s typical, 120 s bound | Tally + seconds; the partial answer as it forms, labelled "Lleva escrito hasta ahora"; "Suele tardar alrededor de un minuto" | **Cancelar la pregunta**; leaving the screen is explicitly allowed |
| Monthly summary | background | "Escribiendo el resumen de julio", start time, tally, "Puedes cerrar la app: cuando vuelvas, estará listo" | nothing to cancel — it never blocks the user (11.17) |
| Saving | fast | Button becomes "Guardando…" and disabled; "Se guarda en tu computador" | — |

The tone target was *patient, not apologetic*. There is no "still working…", no
"sorry", no "this may take a while", and nothing anywhere celebrates or reassures.

---

## Screens

Grouped as in `index.html`. Every file is one 390×844 phone screen unless noted.

**Finanzas** — `finanzas-hoy` (1.1, 1.2, 1.4, 4.1, 2.5) · `finanzas-hoy-vacio`
(4.5) · `finanzas-mes` (4.2, 4.3, 4.4, 4.7) · `finanzas-mes-vacio` (4.5) ·
`finanzas-ajustes` (3.2, 3.3, 14.2, and the `/api/status` readout for 11.4) ·
`finanzas-ajustes-quitar` (3.4, using `details.affected_expenses`)

**Anotar un gasto** — `gasto-nuevo` (2.1, 2.8) · `gasto-nuevo-error` (2.2, 2.3) ·
`gasto-nuevo-nueva-categoria` (3.2) · `gasto-guardando` · `gasto-guardar-fallo`
(13.5) · `gasto-editar` (5.1) · `gasto-eliminar` (5.2)

**Voz** — `voz-escuchando` (8.1) · `voz-transcribiendo` (8.8) ·
`gasto-voz-revision` (9.1, 9.2, 8.2, 8.6 — amount filled, category *sugerido*,
payment method empty and marked, description from the transcript) ·
`gasto-voz-largo` (`description_truncated`) · `voz-fallo` (8.4) ·
`voz-sin-permiso` (8.5) · `diario-voz-revision` (10.1, 10.2, 10.3)

**Diario** — `diario` (7.1, 6.4) · `diario-vacio` (7.3) · `diario-fecha-vacia`
(7.2) · `diario-entrada` (6.4, 6.5, 5.3) · `diario-escribir` (6.1, 6.6) ·
`diario-escribir-error` (6.2)

**Análisis** — `analisis` (11.14, 11.15, 11.18) · `analisis-sin-resumen` ·
`analisis-generando` · `analisis-periodo-vacio` (11.16) · `analisis-resumen-fallo`
· `analisis-esperando` (11.5, 11.12, 11.13) · `analisis-respuesta` (11.8, 11.9,
11.11 — with the `journal_truncated` notice and the `period_assumed` label) ·
`analisis-ocupado` (409 `busy`) · `analisis-ia-no-disponible` (11.4) ·
`analisis-errores` (the five terminal `error_code` values)

**Sistema** — `gimnasio` (1.3) · `sin-servidor` (13.2, 13.8) ·
`sin-servidor-banner` (13.2, 13.3) · `estados-interactivos` (the interaction-state
catalogue)

Every state depicted maps to something the Interface Contract can actually
produce. Placeholder data uses the contract's shapes: `by_category` ordered
descending with integer percentages summing to exactly 100 (32+23+15+12+7+6+3+2),
`by_payment_method` with amounts and no percentage, expenses with `amount_cop`
integers rendered through one formatter, `journal_entries_used`/`considered` as two
counts, `details.affected_expenses` as a count. Nothing shows a field the contract
does not return — in particular **no list distinguishes a voice entry from a typed
one**, because `source` is never in a response body (9.5, 10.4).

---

## States Covered

The full matrix is browsable at `mockups/matriz.html`.

| Row | Captured | Where |
|---|---|---|
| default | yes, 40 screens | matrix row 1 |
| **hover** | yes, 10 controls | `estados-interactivos.png` |
| **focus-visible** | yes, 10 controls | same |
| **active / pressed** | yes, 10 controls | same |
| **disabled** | yes, where it can occur | same — and where it *cannot* occur, the cell says so rather than faking one |
| empty | yes, 6 screens | matrix row "Vacío" |
| loading | yes, 6 screens incl. two waits at two moments each | matrix row "Esperando" |
| error | yes, 11 screens/cards | matrix row "Error" |
| narrow viewport | yes, 360 px and 320 px | matrix row "Otros anchos" |
| wide viewport | yes, 900 px | same |
| scrolled | yes, 6 screens | matrix row "Desplazado" |
| dark mode | **not applicable** | constraint 22 is light-only; the stylesheet has no `prefers-color-scheme` rule and sets `color-scheme: light`, so there is no dark variant that could exist |

**How the interaction states were forced.** Each state is applied by a class that
shares its rule with the real pseudo-class — `.btn--primary:hover,
.btn--primary.is-hover { … }` — so the forced state and the touched state are
literally the same declaration and cannot drift. This is the specific fix for the
hover-accent violation that escaped the previous pilot: that one sat in the CSS,
visible to nobody, because no render ever asked for `:hover`.

**Nothing was left uncaptured.** There is no state in this set that I have called
"not screenshotable".

Two things in the renders are mockup scaffolding rather than app UI, and should not
be read as design: the phone frame (fixed 844 px height, rounded corners, drop
shadow) and the simulated status bar. The real app is a browser page.

---

## Contradictions and gaps I found

1. **The design's route list has no home for criteria 3.3, 3.4 and 14.2.**
   `design.md § Frontend structure` lists five routes; none of them can host
   renaming a category, removing one with an in-use warning, or exporting. The
   endpoints exist in the contract (`PATCH`/`DELETE /api/categories`,
   `GET /api/export`). I placed them at **`/finanzas/ajustes`**, reached from a
   labelled "Ajustes" control in the Finanzas app bar. That is a sixth route inside
   Finanzas, not a fourth destination — but it is an addition to Architect's list
   and should be confirmed rather than assumed.

2. **Análisis is rendered as a third in-module tab** (`Hoy · Este mes · Análisis`),
   not as a link buried in the page. The design says "a labelled control on the
   Finances screens", and the bottom navigation still has exactly three items — but
   a tab strip is the closest a control can get to looking like a destination
   without being one. If that reads wrong, it becomes a labelled row at the foot of
   Hoy and Mes instead. Diario reaches the same route from an "Análisis" control in
   its app bar (11.9).

3. **Two microphones are on screen at once in `/finanzas/analisis`** — the capture
   bar's mic (records an expense, required by 1.4) and the ask box's mic (records a
   question, required by 11.10). Both are mandated. I distinguished them by shape
   and position: the capture mic is a circle in the thumb bar, the ask mic is a
   rounded square attached to the question field. This is the weakest spot in the
   set and I would like a look at it.

4. **A failed monthly summary has no retry.** There is no endpoint to re-run one,
   and KD-12 gives it three automatic attempts. So `analisis-resumen-fallo` states
   the failure and points at the server status, and promises nothing. Confirm that
   silence is preferred over a button that cannot exist.

5. **Criterion 6.5 (a 5.000-character entry displayed in full)** is met in the
   entry view. In the *list*, a long entry clamps at seven lines with an explicit
   "Seguir leyendo" control. That is not silent truncation, but it is a reading of
   6.5 and worth stating.

6. **Multiple validation errors at once** (`gasto-nuevo-error`) are shown as
   **client-side** pre-flight — the request is never sent. The contract's `fields`
   array can carry several entries, so this is representable server-side too, but
   the mockup does not depend on that.

7. **`llm_unavailable` as a question's terminal `error_code`** is shown as the
   app-level state (`analisis-ia-no-disponible`, which also disables the ask box
   and keeps everything else working) rather than as a sixth card in the error
   catalogue, since `/api/status` will normally surface it first.

8. **Font hosting.** The mockups name Lato in a font stack and resolve it from this
   machine's installed copy; they do not embed it, because embedding a base64
   woff2 in 40 files would add ~14 MB for a review artefact. On a device without
   Lato the mockups fall back to `system-ui` and the proportions shift slightly.
   Phase 2 self-hosts the Lato woff2 in the repo, per KD-14 — no Google Fonts link,
   no external request.

---

## Open Questions for the Human

1. **The tally.** It is the one real risk in this set. It is honest, it is legible
   at arm's length, and it comes from the notebook idea — but it is unusual, and if
   it reads as decoration rather than as a clock it should become a plain elapsed
   counter with a slow violet pulse. Look at `analisis-esperando--68s.png` and
   `voz-transcribiendo--14s.png` and say.

2. **Análisis as a tab** (contradiction 2) — right call, or too close to a fourth
   destination?

3. **`/finanzas/ajustes`** (contradiction 1) — confirm the settings/export surface
   belongs inside Finanzas, since Architect's route list does not mention it.

4. **Two mics on the Análisis screen** (contradiction 3) — acceptable, or should
   the capture bar be suppressed on that route the way it is on Gimnasio?

5. **Waiting copy.** "Suele tardar alrededor de un minuto" and "entre 7 y 15
   segundos" are honest typical ranges, not promises. Constraint 28 forbids
   implying an instant response; it does not forbid setting a true expectation.
   If you would rather the app say nothing about duration at all, that is a
   two-line change.

Everything else I consider settled by the brief and the contract.
