# Autonom-OS — Conventions Pack

The rules a contributor must not violate. Each rule is labelled:

- **[ENFORCED]** — a test or build step fails if you break it. Cited by
  `path:line`. Treat as a hard rule.
- **[HABIT]** — the codebase does this consistently but nothing checks it.
  Match it anyway; a reviewer will notice.

---

## Language & Tooling

Languages in the repo (index `summary.languages`): Python 10 044 LOC (61 files),
TypeScript 5 204 LOC (38 files), CSS 2 005 LOC (17 files), JavaScript 1 600 LOC
(tools + service worker), SQL 106 LOC (one migration). The `other`/HTML bulk is
`mockups/` and PNG screenshots, not application code.

### Verified commands

All four were run against this working tree and passed.

| Purpose | Command | Result observed |
| --- | --- | --- |
| Backend tests | `cd backend && uv run --python 3.12 --extra dev pytest -q` | `261 passed, 1 warning in 11.49s` |
| Frontend tests | `cd frontend && npm run test` | `6 files, 41 passed` |
| Frontend build + typecheck | `cd frontend && npm run build` | `✓ built in 1.61s` (`tsc --noEmit && vite build`, `package.json:8`) |
| Single test file | `npm run test -- src/test/estilos.test.ts` / `pytest -q tests/test_contract_conformance.py` | both pass |

**Correction worth carrying:** `uv run --python 3.12 pytest -q` (without
`--extra dev`) **fails** with `Failed to spawn: pytest` — pytest lives in the
optional `dev` extra (`backend/pyproject.toml:15-18`). `backend/.venv` exists but
has no pytest installed either. Use `--extra dev`.

Backend pytest config is in `pyproject.toml:26-30`: `testpaths=["tests"]`,
`asyncio_mode="auto"` (so `async def test_…` needs no decorator),
`DeprecationWarning` filtered.

Runtime: Python pinned `==3.12.*` (`pyproject.toml:4`). Dev server for the SPA is
`npm run dev`; the API serves the built SPA in production
(`backend/autonomos/main.py:118-143`). The API port is **8001**, not 8000
(`ops/README-setup.md:25-33`); screenshot tooling defaults to
`http://127.0.0.1:8001` (`frontend/tools/shots.mjs:28`).

---

## Naming & Structure

### Backend

- **[HABIT]** Package layout is by *layer*, not by feature: `api/`, `repo/`,
  `db/`, `parsing/`, `providers/`, `insights/`. A new expense capability adds to
  `repo/expenses.py` and `api/expenses.py`, not to a new `expenses/` package.
- **[ENFORCED]** Routers contain no business logic — validation and SQL live in
  `repo/`. Not directly asserted, but the contract-conformance and API tests
  exercise the repo through the router; the stated rule is `api/__init__.py:1`.
  *(The "no logic" part is [HABIT]; what is enforced is the endpoint set.)*
- **[HABIT]** Every module opens with a docstring naming the requirement /
  key-decision it implements, e.g. `repo/expenses.py:1-6`, `api/lookups.py:1-6`,
  `errors.py:1-6`. Inline comments explain *why*, citing criteria (`2.7`, `4.3`)
  or decisions (`KD-8`, `QA D5`). Follow this; the codebase is dense with it.
- **[HABIT]** `from __future__ import annotations` is the first import in every
  module (e.g. `repo/expenses.py:8`, `api/expenses.py:3`).
- **[HABIT]** Private helpers are `_leading_underscore` (`_validate_amount`,
  `_validate_fk`, `_SELECT`). Public repo functions are bare verbs: `create`,
  `get`, `update`, `delete`, `list_expenses`.
- **[HABIT]** Repo functions take `conn: sqlite3.Connection` as the first
  positional argument; routers obtain it with `get_db()`
  (`api/expenses.py:51`). Keyword-only filters after `*`
  (`repo/expenses.py:242-249`).
- **[HABIT]** Row→dict conversion has one named function per table
  (`row_to_expense` `repo/expenses.py:28`, `_row_to_item`
  `repo/lookup.py:39`), and a module-level `_SELECT` constant holds the join
  (`repo/expenses.py:18-25`).
