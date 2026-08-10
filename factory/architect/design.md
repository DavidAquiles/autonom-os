# Autonom-OS — Technical Design (Run 02, brownfield feature)

**Status: FINAL.** Designed to `factory/pm/spec.md` (criteria 16.1–18.13, assumptions
A23–A42, behaviour changes B1–B2) and `factory/pm/visual-direction.md`
(constraints 29–43; 1–28 carry over).

This document is **additive** to `factory/runs/01-greenfield/architect/design.md`
("Run 01"), which remains in force in full. Its Interface Contract
(`runs/01-greenfield/architect/design.md:929-1253`) is the product's live API
contract; every endpoint not restated below is unchanged and still governs.
Key decisions continue from KD-17, so this run introduces **KD-18 … KD-27**.

---

## Summary

Three screens and one query, on top of a schema and an API that already hold
everything needed. **No migration. No new index. No new endpoint path.**

`GET /api/expenses` — today an unused-by-the-frontend list — grows three query
parameters (`order`, `category_id`, `before_id`) and one response field
(`next_before_id`). Historial reads it with `order=registered`; the month's
category drill-down reads it with `month` + `category_id`. Registration order is
`ORDER BY id DESC` — the AUTOINCREMENT primary key is monotonic with insertion,
total by construction, and is the table's own rowid, so the ordering needs no
index and no sort. Paging is keyset on that id, not offset, because offset paging
duplicates rows when an expense is captured mid-scroll and skips rows when one is
deleted — both fatal to 16.7/16.8.

The read-only detail screen takes over the **existing** route
`/finanzas/gasto/:id`, and the edit form moves to `/finanzas/gasto/:id/editar` —
mirroring `/diario/:id` and `/diario/:id/editar` exactly (A25). That single move
*is* B1: every list row already links to `/finanzas/gasto/${id}`, so no call site
changes and none can be forgotten. B2 is solved by moving the viewed month and
the selected category out of `useState` in `Mes.tsx:33` and into the URL as
`?mes=&categoria=`, so a location entry carries them and browser back restores
them for free.

**Biggest risk:** 17.8 requires the list to come back at the *same position*, and
the app scrolls inside `<main>` (`Screen.tsx:30`), not the window — so nothing
restores it for us. See R1.

---

## Key Decisions

### KD-18 — One list endpoint that grows two orthogonal capabilities, not new paths

`GET /api/expenses` gains `order`, `category_id` and `before_id`. It stays one
path.

*Rejected: a new `GET /api/expenses/historial` (and/or `/api/expenses/by-category`).*
Two new paths mean two entries in `CONTRACT_PATHS`
(`backend/tests/test_contract_conformance.py:16-47`), two response models, and a
second SQL builder that must keep `_SELECT` (`repo/expenses.py:18-25`) and its
category/payment-method joins in step with the first. The two capabilities are an
ordering and a filter over the same rows; they are parameters of one query, not
two resources. The existing path has, in its favour, that **no frontend code
calls it at all today** (`api/queries.ts` has day/month summaries and
`useExpense` only) — so extending it cannot regress a live screen.

*Rejected: putting the category drill-down on `/api/summary/month`.* The month
summary is an aggregate; making it optionally return rows would give one endpoint
two response shapes, and `by_category` (`repo/expenses.py:318-338`) is already
correct and already on screen.

### KD-19 — Registration order is `ORDER BY id DESC`, not `created_at`

`expenses.id` is `INTEGER PRIMARY KEY AUTOINCREMENT` (`0001_init.sql:48`): unique,
never reused, and assigned in insertion order. Ordering by it is therefore
**total by construction** — there is no tie to break — and it is SQLite's rowid,
so `ORDER BY id DESC LIMIT n` is a backwards walk of the table B-tree with no
sort step and **no index**. 16.4 (editing must not move a row) holds trivially:
nothing an edit can do changes an id.

*Rejected: `ORDER BY created_at DESC, id DESC`.* It needs `id` as a tiebreaker
anyway, so it is strictly more machinery for the same result; it needs a new
index on `created_at` to avoid a full sort of the table on every Historial page;
and it makes correctness depend on the lexicographic ordering of ISO strings
carrying a UTC offset, which is only sound while `APP_TZ` never changes. (Note
the brief's premise that `created_at` is second-resolution is wrong —
`clock.now_iso()` emits **millisecond** precision, `clock.py:44-51`, deliberately
so the journal's `before` cursor can separate two entries in the same second.
Even so, `id` is the better key for the three reasons above.)

`created_at` is not discarded — it is what the detail screen *displays* for 17.4.
Ordering by the id and displaying the timestamp separates "the order it went in",
which the primary key knows exactly, from "when I wrote it down", which is a fact
about the record.

### KD-20 — Keyset paging on `before_id`, never offset, for Historial

Historial pages with `limit` + `before_id`, and the server answers
`next_before_id`. The pattern is copied verbatim from the journal
(`repo/journal.py:88-96`): fetch `limit + 1` rows, return `limit`, and set the
cursor from the last returned row only when the extra row appeared.

*Rejected: `limit` + `offset` (which the endpoint already has).* Its two failure
modes are exactly the ones 16.7 and 16.8 forbid, and both are reachable in normal
use because Historial sits inside `FinanzasTabs` and therefore carries the
capture bar (`Screen.tsx:98-118`):

