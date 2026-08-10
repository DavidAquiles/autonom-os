# Autonom-OS — Architecture Pack

Context pack for the AI Software Factory. Every claim below is grounded in a file
read at the commit named in **Built From**. Citations are `path:line`. Anything
marked *(inferred)* was not observed directly.

---

## Overview

Autonom-OS is a single-user, self-hosted "personal life OS" that runs on the
user's own PC and is reached from his phone over Tailscale/LAN. One FastAPI
process (`backend/autonomos/main.py:146`) serves both the JSON API under `/api`
and the built React SPA from the same origin (`main.py:118-143`), backed by one
SQLite file in WAL mode (`backend/autonomos/db/connection.py:26-34`). It records
**expenses** (Colombian pesos, integer, no cents) and **journal entries**, both
capturable by typing or by voice, and produces **insights** (LLM-phrased,
SQL-computed) via two loopback AI sidecars behind provider interfaces.

The whole UI is Spanish (`frontend/src/copy/es.ts`), light-mode only, phone-first.

---

## Process Topology

```
phone browser ──HTTPS──> uvicorn (1 worker) ──> SQLite  data/autonomos.db (WAL)
                          ├ /api/*   FastAPI routers
                          ├ /*       static SPA (frontend/dist)
                          ├ Scheduler task (in-process)
                          └ InferenceArbiter ──> Ollama 127.0.0.1:11434
                                             └─> whisper-server 127.0.0.1:8081
```

Source: `main.py:100-116` (app assembly), `main.py:49-68` (lifespan starts
scheduler), `factory/runs/01-greenfield/architect/design.md:772-803`.

**Exactly one uvicorn worker** — the scheduler and the arbiter are in-process
singletons, so two workers means two arbiters (`main.py:1-5`).

The API listens on **8001**, not 8000 — port 8000 on this machine belongs to
another project (`ops/README-setup.md:25-33`).

---

## Module Map — Backend (`backend/autonomos/`)

Ordered by how much everything else depends on it.

| Module | Responsibility | Key files |
| --- | --- | --- |
| `errors.py` | The error envelope and the **closed** error-code + validation-reason sets. Imported by every router and repo. | `errors.py:16-49` sets, `:52-111` exception classes, `:114-120` handlers |
| `db/` | Per-thread SQLite connection, PRAGMAs, numbered migration runner, seed. | `db/connection.py:26-47`, `:100-130`; `db/migrations/0001_init.sql`; `db/seed.py` |
| `repo/` | All SQL and all business validation. Routers hold none. | `repo/expenses.py`, `repo/journal.py`, `repo/lookup.py`, `repo/summaries.py`, `repo/jobs.py` |
| `api/` | FastAPI routers + pydantic wire models. "Contains no business logic" (`api/__init__.py:1`). | `api/__init__.py` (router tree), `api/models.py`, `api/expenses.py`, `api/lookups.py`, `api/summary.py`, `api/journal.py`, `api/voice.py`, `api/insights.py`, `api/health.py`, `api/export.py` |
| `clock.py` | The **only** place a calendar day or month boundary is computed, in `APP_TZ`. | `clock.py` (`today_str`, `current_month`, `month_bounds`, `parse_date`, `is_valid_month`) |
| `config.py` | Env-var settings singleton (`get_settings`), origins, timeouts. | `config.py:1-236` |
| `parsing/` | Spanish numeral grammar, amount extraction, alias matching. Pure functions, no I/O, no model. | `parsing/numerals.py`, `parsing/extractor.py`, `parsing/aliases.py`, `parsing/text.py` |
| `providers/` | `LLMProvider` / `TranscriptionProvider` interfaces + OpenAI-compatible and whisper.cpp HTTP adapters. **The only place vendor names may appear.** | `providers/base.py`, `providers/openai_compatible.py`, `providers/whispercpp_http.py` |
| `arbiter.py` | One inference slot across both sidecars; priority ordering transcription > question > category-assist; quiet period; preemption. | `arbiter.py:1-247` |
| `insights/` | Question router, fact builder (SQL), prompt builder, NumericGuard, job runner. | `insights/router.py`, `facts.py`, `prompts.py`, `guard.py`, `runner.py` |
| `scheduler.py` | Boot catch-up scan, 15-min tick, monthly summary enqueue, nightly DB snapshot. | `scheduler.py:1-174` |

Entrypoints (from the index): `backend/autonomos/main.py` (ASGI app),
`backend/autonomos/serve.py` (uvicorn launcher), plus two dev tools
`backend/tools/grounding_check.py`, `backend/tools/live_check.py`.