- **[HABIT]** Migrations are `db/migrations/NNNN_name.sql`, numbered, applied in
  filename order, version recorded in `meta` (`db/connection.py:88-119`). Never
  edit an applied migration — add the next number. Migrations must be idempotent
  in effect; `test_durability_and_deadline.py::test_migrations_are_idempotent`
  covers the runner. **[ENFORCED]**

### Frontend

- **[HABIT]** Layout is by *route module*: `src/routes/<modulo>/<Pantalla>.tsx`
  with a sibling `<Pantalla>.module.css`. Shared primitives live in
  `components/ui/`, the frame in `components/shell/`.
- **[HABIT]** Component files and exported components are **PascalCase and
  Spanish** for screens (`Hoy.tsx`, `Mes.tsx`, `GastoForm.tsx`, `Ajustes.tsx`,
  `Analisis.tsx`, `SinServidor.tsx`, `Entrada.tsx`), **English** for generic
  primitives (`Button.tsx`, `Chip.tsx`, `Sheet.tsx`, `Panel.tsx`).
- **[HABIT]** Route *segments* are Spanish (`/finanzas/gasto/nuevo`) — rationale
  at `design.md:854-856`.
- **[HABIT]** CSS Modules are imported as `s`:
  `import s from './Finanzas.module.css'` (`Hoy.tsx:8`), used as `className={s.row}`.
  Shared modules are re-exported with an explicit name
  (`export const panelStyles = s`, `Panel.tsx:44`; `screenStyles`,
  `Screen.tsx:144`).
- **[HABIT]** Query hooks are `useThing` / `useCreateThing` / `useUpdateThing` /
  `useRemoveThing`, all in `api/queries.ts`, with the query key registered in the
  `keys` object first (`api/queries.ts:24-36`). Components never call `fetch` or
  `api.*` directly — they call a hook.
- **[HABIT]** Multi-mode screens are one component with a `mode` prop plus thin
  named exports, e.g. `NuevoGasto`/`EditarGasto` → `GastoForm`
  (`GastoForm.tsx:51-58`), `EntradaLeer`/`EntradaEscribir`.

---

## Spanish Copy Rules

- **[ENFORCED]** Every code in the closed error set has Spanish copy, and
  `errores` contains **nothing outside** that set —
  `frontend/src/copy/es.test.ts:28-42` (both directions), with the fallback
  asserted at `:39-41`.
- **[ENFORCED]** No obviously-English word may appear in any static copy string:
  `es.test.ts:62-71` scans every string in every exported object against
  `/\b(save|cancel|delete|loading|error|settings|today|month|search|submit)\b/i`.
- **[ENFORCED]** Accents, `ñ` and opening `¿`/`¡` must survive —
  `es.test.ts:73-77`.