- An expense captured while the user is part-way down Historial shifts every
  offset by one, so the next "ver más" **repeats** the row at the old boundary —
  16.7's "without changing the order of what is already on screen" broken, and a
  visibly duplicated row.
- An expense deleted mid-scroll shifts the other way, so the next page **skips** a
  row — 16.8's "no recorded expense shall be permanently unreachable" broken,
  silently.

Keyset on a strictly decreasing primary key has neither. A row inserted mid-scroll
has a *higher* id than the cursor and so simply never enters a later page (it
appears at the top on the next refresh, which is what 16.3 wants). A deleted row
vanishes with no gap (16.11). Termination is guaranteed: each page's cursor is
strictly less than the last, and ids are bounded below, so repeated use reaches
the first row ever inserted and then returns `next_before_id: null` (16.8, 16.9).

*Rejected: a composite keyset on `(created_at, id)`.* Correct, but it needs the
`a < ? OR (a = ? AND b < ?)` predicate, an opaque two-part cursor on the wire, and
an index to be fast — all to reproduce what the primary key gives for free.

### KD-21 — The filtered month list is not paged

`month` + `category_id` returns up to `limit` rows (default 200, the existing cap
at `api/expenses.py:58`) with no "show more". Requirement 18 asks for no such
control, and one month of one category for one person is tens of rows.

*Rejected: paging it too, for symmetry.* Constraint 41 and the "not a banking app"
non-goals push against extra machinery on that screen, and a control that never
appears is a control that is never tested. The truncation risk this leaves is
named as R4, and is bounded by making the count in 18.3 come from `total_count`
(which ignores `limit`) so the number on screen is right even in the case where
the list is not complete.

### KD-22 — 18.3's two numbers come from data already on screen plus `total_count`

The category's total for the month is the `amount_cop` of its entry in
`by_category`, which `Mes` already has (`Mes.tsx:80-97`); the count is
`total_count` from the filtered list response.

*Rejected: adding `expense_count` to `CategoryBreakdown` (`api/models.py:132-137`).*
It changes the shape of a response a shipped screen already consumes, to deliver a
number the new request returns anyway, and it creates two sources of truth for one
count that must then agree. *Rejected: a new `/api/summary/category` endpoint* —
a new contract path for one integer.

### KD-23 — The detail screen takes the existing route; the form moves under it

`/finanzas/gasto/:id` → the new read-only `GastoDetalle`.
`/finanzas/gasto/:id/editar` → the existing `GastoForm` in `editar` mode.
`/finanzas/gasto/nuevo` unchanged.

This mirrors `/diario/:id` (read) and `/diario/:id/editar` (write) —
`App.tsx:60-61` — which A25 asks for explicitly. Its decisive property is that
**B1 is implemented by changing nothing at the call sites**: `Hoy.tsx:53` already
links to `` `/finanzas/gasto/${e.id}` ``, and so will the two new lists, so
"tapping an expense opens the detail" holds by construction and cannot be missed
in one of three places.

*Rejected: keeping `/finanzas/gasto/:id` as the form and adding
`/finanzas/gasto/:id/ver`.* It diverges from Diario for no reason, and it leaves
the existing row link pointing at the form — meaning B1 would have to be
implemented by editing every list, and a list added later would default to the
old, wrong behaviour.

### KD-24 — Month and category are URL search params, not component state

`Mes` reads and writes `?mes=YYYY-MM` and `?categoria=<id>` via `useSearchParams`,
replacing the `useState<string|undefined>` at `Mes.tsx:33`. This is A39 and B2: the
month becomes part of the navigable location, so returning from a detail restores
it (18.9) with no bookkeeping, and it survives a reload.

*Rejected: React Router `location.state` on the forward navigation.* State is
attached to the entry you are leaving *for*; bringing it back requires the return
path to reconstruct it, works only for `navigate(-1)`, and is lost on reload.
*Rejected: a context or store.* The project has exactly one server-state store and
no client store (`factory/context/architecture.md:341`); introducing one for two
scalars that the URL already models is disproportionate and would become the place
future state accretes.

Segments and parameter names are Spanish, per the rationale at
`runs/01-greenfield/architect/design.md:854-856`.

### KD-25 — Historial's pages live in the query cache, not in component state

Historial uses TanStack Query's `useInfiniteQuery`, keyed on `['expenses', …]`,
with `getNextPageParam` reading `next_before_id`.

*Rejected: `useState<Expense[]>` accumulating pages.* Component state dies when
the detail screen unmounts Historial, so returning would show only the first page
— failing 17.8's "same position in the list" outright, and making a user who had
paged back six months start over. The cache survives the round trip, so the list
re-renders at full length. It also gives 16.7's "append without returning to the
top" and 16.9's "no control when none remain" (`hasNextPage` is exactly
`next_before_id !== null`) without extra state.

