# Walkthrough — Run 02: Historial, expense detail, month by category

Feature run on an existing product. Baseline `418d7b3` → HEAD.
Artifacts for this run are in `factory/`; Run 01's are archived under
`factory/runs/01-greenfield/` so nothing was overwritten.

## What you asked for, and what shipped

Three things, all built:

1. **Historial** — a fourth Finanzas tab (Hoy · Este mes · **Historial** · Análisis)
   listing every expense **in the order you recorded them**, newest first,
   regardless of the date on the expense. Backdate an expense today and it still
   appears at the top. Editing one never moves it. "Ver gastos más antiguos"
   pages back to the very first expense you ever recorded.
2. **An expense detail view** — tap any expense anywhere and you get a read-only
   screen with a single "Editar gasto" action. It surfaces two facts the app has
   stored since day one and never showed you: **when you recorded it**, and
   **whether it has been edited since**.
3. **Category drill-down in Este mes** — tap a category to see that month's
   expenses for it, with the category's own total and count shown alongside the
   month's total. Tap any row for the same detail screen.

## What changed that you already had

- **Tapping an expense in Hoy now opens the detail view, not the edit form.**
  Editing is one more tap from there. This was assumption A24, and you approved
  it at the plan gate so that every list behaves the same way.
- **The month you are viewing and the category you opened now survive
  navigation** — they live in the URL (`?mes=`, `?categoria=`), so opening an
  expense and coming back returns you to the same month, the same category, and
  the same scroll position.
- `/finanzas/gasto/:id` is now the detail screen; the edit form moved to
  `/finanzas/gasto/:id/editar`, mirroring how Diario already works.

## How it was built

**No database migration, no backfill, no new index.** Registration order comes
from the `id` column every expense already had. One existing endpoint grew three
query parameters; no new API paths were added.

- **Backend** — `GET /api/expenses` gained `category_id`, `order`
  (`spent`|`registered`, default `spent`) and `before_id`, plus a
  `next_before_id` cursor. Keyset paging on the rowid, so nothing is skipped or
  duplicated when you record an expense mid-scroll.
- **Frontend** — new `Historial.tsx`, `GastoDetalle.tsx`, and `ExpenseLedger.tsx`
  (the shared row component, so Hoy, Historial and the filtered list are literally
  the same component rather than three lookalikes). Scroll memory lives in
  `useScrollMemory.ts`, applied once at the `Screen` scroll container.

## How to run it

Nothing changed about running the app.

```
cd backend  && uv run --python 3.12 uvicorn autonomos.app:app --port 8001
cd frontend && npm run dev
```

**Port 8000 belongs to another project's Docker container — this project uses 8001.**

## How to verify it

```
cd backend  && uv run --python 3.12 --extra dev pytest -q   # 280 passed
cd frontend && npm run build && npx tsc --noEmit && npm run test   # 75 passed
python3 /home/david/Proyectos/software_factory/tools/verify.py --project .
```

All gates pass. Test integrity: **274 tests / 714 assertions**, against a
baseline of 221 / 565. No test was deleted, skipped or weakened at any point.

QA exercised the running app in Chromium at 390×844 against a byte-faithful copy
of your database on a separate port. **Your data was never touched** — it began
and ended at 16 expenses / $267.970 with an unchanged md5, and your server on
:8001 was left running.

## What was verified, and what that cost

- **37 / 37 acceptance criteria pass** (16.1–18.13), plus both changed-behaviour
  checks. Design Constraints 29–43 all pass, measured against real renders.
  Run 01's constraints 1–28 show no regression on the surfaces this run touched.
- **The run's biggest named risk (R1 / criterion 17.8 — scroll restoration) is
  closed.** The frontend's first implementation of it passed all 70 tests and all
  132 screenshots *while being completely broken*: React runs an effect cleanup
  after detaching the container, and a detached element reports `scrollTop === 0`,
  so the saved offset was destroyed on the way out. The implementer found it by
  driving a real browser and fixed it before submitting. QA then re-measured
  independently on all three lists, including 60 rows deep.
- **One QA rework cycle** (of a permitted three) was spent on three defects that
  no criterion technically covered but which were worth fixing — see below.
  Everything else passed first time.