- **[HABIT, load-bearing]** *All* user-visible strings live in
  `frontend/src/copy/es.ts`; components hold no string literals
  (`es.ts:1-8`). Add a new screen's copy as a new `export const <area> = {…} as
  const` object. Pluralisation is a function on that object, e.g.
  `hoy.gastosContados` (`es.ts:43-44`), `mes.gastosContados` (`es.ts:53`).
  *Not mechanically enforced — `aria-label="Cerrar"` at `Screen.tsx:65` and
  `aria-label="Secciones"` at `Screen.tsx:127` are existing exceptions.*
- **[HABIT]** Backend `message` strings are developer English and are **never
  displayed** (`errors.py:1-5`, `api/client.ts:19-21`). The frontend maps `code`
  via `errorEnEspanol` and `fields[].reason` via `razonEnEspanol`
  (`es.ts:346-353`). A new validation reason needs an entry in `razones`
  (`es.ts:307-335`) or it silently degrades to the generic
  `errores.validation`.
- **[HABIT]** Tone, stated at `es.ts:6-7`: "patient, not apologetic. No 'still
  working', no apology, no celebration." Copy is carried from the approved
  mockups in `mockups/`.

---

## Money, Dates and Time

- **[HABIT, single-source]** One peso formatter for the whole app:
  `formatCOP` → `$14.000` — dot thousands, no cents, no space
  (`frontend/src/format/money.ts:7-9`). One input parser, `parseAmount`, which
  accepts `14.000` / `14000` / `14 000` incl. NBSP/thin space and returns `null`
  for empty (`money.ts:27-32`); `formatAmountInput` regroups while typing
  (`money.ts:35-39`). Covered by `frontend/src/format/money.test.ts`.
  **Never** use `Intl.NumberFormat` ad hoc.
- **[HABIT]** Amounts are **integers of COP** end to end: `amount_cop INTEGER`
  (`0001_init.sql:49`), `amount_cop: int` (`api/models.py:99`). A non-integer is
  `not_an_integer` (`repo/expenses.py:55-56`). The storage ceiling is
  `2**63 - 1` and is enforced as a clean validation error, not a 500
  (`repo/expenses.py:43-63`) — this was a QA fix (D5).
- **[HABIT]** Dates are rendered only by `frontend/src/format/dates.ts`:
  `longDate` → `miércoles 5 de agosto` (`:37`), `shortDate` (`:43`),
  `monthLabel` → `agosto 2026` (`:49`), `clockTime` → `21:14` (`:61`),
  `stamp` (`:72`). Month/day arithmetic is string arithmetic, never `Date` in
  local time (`:77-90`). Covered by `format/dates.test.ts`.
- **[HABIT, architectural]** The **server is authoritative for "today" and "this
  month."** The frontend derives them from `health.server_time`
  (`Mes.tsx:30-32`, `GastoForm.tsx:66`, `Diario.tsx:48-49`), never from the
  device clock (`format/dates.ts:1-6`). Backend boundaries come only from
  `backend/autonomos/clock.py`.
- **[HABIT]** Wire formats: dates `YYYY-MM-DD`, months `YYYY-MM`, timestamps
  ISO-8601 **with offset** (`design.md:931-933`).

---

## Error Handling

### Backend

- **[ENFORCED]** Error codes come from a closed frozenset; `ApiError.__init__`
  asserts membership (`errors.py:64`). Validation reasons likewise
  (`errors.py:86`). The envelope shape and the closed code set are asserted by
  `backend/tests/test_misc_api.py::test_error_envelope_shape_and_closed_code_set`.
- **[HABIT]** Raise a typed error, never return one: `ValidationError(fields)`,
  `NotFound(what)`, `Conflict(msg)`, `InUse(count)` (`errors.py:82-111`).
  Handlers registered once in `main.py:109-112` turn them into JSON.
- **[HABIT]** **Collect all field errors before raising.** Repo validators append
  to a shared `errors: list[dict]` and raise once
  (`repo/expenses.py:126-146`, `:182-227`) so the form can mark every offending
  field at once.
- **[HABIT]** `field_error(field, reason)` is the only way to build a field entry
  (`errors.py:90-91`). Machine values go in `details`, never inside `reason`
  (`errors.py:1-5`, `design.md:944-947`).
- **[HABIT]** Framework errors are never leaked: pydantic types are mapped to
  contract reasons in `_REASON_BY_PYDANTIC_TYPE` (`main.py:29-39`), 404/405
  become `not_found` (`main.py:92-94`), and any unhandled exception becomes
  `internal` (`errors.py:118-120`).
- **[HABIT]** Endpoints that must never fail the caller return a null-shaped 200
  instead of an error — see `suggest_category` (`api/expenses.py:80-147`), which
  returns `{"category_id": null, "source": "none"}` on timeout, arbiter refusal
  or provider exception.

### Frontend

- **[HABIT]** Two error classes only: `ApiError` (envelope-carrying,
  `api/client.ts:11-31`) and `UnreachableError` (transport,
  `:34-40`). Every mutation `onError` branches on those two
  (`GastoForm.tsx:173-184` is the canonical shape):
  1. `UnreachableError` → a `Banner` with `tone="alarm"` and the user's input
     preserved on screen (`GastoForm.tsx:216-222`);
  2. `ApiError` with `code === 'validation'` → map each
     `fields[].reason` through `razonEnEspanol` into per-field state;
  3. anything else → a generic server-failure banner.
- **[HABIT]** `ApiError.fieldReason(field)` is the accessor for a single reason
  (`api/client.ts:28-30`, used at `GastoForm.tsx:480`).
- **[HABIT]** A `204` response returns `undefined` rather than throwing on empty
  JSON (`api/client.ts:65`).
- **[HABIT]** Loading state is `query.isPending` → a `.skeleton` paragraph with
  `common.cargando` (`Hoy.tsx:17`, `Mes.tsx:36`, `Diario.tsx:16`). Empty state
  is an `<EmptyState title body/>`, never a zeroed chart (`Mes.tsx:74-75`,
  `Hoy.tsx:31-33`).

---

## Testing

### Backend — `backend/tests/`, pytest

- **[HABIT]** One file per API area: `test_expenses_api.py`,
  `test_lookups_api.py`, `test_journal_api.py`, `test_insights_api.py`,
  `test_voice_api.py`, `test_misc_api.py`, plus cross-cutting
  `test_contract_conformance.py`, `test_durability_and_deadline.py`,
  `test_arbiter.py`, `test_parsing.py`, `test_scheduler_and_summaries.py`,
  `test_insights_router_and_guard.py`.
- **[HABIT]** Test names are **sentences naming the acceptance criterion**:
  `test_2_1_saved_expense_is_dated_today_and_appears_in_the_day_total`,
  `test_4_1_list_is_newest_first`, `test_d5_an_absurd_amount_on_patch_is_also_rejected`
  (`d5` = QA defect 5). A new test for criterion X.Y is named
  `test_X_Y_<what is true>`.
- **[HABIT]** Fixtures come from `tests/conftest.py`: `client` (FastAPI
  `TestClient` over a freshly created app, `:145-155`), `db` (`:138-142`),
  `sidecars`/`fake_llm`/`fake_stt` (`:118-135`), and an autouse `isolated_env`
  that points `DB_PATH` at `tmp_path`, disables the scheduler, pins `APP_TZ` and
  resets every singleton before and after (`:100-115`). **Never mock the
  database** — every test runs against a real temporary SQLite file.
- **[HABIT]** AI is faked at the *provider interface* only (`FakeLLM`/`FakeSTT`,
  `conftest.py:30-97`), installed via `providers.set_providers`.
- **[HABIT]** Tests assert on the HTTP envelope, e.g.
  `body["error"]["code"] == "validation"` and the `fields[].reason` values —
  they do not assert on `message`.
- **[HABIT]** Local helper builders sit at the top of the file
  (`make_expense` in `test_expenses_api.py`, `seed_expense` in
  `test_insights_api.py`).

### Frontend — vitest + Testing Library

- **[HABIT]** Two placements, both used deliberately:
  *co-located* unit tests next to pure modules (`src/format/money.test.ts`,
  `src/format/dates.test.ts`, `src/copy/es.test.ts`), and *cross-cutting*
  behaviour tests in `src/test/` (`captura.test.tsx`, `origenes.test.tsx`,
  `estilos.test.ts`).
- **[HABIT]** Component tests mount the **whole `<App/>`** inside
  `QueryClientProvider` + `MemoryRouter` with an initial route, via a local
  `mount()` helper (`test/captura.test.tsx:14-25`). Retries are disabled in the
  test QueryClient (`:16`).
- **[HABIT]** The network is stubbed by `installApi()`
  (`src/test/server.ts:14-94`), which stubs global `fetch` with
  **contract-shaped payloads** and records `calls` for assertions. Add new routes
  via its `overrides` argument (`server.ts:14`, `:66`) rather than hand-rolling a
  mock. Anything `installApi` cannot produce is something the UI must not depend
  on (`server.ts:3-7`).
- **[HABIT]** Queries are found by **accessible role and Spanish label**
  (`getByRole('radio', {name: 'Transporte'})`,
  `findByLabelText('Monto')` — `captura.test.tsx:41-54`), never by test id.
- **[HABIT]** `describe` blocks are titled with the criterion:
  `describe('criterion 2.8 — a complete expense in four interactions')`.
- **[HABIT]** `afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks() })`
  (`captura.test.tsx:9-12`).
- Global setup: `src/test/setup.ts` (jest-dom).

---

## CSS / Design-Token Discipline

`frontend/src/test/estilos.test.ts` is a source-reading test — it is the hard
enforcer for the visual Design Constraints in
`factory/runs/01-greenfield/pm/visual-direction.md:38-118`.

- **[ENFORCED]** **No literal colour outside `styles/tokens.css`.** Any
  `#rrggbb` other than `#fff`/`#ffffff` fails, and any `rgb()/hsl()/rgba()`
  outside `Sheet.module.css` fails — `estilos.test.ts:37-51`. Use
  `var(--token)`.