## Module Map — Frontend (`frontend/src/`)

| Module | Responsibility | Key files |
| --- | --- | --- |
| `copy/es.ts` | **Every** user-visible string, plus the error-code→Spanish map. Components hold no string literals. | `copy/es.ts:1-353` |
| `api/client.ts` | `fetch` wrapper; relative `/api` base only; throws `ApiError` (envelope) or `UnreachableError`. | `api/client.ts:8`, `:11-31`, `:34-40`, `:50-82`, `:95-100` (`qs`) |
| `api/queries.ts` | Every TanStack Query hook and mutation + the query-key registry and invalidation policy. | `api/queries.ts:24-36` keys, `:42-45` invalidation |
| `api/types.ts` | TS mirrors of the Interface Contract wire shapes. | `api/types.ts:1-198` |
| `components/shell/Screen.tsx` | The app frame: `Screen`, `AppBar`, `FormBar`, `Tabs`, capture bar, bottom nav. | `Screen.tsx:14-35`, `:58-73`, `:75-90`, `:98-118`, `:120-142` |
| `components/ui/` | Primitives: `Button`, `Chip`/`ChipRow`/`Tag`, `Field`/`FieldError`/`Hint`/`Note`/`TextInput`/`AmountInput`, `Panel` (`Banner`, `EmptyState`, `SectionLabel`), `Sheet`, `Tally`, `Icon`. Each paired with a `*.module.css`. | `components/ui/Panel.tsx:30-42` |
| `routes/` | One directory per module: `finanzas/`, `diario/`, plus `Gimnasio.tsx`, `SinServidor.tsx`. | see route tree below |
| `format/` | The single peso formatter/parser and the single date renderer. | `format/money.ts:7-39`, `format/dates.ts:37-106` |
| `state/origin.ts` | Remembers the *other* origin learned from `/api/health` for the offline screen. | `state/origin.ts` |
| `voice/` | `VoiceProvider` context, the full-screen `VoiceScreen`, browser WAV encoding. | `voice/VoiceContext.tsx`, `voice/VoiceScreen.tsx`, `voice/wav.ts` |
| `styles/` | `tokens.css` (the entire palette) and `base.css` (reset, self-hosted Lato). | `styles/tokens.css:10-54` |
| `sw/sw-template.js` | Service worker: caches the shell, `/api/*` is NetworkOnly, no write queue. | enforced by `test/estilos.test.ts:105-123` |
| `test/` | Cross-cutting tests + the contract-shaped fetch stub. | `test/server.ts:14-94`, `test/setup.ts` |

`frontend/tools/` holds the screenshot/audit harness driven over CDP
(`tools/shots.mjs:1-30`), a seeder (`tools/seed.mjs`) and an e2e helper.

---

## Layering & Data Flow

### Write path (create an expense)

1. `GastoForm` submit handler validates locally first and maps each offending
   field to Spanish before any request (`routes/finanzas/GastoForm.tsx:146-163`).
2. `useCreateExpense` → `api.post('/expenses', input)`
   (`api/queries.ts:167-173` → `api/client.ts:86`).
3. Router `create_expense` hands the pydantic dump straight to the repo
   (`api/expenses.py:49-51`) — no logic in the router.
4. `repo.expenses.create` validates every field, collecting *all* errors, then
   `INSERT` and re-`get` the joined row (`repo/expenses.py:126-166`).
5. Any `ApiError` is turned into the envelope by `api_error_handler`
   (`errors.py:114-115`, registered at `main.py:109`).
6. On success the mutation invalidates `['summary']` and `['expense']`
   (`api/queries.ts:42-45`), which is how "totals update without a manual
   refresh" holds.
7. Client-side, a non-2xx becomes `ApiError` carrying `code` + `fields`
   (`api/client.ts:74-80`); the form maps `fields[].reason` through
   `razonEnEspanol` (`GastoForm.tsx:176-183`).

### Read path (today's screen)

`Hoy` → `useDaySummary()` → `GET /api/summary/day` → `api/summary.py:21-26` →
`repo.expenses.day_summary` (`repo/expenses.py:271-279`) → `list_expenses` →
joined rows including `category_name`/`payment_method_name`
(`repo/expenses.py:18-25`). The component renders with `formatCOP` and
`longDate`/`clockTime` only (`routes/finanzas/Hoy.tsx:20-67`).

### The seam between lanes

