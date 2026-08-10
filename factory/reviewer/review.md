# Reviewer — Run 02 (brownfield feature), static review

Reviewed `418d7b3da081..HEAD` under `backend/` and `frontend/` against
`factory/architect/design.md` (Interface Contract, KD-18…KD-27, the push/pop
table, the navigation-state section, and the gate rulings folded in after
approval), `factory/pm/spec.md` (16.1–18.13, A23–A42, B1–B2, Non-Goals),
`factory/pm/visual-direction.md` constraints 29–43, the approved mockups in
`factory/implementer-frontend/mockups/`, and both implementers' notes.

`state.verification` at this revision: `frontend:build` pass, `frontend:typecheck`
pass, `frontend:unit` pass (70), `backend:unit` pass (280), `backend:contract`
pass (42), `test_integrity` **pass** (269 tests / 691 assertions / 24 files vs a
221 / 565 baseline). No gate failed, so nothing here is an approval over a red
gate, and no finding below contradicts a gate that passed.

## What I checked and found correct

Recorded so the approval is not read as broader or narrower than it is.

**Backend ↔ frontend against the Interface Contract (the seam nothing before me
compares).** Parameter names, types and defaults agree in both lanes:
`api/expenses.py:57-63` publishes `{date, month, category_id, order, before_id,
limit, offset}` with `order: Literal["spent","registered"] = "spent"`,
`category_id`/`before_id` as `Query(None, ge=1)`; the contract's closed set is
pinned in both directions at `tests/test_contract_conformance.py:77-105`; and the
frontend sends exactly `order=registered&limit=30[&before_id=]`
(`api/queries.ts:184-191`) and `month=…&category_id=…` with no `order`
(`:207-208`), never `offset`. The response shape
`{items, total_count, next_before_id}` (`api/models.py:110-118`) matches
`api/types.ts:100-104` field for field, `source` is absent on both sides, and
`hasNextPage` is derived from `next_before_id` alone (`queries.ts:195`). No drift
found.

**The four things I was asked to attack.**

- `repo/expenses.py:327-329` — `order == "registered" and has_more and items` is
  correct on all three terms. `has_more` comes from the `limit + 1` fetch
  (`:319-321`) so the cursor cannot be reported on the last page (16.9);
  `order == "registered"` keeps it `null` for `spent` as the contract requires;
  `items[-1]["id"]` under `ORDER BY e.id DESC` is the page's smallest id, so
  `e.id < ?` (`:313`) cannot repeat or skip the boundary row (16.7/16.8). The
  archived-category filter is `e.category_id = ?` and nothing else (`:301-303`) —
  no `archived_at` predicate anywhere in `list_expenses`, which is the reading the
  contract's normative sentence demands and the backend note declares.
  `total_count` is computed from `conditions` before `before_id` is appended
  (`:306-314`), so it ignores the cursor, `limit` and `offset` as specified.
- `api/queries.ts:51-58` — `invalidateExpenseViews` invalidates `['expense']`
  **and** `['expense-list']`, so the deliberately-distinct KD-25 prefix is
  covered; `rutas.test.ts:37-49` pins it and additionally pins that no
  `['expenses'` prefix exists in the code (comments stripped). 16.11 holds.
- `Mes.tsx:61-70` — `go()` is the only writer of either search param
  (`setParams` appears once in the whole `src/` tree, at `Mes.tsx:69`), and
  `const c = 'mes' in next ? null : …` forces the category to null on every month
  change, so 18.7 cannot be bypassed. 18.6 replaces rather than combines because a
  single `categoria` key is written each time.
- `useScrollMemory.ts` — the committed version takes **no** reading in the
  `useEffect` cleanup (`:51` removes the listener only), which is the defect class
  the frontend note describes; the restore loop guards its own writes with
  `restoring` (`:35`, `:41`, `:62`) so a clamped intermediate value cannot decay
  the stored offset; and it is installed once at the shared scroll container
  (`Screen.tsx:31-32`, `:37`), so it covers Hoy, Historial **and** the filtered
  month list rather than Historial alone. One residual asymmetry is F3 below.