Consequence to honour: the new key must be added to `invalidateExpenseViews`
(`api/queries.ts:42-45`), or 16.11 (a deleted expense leaves Historial) and 18.10
(a category's list going empty) will need a manual refresh.

### KD-26 — One expense row component, three content variants

`ExpenseLedger` (today defined and exported inside `Hoy.tsx:48-68`) moves to
`frontend/src/routes/finanzas/ExpenseLedger.tsx`, keeps its name and its
stylesheet (`Finanzas.module.css:74-127`), and serves all three lists. Which facts
occupy the secondary line differs per use — Hoy keeps what it renders today;
Historial shows category, payment method and the date the expense is dated for
(16.5); the filtered category list shows payment method, date and description
where present (18.12). The discriminator's shape is the implementer's.

*Rejected: three list components.* Design constraint 30 requires Historial's rows
to be structurally identical to Hoy's — "the two screenshots differ in content,
not in structure" — which is a property that survives review only if there is one
implementation. Three copies drift on the first CSS tweak.

*Rejected: making the row generic enough to configure field-by-field.* Three named
variants is the whole requirement; a field-list prop is a small layout engine.

### KD-27 — The detail and the edit form share one data path: `useExpense`

`GastoDetalle` reads `useExpense(id)` (`api/queries.ts:150-156`) →
`GET /api/expenses/{expense_id}`, the same hook and the same query key
`keys.expense(id)` the edit form already uses (`GastoForm.tsx:69`). Opening the
form from the detail is therefore cache-warm, and after a save the shared key is
invalidated so the detail shows stored values (17.7).

*Rejected: passing the row through router state from the list.* The list response
already carries a complete expense object, so this is genuinely available — and
wrong: it is stale the moment an edit returns (17.7 says "showing the values
currently stored"), it cannot survive a reload, and it gives 17.11 no way to
distinguish "not passed" from "does not exist". The single fetch is one request
against a local SQLite file on the same machine.

---

## Components / Interfaces

### Backend — two files change, nothing is added

| Piece | Change | Responsibility |
| --- | --- | --- |
| `repo/expenses.py` `list_expenses` (`:242-268`) | extended | Two new keyword-only filters (`category_id`, `before_id`) and an ordering mode. Returns `(items, total_count, next_before_id)`. All SQL and all validation stay here (`conventions.md` § Notable Patterns). |
| `api/expenses.py` `list_expenses` (`:54-68`) | extended | Declares and type-constrains the new query parameters, passes them through. Stays a pass-through; no logic. |
| `api/models.py` `ExpenseList` (`:110-113`) | extended | `next_before_id: int \| None` added. Additive; `Expense` itself is untouched. |
| `tests/test_contract_conformance.py` | extended | A **new** closed-set test over the query parameters of `GET /api/expenses` (see § Guarding the parameters). `CONTRACT_PATHS` is **unchanged** — no path is added or removed. |
| `tests/test_expenses_api.py` | extended | Criterion-named tests for 16.2, 16.3, 16.4, 16.8, 16.9, 18.2, 18.13 and the unchanged default order. |

Nothing else in the backend moves. `create`, `get`, `update` (`repo/expenses.py:126-233`)
and their routes are untouched, and so are `day_summary` and `month_summary`,
which both call `list_expenses` — so its signature change must keep every existing
call working (`repo/expenses.py:272`).

### Frontend — three new screens, four existing files change

New:

- `routes/finanzas/Historial.tsx` (+ reuses `Finanzas.module.css`) — the fourth
  tab. Infinite list, the order statement (16.6), the show-more control (16.7),
  the empty state (16.10).
- `routes/finanzas/GastoDetalle.tsx` + `GastoDetalle.module.css` — the read
  surface. Frame identical to `Entrada.tsx:34` (constraint 36).
- `routes/finanzas/ExpenseLedger.tsx` — the shared row/list (KD-26), moved out of
  `Hoy.tsx`.

Changed:

- `App.tsx` — a fourth tab item at `:83-87`; a route `/finanzas/historial` inside
  `<FinanzasTabs>` at `:43-47`; `/finanzas/gasto/:id` now renders `GastoDetalle`;
  a new `/finanzas/gasto/:id/editar` rendering `EditarGasto` (`:52`).
- `routes/finanzas/Mes.tsx` — search-param state (KD-24), tappable category rows
  (18.1), the selected-category panel and its list (18.2–18.5), clearing on month
  change (18.7).
- `routes/finanzas/GastoForm.tsx` — return targets only: `editar` mode closes and
  saves back to the detail (17.7); deleting lands on the list, never the dead
  detail (17.9). `nuevo` mode is untouched.
- `api/queries.ts` — `keys.expenses(...)`, `useExpenseList` /
  `useHistorial` (naming is the implementer's, matching the `useThing` habit), and
  the new key added to `invalidateExpenseViews` (`:42-45`).
- `copy/es.ts` — `tabs.historial` plus one new exported object per new screen.
- `api/types.ts` — `next_before_id` on the list response type.
- `test/server.ts` — a `GET /api/expenses` stub route (the stub keys off the bare
  path, `:73`, so one entry covers every parameter combination).

### Data flow

```
Historial          useInfiniteQuery(['expenses','registrados'])
                     → GET /api/expenses?order=registered&limit=30[&before_id=]
                     → repo.list_expenses(order='registered', before_id=…)
                     → ORDER BY e.id DESC LIMIT 31         (rowid walk, no sort)

Mes (categoría)    useMonthSummary(mes)     → GET /api/summary/month   [unchanged]
                   useQuery(['expenses','mes',mes,categoria])
                     → GET /api/expenses?month=YYYY-MM&category_id=N&limit=200
                     → ORDER BY e.spent_on DESC, e.created_at DESC, e.id DESC

Detalle            useExpense(id)           → GET /api/expenses/{id}   [unchanged]
Editar             useExpense(id) (same key) + useUpdateExpense        [unchanged]
```

---

## Interface Contract

Base path `/api`. Everything in Run 01's contract
(`runs/01-greenfield/architect/design.md:929-1253`) still holds — the error
envelope, the closed error-code set, the closed `reason` vocabulary, and every
endpoint not named below. Only the entries here are new or changed.

### GET /api/expenses — **CHANGED** (three new query parameters, one new response field)

- query:
  - `date` — `YYYY-MM-DD`, optional. **Unchanged.**
  - `month` — `YYYY-MM`, optional. **Unchanged.** `date` and `month` are mutually
    exclusive; when both are sent `date` wins and `month` is ignored (existing
    behaviour, `repo/expenses.py:252-258` — documented, not introduced).
  - `category_id` — **new**, int ≥ 1, optional, default absent. Restricts the
    result to that category. Combines with `date`, with `month`, with neither, and
    with either `order`. An id that does not exist, or belongs to an **archived**
    category, is not an error: it yields `200` with `items: []` and
    `total_count: 0`. Archived categories are *not* excluded — they still appear in
    `by_category` (`repo/expenses.py:318-338`) and their expenses must remain
    reachable.
  - `order` — **new**, `"spent"` | `"registered"`, default `"spent"`.
    - `"spent"` → `ORDER BY spent_on DESC, created_at DESC, id DESC` — byte-for-byte
      today's ordering (`repo/expenses.py:264`). The default exists so no existing
      caller changes behaviour.
    - `"registered"` → `ORDER BY id DESC`. The ordering is **total**: `id` is the
      AUTOINCREMENT primary key, so no two rows compare equal and no tiebreaker is
      needed (KD-19).
  - `before_id` — **new**, int ≥ 1, optional. Returns only rows with `id <
    before_id`, strictly. Order-independent by definition, and applied before
    ordering, `limit` and `offset`. It is the keyset cursor for
    `order=registered`; it is accepted with `order=spent` and means the same
    thing there, but no client sends that combination and `next_before_id` is
    `null` for it.
  - `limit` — int 1..200, default 200. **Unchanged.**
  - `offset` — int ≥ 0, default 0. **Unchanged.** Not used together with
    `before_id` by any client.
- response: `200 { "items": [ expense ], "total_count": int, "next_before_id": int|null }`
  - `items` — full expense objects, shape unchanged (`api/models.py:97-108`):
    `id`, `amount_cop`, `category_id`, `category_name`, `payment_method_id`,
    `payment_method_name`, `spent_on`, `description` (`string|null`), `created_at`,
    `updated_at`. **`source` is absent, as everywhere** — 9.5 and A38/constraint 43.
  - `total_count` — int. The number of rows matching `date`/`month`/`category_id`,
    **ignoring `before_id`, `limit` and `offset`**. It is therefore stable while
    paging, and it is the count 18.3 renders.
  - `next_before_id` — **new**. `int` when `order="registered"` **and** at least one
    older row exists beyond this page; otherwise `null`. `null` is the single,
    unambiguous "everything is shown" signal 16.9 renders against. Always `null`
    when `order="spent"`.
- errors:
  - `400 { "error": { "code": "validation", "fields": [ … ] } }`
    - `date` / `month` malformed → `reason: "required"` (existing behaviour,
      `api/expenses.py:61-64`).
    - `order` not one of the two literals → field `order`, `reason: "required"`
      (FastAPI's literal error falls through `_REASON_BY_PYDANTIC_TYPE`,
      `main.py:29-39,83`).
    - `category_id` / `before_id` / `limit` / `offset` non-integer → `reason:
      "not_an_integer"`; below their minimum → `reason: "must_be_positive"`.
  - No new error code and no new `reason` value is introduced. The closed sets in
    `errors.py:16-49` and the Spanish maps in `copy/es.ts:273-335` are untouched.
- notes: the ordering, the filter and the cursor are three independent axes; every
  combination is defined above and none is silently ignored.
- requirements: 16.2, 16.3, 16.4, 16.7, 16.8, 16.9, 16.13, 18.2, 18.3, 18.10, 18.13

### GET /api/expenses/{expense_id} — **UNCHANGED**, reused

- response: `200` expense object (as above)
- errors: `404 { "error": { "code": "not_found", … } }`
- notes: this is the whole data source for the detail screen. `created_at` is the
  recorded moment (17.4); `updated_at` is the edited-since signal (17.5) — an
  expense has been edited when `updated_at !== created_at` as exact strings, since
  `create` writes one timestamp into both (`repo/expenses.py:148,162-163`) and
  `update` rewrites `updated_at` only (`repo/expenses.py:228-231`). No server
  change is needed or wanted for either. `source` is absent, satisfying 17.10 by
  construction.
- requirements: 17.2, 17.4, 17.5, 17.10, 17.11

### PATCH /api/expenses/{expense_id} — **UNCHANGED**, reused

- request: any subset of `{ amount_cop, category_id, payment_method_id, spent_on, description }`
- response: `200` expense object; errors `400 validation`, `404 not_found`
- notes: **do not build a new update path.** It exists (`api/expenses.py:155-157` →
  `repo/expenses.py:176-233`), it is in `CONTRACT_PATHS`
  (`test_contract_conformance.py:30`), and it is wired as `useUpdateExpense`
  (`api/queries.ts:175-182`). It maintains `updated_at` already, which is what 17.5
  reads. It does not touch `id` or `created_at`, which is what makes 16.4 true.
- requirements: 16.4, 17.5, 17.6, 17.7

### DELETE /api/expenses/{expense_id} — **UNCHANGED**, reused

- response: `204`; errors `404 not_found`
- notes: the row is really gone, so it leaves Historial and any filtered list with
  no tombstone (A29). The client obligation is the invalidation in KD-25.
- requirements: 16.11, 17.9, 18.10

### GET /api/summary/month — **UNCHANGED**, reused

- response: unchanged, including `by_category[] = { category_id, name, amount_cop, percent }`
  and `is_empty`
- notes: the source of the category list that becomes tappable (18.1), of the
  category's own total (18.3), of the month total that stays visible (18.4), and of
  the "no expenses at all" state that suppresses selection entirely (18.11, Run 01
  criterion 4.5). Archived categories still appear here, which is why the filter in
  `GET /api/expenses` must not exclude them.
- requirements: 18.1, 18.3, 18.4, 18.11

### Client-side contract (no server endpoint)

Frontend obligations, listed here so requirement coverage stays computable across
the whole design — same convention as
`runs/01-greenfield/architect/design.md:1131-1212`.

- **The fourth Finanzas tab** — `Hoy · Este mes · Historial · Análisis`, in that
  order (A23), as a fourth item in the `Tabs` array at `App.tsx:83-87` and a route
  under `<FinanzasTabs>`. Not a bottom-nav destination; Run 01 criterion 1.1 and
  constraint 11 continue to bind. All four labels legible at 390 px with no
  truncation, wrap or per-label size reduction (constraint 29) — see R2.
  `requirements: 16.1`
- **Historial's screen** — a flat list with no grouping, no headings and no
  operable control other than show-more (A27, A36, constraints 33 and 34); a
  visible statement of the ordering placed above the first row (16.6, constraint
  31); the show-more control present exactly while `next_before_id !== null` and
  absent, with no spinner or trailing affordance, when it is `null` (constraint
  32); a designed empty state when nothing has ever been recorded (constraint 42).
  Rows carry amount, category, payment method and the date the expense is dated
  for. The shell's capture bar and bottom nav are frame, not screen content, and
  are not what constraint 34 forbids.
  `requirements: 16.1, 16.5, 16.6, 16.7, 16.9, 16.10`
- **Historial's pages survive leaving the screen** — the loaded pages live in the
  query cache (KD-25), so returning from a detail shows the same rows already
  loaded, in the same order, at the same scroll offset. The scroll container is
  `<main>` inside `Screen` (`Screen.tsx:30`), not the window, so the offset must be
  captured and restored explicitly; the mechanism is the implementer's, the
  behaviour is not. `requirements: 16.7, 17.8, 18.9`
- **Every expense row anywhere links to `/finanzas/gasto/:id`** — Hoy, Historial
  and the filtered category list, through the single `ExpenseLedger` (KD-26). That
  route renders the read-only detail. No list links to `…/editar`. *(B1.)*
  `requirements: 16.12, 17.1, 18.8`
- **The detail screen** — a reading surface with no input, no chip, no editable
  field and exactly one labelled edit action (17.6, constraint 35); the same frame
  as the journal read screen (constraint 36, `Entrada.tsx:34`); amount, category,
  payment method, the dated-for date, and the description **in full and unclamped**
  when there is one, omitted entirely when there is not — no dash, no placeholder,
  no "seguir leyendo" (17.2, 17.3, constraint 37); the recorded moment shown and
  labelled, separated from the dated-for date so the two cannot read as a range
  (17.4, constraint 37); a neutral edited-since indication with no red, no warning
  icon and no error styling (17.5, constraint 38); nothing revealing capture source
  (17.10, constraint 43); and a plain Spanish state when the expense does not exist
  — the `not_found` `ApiError` from `useExpense`, never a blank screen, an endless
  spinner or a raw error (17.11). All rendering through `formatCOP`, `longDate`,
  `stamp`/`clockTime` and `copy/es.ts` — no new formatter, renderer or copy
  mechanism (A40).
  `requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.10, 17.11`
- **Leaving the detail and leaving the form** — closing the detail returns to the
  list the user arrived from, in the same tab, month, category selection and
  position (17.8): a history pop, so the previous location entry — which carries
  `?mes=` and `?categoria=` — is restored intact. Saving the edit, or closing it
  without saving, returns to that expense's detail showing stored values (17.7),
  mirroring `Entrada.tsx:131`. Deleting from within the edit form must not land on
  the detail of a deleted record (17.9): it navigates to the originating list,
  carried forward as a router-state hint from the row that opened the detail, with
  `/finanzas` as the fallback. `requirements: 17.7, 17.8, 17.9`
- **The month view's category drill-down** — every `by_category` row selectable in
  one interaction and visibly tappable, with the payment-method rows visibly not
  (18.1, A35, constraint 39); a selection showing the category name, its total for
  that month and how many expenses it contains, with the month's own total still on
  screen and distinguishable by position, label and weight (18.3, 18.4, A33,
  constraint 40); a visible, single-interaction way to clear it without scrolling,
  worded as opening/closing a category rather than as a filter control (18.5,
  constraint 41 and the Feel & Tone "avoid" list); selecting another category
  replaces rather than combines (18.6, A32); changing month clears the selection so
  no month's heading can ever sit over another month's expenses (18.7, A34); a
  designed state when the selected category has nothing left in that month (18.10,
  constraint 42); no selection offered at all in an empty month (18.11); rows
  carrying amount, payment method, dated-for date and description when present
  (18.12); ordered by dated-for date, newest first (18.13, A37).
  `requirements: 18.1, 18.3, 18.4, 18.5, 18.6, 18.7, 18.10, 18.11, 18.12`
- **The viewed month and the selected category are navigable state** — held in the
  URL as `?mes=YYYY-MM` and `?categoria=<id>` on `/finanzas/mes` (KD-24), so a
  detail round trip returns to the same month and the same category rather than a
  reset current month. *(B2, A39.)* `requirements: 18.9`
- **Expense mutations invalidate the new list key** — `invalidateExpenseViews`
  (`api/queries.ts:42-45`) must also invalidate `['expenses']`, so a create,
  edit or delete is reflected in Historial and in a filtered category list without
  a manual refresh (Run 01 criterion 4.6 continues to bind).
  `requirements: 16.3, 16.11, 18.10`
- **Spanish copy for the new surfaces** lives in `copy/es.ts` as new exported
  objects; components hold no string literals. New strings are needed for: the tab
  label (the user's own word, A40); Historial's ordering statement, show-more
  control and empty state; the detail's two date labels, its edited-since phrase,
  its edit action and its not-found state; and the month view's category header,
  count, clear-selection control and empty-category state. No new error code and no
  new validation reason, so `errores` and `razones` are unchanged and
  `copy/es.test.ts:28-42` stays green. Watch `es.test.ts:62-71`: no string may
  contain `save|cancel|delete|loading|error|settings|today|month|search|submit`.
  `requirements: 16.6, 16.10, 17.4, 17.5, 17.11, 18.3, 18.5, 18.10`

### Guarding the parameters (the hole in the existing gate)

`test_contract_conformance.py` compares `(method, path)` pairs only
(`:50-56`). It will catch a new path in either direction, and it will **not**
notice a query parameter that appears, disappears or is renamed. Every parameter
this design adds is therefore unguarded by the repo's strictest test, and the
frontend is built against this document without seeing the backend.

The honest answer is a test. Add to `test_contract_conformance.py` a second
closed set, in the same style and asserted in both directions, over the query
parameters FastAPI publishes for `GET /api/expenses` in `/api/openapi.json`:

```
{"date", "month", "category_id", "order", "before_id", "limit", "offset"}
```

Missing one fails; adding one without amending this contract fails. Pair it with
behavioural tests in `test_expenses_api.py` for the parts a name check cannot see:
the default `order` still produces today's ordering, `order=registered` ignores
`spent_on` entirely, `before_id` never returns the cursor row, and
`next_before_id` is `null` exactly on the last page.
`requirements: none — internal; protects 16.2, 16.7, 16.8, 16.9, 18.2, 18.13 from
silent drift between the two lanes.`

---

## Data model / migration

**No migration. No backfill. No new index.** Migration `0001_init.sql` stays the
only migration and `schema_version` stays 1. Concretely:

- **No new column.** Registration order needs `id` (`0001_init.sql:48`); "when it
  was recorded" needs `created_at` (`:56`); "edited since" needs `updated_at`
  (`:57`); the filter needs `category_id` (`:50`). All four exist on every row,
  including every row written before this feature, which is why A41 holds and
  Historial is correct for historical data with no backfill.
- **No new index — decided, not assumed.** The brief flags that `ix_expenses_spent_on`
  (`:59`) is a composite led by `spent_on` and that nothing indexes `created_at`
  alone. That would matter if registration order were `created_at`-ordered. Under
  KD-19 it is `ORDER BY id DESC`, and `id` is `INTEGER PRIMARY KEY`, i.e. SQLite's
  rowid: the ordering is a backwards traversal of the table itself, `WHERE id < ?`
  is a rowid seek, and no sort step or index exists to add. Adding an index on
  `created_at` would cost a write on every insert to serve a query nobody makes.
- The category filter uses `ix_expenses_category` (`:60`) or `ix_expenses_spent_on`
  (`:59`), whichever SQLite prefers; a composite `(category_id, spent_on)` would
  help only at a data volume this application will not reach — one person's
  spending, one category, one month.
- If a future run ever needs to order by `created_at` (for example to page a merged
  timeline), that run needs the index. Recorded here so the omission is visibly a
  decision.

The seven-line docstring habit applies: `repo/expenses.py`'s new code should name
16.2/16.7/18.2 and KD-19/KD-20, as the module already does for its existing rules.

---

## Frontend structure

### Routes (`App.tsx`)

```
── <FinanzasTabs>                        tabs: Hoy · Este mes · Historial · Análisis
   /finanzas                          → Hoy                        unchanged
   /finanzas/mes[?mes=&categoria=]    → Mes                        CHANGED (KD-24)
   /finanzas/historial                → Historial                  NEW
   /finanzas/analisis                 → Analisis                   unchanged
/finanzas/gasto/nuevo                 → NuevoGasto                 unchanged
/finanzas/gasto/:id                   → GastoDetalle               NEW behaviour (was EditarGasto)
/finanzas/gasto/:id/editar            → EditarGasto                NEW path, existing component
/finanzas/ajustes[...]                                             unchanged
```

`GastoDetalle` and `EditarGasto` sit **outside** `<FinanzasTabs>`, like
`GastoForm` does today (`App.tsx:51-52`), so each builds its own `<Screen>` with a
`FormBar` and `capture={null}` — the frame constraint 36 asks for.

### Navigation state, precisely

Three mechanisms, each doing one job:

1. **Search params on `/finanzas/mes`** (`?mes`, `?categoria`) — the month and the
   selected category. They are in the location, so a history entry carries them and
   any return to that entry restores them. This is the whole of B2 and 18.9.
2. **A history pop for "back"** — `FormBar`'s `back` prop already accepts a number
   and passes it to `navigate` (`Screen.tsx:58-66`), so the detail can close by
   popping. Popping is what restores the *previous entry*, which is the only thing
   that knows the tab and the search params without re-deriving them (17.8).
3. **A router-state hint `from`, threaded row → detail → form** — the originating
   list's path, used for exactly one thing: where to land after deleting from the
   form, since the detail entry behind it is dead (17.9). It is a hint with a
   `/finanzas` fallback and never a data source.

`?categoria` is dropped whenever `?mes` changes (18.7). An unknown or archived
`categoria` renders the empty-category state (18.10) rather than an error, because
the server returns `items: []` for it.

### Components

| Component | Where | Notes |
| --- | --- | --- |
| `ExpenseLedger` | `routes/finanzas/ExpenseLedger.tsx` (moved) | KD-26. One row treatment for three lists (constraint 30). Links to `/finanzas/gasto/:id` with the `from` hint. |
| `Historial` | `routes/finanzas/Historial.tsx` | `useInfiniteQuery`; order statement; show-more; empty state. Reuses `Finanzas.module.css`. |
| `GastoDetalle` | `routes/finanzas/GastoDetalle.tsx` + own CSS module | `useExpense`; `Screen`+`FormBar`; edit action; not-found state. |
| `Mes` | `routes/finanzas/Mes.tsx` (changed) | Search params; tappable `by_category` rows; selected-category panel + list; clear control. |
| `GastoForm` | `routes/finanzas/GastoForm.tsx` (changed) | `editar` mode only: `back` and both success paths point at the detail; delete points at `from`. `nuevo` untouched. |

### CSS and the red allowlist

**No change to `estilos.test.ts:62-74` is required or permitted by this design.**
Nothing new needs `var(--danger…)`: constraint 38 requires the edited-since mark to
be *neutral*, the delete path stays inside `GastoForm` which already uses the
allowlisted `Button.module.css`, and 17.11's not-found state is a plain designed
state, not an alarm. Any new module reaching for red is a design error, not an
allowlist gap. The new modules must also carry no literal colours
(`estilos.test.ts:37-51`) — tokens only.

---

## B1 and B2 — what a test must pin

These are the two places a regression hides, because both are changes to behaviour
that works today.

**B1 — tapping an expense opens the detail, never the form.** Two tests, because
one of them checks the behaviour and the other checks that the behaviour cannot be
undone in a place the first does not look:

1. *Behavioural* (vitest, whole-`<App/>` mount per `test/captura.test.tsx:14-25`):
   from `/finanzas` with a day summary containing one expense, tapping the row
   lands on a screen that shows the amount as text and offers an edit action, and
   contains **no** amount input, no chip row and no save control. Named for the
   criterion: `describe('B1 / 17.1 — tapping an expense opens the detail, not the form')`.
   Repeat the same assertion for a Historial row and a filtered-category row, since
   17.1 names all three surfaces.
2. *Structural* (a source-reading test, in the style of `estilos.test.ts`): no file
   under `routes/finanzas/` other than `GastoDetalle.tsx` contains a link or
   navigation to a `/finanzas/gasto/…/editar` path. This is what stops a list added
   in a later run from quietly re-pointing at the form, which is precisely how B1
   would regress — invisibly, with every other test still green.

**B2 — the viewed month survives navigation.** Three assertions:

1. Mounting at `/finanzas/mes?mes=2026-07` renders July, not the current month —
   i.e. the month is read from the location, not from state.
2. A round trip Mes → expense detail → back leaves the same month heading and the
   same category selected. This is 18.9 stated as a test.
3. Changing month with a category selected drops `?categoria` and renders the full
   breakdown (18.7) — the guard against one month's heading over another month's
   expenses.

Backend regressions worth pinning alongside them: `GET /api/expenses` with no new
parameters returns exactly today's ordering and today's two fields plus a `null`
cursor (nothing that exists changed), and `day_summary`/`month_summary` still work
through the widened `list_expenses` signature (`repo/expenses.py:272`).

---

## Risks / Tradeoffs

**R1 — "Same position in the list" (17.8) has no free implementation.** The app
scrolls inside `<main className={s.scroll}>` (`Screen.tsx:30`), not the document,
so neither the browser's history scroll restoration nor React Router restores it.
KD-25 gets the *list length* back (the pages are cached), which is the larger half;
the *offset* still has to be captured on leave and reapplied on return, after the
cached pages have rendered. This is the single most likely criterion to be quietly
failed, because the screen will look right in every manual test that does not
scroll first. QA should test it scrolled to page three, not at the top.

**R2 — Four tabs at 390 px (constraint 29).** `Hoy · Este mes · Historial ·
Análisis` at 16 px semibold with the current `.tab` padding of 9 px each side and a
10 px gap (`Screen.module.css:103-121`) estimates to roughly 360 px inside a 390 px
viewport — it fits, but with under 30 px of margin, and estimated rather than
measured. If it overflows, the permitted moves are uniform: reduce the `.tabs` gap
and `.tab` padding, or reduce all four font sizes together. Constraint 29 forbids
shrinking one label relative to its neighbours, and constraint 10 forbids dropping
below a 44×44 target. Verify by screenshot (`frontend/tools/shots.mjs`), not by
eye.

**R3 — "Edited since" is true after a save that changed nothing.** `GastoForm`
sends all five fields on every submit (`GastoForm.tsx:165-171`) and the repo
rewrites `updated_at` whenever any settable key is present
(`repo/expenses.py:228-231`), so opening the form and pressing "Guardar cambios"
with no modification marks the expense edited. Accepted deliberately: the
alternative is comparing old and new values server-side, which changes the
semantics of a shipped, tested PATCH (`test_expenses_api.py::test_5_1_…`) for a
cosmetic gain. 17.5 says "has been edited since it was recorded", and the user did
save an edit. Named here so it is not later mistaken for a bug.

**R4 — The filtered category list is capped at 200 rows with no control (KD-21).**
A month in which one category holds more than 200 expenses would show 200 of them
with no affordance to reach the rest, and 18.2 says "every expense of that
category". The cap is the existing one (`api/expenses.py:58`). Bounded by making
18.3's count come from `total_count`, so the figure on screen is never wrong even
where the list is short; and the volume required (≈7 expenses per day in a single
category for a month) is far outside this user's pattern. If it ever bites, the fix
is the `before_id` cursor that already exists on the same endpoint.

**R5 — A new query parameter is invisible to the repo's strictest gate.** Stated in
full under § Guarding the parameters. Until that test exists, a renamed parameter
breaks the frontend at integration time — the exact failure mode the contract exists
to prevent, arriving after both lanes think they are done.

**R6 — Two orderings, two orderings' worth of confusion.** Historial is
registration-ordered and the filtered month list is spent-date-ordered, on purpose
(A37, 18.13). A row component shared between them (KD-26) makes the two lists look
identical, which is what constraint 30 wants and also what makes the difference
invisible. 16.6's on-screen statement of Historial's order is the mitigation, and
it is a criterion rather than a nicety for exactly this reason.

**R7 — Cache invalidation reaches further than before.** Adding `['expenses']` to
`invalidateExpenseViews` means every create, edit and delete now also refetches
every loaded Historial page (TanStack Query refetches all pages of an infinite
query on invalidation). Correct, and cheap against local SQLite, but it is more
work per mutation than today. Acceptable; noted so a slow-feeling save is
diagnosed here rather than hunted elsewhere.

---

## Deferred Decisions

Left to the Implementers, inside the structure above:

1. **Historial's page size.** 30 rows is the intended value — roughly three
   screenfuls at 390×844 with the existing ~60 px row (`Finanzas.module.css:84`) —
   but any value in 20…50 satisfies 16.13 and constraint 32. The contract's cap of
   200 is the only hard bound.
2. **The `ExpenseLedger` variant discriminator** — a prop, three components sharing
   one row, or a render slot. One implementation of the row is the binding part
   (KD-26); its parameterisation is not.
3. **How the scroll offset is captured and restored** (R1) — session storage keyed
   by the router location key, a ref plus a layout effect, or otherwise. The
   behaviour is required; the mechanism is not specified.
4. **Push vs replace when switching between categories** in the month view. 18.5's
   on-screen clear control must exist regardless of history behaviour, and 18.9
   must hold; whether switching category pushes an entry is otherwise free.
5. **The detail screen's title text and layout** — constraint 36 fixes the frame
   and constraints 35/37/38 fix the content rules; the arrangement inside is the
   frontend's craft, judged at mockup approval against the "small receipt" Feel &
   Tone.
6. **The exact Spanish wording** of every new string. The design names which
   strings must exist and where they live; the words are the frontend's, carried
   from the mockups, within `es.test.ts`'s English-word ban and the app's stated
   tone (`es.ts:6-7`).
7. **Query-key shape** under `['expenses', …]` — only the prefix matters, because
   invalidation keys off it.

### Open items resolved before finalizing (not guessed)

- **Does registration order need `created_at` and therefore an index?** Resolved
  against the schema, not assumed: `id` is `INTEGER PRIMARY KEY AUTOINCREMENT`
  (`0001_init.sql:48`), so it is both a total registration order and the rowid.
  Ordering on it removes the index question entirely (KD-19, § Data model).
- **Is `created_at` second-resolution, making ties likely?** The brief says so; the
  code says otherwise — `clock.now_iso()` emits milliseconds and documents why
  (`clock.py:44-51`). Resolved by reading the source. It changes nothing, because
  KD-19 does not order on the timestamp at all.
- **Where does `updated_at` come from, and does PATCH maintain it?** Verified: yes,
  `repo/expenses.py:228-231`, and `create` writes one timestamp into both columns
  (`:148,162-163`), so `updated_at !== created_at` is a sound edited-since test. The
  one wrinkle is R3.
- **Does the detail need new data?** No. `GET /api/expenses/{expense_id}` already
  returns every field 17.2–17.5 needs and omits the one 17.10 forbids.
- **Constraint 34 ("nothing else operable") versus constraints 9/11 (capture bar
  and bottom nav from every screen).** Reconciled rather than escalated: the capture
  bar and bottom nav belong to `Screen`, the frame every tabbed route inherits
  (`Screen.tsx:14-35`, `App.tsx:76-98`), and constraint 34 governs the screen's own
  content — the same reading under which Hoy and Mes already comply. Stated so QA
  does not read it as a violation.

Nothing remains open. No question needed escalation to the human in this run.