`frontend/dist` is the only integration point; the backend mounts it via the
`FRONTEND_DIST` env var (`main.py:118-126`,
`design.md:815-816`). Neither lane imports the other's source. The **Interface
Contract** in `design.md:929-1253` is the shared truth, and it is mechanically
enforced in both directions (see *Contract conformance*, below).

### Cross-cutting invariants observed

- **The server owns "today" and "this month."** `clock.py` computes every
  boundary; the frontend reads `health.server_time` instead of the device clock
  (`routes/finanzas/Mes.tsx:30-32`, `GastoForm.tsx:66`, `format/dates.ts:1-6`).
- **`source` is stored and never returned.** `expenses.source` exists in the
  schema (`0001_init.sql:54`) but is absent from `_SELECT`
  (`repo/expenses.py:18-25`) and from the `Expense` model (`api/models.py:97-108`).
- **All AI calls go through the arbiter.** e.g. `api/expenses.py:108-135`.
- **Nothing is hard-deleted by the system.** Categories/methods archive
  (`repo/lookup.py:1-6`); expenses and entries go only by explicit user action.

---

## Persistence Schema

Single migration file today: `backend/autonomos/db/migrations/0001_init.sql`
(106 lines, schema_version 1). Migrations are numbered `NNNN_name.sql`, applied
in order, version tracked in `meta` (`db/connection.py:88-119`); the runner is
idempotent and re-run on every `get_db()` first use.

Tables: `meta`, `categories`, `payment_methods`, `category_aliases`,
`payment_method_aliases`, `expenses`, `journal_entries`, `summaries`,
`insight_jobs`.

### `expenses` (`0001_init.sql:47-61`) — read this closely

```sql
id                INTEGER PRIMARY KEY AUTOINCREMENT   -- :48
amount_cop        INTEGER NOT NULL CHECK (amount_cop > 0)  -- :49
category_id       INTEGER NOT NULL REFERENCES categories(id)        -- :50
payment_method_id INTEGER NOT NULL REFERENCES payment_methods(id)   -- :51
spent_on          TEXT NOT NULL   -- YYYY-MM-DD, local APP_TZ       -- :52
description       TEXT                                              -- :53
source            TEXT NOT NULL DEFAULT 'manual' CHECK (…)          -- :54-55
created_at        TEXT NOT NULL                                     -- :56
updated_at        TEXT NOT NULL                                     -- :57
```

Indexes: `ix_expenses_spent_on (spent_on DESC, created_at DESC)` `:59`,
`ix_expenses_category (category_id)` `:60`, `ix_expenses_method` `:61`.

**Registration order:** there is no column named for it, but two usable
registration-order keys already exist and are populated on every insert:
`created_at` (ISO-8601 local with offset, set from `now_iso()` at
`repo/expenses.py:148,162-163`) and the monotonic `AUTOINCREMENT` `id`. What does
*not* exist is any query path that orders by them alone — see *Finanzas
subsystem*.

Other tables in one line each: `categories`/`payment_methods` carry
`sort_order` + `archived_at`, unique on `name` **among non-archived rows only**
(`0001_init.sql:18-19, 28-29`); `*_aliases` are `(target_id, alias)` seed data
with no UI; `journal_entries` has `written_at` as the ordering key;
`summaries` is keyed by `period_key` (`YYYY-MM`) with statuses
`generating|ready|empty|failed` and no `pending` (`:74-90`); `insight_jobs` is
uuid-keyed with `partial_answer` that is deliberately never serialised
(`api/models.py:258-262`).

**Durability:** WAL + `synchronous=FULL` + `foreign_keys=ON` +
`busy_timeout=5000` (`db/connection.py:30-33`); asserted by
`backend/tests/test_durability_and_deadline.py`.

---

## API Surface

Base `/api`, assembled in `backend/autonomos/api/__init__.py:8-20`. The full set
is exactly the 30 operations listed in
`backend/tests/test_contract_conformance.py:16-47`:

- `GET /api/health`, `GET /api/status`
- `GET|POST /api/categories`, `PATCH|DELETE /api/categories/{item_id}` — same
  four for `/api/payment-methods` (one router factory, `api/lookups.py:19-45`)
- `POST|GET /api/expenses`; `GET|PATCH|DELETE /api/expenses/{expense_id}`;
  `POST /api/expenses/parse`; `POST /api/expenses/suggest-category`
- `GET /api/summary/day`, `GET /api/summary/month`
- `POST|GET /api/journal`, `GET|PATCH|DELETE /api/journal/{entry_id}`
- `POST /api/voice/transcribe`
- `POST /api/insights/questions`, `GET|DELETE /api/insights/questions/{job_id}`,
  `GET /api/insights/summaries/latest`
