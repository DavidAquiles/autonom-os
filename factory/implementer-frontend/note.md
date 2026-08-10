# Frontend — Phase 2 implementation note (Run 02, brownfield feature)

## Summary

Three screens shipped against the approved mockups: **Historial** (the fourth
Finanzas tab), the **read-only expense detail** at `/finanzas/gasto/:id`, and the
**month opened by category** on `/finanzas/mes`. The expense form moved to
`/finanzas/gasto/:id/editar` (KD-23) — that one route move *is* B1, because every
list already linked to `/finanzas/gasto/:id`. `ExpenseLedger` moved out of
`Hoy.tsx` into its own file and now serves all three lists in three content
variants (KD-26). The month and the selected category became `?mes=` /
`?categoria=` search params (KD-24, B2).

Gates: **`npx tsc --noEmit` clean · `npm run build` ✓ built · `npm run test`
70 passed / 9 files** (41 baseline + 29 new; no existing test deleted or
weakened) · **`node tools/shots.mjs` 132 captures, 0 audit findings**.

Two defects were found by rendering rather than by reading, and both are fixed:
the **authorised** `Button.module.css` `.text:disabled` fix, and a bug **in my own
scroll-restoration code** that would have failed 17.8 on all three lists while
looking correct in every screenshot and in the unit suite (see *R1*, below —
this is the thing to check hardest).

Nothing under `backend/` was read or written.

---

## Files changed

New:

| file | what |
| --- | --- |
| `frontend/src/routes/finanzas/Historial.tsx` (61) | the fourth tab |
| `frontend/src/routes/finanzas/GastoDetalle.tsx` (125) | the read surface |
| `frontend/src/routes/finanzas/GastoDetalle.module.css` (89) | its styles |
| `frontend/src/routes/finanzas/ExpenseLedger.tsx` (78) | the shared row, moved (KD-26) |
| `frontend/src/components/shell/useScrollMemory.ts` (79) | 17.8's offset capture/restore |
| `frontend/src/test/historial.test.tsx` | 9 tests, 16.x |
| `frontend/src/test/gastoDetalle.test.tsx` | 16 tests, B1/B2, 17.x, 18.x |
| `frontend/src/test/rutas.test.ts` | 4 source-reading tests, B1 structural + KD-25 |
| `frontend/tools/verificar-scroll.mjs` | drives a real browser through 17.8 |

Changed: `App.tsx`, `api/queries.ts`, `api/types.ts`, `copy/es.ts`,
`routes/finanzas/{Mes,Hoy,GastoForm}.tsx`, `routes/finanzas/Finanzas.module.css`,
`components/shell/Screen.tsx`, `components/ui/Button.module.css`,
`test/server.ts`, `tools/shots.mjs`, plus the regenerated `tools/shots/*.png`
and `audit.json`.