- `GastoForm.tsx:82-88` — `location.key !== 'default'` is only false on the
  session's first history entry, which no affordance in the app can produce for
  `…/editar`; both exits (`:217` save, `:242` close) take the same pop.

**The two authorised out-of-list files are minimal and as described.**
`Button.module.css:123-134` adds `background: none` to `.text:disabled` alongside
the pre-existing `color`/`cursor`, at equal specificity to and later than
`.text:hover` — the shipped bug, fixed, and nothing else in the file touched.
`Screen.tsx` gains an import, a `useRef`, the hook call and a `ref` attribute
(`:1`, `:6`, `:31-32`, `:37`) — the note says "two lines"; it is four, all of them
the mechanism the design's own client-side contract mandates at that container.

**Mockups.** `tools/shots/finanzas-historial.png`, `gasto-detalle.png` and
`finanzas-mes--categoria.png` match `mockups/shots/historial.png`,
`gasto-detalle.png` and `finanzas-mes--categoria.png` in structure, type scale,
rule placement and control treatment; the four declared departures (mockup status
bar, Transporte instead of Comida in one capture, the unreachable banner on the
detail, the ~1 s `Cargando…` before 17.11) are each real, each minor, and each
honestly described. No undeclared departure found.

**Design Constraints 29–43** are all expressed in the shipped source and visible
in the shipped captures: 29 (four tabs, one line, uniform size —
`App.tsx:95-99`, `finanzas-historial.png`), 30 (literally one component,
`ExpenseLedger.tsx`, no Historial-specific CSS override), 31
(`Historial.tsx:35-37` above the list), 32 (`Historial.tsx:46` gates on
`hasNextPage` only; both states captured), 33 (no grouping markup exists), 34
(nothing operable beyond rows and the show-more control), 35–38
(`GastoDetalle.tsx`, `GastoDetalle.module.css` — one edit action, journal frame,
two labelled dates, unclamped `.description`, neutral `.stamp` for the edited
line), 39–41 (`Finanzas.module.css:246-344` — full-bleed `.catrow` + chevron
against inset `.pm`; 22 px/700 category total under 40 px/300 month total;
`.cerrar` inside the band), 42 (both new empty states designed), 43 (`source` is
not in `api/types.ts`, so no component can render it). All new CSS uses tokens
only and no module reaches for the red family. Feel & Tone I treated as guidance;
nothing there is a finding.

## Findings

### F1 — [deferred] Deleting from the edit form leaves the dead detail one Back away
- location: `frontend/src/routes/finanzas/GastoForm.tsx:468`
- injected-at: architect
- scenario: `onSuccess: () => navigate(desde, { replace: true })` replaces the
  *editar* entry, so the stack goes `[lista, detalle, editar]` →
  `[lista, detalle, lista']`. After deleting, one browser Back lands on the detail
  of the record just deleted. The design's push/pop table
  (`factory/architect/design.md:582`) states the resulting stack is `[lista]`,
  which a single `replace` from the editar entry cannot produce — the mechanism
  column ("replace, to `estado.desde`") and the stack column disagree, and the
  implementer followed the mechanism. Impact is bounded: at the moment of deletion
  the user is on the list, which is what 17.9 actually requires, and the Back
  target renders 17.11's designed *"Este gasto ya no existe."* rather than a
  blank or an error. Not this run's problem; recorded so the table and the code
  can be reconciled deliberately.
- requirement: 17.9 / design push-pop table