- `GET /api/export`

Error envelope (every non-2xx), from `errors.py:72-79`:

```json
{"error": {"code": "…", "message": "developer string", "fields": [{"field":"…","reason":"…"}], "details": {}}}
```

`fields` is present for `validation`; `details` carries machine values (today
only `in_use` → `{"affected_expenses": int}`, `errors.py:104-111`). FastAPI's own
body-validation errors are rewritten into the same envelope
(`main.py:70-86`), as are Starlette `HTTPException`s (`main.py:89-97`) and
unhandled exceptions (`errors.py:118-120`).

---

## Frontend Route Tree

From `frontend/src/App.tsx:39-68`. Segments are Spanish throughout.

```
/                         → redirect /finanzas
── <FinanzasTabs> (Screen + AppBar + 3 tabs + capture bar + bottom nav)
   /finanzas              → Hoy            App.tsx:44
   /finanzas/mes          → Mes            App.tsx:45
   /finanzas/analisis     → Analisis       App.tsx:46
/finanzas/ajustes         → Ajustes        App.tsx:49
/finanzas/ajustes/:kind/:id → EditarNombre App.tsx:50
/finanzas/gasto/nuevo     → NuevoGasto     App.tsx:51
/finanzas/gasto/:id       → EditarGasto    App.tsx:52
── <DiarioTabs>
   /diario                → DiarioTodo     App.tsx:55
   /diario/fecha          → DiarioPorFecha App.tsx:56
/diario/nueva | /diario/:id | /diario/:id/editar    App.tsx:59-61
/gimnasio                 → Gimnasio       App.tsx:63
/sin-servidor             → SinServidor    App.tsx:64
*                         → redirect /finanzas
```

Two shells wrap groups of routes with `<Outlet/>`: `FinanzasTabs`
(`App.tsx:76-98`) and `DiarioTabs` (`App.tsx:101-122`). Routes rendered *outside*
a tab shell build their own `<Screen>` with a `FormBar`
(e.g. `GastoForm.tsx:214`).

Two global interceptors sit above the router in `Shell` (`App.tsx:26-37`):
never-reached server → `<SinServidor/>`; active voice capture → `<VoiceScreen/>`.

---

## Finanzas Subsystem (emphasis for the upcoming feature)

### What exists today

| Concern | Where | Notes |
| --- | --- | --- |
| Day view | `routes/finanzas/Hoy.tsx:14-41` | `useDaySummary()`; renders hero total + `ExpenseLedger` |
| Expense row → detail | `Hoy.tsx:48-67` | each row is a `<Link to={/finanzas/gasto/${e.id}}>` — **it lands directly on the edit form**, there is no read-only detail screen |
| Month view | `routes/finanzas/Mes.tsx:28-114` | `useMonthSummary(month)`; month paging via `shiftMonth`; category list at `:80-98` renders `by_category` rows that are **plain `<li>`, not links** |
| Create / edit / delete form | `routes/finanzas/GastoForm.tsx:60-447` | one component, `mode: 'nuevo' \| 'editar'`; edit seeds from `useExpense` at `:132-141`; submit branches at `:186-196`; delete goes through a `Sheet` confirmation at `:408-444` |
| Settings | `routes/finanzas/Ajustes.tsx` | rename/archive categories & methods, export |
| Insights | `routes/finanzas/Analisis.tsx` | third tab |
| Shared CSS | `routes/finanzas/Finanzas.module.css` | `.hero .when .sum .sub .ledger .row .what .cat .meta .amt .brk .line .name .val .pct .track .fill .pm .tail .skeleton` |

### The three gaps the feature will hit

**1. There is no "list expenses in registration order" query.**
`repo.list_expenses` hard-codes `ORDER BY e.spent_on DESC, e.created_at DESC,
e.id DESC` (`repo/expenses.py:264`) and takes only `date`, `month`, `limit`,
`offset` (`:242-249`). The HTTP layer exposes exactly those and validates them
(`api/expenses.py:54-68`), with `limit` capped at 200 (`:58`). So:
*insertion order* (`created_at DESC, id DESC` with no `spent_on` term) is
**not reachable through any existing endpoint or repo function**, even though
both columns exist. Note also there is no index on `created_at` alone
(`0001_init.sql:59` is a composite led by `spent_on`).