- **[ENFORCED]** The palette lives only in `styles/tokens.css`, which must keep
  `--violet: #5a2fce`, `--danger: #c0182b` and the ten-step ramp `--t1…--t10` —
  `estilos.test.ts:53-59`. Current tokens: `tokens.css:10-54` (surfaces `--paper
  --paper-sunk --rule --rule-strong`; ink `--ink --ink-soft --ink-ghost`; violet
  `--violet --violet-deep --violet-line --violet-wash --violet-wash2`; danger
  family; ramp; spacing `--pad --pad-diario --r-sheet`).
- **[ENFORCED]** **`var(--danger…)` may appear only in
  `Button.module.css`, `Form.module.css`, `Panel.module.css`** — red is reserved
  for destructive paths, validation errors and the failed-save banner
  (`estilos.test.ts:62-74`). A new module that wants red will fail the suite.
- **[ENFORCED]** No `@media (prefers-color-scheme: …)` anywhere; `tokens.css`
  must declare `color-scheme: light` — `estilos.test.ts:25-34`.
- **[ENFORCED]** The "needs input" mark is one visual region declared twice
  (`.missing` in `Chip.module.css`, `.needsInput` in `Form.module.css`) and both
  must keep `1.5px dashed var(--violet-line)`, `border-radius: 16px`,
  `padding: 10px`, `background: var(--violet-wash)` —
  `estilos.test.ts:76-94`.