### F2 — [deferred] The zero-offset branch of `useScrollMemory` does not arm its own guard
- location: `frontend/src/components/shell/useScrollMemory.ts:57-60`
- injected-at: implementer-frontend
- scenario: `const target = offsets.get(key) ?? 0; if (target === 0) { el.scrollTop
  = 0; return }` writes `scrollTop` **without** setting `restoring.current = true`,
  unlike the non-zero branch at `:62`. Because `FinanzasTabs` keeps one `<main>`
  mounted across Hoy/Mes/Historial, switching tabs from a scrolled list changes
  only `location.key`: the layout effect writes `scrollTop = 0` during commit while
  the outgoing key's `scroll` listener is still attached (its removal is the
  passive cleanup at `:51`), so a `scroll` event dispatched before that cleanup
  would run `offsets.set(oldKey, 0)` and discard the outgoing tab's offset. No
  acceptance criterion covers tab-switch-then-Back (17.8 is the detail round trip,
  which is unaffected — that path unmounts the container and reads nothing), and
  the effect/event interleaving is not decidable by reading. **This is a QA note,
  not a defect claim:** worth exercising as scroll Hoy → tab to Historial →
  browser Back. The one-line remedy, if it ever reproduces, is to set
  `restoring.current = true` around the zero write too.
- requirement: 17.8 (adjacent), R1

### F3 — [optional] The two exits from the edit form disagree on push vs replace in the no-history fallback
- location: `frontend/src/routes/finanzas/GastoForm.tsx:242` with
  `frontend/src/components/shell/Screen.tsx:78`
- injected-at: implementer-frontend
- scenario: `back={mode === 'editar' ? (canPop ? -1 : `/finanzas/gasto/${expenseId}`) : '/finanzas'}`
  hands `FormBar` a string, and `FormBar` calls `navigate(back)` with no options,
  so the fallback close **pushes** a detail entry — while `backToDetalle` at `:85`
  uses `navigate(..., { replace: true })` for the same case, which is what the
  design specifies (`design.md:597`). Only reachable by hand-typing
  `…/editar` as the first entry of a session; the visible consequence is that Back
  from the detail returns to the edit form.
- requirement: design client-side contract, *Leaving the detail and leaving the form*

### F4 — [optional] `?categoria=0` renders the empty-category state for what is a 400
- location: `frontend/src/routes/finanzas/Mes.tsx:43`
- injected-at: implementer-frontend
- scenario: `/^\d+$/.test(raw)` accepts `"0"`, so `categoryId` is `0`, which is not
  `null`; the band opens and `useCategoryExpenses` sends `category_id=0`, which
  `api/expenses.py:59` (`Query(None, ge=1)`) rejects with a 400. `Mes` has no error
  branch for `filtered`, so it falls through to the 18.10 empty-category state and
  reports "nothing left in that category" for a malformed value. Unreachable
  through any affordance — every id the UI can produce comes from the server's own
  `by_category`.
- requirement: none (defensive)

## Verdict

APPROVED

No blocking finding. Counts: 0 blocking, 2 deferred (F1, F2), 2 optional (F3, F4).
F1 and F2 go to the orchestrator to queue or drop; neither justifies a rework
cycle now.

## Scope Statement

Static only — nothing was executed, and I have no tool to execute it with. In
particular I did **not** verify at runtime: that the scroll offset is actually
restored on any of the three lists (I confirmed the mechanism exists, is installed
once at the correct container, and is free of the cleanup-read defect the note
describes — whether it *renders* at the right offset is QA's, on all three lists
scrolled, per R1); that paging Historial repeatedly terminates against real data;
that `npm run shots` reproduces the committed captures; or that the Design
Constraints render as the source expresses them — I checked 29–43 are expressed in
code and are consistent with the committed 390×844 captures, which is confirmation
that the constraint is *present*, not that it renders correctly on device.

I did not re-litigate the build or the suites (`state.verification` is fact), and
I did not raise the three items the run already ruled on: KD-21/R4's 200-row cap,
R3's no-op save marking an expense edited, and Diario's 50-entry cap (Non-Goal 12).
I did not review test *quality* beyond confirming the new tests are
criterion-named, assert behaviour rather than restating implementation, and that
`test_integrity` shows nothing removed or weakened. Requirements 16.x/17.x/18.x
were checked for design fidelity and contract conformance, not for acceptance —
running them against the criteria is QA's pass.