**Two files are outside the design's stated Frontend changed-file list.** Both
are named as deviations below, neither is incidental: `Button.module.css` (the
authorised fix I was cleared for) and `Screen.tsx` (two lines, required by the
design's own client-side contract — see *Deviations*).

### What each change serves

```
api/types.ts:100-111                <- Interface Contract GET /api/expenses response   (16.9, 18.3)
api/queries.ts:40                   <- KD-25 key prefix `['expense-list', …]`
api/queries.ts:51-58                <- KD-25 consequence: invalidate the new prefix     (16.11, 18.10)
api/queries.ts:172-199 useHistorial <- KD-20 keyset paging, KD-25 pages in the cache    (16.2, 16.7-16.9, 16.13)
api/queries.ts:201-215 useCategory… <- KD-21 unpaged month+category                     (18.2, 18.13)
routes/finanzas/ExpenseLedger.tsx   <- KD-26 one row, three variants                    (16.5, 17.1, 18.12)
routes/finanzas/Historial.tsx       <- client contract "Historial's screen"             (16.1-16.10)
routes/finanzas/GastoDetalle.tsx    <- KD-23, KD-27, client contract "The detail screen" (17.1-17.6, 17.10, 17.11)
routes/finanzas/Mes.tsx:40-75       <- KD-24 search params                              (18.6, 18.7, 18.9)
routes/finanzas/Mes.tsx:124-144     <- the opened band                                  (18.3-18.5, 18.10)
routes/finanzas/Mes.tsx:169-197     <- tappable category rows                           (18.1, 18.11)
routes/finanzas/GastoForm.tsx:67-88 <- push/pop table: pop on both exits, `estado.desde` (17.7, 17.9)
components/shell/useScrollMemory.ts <- R1 / "Every list returns in the state it was left in" (16.7, 17.8, 18.9)
App.tsx:46, 57-58, 88-91            <- routes + the fourth tab                          (16.1, 16.12, 17.1)
copy/es.ts:21, 61-108               <- client contract "Spanish copy"                   (16.6, 16.10, 17.4, 17.5, 17.11, 18.3, 18.10)
tools/shots.mjs                     <- design § Screenshot recipes                      (constraints 29-43)
```

---

## Fidelity to the approved mockups

Every screen was built from `factory/implementer-frontend/mockups/` and the CSS
was carried from that set's delta (`mockups/_build/css02.py`) rather than
re-authored: `.orden`, `.verMas`, `.catrow`, `.opened`/`.cerrar`/`.figures` and
the whole `GastoDetalle.module.css` are the mockup's declarations under the
project's camelCase module names. Compare `tools/shots/finanzas-historial.png`
with `mockups/shots/historial.png`, `tools/shots/gasto-detalle.png` with
`mockups/shots/gasto-detalle.png`, `tools/shots/finanzas-mes--categoria.png`
with `mockups/shots/finanzas-mes--categoria.png`.

**Gate rulings honoured, not revisited.**

- **OQ1** — the show-more control ships as drawn: `Button kind="text"`, 16 px/700,
  centred, no border, no fill.
- **OQ2 — ship as drawn.** Nothing in `Screen.module.css` changed; the tab strip
  keeps Run 01's metrics. `historial-tira-estrecha.html` remains a drawn record
  of a rejected option and has no counterpart in `src/`.
- **OQ3 — figures dropped.** `Mes.tsx:132` gates the total and the count on the
  category having something in the month, so an empty category's band carries
  the name and `✕ Cerrar` and nothing else. `tools/shots/finanzas-mes--categoria-vacia.png`.
- **OQ4 — no closing line.** Historial's last page ends at the last hairline.
  `grep` finds no "ya viste" string anywhere.
- **OQ5** — `✕ Cerrar` (`common.cerrar`, which already existed).
- **OQ6** — the edit line keeps the timestamp: `Editado el 7 de agosto a las 09:20.`
- **OQ7** — implemented as ruled: the band's name is `by_category` → `useCategories()`
  → nothing. `Mes.tsx:77-79`. Verified live: `?categoria=8` (Ropa, absent from
  August's `by_category`) renders "Ropa" from `useCategories`.

### Departures from the mockups

1. **The mockups drew a phone status bar (19:47, signal, battery).** That is
   mockup chrome, not app UI; the real app has never drawn one. Not a departure
   in the UI, but it is why the shots are ~40 px shorter at the top.
2. **`finanzas-mes--categoria` is photographed on Transporte, not Comida.** The
   live database holds one Comida expense this month and eight Transporte ones,
   and a one-row list photographs nothing. The screen is identical; only the
   category differs.
3. **A non-`not_found` failure on the detail shows the app's unreachable banner**
   (`GastoDetalle.tsx:60-66`). The mockups have no such state because the
   contract's only detail failure is `not_found`. Saying "Este gasto ya no
   existe" when the server is merely out of reach would be a lie, and this screen
   sits outside `<FinanzasTabs>` so it does not inherit `ReachabilityBanner`. It
   reuses the existing `Banner` and the existing `servidor.*` copy — nothing new
   invented (client contract: "no invention required and none permitted").
4. **Opening a deleted expense shows `Cargando…` for about a second** before
   17.11's state, because `main.tsx:15` sets `retry: 1`. That is Run 01's policy,
   17.11 forbids a spinner *that never ends*, and I did not change a shipped
   default to make a screenshot nicer. The recipe waits it out
   (`shots.mjs`, `gasto-detalle--no-existe`).

---

## Visual Direction Conformance (constraints 29–43)

Each is checked against a real 390×844 render in `frontend/tools/shots/`.

- **29 — four legible tabs.** `finanzas-historial.png` (390) and
  `finanzas-historial--360.png`: one line, no ellipsis, no per-label size change,
  all four at 16 px. The audit reports no overflow and no sub-44×44 target at 390,
  360 or 320. At **320** `Este mes` wraps to two lines
  (`finanzas-historial--320.png`) — measured in Phase 1 as beginning at ≤330 px,
  outside the constraint's stated viewport, and **ruled "ship as drawn" at the
  gate**. Recorded, not hidden.
- **30 — Historial's rows are Hoy's rows.** Literally the same component and the
  same `.row`/`.what`/`.cat`/`.meta`/`.amt` rules; no Historial-specific override
  exists. `finanzas-historial.png` against `finanzas-hoy.png`.
- **31 — the ordering statement.** Above the first row,
  `finanzas-historial.png`. The live shot earns it: the dates read 8, 7, 7, 1, 2,
  2, 6 — visibly not descending. `historial.test.tsx` asserts the DOM order.
- **32 — both states, distinguishable on sight.** Absent:
  `finanzas-historial.png` (live; 16 expenses against a page of 30 — **checked,
  not assumed**, per N1). Present: `finanzas-historial--ver-mas.png` (stubbed,
  because the live seed cannot produce it). In flight:
  `finanzas-historial--ver-mas-en-curso.png`.
- **33 — flat.** No heading, separator, band or sticky header exists in the
  markup; `finanzas-historial--desplazado.png` is where one would appear.
- **34 — nothing else operable.** Title area, rows, and the show-more control.
  The five inherited shell operables are the design's ratified enumeration.
  `historial.test.tsx` asserts no textbox, combobox or radio on the screen.
- **35 — a reading surface.** `gasto-detalle.png`. No input, no chip, no select,
  nothing greyed out; one control that touches the expense. Asserted by
  `expectReadingSurface()` in `gastoDetalle.test.tsx` on all three entry points.
- **36 — the journal read frame.** Literally `Screen` + `FormBar` +
  `capture={null}`, the same three things `Entrada.tsx:34` uses.
- **37 — two labelled dates, description unclamped.** `Fecha del gasto` sits
  inside the ruled facts block; `Anotado el…` sits outside it, below the rule, in
  13.5 px footnote type. `gasto-detalle--descripcion-larga.png` shows ~600
  characters whole, with no clamp and no "seguir leyendo" anywhere in the CSS.
- **38 — the edited mark is neutral.** `gasto-detalle--editado.png`: same colour,
  size and block as `Anotado el…`. `estilos.test.ts:62-74` proves no new module
  reaches for red — and it caught me naming the token in a *comment*, which is
  the check doing its job.
- **39 — tappable versus not.** `finanzas-mes--frontera.png`: category rows run
  full-bleed with a violet chevron; payment rows keep today's inset rule. Never
  colour alone. Hover, focus-visible and active captured separately.
- **40 — two totals, never ambiguous.** `finanzas-mes--categoria.png`: month
  `$267.970` at 40 px/300 under "agosto 2026"; category `$77.010` at 22 px/700
  under "Transporte". Four axes where the constraint asks for three.
- **41 — clear without scrolling.** `✕ Cerrar` sits in the band, on screen in the
  default 390×844 shot.
- **42 — both new empty states designed.** `finanzas-historial-vacio.png` and
  `finanzas-mes--categoria-vacia.png`. Neither is a blank area, a zero row, an
  error or a bare frame.
- **43 — nothing reveals voice versus typed.** No badge, icon, tint, label or
  field on any of the three surfaces; `source` is absent from `api/types.ts`, so
  no component can render it.

Carried-over constraints most at risk: **2, 3** no new colour token and no red in
any new module; **6** name, amount and percentage stay adjacent to every bar and
tappability is carried by rule + chevron + wash; **12** no `font-family` is set
anywhere new; **21** `$267.970`, `$77.010`; **22** no `prefers-color-scheme`
rule; **23, 24** every new string Spanish, accents intact (`es.test.ts` green).

### Screenshot matrix

| row | captured |
| --- | --- |
| default | `finanzas-historial`, `gasto-detalle`, `finanzas-mes--categoria`, `finanzas-mes` |
| **hover** | `finanzas-historial--fila-hover`, `--ver-mas-hover`, `--pestana-hover`, `gasto-detalle--editar-hover`, `finanzas-mes--categoria-hover`, `--cerrar-hover` |
| **focus-visible** | `finanzas-historial--fila-foco`, `--ver-mas-foco`, `--pestana-foco`, `gasto-detalle--editar-foco`, `--cerrar-foco`, `finanzas-mes--categoria-foco`, `--cerrar-foco` |
| **active / pressed** | `finanzas-historial--ver-mas-pulsado`, `--pestana-pulsada`, `gasto-detalle--editar-pulsado`, `finanzas-mes--categoria-pulsada` |
| **disabled** | `finanzas-historial--ver-mas-en-curso` — the only shot that exercises the Button fix; see below |
| empty | `finanzas-historial-vacio`, `finanzas-mes--categoria-vacia` |
| loading | covered by the in-flight control above; the `Cargando…` skeleton is Run 01's, already in the matrix |
| error | `gasto-detalle--no-existe` |
| scrolled | `finanzas-historial--desplazado`, `finanzas-mes--frontera`, `finanzas-historial--ver-mas` |
| narrow | `finanzas-historial--320`, `--360`, `finanzas-mes--categoria-320`, `gasto-detalle--320` |
| dark mode | not applicable — constraint 22, light only |

**The disabled state needed a new mechanism.** Against a stub the "ver más" fetch
resolves in microseconds, so the in-flight state cannot be caught by timing. I
added an `eval` action to `shots.mjs` (the attribute-state analogue of
`CSS.forcePseudoState`) which sets `disabled` and the in-flight label on the
**real** control, then forces `:hover` on it. That is the difference between "not
screenshotted" and "not screenshotable", and it is the shot that proves the
Button fix: the control greys and does **not** wash violet under the pointer.

---

## Interface Contract conformance

`GET /api/expenses` — consumed exactly as specified, verified against the live
`/api/openapi.json` (`{date, month, category_id, order, before_id, limit, offset}`):

- `order=registered` + `limit=30` + `before_id=<cursor>` — Historial
  (`queries.ts:181-199`). `before_id` comes only from the previous response's
  `next_before_id`; `offset` is never sent on this path, asserted by
  `historial.test.tsx`.
- `month` + `category_id` — the filtered list (`queries.ts:204-214`). No `order`,
  so the server's default `spent` ordering applies, which is 18.13.
- `next_before_id` — read as `getNextPageParam`, so `hasNextPage` is exactly
  `next_before_id !== null` (16.9). Never rendered as a number.
- `total_count` — the count in 18.3's band, and nothing else (KD-22).
- `items[]` — `id`, `amount_cop`, `category_name`, `payment_method_name`,
  `spent_on`, `description`, `created_at`, `updated_at`. `source` is absent from
  the type, so no component can reach for it.
- An **archived** category lists its expenses normally; only an unknown id, or a
  real category with nothing in the queried month, reaches the empty state. The
  UI treats both identically and neither as an error — matching the backend's
  ruling on the contract's one self-contradictory sentence.

`GET /api/expenses/{expense_id}` — the whole data source for the detail
(`useExpense`, unchanged hook and key, KD-27). `created_at` → 17.4;
`updated_at !== created_at` as exact strings → 17.5; `404 not_found` → 17.11.

`PATCH` and `DELETE /api/expenses/{expense_id}`, `GET /api/summary/month` —
unchanged and reused. No new update path was built.

---

## Escalations / Deviations

**No escalation was needed.** Four deviations, all deliberate:

1. **`components/shell/Screen.tsx` (2 lines) is outside the stated changed-file
   list.** The design's client-side contract requires the scroll offset to be
   restored "on all three lists" and says "one mechanism, applied once at the
   `Screen` scroll container, is expected rather than three screen-local copies"
   — and that container is `Screen.tsx:30`. The file list omits it; the contract
   requires it. I followed the contract: a ref on `<main>` and one hook call. A
   consequence worth naming: switching Finanzas tabs now returns to the top of
   the new tab instead of inheriting the previous tab's offset from the shared
   `<main>`. That is standard navigation behaviour and I judge it an improvement,
   but it is a behaviour change nobody asked for.
2. **`components/ui/Button.module.css` `.text:disabled` gains `background: none`**
   — the authorised out-of-list fix, kept to that one rule.
3. **`test/server.ts` gained function-valued routes.** One path could not answer
   differently per `before_id`, so 16.7/16.8's append could not be tested
   honestly. Six lines, still contract-shaped payloads, no hand-rolled mock.
4. **Deferred 4 (push vs replace between categories) resolved as *replace*,** and
   month changes likewise. Reasons in `Mes.tsx:52-60`: it is what the `useState`
   this displaces did, so the back button still means "leave Finanzas" rather
   than "walk back through the months I paged"; 18.5's on-screen control is what
   clears a selection; and 18.9 holds either way because the restored *entry*
   carries the search string. Verified by round-trip test and in a real browser.

---

## Acceptance criteria mapping

**Requirement 16 — Historial.** 16.1 fourth tab + route (`App.tsx:46,88-91`),
one interaction from any tab (test). 16.2 `order=registered`, asserted on the
request and visible in the live shot. 16.3, 16.4 server-side ordering by `id`;
the client neither re-sorts nor re-keys. 16.5 all four facts on the row. 16.6
the statement, above the first row. 16.7 append via `useInfiniteQuery`, order
preserved, no jump to the top (test asserts first and last row after paging).
16.8 the cursor is `next_before_id`, never an offset; termination is the
server's. 16.9 no control, label or spinner when the cursor is null. 16.10 the
designed empty state. 16.11 the `['expense-list']` invalidation, tested through a
real delete flow. 16.12 rows link to the detail. 16.13 `limit=30`, asserted.

**Requirement 17 — the detail.** 17.1 all three surfaces (three tests + a
source-reading test that no list can re-point at the form). 17.2, 17.3
description whole / omitted. 17.4 the recorded moment, labelled, kept away from
the dated-for date. 17.5 neutral, with the timestamp (OQ6). 17.6 one edit action,
opening the pre-filled form. 17.7 both exits pop to the detail. **17.8 verified
in a real browser on all three lists** — see below. 17.9 delete replaces to
`estado.desde` (path + search). 17.10 `source` is not on the wire and not in the
type. 17.11 plain Spanish.

**Requirement 18 — the month.** 18.1 one interaction, visibly tappable. 18.2 the
server's filter; the UI adds none. 18.3 name + `by_category` total +
`total_count`. 18.4 the month total stays put (A33). 18.5 `✕ Cerrar`, on screen
without scrolling. 18.6 one param, so a second selection replaces. 18.7 changing
month drops `?categoria` (test). 18.8 rows link to the detail. 18.9 the round
trip (test). 18.10 the designed state, no zero row (test asserts `$0` and
`0 gastos` are absent). 18.11 no selection in an empty month (test). 18.12 the
`categoria` row variant. 18.13 the server's `spent` ordering.

**Not mine:** 16.2/16.3/16.4/16.8's server halves, 18.2's and 18.13's SQL. Those
are `implementer-backend`'s and I have not claimed them.

---

## What to look at hardest

1. **`useScrollMemory.ts:39-51` — and the reason the comment there is long.** My
   first version took a final reading in the `useEffect` cleanup. React runs that
   cleanup *after* detaching the container, and a detached element reports
   `scrollTop === 0` — so the "safety" read did not capture the offset, it
   **destroyed** the one the scroll listener had already captured, and every list
   returned to the top. Every unit test passed. Every screenshot was correct. It
   is exactly R1's stated failure mode, and I only found it by driving Chromium
   through scroll → open → back and reading `main.scrollTop`. That check is
   committed as `tools/verificar-scroll.mjs`; against the shipped build it
   reports **OK Historial (420→420), OK mes + categoría (251→251)**, and SKIP for
   Hoy when today is empty. I verified Hoy by creating twelve expenses dated
   today (**OK, 394→394**) and then deleting exactly those twelve; the database
   is back at 16 expenses / `$267.970`, as I found it.
2. **`GastoForm.tsx:82-88` — `location.key !== 'default'` as the "can I pop?"
   test.** It is a heuristic for the one case the design names (a hand-typed
   `…/editar` URL). It is right for every path an affordance can produce, but a
   reviewer should be satisfied it cannot mis-fire.
3. **`Mes.tsx:61-70` — `go()` is the only writer of both search params.** 18.7
   depends on `'mes' in next` forcing the category to null. Read it against
   18.6/18.7 together.
4. **The `finanzas-mes--categoria-vacia` name path.** `Mes.tsx:77-79` is OQ7's
   ruling; the case where no name exists anywhere renders the band with the close
   control and no heading. That is unreachable through the UI and untested live.

### One observation outside my slice

`npm run shots` drives the **real** API, and a pre-existing recipe
(`gasto-guardando`, which delays the POST rather than failing it) intermittently
writes a real `$14.000 Transporte` expense into the database — one per run, three
across my runs. I deleted the three I created, and the database is back to its
starting state. I have not changed that recipe: it is Run 01's, it is outside
this feature, and silently rewriting another lane's harness behaviour is worse
than reporting it. QA should know that running the matrix can mutate the data it
is photographing.

---
---

# Frontend — QA rework note (cycle qa_impl 1: D1, D2, D3)

> Appended by a **cold-spawned** frontend agent; the Phase 2 transcript above is
> its predecessor's and was not available. Everything below was derived from
> `factory/qa/report.md`, `factory/architect/design.md`, the approved mockups and
> the code on disk.

## Summary

Three QA defects fixed, one file added, six touched. **D1** (Back after deleting
showed the dead expense in full, with a working edit action) had two causes and
both are fixed: the delete now **pops twice** instead of replacing, so the stack
after deleting is the design's stated `[lista]`; and the not-found detail now
**replaces** the record instead of rendering above it, so no cached expense and
no "Editar gasto" survive a `404`. **D2** and **D3** were the same defect on two
screens — a request that *failed* was reported as a list that came back *empty*
(the month's category band) or as nothing at all (Historial) — and both now use
one new shared state, `ListFailure`, which says the list did not load and offers
a retry, and which stays silent when the app is already saying it cannot reach
the server.

The misleading save copy is **now unreachable** and was left alone (below).
Scroll restoration (17.8, the run's biggest risk) was not touched; the Reviewer's
F2 was not "fixed"; D4, D5, D6 were not touched — though D6 *changes as a
consequence* of D1(a), see Deviations.

Gates: **`npm run build` ✓ built in 1.48s · `npx tsc --noEmit` clean ·
`npm run test` 75 passed / 9 files** (70 before, 5 added, none deleted or
weakened) · **screenshot matrix 20 captures over the reworked states, 0 audit
findings**. The user's database ends at **16 expenses / $267.970**, md5
`f40f1c0965351565d9dccac1e6bd81b5` — unchanged; the server on `:8001` (pid 4663)
was left running and untouched.

## What changed, per defect

### D1(a) — the navigation stack

    GastoForm.tsx:89-110   afterDelete()                    <- design.md:582 push/pop table (17.9)
    GastoForm.tsx:492      remove.mutate onSuccess
    GastoDetalle.tsx:41-42 hayLista / back
    GastoDetalle.tsx:80-92 !missing, and state: { desde, hayLista }

**I implemented the table's stated stack, not its mechanism column** — the two
disagree, and QA reproduced the disagreement. `navigate(desde, { replace: true })`
at `[lista, detalle, editar]` yields `[lista, detalle, lista']`, so one Back tap
lands on the deleted expense's detail. `afterDelete` pops **two** entries
instead, which lands on `[lista]` *and* returns the user to the very location
entry the row was tapped from, carrying its `?mes=`, `?categoria=` and recorded
offset rather than a fresh copy of the same URL.

**Architect: the table's mechanism column at `design.md:582` needs correcting**
from "replace, to `estado.desde`" to "pop ×2, `estado.desde` as fallback". The
predecessor followed the mechanism and was right to; the stack column is the one
that expresses 17.9's intent.

Knowing *whether* two entries exist cannot be read from `location.key` alone, so
the detail now threads `hayLista` (there is an entry behind me) in router state
alongside `desde` — the same mechanism, the same fallback discipline. Where it is
false (a hand-typed `…/editar`, or a detail opened as the session's first entry)
the old `replace` to `desde` still applies.

**Popping cannot erase the FORWARD entries** — no History API can. That is why
D1(b) is fixed *as well as*, not *instead of*, D1(a): the dead detail is still
reachable by the forward button, and it must be harmless when it is reached.
Captured: `tools/shots/qa-d1-adelante-gasto-borrado.png`.

### D1(b) — the detail rendering cached data under its own not-found message

    GastoDetalle.tsx:80    {expense.data && !missing && <Recibo …>}

TanStack keeps the last good `data` when a refetch fails, so `expense.data` and
`expense.error` were both truthy and the screen rendered both. `!missing` makes
the not-found state **replace** the record. Any *other* failure still shows the
cached record under the unreachable banner, which is deliberate and is what the
approved mockup draws: out of date is worth reading, gone is not.

### The misleading save copy — left alone, and now unreachable

The `guardarFalloTitulo` / `guardarFalloCuerpo` pair ("no alcanzo tu servidor…
vuelve a intentarlo cuando el computador esté despierto" for a live `404`) is Run
01 copy on a Run 01 code path. It was reachable only through the edit button on a
dead detail. With (b) there is no edit button on that screen, and with (a) the
screen is not behind Back at all — so **I changed no copy and no branch there**,
per the brief.

### D2 — a failed category list reported as an empty category

    Mes.tsx:154-175   isError → ListFailure; isSuccess → 18.10's empty state

`filtered.isSuccess && items.length === 0` is the whole fix: it is the difference
between "there is nothing here" and "I do not know what is here". The empty-state
claim is now made only about a list the server actually returned. `?categoria=0`
(the 400) is no longer special-cased — it lands in the same branch as a 500, a
locked database or a dropped request, which is what QA asked for.

The `?categoria` parse at `Mes.tsx:43` was **not** touched: rejecting `0`
client-side would fix the cheapest trigger and leave the branch broken.

### D3 — Historial blank on a partial failure

    Historial.tsx:35      isError → ListFailure above whatever arrived
    Historial.tsx:37-44   16.10's empty state only when the request succeeded

The banner sits **above** the rows that did arrive, which is the shape
`mockups/shots/historial--sin-servidor.png` drew; with nothing cached it is the
whole screen. 16.10's copy is no longer reachable from a failure.

### The new state

    routes/finanzas/ListFailure.tsx   (new, 42 lines)
    copy/es.ts:311-319                servidor.listaFallo{Titulo,Cuerpo}
    components/ui/Panel.module.css:29-56   .action as a button; .action:disabled

One component for both screens, for constraint 30's reason: two copies of an
error state drift. It is the app's existing violet `Banner` — **no `var(--danger…)`**,
so `estilos.test.ts:62-74` still passes with red confined to its three files.
Copy: *"No pude cargar esta lista. / Tu servidor está respondiendo, pero esta
lista no llegó. Lo que anotaste sigue guardado."* with **Reintentar**. It states
what happened, does not apologise, does not claim anything about the data, and
distinguishes itself from the outage the user already knows — which is the
confusion QA named ("a user cannot tell the two situations apart").

**It renders nothing when `useHealth()` is errored**, because `ReachabilityBanner`
is already on screen saying exactly that. Two banners about one condition, in two
wordings, is the self-contradicting screen D2 is about. Health — not the error's
class — is the right signal: QA's repro blocks `/api/expenses` at the network
layer while `/api/health` keeps answering, which raises `UnreachableError` for a
server that is in fact reachable.

## Tests added (5) — each verified to FAIL without its fix

| test | file | fails without the fix as |
| --- | --- | --- |
| Back after deleting does not reach the dead detail (D1a) | `gastoDetalle.test.tsx:242` | `expected <h2>Este gasto ya no existe.</h2> to be null` |
| the not-found state replaces the record (D1b) | `gastoDetalle.test.tsx:277` | `expected <div class="_amount_…"> to be null` |
| a failed category list is not an empty category (D2) | `gastoDetalle.test.tsx:423` | the 18.10 copy renders |
| the list did not load, with a retry, never "nothing recorded" (D3) | `historial.test.tsx:228` | blank `<main>`; no banner found |
| the retry loads the list (D3) | `historial.test.tsx:240` | no banner found |

Two small harness capabilities, both additive: `test/server.ts:90-97` lets a
route answer with its own `Response` (the real 400) or throw (a request that
never reaches a live server), and `gastoDetalle.test.tsx:36-59` adds an in-router
**Back** control — the gesture QA used to find D1 and the only one no test was
making.

## Screenshot matrix — re-rendered against the built UI

Run against a **scratch** database (a read-only `sqlite3` backup of the user's,
so the WAL was captured) served by a scratch API on **:8011**; both deleted
afterwards. `npm run shots` was **not** run — `tools/shots.mjs` gained
`--only <regex>` precisely so a rework pass can re-photograph a handful of states
without the `gasto-guardando` recipe reaching a database. A filtered run now
writes `audit-parcial.json` so it cannot overwrite the full matrix's report.

| state | capture |
| --- | --- |
| default (Historial, list failed) | `qa-d3-historial-lista-falla.png` |
| **hover** | `…--reintentar-hover.png` — underline only, no colour change |
| **focus-visible** | `…--reintentar-foco.png` — violet ring, unclipped |
| **active/pressed** | `…--reintentar-pulsado.png` |
| **disabled (retry in flight)** | `…--reintentando.png` — `--ink-soft`, contrast passed |
| error over cached rows (the mockup's shape) | `…--sobre-filas.png` |
| retry with nothing cached | `…--reintentando-sin-filas.png` |
| narrow (320) | `…--320.png` |
| D2, stubbed failure | `qa-d2-mes-categoria-lista-falla.png` |
| D2, live `?categoria=0` (real 400) | `qa-d2-mes-categoria-cero.png` |
| D2 control — a category that really *is* empty | `qa-d2-mes-categoria-vacia-de-verdad.png` |
| D1(a), Back after deleting | `qa-d1-atras-tras-eliminar.png` — lands on Hoy |
| D1(b), forward onto the dead detail | `qa-d1-adelante-gasto-borrado.png` — message alone |

0 audit findings (contrast, 44×44 targets, horizontal overflow, dark-mode
tripwire). **Not captured:** dark mode — constraint 22 is light-only and
`estilos.test.ts` tripwires any `prefers-color-scheme` rule. **Loading** for
these screens is the pre-existing `.skeleton`, unchanged, already in the matrix.

Two states are captured in a way worth naming, because the naive version of each
would have proved nothing:
- the **disabled** retry only exists when the query has data (a query with no
  data returns to `pending` on refetch and shows the skeleton), so the capture
  loads live rows first and fails the *refetch* — `stubFrom` in the harness;
- **Back after deleting**, entered directly at `/finanzas/historial`, leaves the
  app entirely (correct — nothing is behind the list) and photographs a blank
  browser page. The shot enters through the tab so there is a screen behind it.

## Escalations / Deviations

1. **The design doc is internally inconsistent at `design.md:582`** and I
   implemented the stated stack. Flagged above for Architect.
2. **D6 changes as a consequence, without being targeted.** Deleting from a list
   now returns to the list's *saved offset* rather than to the top, because
   popping restores the entry the offset was recorded against. D6 was deferred as
   "cosmetic, arguably correct"; this is the deferred behaviour resolving itself
   in the direction QA called consistent. Nothing was written to make it happen
   and `useScrollMemory` was not touched.
3. **`ListFailure` renders `null` when health is errored.** A deliberate
   condition, argued above. The consequence: in a *warm* total outage with no
   cached rows, Historial shows the reachability banner and nothing else — not a
   blank `<main>`, but not this new state either.
4. Nothing under `backend/` was read or written. No existing test deleted or
   weakened (70 → 75).

## Acceptance criteria

No criterion changed hands. The fixes serve the **intent** of 17.9 and 17.11
(D1), 18.10 (D2) and 16.10 + constraint 42 (D3); QA recorded all four as passing
as written before this cycle, and each still passes — the 18.10 and 16.10
empty-state tests were kept as the guard against over-correcting, and both are
green.