- **[ENFORCED]** Fonts are self-hosted Lato from `src/assets/fonts/`, and
  `base.css` may contain no `http(s)://` — `estilos.test.ts:96-103`.
- **[ENFORCED]** Service worker: `/api/*` is NetworkOnly and checked before any
  `caches.match`; no sync/indexedDB/localStorage write queue —
  `estilos.test.ts:105-123`.
- **[HABIT]** No UI framework and no chart library (`package.json:12-17`);
  proportional bars are divs with an inline `width: %` and a ramp token
  (`Mes.tsx:87-96`).
- **[HABIT]** Non-colour constraints that the style test does **not** check —
  44×44 px touch targets, 390×844 viewport, one typeface, designed empty states,
  destructive-action confirmation — are held by review/QA and the screenshot
  audit (`frontend/tools/shots.mjs`, `frontend/tools/audit.mjs`). Meet them
  anyway.

---

## Contract Conformance (mandatory for any API change)

`backend/tests/test_contract_conformance.py` is the strictest gate in the repo.

- **[ENFORCED]** `CONTRACT_PATHS` (`:16-47`) is a **closed set of 30
  `(METHOD, path)` pairs** compared against the live OpenAPI schema in **both**
  directions: `test_every_contract_endpoint_exists` (`:59-61`) and
  `test_no_endpoint_exists_beyond_the_contract` (`:64-66`). Adding an endpoint
  without adding it here fails; adding it here without implementing it also
  fails.
- Path templates must match FastAPI's own parameter names exactly — e.g.
  `("PATCH", "/api/expenses/{expense_id}")` because the handler parameter is
  `expense_id` (`api/expenses.py:156`).
- Adding a **query parameter** to an existing path does **not** change the
  `(method, path)` set and so does not trip this test *(inferred from how the set
  is derived at `:50-56`)*. It still needs its contract entry updated.
- **[HABIT, authoritative]** The prose Interface Contract lives at
  `factory/runs/01-greenfield/architect/design.md:929-1253`. `api/models.py:5-6`
  states plainly: "Where this file and the design document disagree, the design
  document wins." A new endpoint should land in three places: the design
  contract, `CONTRACT_PATHS`, and `api/models.py` request/response models.
- **[ENFORCED]** **No vendor name outside `providers/`.** Every `.py` under
  `autonomos/` except `config.py` is scanned for `ollama`, `whisper`, `qwen`,
  `llama`, `ggml`, `gguf` in non-comment, non-docstring code
  (`test_contract_conformance.py:69-97`).