**2. There is no filter by category.** No `category_id` parameter exists in
`list_expenses` (repo or API). `ix_expenses_category` exists
(`0001_init.sql:60`), and `month_summary` already groups by category
(`repo/expenses.py:318-338`), but the per-category *expense list* is not
available.

**3. The frontend has no expense-list hook.** `api/queries.ts` exposes
`useDaySummary`, `useMonthSummary`, `useExpense` (single, `:150-156`),
`useCreateExpense`, `useUpdateExpense`, `useDeleteExpense` — but nothing that
calls `GET /api/expenses`. The `qs()` helper (`api/client.ts:95-100`) is the
existing way to build query strings.

### What already exists and must NOT be rebuilt

- **Update endpoint: yes.** `PATCH /api/expenses/{expense_id}` is implemented
  (`api/expenses.py:155-157`), backed by `repo.expenses.update`
  (`repo/expenses.py:176-233`), in the contract (`design.md:1020-1024`), in the
  conformance set (`test_contract_conformance.py:30`), covered by
  `backend/tests/test_expenses_api.py::test_5_1_every_field_is_editable_and_persists`,
  and wired on the client as `useUpdateExpense` (`api/queries.ts:175-182`).
  PATCH semantics are *presence-based*: `payload.model_dump(exclude_unset=True)`
  (`api/expenses.py:157`) so only keys the client sent are touched
  (`repo/expenses.py:186-224`).
- **Editing an expense filed under a since-archived category still works** —
  `_validate_fk(..., allow_archived=<current value>)` (`repo/expenses.py:67-99,
  191-211`). Only *moving* an expense onto an archived row is refused.
- **The edit UI exists** as `EditarGasto` (`GastoForm.tsx:55-58`), reachable at
  `/finanzas/gasto/:id`.

### Seams a new Finanzas surface would attach to

- A new tab goes in the `Tabs` items array at `App.tsx:83-87`, with its label in
  `copy/es.ts:17-23` (`tabs`), and a new `<Route>` under `<FinanzasTabs>` at
  `App.tsx:43-47`.
- A new backend endpoint (or a new query param on an existing one) must be added
  to `test_contract_conformance.py:16-47`; a *new path* additionally needs an
  entry in `design.md`'s Interface Contract, which `api/models.py:5-6` names as
  the authority when the two disagree. A new query parameter on an existing path
  does not change the `(method, path)` set and so does not trip that test —
  *(inferred from how the test computes its set at `:50-56`)*.
- Row-tap targets follow `Hoy.tsx:51-64`: `<li><Link className={s.row}>` with a
  `.what/.cat/.meta` left block and a `.amt` right block.

---

## External Dependencies

**Backend** (`backend/pyproject.toml:5-12`): `fastapi>=0.115` (routing, DI,
OpenAPI), `uvicorn[standard]>=0.32` (ASGI server, `serve.py`), `httpx>=0.27`
(calls to the two AI sidecars from `providers/`), `python-multipart>=0.0.12`
(the WAV upload on `/api/voice/transcribe`), `pydantic>=2.9` (wire models,
`api/models.py`). Dev extra: `pytest>=8.3`, `pytest-asyncio>=0.24`
(`pyproject.toml:15-18`). SQLite is stdlib `sqlite3`. Python is pinned
`==3.12.*` (`pyproject.toml:4`).

**Frontend** (`frontend/package.json:12-17`): `react` + `react-dom` 18.3,
`react-router-dom` ^6.28 (routing), `@tanstack/react-query` ^5.62 (**the only
server-state store — there is no Redux/Zustand/Context store for data**). Dev:
`vite` 6, `typescript` 5.7, `vitest` 2.1, `@testing-library/react` +
`user-event` + `jest-dom`, `jsdom`. **No UI framework and no chart library** —
the month breakdown bars are plain divs (`Mes.tsx:87-96`).

---

## Built From

- Index: `factory/context/index.json`, `generated_at` **2026-08-10T18:38:00Z**,
  schema_version 1.
- Commit: **418d7b3da081d4871d654a6b91615c33d0d53bcd** (`main`).
- `git.dirty: true` at index time — the dirt is confined to `factory/` bookkeeping
  (deleted previous-run artifacts now archived under `factory/runs/01-greenfield/`,
  plus `factory/journal.jsonl` and `factory/state.json`). No `backend/` or
  `frontend/` file was modified, so the index is accurate for all application code.
- Archived prior-run artifacts referenced above live at
  `factory/runs/01-greenfield/` (`pm/spec.md`, `pm/visual-direction.md`,
  `architect/design.md`).
