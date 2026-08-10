> **PERSISTED BY THE ORCHESTRATOR.** The QA role's `Write` was blocked in this
> environment ("Subagents should return findings as text, not write report
> files"), so it returned its complete report as chat text and said so
> explicitly. Everything below the horizontal rule is QA's report **verbatim and
> unedited**. QA did not have write access to this file; do not read it as
> evidence that it did. The 51 screenshots it cites are on disk at
> `factory/qa/shots/` — written by QA itself, which had permission there.
>
> Persisted: 2026-08-10. QA agent id `af7cd09e959d58743`. Run 02 (feature).
> This is the **third** blocked role `Write` in this project (artifact-analyst
> twice, QA once) — a defect in the factory's tool grants, not a quirk.

---

**Headline:** 37/37 criteria Pass, constraints 29–43 all Pass, no Run 01 regression, 6 non-blocking defects (all frontend). Database left exactly as found: **16 expenses / $267.970**, md5 unchanged, user's server on :8001 untouched.

---

# QA report — Autonom-OS Run 02 (brownfield feature: Historial, expense detail, month by category)

**Verdict: PASS with defects.** 37 of 37 acceptance criteria pass. Design Constraints 29–43 all pass; Run 01's constraints 1–28, spot-checked on the surfaces this run touched, show no regression. Six defects are recorded below; **none of them breaks a criterion as written**, and none is blocking. The most important is **D1**, which confirms and extends the Reviewer's deferred F1: one Back tap after any deletion lands on a full, apparently-live rendering of the deleted expense with a working edit action, and saving from there tells the user the server is unreachable when it is not.

The run's single biggest named risk, **R1 / criterion 17.8 (scroll restoration on all three lists)**, **holds** — verified by driving a real browser, not by reading tests. The Reviewer's F2 (a tab switch destroying the outgoing list's offset) **does not reproduce** in four attempts including wheel-driven scrolling and a 200 ms tab switch; my observation overrides the concern.

## How it was exercised

- **Everything below was run**, in Chromium 150 at a 390×844 mobile viewport driven over CDP, against the real production build (`frontend/dist`, the artefact the `frontend:build` gate produced) served by the real FastAPI app.
- **The user's database was never touched.** I ran a second API instance on **:8011** (8000 is another project's container; 8001 is the user's own server, which I left running untouched, pid 4663) against a byte-faithful `sqlite3` backup of `data/autonomos.db` — taken via the read-only backup API so the WAL was captured, which a plain `cp` misses (a plain copy reported 13 expenses / $201.310 instead of 16 / $267.970). A third instance on :8012 with an empty database was used for the two "nothing has ever been recorded" states.
- **Database state on exit:** the user's `data/autonomos.db` is at **16 expenses / $267.970**, md5 `f40f1c0965351565d9dccac1e6bd81b5`, identical to what I found. Every expense I created (69 in the copy, of which I deleted 3 and edited 2) lived and died in `data/qa-run02.db`, which is deleted. `data/qa-vacio.db` is deleted. No browser profile, log or scratch file remains inside the repo; `git status` shows only `factory/` changes.
- **I did not run `npm run shots`.** The frontend implementer reported that the pre-existing `gasto-guardando` recipe intermittently writes a real expense into whatever database it is pointed at. I took my own 51 captures from the running app instead.
- I did not re-run the suites; `state.verification` is fact (backend 280, frontend 70, `test_integrity` **pass**, 269 tests / 691 assertions vs a 221/565 baseline — no test was removed or weakened, so the evidence base under this report is sound).
- **Rework history:** `state.loops` is `{review_impl: 0, qa_impl: 0}`. **Every criterion below passed on the first QA attempt; nothing in this run has been reworked.** One process event is worth recording even though it is not a rework cycle: the frontend agent died after the mockup gate (`state.history`, 20:51:46) and Phase 2 was implemented by a cold-spawned replacement without the original transcript. That work is the source of every frontend criterion here and it passed first time, including the scroll-restoration trap the implementer found and fixed itself before submitting.
- All screenshots cited are at `/home/david/Proyectos/Autonom-OS/factory/qa/shots/`.

---

## Acceptance Criteria

### Requirement 16 — Historial

| # | Verdict | Evidence |
| --- | --- | --- |
| **16.1** | **Pass** | Opened `/finanzas`, `/finanzas/mes` and `/finanzas/analisis` in turn; from each, a single click on the "Historial" tab landed on `/finanzas/historial`. The strip renders four tabs — Hoy, Este mes, Historial, Análisis — all `<a>` elements, each 46 px tall. `shots/02-historial.png`. Cycles: 1. |
| **16.2** | **Pass** | Historial issues exactly `GET /api/expenses?order=registered&limit=30` and renders ids `87,86,85,…` — strictly descending by registration. Against the 69-row database I confirmed in SQL that `ORDER BY id DESC` and `ORDER BY created_at DESC` produce the identical sequence, so "by when each was recorded" and the shipped ordering key agree on every row. Dates on screen visibly do **not** descend (8 ago, 7 ago, 7 ago, 1 ago, 2 ago…), which is the point. `shots/02-historial.png`. |
| **16.3** | **Pass** | Recorded a new expense through the real capture bar (Anotar gasto → $99.999 → Hogar → Daviplata → Cambiar → 15 July 2026 → Guardar). It appears as the **first** row of Historial, above rows dated 8, 7 and 6 August. `shots/15-historial-retro-arriba.png`. |
| **16.4** | **Pass** | Expense id 60 sat at index 27 of page 1, between 61 and 59. I opened it, edited **both** its amount ($1.028 → $77.777) and its date (5 Aug → 1 May), saved, and returned to Historial: id 60 is still at index 27, still between 61 and 59, and the whole 30-id page-1 sequence is identical to before the edit. |
| **16.5** | **Pass** | Every row renders category, `«fecha» · «método de pago»` and amount: e.g. "Ocio / 8 de agosto · Transferencia / $40.000". `shots/02-historial.png`. |
| **16.6** | **Pass** | "En el orden en que los anotaste, no por su fecha." renders above the first row, in Spanish. `shots/02-historial.png`. |
| **16.7** | **Pass** | With 69 expenses, "Ver gastos más antiguos" is present. Clicking it appended 26 rows: the 30 ids already on screen were unchanged and still in the same order (prefix comparison), and `main.scrollTop` stayed at **1632 → 1632**. Repeated at a deeper offset after paging: **2400 → 2400**, 60 rows retained. `shots/11-historial-ver-mas.png`. |
| **16.8** | **Pass** | Clicked the control repeatedly under a bounded loop until it disappeared. The union of pages contains **no duplicate id**, is strictly descending, and the final row is **id 1 — the first expense ever recorded**. The cursor terminated on its own; no expense was unreachable. `shots/12-historial-final.png`. |
| **16.9** | **Pass** | Two independent states checked. (a) 16 expenses, page size 30: scrolled to the bottom; the only operable elements inside `<main>` are the 16 rows — no button, label, spinner or trailing affordance (`shots/03-historial-fondo.png`). (b) After paging to the end of 56 rows the control is gone and the list ends silently at the last hairline, with no closing line — the ruled-on behaviour, not an omission. |
| **16.10** | **Pass** | Against an empty database on :8012, Historial renders a designed state: "Todavía no has anotado ningún gasto. / Cuando anotes el primero, aquí van quedando todos, del último al primero." Zero operable elements in `<main>`; not a blank screen, not an error, not an empty frame. `shots/37-historial-vacio.png`. |
| **16.11** | **Pass** | Deleted expense 84 through the edit form's confirmation. Historial no longer lists `/finanzas/gasto/84`; the page refilled to 30 rows from the server; the list text contains no "eliminado"/"borrado" placeholder and no gap. `shots/27-tras-eliminar.png`. |
| **16.12** | **Pass** | Every row is an `<a href="/finanzas/gasto/{id}">`; clicking one navigates to that expense's detail. `shots/04-gasto-detalle.png`. |
| **16.13** | **Pass** | Network log for a cold load of `/finanzas/historial` contains exactly one expense request: `GET /api/expenses?order=registered&limit=30`. No unbounded fetch, no `offset`, `total_count` never rendered as a number. |

### Requirement 17 — the expense detail

| # | Verdict | Evidence |
| --- | --- | --- |
| **17.1** | **Pass** | Tapped a row on all three surfaces: **Hoy** (`/finanzas` → `/finanzas/gasto/85`), **Historial** (→ `/finanzas/gasto/13`), **filtered month list** (→ `/finanzas/gasto/74`). All three land on the read surface — a `<main>` with **0** inputs/selects/textareas and exactly one button ("Editar gasto"). The edit form is never reached by tapping a row. This is B1's changed surface and it holds on Hoy, the one that used to work the other way. `shots/04-gasto-detalle.png`, `shots/31-hoy.png`. |
| **17.2** | **Pass** | A 653-character description renders whole: the paragraph's `scrollHeight` equals its `clientHeight` (383 px), computed `-webkit-line-clamp` is `none`, `max-height` `none`, `overflow` `visible`, and "seguir leyendo" appears nowhere. `shots/17-detalle-descripcion-larga.png`, `shots/18-detalle-descripcion-larga-abajo.png`. |
| **17.3** | **Pass** | Expense 72 has no description; the detail shows amount, category, method, date and nothing between the category and the facts block — no empty field, no dash, no placeholder word. `shots/16-detalle-sin-descripcion.png`. |
| **17.4** | **Pass** | Shows "Fecha del gasto — sábado 1 de agosto" inside the ruled facts block and "Anotado el 7 de agosto a las 13:28." below the rule in footnote type. Each labelled, spatially and typographically separated; they cannot read as one value or one range. Also checked with an expense recorded the same day it was dated (id 74): both still shown and labelled. `shots/04-gasto-detalle.png`, `shots/19-detalle-mismo-dia.png`. |
| **17.5** | **Pass** | Expense 4 (whose `updated_at` differed from `created_at` before this run) shows "Editado el 7 de agosto a las 13:17." Verified fresh too: after I edited id 60 the line appeared with the new timestamp. `shots/22-detalle-editado.png`, `shots/25-detalle-editado-ahora.png`. |
| **17.6** | **Pass** | Exactly one action ("Editar gasto"). It opens `/finanzas/gasto/60/editar` pre-filled: monto `1.028`, description "QA carga 28", category Salud and method Transferencia pre-selected, date "miércoles 5 de agosto". `shots/23-form-editar-prefill.png`. |
| **17.7** | **Pass** | Both exits. Saving: `/finanzas/gasto/60/editar` → `/finanzas/gasto/60` showing the newly stored $77.777 / 1 May. Closing without saving (✕ on the form): `/finanzas/gasto/61/editar` → `/finanzas/gasto/61` showing the unchanged $1.029. |
| **17.8** | **Pass** | The run's biggest risk, checked on all three lists by driving the real browser and reading `main.scrollTop` — **Historial 420 → 420, Hoy 394 → 394, filtered month list 400 → 400**, in each case after scrolling, opening a row and going Back. Tab, month and category all survive (`/finanzas/mes?categoria=2` returns as itself with the band open). Also holds at depth **after paging**: 60 rows, 2400 → 2400, appended pages still present and the show-more control still correct. The implementer's own `tools/verificar-scroll.mjs` agrees: `OK Historial (420→420) · OK Hoy (394→394) · OK mes + categoría (389→389)`. `shots/05-historial-vuelta.png`, `shots/32-hoy-vuelta.png`, `shots/33-mes-categoria-vuelta.png`, `shots/40-historial-paginado-vuelta.png`. |
| **17.9** | **Pass** | Deleted an expense from inside the edit form (Eliminar gasto → Eliminar). The user is left on **`/finanzas/historial`** — the list — not on a detail of the dead record. Repeated from a filtered category list: left on `/finanzas/mes?categoria=11`. *See defect D1: a subsequent Back tap can reach the dead detail.* `shots/27-tras-eliminar.png`. |
| **17.10** | **Pass** | Expense id 1 is the database's only `source='voice'` row. Its detail is structurally identical to a typed one, and a regex sweep of the rendered `<main>` HTML for `source|voz|micro|dictad` returns nothing. The wire backs it: `GET /api/expenses/1` returns keys `id, amount_cop, category_id, category_name, payment_method_id, payment_method_name, spent_on, description, created_at, updated_at` — `source` is not on the response at all. `shots/20-detalle-voz.png`. |
| **17.11** | **Pass** | `/finanzas/gasto/99999` renders, after a ~1 s `Cargando…` (a declared divergence, and a spinner that *ends*), "Este gasto ya no existe. / Puede que lo hayas borrado desde otra pantalla. En la lista está todo lo que sí tienes anotado." — plain Spanish, no blank screen, no endless spinner, no raw error. `shots/21-detalle-no-existe.png`. *See defect D1: reached via Back after a delete, the same message renders **above a full copy of the deleted expense**.* |

### Requirement 18 — the month, one category at a time

| # | Verdict | Evidence |
| --- | --- | --- |
| **18.1** | **Pass** | Every category row in "EN QUÉ SE FUE" is a `<button>`; one tap on "Transporte" opens it (`/finanzas/mes?categoria=2`). `shots/07-mes.png`, `shots/38-mes-frontera.png`. |
| **18.2** | **Pass** | Cross-checked the rendered list against SQL truth for August/Transporte: **12 rows, identical ids in identical order** (77, 74, 15, 33, 10, 2, 1, 7, 12, 11, 68, 13). No expense of another category, none from another month. Request: `GET /api/expenses?month=2026-08&category_id=2`. `shots/41-mes-categoria-filas.png`. |
| **18.3** | **Pass** | The band shows the name ("Transporte"), the category total ($93.393) and the count ("12 gastos"); singular is handled ("1 gasto" for Medicina). `shots/08-mes-categoria.png`. |
| **18.4** | **Pass** | The month total stays on screen above the band and is unmistakably the other figure: $336.407 at 40 px / weight 300 at y=175, versus the category's $93.393 at 22 px / weight 700 at y=321. Selecting a category never swaps the hero number. |
| **18.5** | **Pass** | "✕ Cerrar" in the band, one tap, returns to `/finanzas/mes` with the full breakdown restored. |
| **18.6** | **Pass** | From Transporte open → Cerrar → Ocio: the URL becomes `?categoria=6` (one parameter, replaced not combined) and the list contains only Ocio's three expenses; "Transporte" is absent from the screen. *Observation, not a defect:* because the breakdown collapses while a category is open, switching categories costs two taps. That is exactly how the human-approved mockup draws it. |
| **18.7** | **Pass** | With Transporte open in August, tapping "previous month" produced `/finanzas/mes?mes=2026-07` with `?categoria` dropped and July's full breakdown shown. I sampled the DOM every 60 ms across the transition (14 samples): `Cargando…` → julio 2026 with julio's own figures. At no sample did August's rows sit under a July heading. `shots/10-mes-anterior.png`. |
| **18.8** | **Pass** | Tapping a row in the filtered list opens `/finanzas/gasto/74`, the read-only detail. |
| **18.9** | **Pass** | Round trip returns to `/finanzas/mes?categoria=2` with the band still open on Transporte, same month, same scroll offset. Repeated for a **non-current** month: `/finanzas/mes?mes=2026-07&categoria=7` → detail → Back → the same URL, still "julio 2026 · Hogar · $103.038 · 4 gastos". This is B2 and it holds. `shots/34-b2-julio-categoria.png`. |
| **18.10** | **Pass** | Opened Medicina (August, exactly one expense), tapped it, deleted it. The list becomes "En agosto ya no queda nada en Medicina. / Puede que lo hayas borrado o que lo hayas pasado a otra categoría. El resto del mes sigue completo." — designed state, no zero row, no blank area; month total updated to $336.407 / 42 gastos. `shots/35-categoria-vacia.png`. |
| **18.11** | **Pass** | `/finanzas/mes?mes=2026-04` renders Run 01's empty state ("En abril no hay gastos anotados…"). The only buttons in `<main>` are the two month arrows — no category rows, so no selection is offered. `shots/36-mes-vacio.png`. |
| **18.12** | **Pass** | Rows read "7 de agosto / Nequi · Didi casa mateo / $10.000" — date, payment method, description, amount. A row whose expense has no description renders "15 de julio / Daviplata / $99.999", with no dangling separator. `shots/43-julio-hogar-sin-descripcion.png`. |
| **18.13** | **Pass** | The rendered order matches `ORDER BY spent_on DESC` exactly against SQL truth (10, 10, 7, 6, 6, 6, 6, 4, 2, 2, 1, 1 August) — deliberately different from Historial's registration order, which was on screen in the same session. |

### Behaviour that changes

| # | Verdict | Evidence |
| --- | --- | --- |
| **B1** | **Pass** | Rows in Hoy, Historial and the filtered month list all resolve to `/finanzas/gasto/{id}` and render the read surface (0 form inputs). The edit form is only reachable from the detail's single action, at `/finanzas/gasto/{id}/editar`. |
| **B2** | **Pass** | Month and selected category are search params and survive the detail round trip, for the current month and for July. See 18.9. |

**Tally: 37 / 37 Pass. 0 Fail. 0 untested.** Plus B1 and B2, both Pass.

---

## Visual Constraints

Checked against the running UI at **390×844**, from real captures and computed style read off the live DOM.

| # | Verdict | Evidence |
| --- | --- | --- |
| **29** | **Pass** | Four tabs on one line: Hoy 47.3×46, Este mes 81.1×46, Historial 78.5×46, Análisis 71.8×46, **all at 16 px**, all with the same top edge — no truncation, ellipsis, wrap or per-label size change; every target ≥44 px tall. `document.scrollWidth` = `innerWidth` = 390, so no horizontal scroll. `shots/02-historial.png`. |
| **30** | **Pass** | Not merely similar — identical. The Historial row and the Hoy row are the same component emitting the same classes (`_row_15t68_78` / `_what_` / `_cat_` / `_meta_` / `_amt_`); only the meta line's content differs (Historial "10 de agosto · Tarjeta de crédito", Hoy "17:08 · Tarjeta de crédito · Hoy QA 11"). `shots/02-historial.png` vs `shots/31-hoy.png`. |
| **31** | **Pass** | "En el orden en que los anotaste, no por su fecha." sits above the first row, and it is earned: the visible dates run 8, 7, 7, 1, 2, 2, 6 August. `shots/02-historial.png`. |
| **32** | **Pass** | Both states captured and trivially distinguishable: control present (`shots/11-historial-ver-mas.png` — "Ver gastos más antiguos", centred text button, no border, no fill) and absent (`shots/03-historial-fondo.png`, `shots/12-historial-final.png`). No spinner or trailing affordance in the absent state. |
| **33** | **Pass** | Flat. Scrolled through 60 rows spanning July and August, including the boundary: no date heading, day separator, month band or sticky header anywhere. `shots/11-historial-ver-mas.png` shows 17 jul → 1 ago with nothing between them but a hairline. |
| **34** | **Pass** | Enumerated every operable element inside `<main>` on Historial: 16 row links, plus — when more remain — the show-more button. No textbox, combobox, radio, chip bar, search field or sort control. The capture bar and bottom nav are the app-wide shell, outside `<main>`, identical on Hoy. |
| **35** | **Pass** | The detail's `<main>` contains **0** `input`/`textarea`/`select`, 0 `[contenteditable]`, 0 disabled or `aria-disabled` elements, 0 ARIA roles, and exactly one control: "Editar gasto" (350×54). No capture bar. It does not look like a form with the inputs switched off. `shots/04-gasto-detalle.png`. |
| **36** | **Pass** | Same frame as the journal read screen: ✕ + title bar, no capture bar, outlined pill actions. Compare `shots/04-gasto-detalle.png` with `shots/42-diario-entrada.png` (a real journal entry). The difference is content and the number of actions (A31: expenses offer only "Editar"), not the kind of screen. |
| **37** | **Pass** | "Fecha del gasto — sábado 1 de agosto" is a labelled row inside the ruled facts block; "Anotado el 7 de agosto a las 13:28." sits outside it, below the rule, at 13.5 px. Separated by a rule and a colour change; cannot read as a range. Description unclamped (see 17.2). |
| **38** | **Pass** | Measured live: "Editado el 10 de agosto a las 17:09." is `rgb(94, 87, 112)`, 13.5 px, weight 400 — **identical** styling to "Anotado el…". No icon, badge or border. A sweep of every element on the detail screen for a red-family colour (r>150, g<90, b<90 in colour, background or border) returns **false**. `shots/25-detalle-editado-ahora.png`. |
| **39** | **Pass** | Category rows are `<button>` 60 px tall, full-bleed, ending in a violet chevron; the "CÓMO SE PAGÓ" rows are inert `<li>` with no ancestor `a`/`button`, no chevron, and the existing inset rule. The boundary between the two groups is in one shot: `shots/38-mes-frontera.png`. Tappability is carried by shape and chevron, not colour alone (constraint 6 holds: name, amount and percentage adjacent to every bar). |
| **40** | **Pass** | Month total $336.407 at 40 px / weight 300, y=175, under "agosto 2026"; category total $93.393 at 22 px / weight 700, y=321, under "Transporte". Four distinguishing axes where the constraint asks for three. `shots/08-mes-categoria.png`. |
| **41** | **Pass** | "✕ Cerrar" measured at y=275 with the list at `scrollTop = 0`, 44 px tall, fully inside the 844 px viewport. Visible without scrolling. |
| **42** | **Pass** | Both new empty states are designed states, captured live: Historial with nothing ever recorded (`shots/37-historial-vacio.png`) and a category emptied by deleting its last expense (`shots/35-categoria-vacia.png`). Neither is a blank area, zero row, error or bare frame. |
| **43** | **Pass** | Nothing on any of the three surfaces distinguishes voice from typed. Row markup carries only date/category, method, description and amount; the detail's HTML contains no `source`/`voz`/`micro` token; and the API never serialises `source` (verified on the wire), so no component could render it even by accident. |

### Run 01 constraints 1–28 — regression spot-check on the surfaces this run touched

No regression found.

- **1, 12, 22** — white-dominant, one typeface, light only. With `prefers-color-scheme: dark` emulated, `body` background is still `rgb(255,255,255)` on Historial. `shots/39-historial-dark-emulado.png`.
- **2, 3** — no new hue; no red anywhere on the new detail screen (measured, see 38). Red remains only on the journal's destructive action and the expense form's "Eliminar gasto", where it belongs.
- **6** — every bar still carries its name, amount and percentage adjacently.
- **7, 8, 10** — 390 px document width equals viewport width on Historial, the detail and the opened month; no horizontal scroll; targets ≥44 px (tabs 46, close control 44, edit action 54).
- **15** — every screen I could empty had a designed state (Historial empty, category empty, empty month, Hoy empty).
- **21, 23, 24** — `$267.970`, `$99.999`, `$1.011`; all copy Spanish; "Análisis", "Educación", "descripción", "categoría" render with accents intact at every size captured.
- **1.1 (Run 01 criterion)** — the bottom nav still has exactly three destinations, Finanzas / Diario / Gimnasio. Historial is a tab, not a fourth destination.
- Run 01 surfaces still work: Hoy's total is arithmetically right after my creations and deletions ($39.185 across 12 rows), the capture flow saves through the real form, Diario's entry read screen renders, Análisis renders and starts a summary.

---

## Edge Cases Exercised

1. **Paging then leaving and returning.** Paged Historial to 60 rows, scrolled to 2400 px, opened a row on the second page, went Back. All 60 rows still there, offset exact, show-more control still correctly present. A naive implementation loses the appended pages here and silently makes the restored offset meaningless.
2. **Reviewer F2 (tab switch destroying the outgoing offset).** Four attempts: programmatic scroll + tab switch + Back; three wheel-driven runs (`Input.dispatchMouseEvent` mouseWheel ×6) with tab switches at 200 ms and 900 ms. Offset survived every time (420→420, 540→540 ×3). **F2 does not reproduce.** Forward navigation back to a tab correctly starts at the top — the implementer's declared and reasonable behaviour change.
3. **Reviewer F1 (Back after deleting).** Reproduces, and is worse than the static reading suggested — see **D1**.
4. **A partial API failure** (the expense-list endpoint failing while `/api/health` still answers) — see **D2** and **D3**.
5. **A total API outage** (all `/api/*` blocked): both Historial and the opened month correctly show the app's designed "No puedo alcanzar tu servidor." screen with a Reintentar action. `shots/47-historial-api-caida.png`, `shots/48-mes-categoria-api-caida.png`.
6. **Hand-edited URLs:** `?categoria=0` (Reviewer F4 — reproduces, D2), `?categoria=999` (unknown id — renders the empty-category state with generic copy; acceptable, and consistent with the backend's ruling that an unknown id is an empty list, not an error), `?mes=no-es-un-mes` (blank screen — D4), `/finanzas/gasto/abc` (wrong error message — D5).
7. **Same-day expense on the detail** (recorded and dated 10 August): both dates still shown and labelled, no collapsing.
8. **Singular/plural copy:** "1 gasto" vs "12 gastos" in the category band.
9. **Archived-category reading:** the backend's chosen reading (archived categories keep listing their expenses) is consistent with what the month breakdown offers, so no category on screen can be opened and found falsely empty.
10. **Editing amount and date together** — the case 16.4 is most likely to fail — did not move the row.
11. **Deleting the last expense of a category while its list is open** (18.10) and **deleting from Historial while scrolled** (D6).

---

## Defects Found

None fails a criterion as written. Ordered by severity.

### D1 — Back after deleting shows the deleted expense in full, with a working edit action that then lies about why saving failed
- **Severity:** medium. **Lane: frontend.**
- **Steps:** Historial → tap any row → "Editar gasto" → "Eliminar gasto" → "Eliminar". You land on `/finanzas/historial` (correct). Press browser Back once.
- **Expected:** the list, or at worst a screen that only says the expense is gone.
- **Actual:** `/finanzas/gasto/83` renders "Este gasto ya no existe." **and, below it, the complete record — $2.008, Transporte, "Hoy QA 8", Método de pago Transferencia, Fecha del gasto lunes 10 de agosto, Anotado el…, and a live "Editar gasto" button.** Tapping that button opens `/finanzas/gasto/83/editar` fully pre-filled with the deleted expense. Changing the amount and pressing "Guardar cambios" shows **"No pude guardar: no alcanzo tu servidor. / Nada se perdió. Lo que escribiste sigue aquí tal como está; vuelve a intentarlo cuando el computador esté despierto."** The server is up and answers `PATCH /api/expenses/83` with `404 {"error":{"code":"not_found"}}` — verified by curl at the same moment. The user is told to wait for a computer that is awake, about a record that no longer exists.
- **Screenshots:** `shots/28-f1-atras-tras-eliminar.png`, `shots/29-editar-gasto-borrado.png`, `shots/30-guardar-gasto-borrado.png`.
- **Criterion:** none violated as written — 17.9 is met (the system leaves the user on the list) and 17.11 is met (it does say so plainly). This is 17.9's and 17.11's **intent** breaking down one Back tap later. It is the Reviewer's deferred **F1**, confirmed by execution and extended: F1 said the Back target "renders 17.11's designed state rather than a blank or an error", which is only half of what renders.
- **Two separable causes, in case they are fixed separately:** (a) the navigation stack, which F1 already describes; (b) the detail screen rendering cached data *underneath* its own not-found message instead of replacing it, and offering an edit affordance from that state. The wrong save message (unreachable-server copy for a 404) is Run 01 copy on a Run 01 code path, newly reachable because of (a) and (b).

### D2 — A failed category-list request is reported to the user as "there is nothing left in that category"
- **Severity:** low-medium. **Lane: frontend.**
- **Steps:** open any month, open a category, and make that one request fail — I blocked `*/api/expenses*` at the network layer while `/api/health` kept answering (equivalent to a transient 500, a locked database, or the 400 the server returns for a malformed `category_id`).
- **Expected:** an error or a retry, or at minimum not a factual claim about the data.
- **Actual:** the band shows **"En agosto ya no queda nada en Transporte. / Puede que lo hayas borrado o que lo hayas pasado a otra categoría."** — while the month breakdown directly above still says Transporte, $93.393. The screen contradicts itself and the reassuring half is the false one.
- **Reproducible without any tooling:** browse to `/finanzas/mes?categoria=0`. The server rejects `category_id=0` with a 400 and the same false empty state renders (`shots/49-categoria-cero.png`). This is Reviewer **F4**, filed as "unreachable through any affordance" with requirement "none" — the URL is only the cheapest trigger; the same branch catches **every** failure of that request.
- **Screenshot:** `shots/46-mes-categoria-lista-falla.png`.
- **Criterion:** none violated as written (18.10 says what to do when the list *is* empty, not what to do when the request fails).

### D3 — Historial renders a blank screen when its list request fails while the server appears reachable
- **Severity:** low. **Lane: frontend.**
- **Steps:** as D2, on `/finanzas/historial`.
- **Expected:** something — the unreachable banner, an error, a retry.
- **Actual:** `<main>` is completely empty: no rows, no ordering line, no message, no spinner, no control. `shots/46b-historial-lista-falla.png` (compare the mockup `mockups/shots/historial--sin-servidor.png`, which draws the banner over cached rows).
- **Note:** the *total* outage case is handled correctly (Edge Case 5), so this only bites on a partial failure. It is not a 16.10 violation — the empty-state copy correctly does **not** appear — but a blank screen is the one thing 16.10 and constraint 42 exist to prevent, and a user cannot tell the two situations apart.

### D4 — A malformed `?mes=` renders a blank month screen
- **Severity:** cosmetic. **Lane: frontend.**
- **Steps:** `/finanzas/mes?mes=no-es-un-mes`. **Actual:** `<main>` is empty. Only reachable by hand-editing the URL; no affordance produces it.

### D5 — A malformed expense id says the server is unreachable
- **Severity:** cosmetic. **Lane: frontend.**
- **Steps:** `/finanzas/gasto/abc`. **Actual:** "No alcanzo tu servidor. / Lo que ves puede estar desactualizado…" while the server is up and answering. The implementer declared this branch (any non-`not_found` failure shows the unreachable banner) and the reasoning is sound for a genuine outage; it is wrong for a malformed id. URL-only.

### D6 — Deleting from a list returns to the top of that list
- **Severity:** cosmetic, arguably correct. **Lane: frontend.**
- **Steps:** scroll Historial to 250 px, open a row, delete it. **Actual:** you land on Historial at `scrollTop = 0`, not 250. 17.8 governs *leaving the detail without editing* and is unaffected; recorded only because the rest of the run is so consistent about restoring position that this reads as an inconsistency rather than a decision.

### Not defects — checked and cleared
- **Reviewer F2** does not reproduce (Edge Case 2). Reviewer explicitly asked QA to probe it; the probe is negative four times, including the fast-switch timing the finding depends on. No fix is warranted on the evidence.
- The **200-row cap** on the filtered category list, a **no-op save marking an expense edited**, **Diario's 50-entry cap**, **ship-as-drawn tab metrics**, **no total/count on an empty category band**, and **Historial's last page ending with no closing label** — all ruled on at a gate; I verified the last of these renders as ruled and treated none of them as findings.
- **`test_integrity` is green**, 269 tests / 691 assertions against a 221/565 baseline; nothing was removed or weakened during this run.