- **[ENFORCED]** Related closed-set gates worth knowing:
  `test_misc_api.py::test_kd16_there_is_no_gym_endpoint`,
  `::test_no_csv_export_endpoints_exist`,
  `::test_unknown_api_path_returns_the_envelope`, and
  `test_expenses_api.py::test_source_is_never_returned`.
- **[ENFORCED]** The frontend mirror: `copy/es.test.ts:35-37` asserts the
  Spanish error map equals the contract's code set exactly. A new backend error
  code therefore requires a matching entry in `copy/es.ts` *and* in the
  `CONTRACT_CODES` list at `es.test.ts:9-26`.

---

## Notable Patterns

- **Repo-owns-validation.** The router is a five-line pass-through
  (`api/expenses.py:49-51`, `:150-157`); all rules live in `repo/`. Put new
  validation in the repo so both the API and any internal caller get it.
- **PATCH is presence-based, not null-based.** `model_dump(exclude_unset=True)`
  (`api/expenses.py:157`) plus `if "field" in payload` in the repo
  (`repo/expenses.py:186-224`). Omitting a key leaves it untouched; sending
  `null` for a required field is a `required` error (`:212-214`).
- **Archived lookups stay resolvable.** Nothing is hard-deleted; archived
  categories still appear in month totals and stay editable on old expenses via
  `allow_archived` (`repo/expenses.py:67-99`). Any new expense query must keep
  joining `categories`/`payment_methods` for the historical name.
- **`source` never crosses the wire** on expenses or journal entries
  (`repo/expenses.py:1-6`). Do not add it to a response model.
- **One query-key registry + one invalidation policy.** New expense-touching
  mutations must call `invalidateExpenseViews(qc)` (`api/queries.ts:42-45,
  171,180,189`) so day and month totals refresh without a manual reload.
- **One inference slot.** Any new call into `providers/` must acquire an arbiter
  lease and release it in a `finally` (`api/expenses.py:108-135`).
- **`Screen` is the frame.** Every screen renders exactly one `<Screen>` with a
  `header`, a `capture` module (or `null`) and an `active` bottom-nav key
  (`Screen.tsx:14-35`); tabbed routes get theirs from the shell's `<Outlet/>`
  (`App.tsx:76-98`). Never re-implement the bottom nav.
- **Destructive actions open a `Sheet`, they do not act.** `GastoForm.tsx:399`
  sets `confirmDelete`; the sheet at `:408-444` carries the subject being deleted
  and the actual mutation.
- **Voice-captured records are indistinguishable from typed ones** in every list
  and detail view — no badge, no icon, no field (`Hoy.tsx:43-47`,
  `Diario.tsx:99-102`).

---

## Verification Gates Before Committing

No CI config, git hook, linter config or `Makefile` was found in the repo
(searched the repo root, `backend/`, `frontend/`). There is no ESLint or Ruff
configuration — the `eslint-disable` comment at `GastoForm.tsx:128` is vestigial.
So the gates are the commands themselves:

1. `cd backend && uv run --python 3.12 --extra dev pytest -q` → expect **261
   passed** (baseline at this commit).
2. `cd frontend && npm run test` → expect **41 passed / 6 files**.
3. `cd frontend && npm run build` → runs `tsc --noEmit` first, so this is the
   typecheck gate too.
4. Visual changes: `npm run shots` (`frontend/tools/shots.mjs`, needs the app
   running at `http://127.0.0.1:8001`) regenerates
   `frontend/tools/shots/*.png` and `audit.json`. Chromium is present on this
   host; Playwright is not (`factory/state.json` → `environment_verified`).

`.impeccable/config.json` holds a design-detector allowlist (Lato is an
acknowledged intentional font choice) — informational, not a gate.

---

## Built From

- Index: `factory/context/index.json`, `generated_at` **2026-08-10T18:38:00Z**.
- Commit: **418d7b3da081d4871d654a6b91615c33d0d53bcd** (`main`).
- `git.dirty: true` at index time, confined to `factory/` bookkeeping; no
  `backend/` or `frontend/` file was modified.
- Command results quoted above were observed by running them against this
  working tree on 2026-08-10.