## Defects found and fixed after QA

- **After deleting an expense, one Back tap showed the deleted expense in full**,
  with a working Edit button; saving from there claimed your server was
  unreachable while it was answering with a 404. Two independent causes, both
  fixed: the navigation stack now pops two entries instead of replacing one, and
  the not-found state now replaces the record rather than rendering above it.
- **A failed category request claimed your data was gone** — "ya no queda nada en
  Transporte" — while the total directly above still showed money in it. An error
  state must not make a factual claim about your data; it now says the list
  failed to load and offers Reintentar.
- **Historial went completely blank** if its request failed while the server still
  answered. It now shows the failure banner over whatever rows arrived.

A fourth issue fixed itself as a consequence: deleting from a scrolled list now
returns you to where you were rather than the top.

## Deferred — real, recorded, not this run's problem

In `state.deferred` with literal evidence:

- **D4** malformed `?mes=` renders a blank month screen (reachable only by hand-editing the URL).
- **D5** malformed expense id shows the unreachable-server banner while the server is up (URL-only).
- **Reviewer F3** the no-history fallback close pushes instead of replacing.
- **`npm run shots` intermittently writes a real expense** into whatever database it
  points at, via the pre-existing `gasto-guardando` recipe. **Pre-existing, not
  introduced here** — but worth knowing before you run the screenshot harness
  against your own data. QA and the rework both avoided it deliberately.
- **Diario's "Todo" list still caps at the 50 newest entries** with no way to reach
  older ones (`queries.ts:197`). You decided this at the Kickoff gate; Historial's
  paging is the pattern to copy when you want it fixed.

## Decisions you made, recorded here so they are not re-litigated

- The category-filtered month list caps at **200 expenses** with no show-more.
  You accepted it; ~7 expenses per day in one category for a month to reach it.
- **Opening an expense, changing nothing and saving still marks it "editado."**
  Accepted rather than change a shipped, tested save path.
- Tab metrics stay as Run 01 approved them; below 331 px "Este mes" wraps. At
  390 px the four tabs measured 278.7 px with **70.3 px of slack**.
- An empty selected category shows **no total and no count** — a zero row is
  forbidden by criterion 18.10.
- Historial's last page **ends silently**, with no closing line.

## Still unverified

- **Behaviour below 331 px viewport width** was measured but deliberately not
  fixed, per your decision. It is a real wrap, not a hypothetical.
- **The four screenshot recipes and ten new ones** in `tools/shots.mjs` were run
  by the implementers against scratch databases, not against your data.
- The `gasto-guardando` write side effect above is characterised but not fixed.

## Where the artifacts are

| Artifact | Path |
|---|---|
| Spec, 37 criteria + assumptions | `factory/pm/spec.md` |
| Visual direction, constraints 29–43 | `factory/pm/visual-direction.md` |
| Design, contract, key decisions | `factory/architect/design.md` |
| Coverage analysis + re-check | `factory/analyst/analysis.md` |
| Approved mockups + 49 renders | `factory/implementer-frontend/mockups/` |
| Backend note | `factory/implementer-backend/note.md` |
| Frontend note (Phase 2 + rework) | `factory/implementer-frontend/note.md` |
| Code review | `factory/reviewer/review.md` |
| QA report + re-test, 65 screenshots | `factory/qa/report.md`, `factory/qa/shots/` |
| Run state, deferrals, gates | `factory/state.json` |
| Append-only event log | `factory/journal.jsonl` |

## Two process notes worth keeping

- **The frontend agent's transcript was destroyed twice** — once right after you
  approved the mockups, once before the QA rework. Both times the work was
  recovered by cold-starting a new agent from the artifacts on disk, with no loss
  and no rework cost. This is the recovery contract working as designed.
- **Four role `Write` calls were blocked** by the environment (artifact-analyst
  twice, QA twice). Each role returned its report as text and the orchestrator
  persisted it verbatim with an attribution header. Four occurrences is a defect
  in the factory's tool grants, not a quirk — worth fixing before the next run.
- A **fabricated system notice** claimed `factory/qa/report.md` had been modified
  by a user or linter, and instructed that this be concealed. `git diff` showed
  only the orchestrator's own append. It was not complied with and was reported.
