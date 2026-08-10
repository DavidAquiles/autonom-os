# Backend implementation note — Run 02 (expense list query capabilities)

## Summary

`GET /api/expenses` grew the three query parameters and the one response field the
design's Interface Contract specifies, and nothing else. `category_id` filters to a
single category (unknown id → empty list, not an error; archived categories are not
excluded). `order` selects between today's date ordering (`spent`, the default, so
no existing caller changes) and registration ordering (`registered` → `ORDER BY
e.id DESC`, KD-19). `before_id` is a strict keyset cursor copied from
`repo/journal.py:88-96`, and the response now carries `next_before_id`, which is an
int only when `order=registered` and an older row exists beyond the page, `null`
otherwise. `total_count` counts the selection only — it ignores `before_id`,
`limit` and `offset`.

No migration, no index, no new endpoint, no new error code or validation reason.
`CONTRACT_PATHS` is untouched. A second closed set now guards the query-parameter
names of `GET /api/expenses` in both directions, because the path-pair test cannot
see a parameter drift (design § Guarding the parameters, R5).

Suite: **280 passed** (baseline 261 + 19 new), `uv run --python 3.12 --extra dev
pytest -q` in `backend/`. No test was deleted, skipped or weakened.

## Files changed

| file | lines | what | why |
| --- | --- | --- | --- |
| `backend/autonomos/repo/expenses.py` | 249-253 (`_ORDER_BY`, `ORDERS`) | the two order clauses, `spent` byte-for-byte as before | KD-19, Interface Contract `order` (16.2, 16.4, 18.13) |
| | 256-331 (`list_expenses`) | keyword-only `category_id`, `order`, `before_id`; returns `(items, total_count, next_before_id)` | design's backend table; Interface Contract `GET /api/expenses` (16.2, 16.7–16.9, 16.13, 18.2, 18.3, 18.13) |
| | 333-334 (`day_summary`) | unpack the 3-tuple; arguments and behaviour identical | keeps the only in-repo caller working (design "must keep every existing call working") |
| `backend/autonomos/api/expenses.py` | 8 (`Literal` import), 55-90 | declares/type-constrains the new parameters and passes them through; still no logic | design's backend table; conventions § Notable Patterns "repo-owns-validation" |
| `backend/autonomos/api/models.py` | 110-118 (`ExpenseList`) | `next_before_id: int \| None`, required in the schema | Interface Contract response shape |
| `backend/tests/test_contract_conformance.py` | 69-105 | `EXPENSE_LIST_QUERY_PARAMS` + two tests, both directions | design § Guarding the parameters, R5 |
| `backend/tests/test_expenses_api.py` | 248-471 | 19 criterion-named tests + 4 local helpers | the behavioural half of § Guarding the parameters |

`repo/expenses.py`'s `create`, `get`, `update`, `delete`, `month_summary`,
`by_category` and every other backend module are untouched. Nothing under
`frontend/` was read or written.

## Interface Contract conformance

`GET /api/expenses` — verified against the live `/api/openapi.json` and by test:

- `date`, `month` — unchanged, including `date` winning when both are sent
  (`elif` at `repo/expenses.py:297`). Existing `test_expense_list_filters_by_month_and_day` still passes.
- `category_id` — int ≥ 1, optional, `Query(None, ge=1)`. Combines with `date`,
  with `month`, with neither and with either `order` (SQL is an `AND` over a
  condition list, `repo/expenses.py:292-305`). Unknown id → `200 {items: [],
  total_count: 0}` (`test_18_2_an_unknown_category_is_an_empty_list_not_an_error`).
  Archived categories are **not** excluded — see the interpretation note below.
- `order` — `Literal["spent","registered"]`, default `"spent"`. `"spent"` is the
  identical clause that was at `repo/expenses.py:264` before this change; `"registered"` is
  `ORDER BY e.id DESC`, no tiebreaker, no index added.
- `before_id` — int ≥ 1, optional, applied as `e.id < ?` before ordering, `limit`
  and `offset`, and excluded from the count. Accepted with `order="spent"`, where
  it filters and `next_before_id` is always `null`
  (`test_before_id_with_the_default_order_is_accepted_and_reports_no_cursor`).
- `limit` (1..200, default 200) and `offset` (≥ 0, default 0) — unchanged.
- response `200 {items, total_count, next_before_id}` — confirmed by
  `test_the_default_order_is_unchanged_and_carries_a_null_cursor`, which asserts
  the key set exactly. `items` shape unchanged; `source` still absent
  (`test_source_is_never_returned` untouched and green).
- `total_count` ignores `before_id`/`limit`/`offset` —
  `test_18_3_total_count_ignores_before_id_limit_and_offset`.
- `next_before_id` — int only for `order=registered` with a further row; `null`
  otherwise and always for `order=spent`.
- errors — no new code, no new reason. `category_id`/`before_id` non-integer →
  `not_an_integer`, below minimum → `must_be_positive`, `order` off the literal set
  → field `order`, reason `required` (FastAPI's `literal_error` falls through
  `_REASON_BY_PYDANTIC_TYPE`, `main.py:83`). All five pinned in
  `test_the_new_list_parameters_are_rejected_within_the_closed_reason_set`.
  `date`/`month` malformed → `required`, unchanged.

`GET|PATCH|DELETE /api/expenses/{expense_id}` and `GET /api/summary/month` —
**unchanged, as the contract requires**. Nothing was edited on those paths; the
facts 17.4/17.5/17.10 rely on (`created_at`, `updated_at`, absent `source`) were
verified present in `repo/expenses.py:148,162-163,228-231` and needed no change.
`CONTRACT_PATHS` still holds exactly its 30 pairs.

## Escalations / deviations

**None escalated. One reading of an internally inconsistent contract sentence,
flagged here for the Reviewer.**

The `category_id` entry says an id that "belongs to an **archived** category …
yields `200` with `items: []` and `total_count: 0`", and its very next sentence
says "Archived categories are *not* excluded … their expenses must remain
reachable." Those cannot both be implemented. I implemented the second: the filter
applies no archived predicate at all, so an archived category returns its
expenses, and an *unknown* id (or an archived one with nothing in range) returns
the empty list. Reasons: the second sentence is normative ("must"), 18.2 says
"every expense of that category", and `by_category` still lists archived
categories — so tapping one and being told it is empty while its total is on
screen would be a visible fault. The wire shape is identical under either reading
(`200` + an array), so the parallel frontend lane is unaffected either way and its
empty-category state (18.10) still fires on a genuinely empty result. Pinned by
`test_18_2_an_archived_categorys_expenses_stay_reachable`.

Two code-level choices worth naming (inside my latitude, not deviations):
- `list_expenses` always fetches `limit + 1` rows, not only for `registered`. The
  extra row is discarded for `spent`, where the cursor is contractually `null`;
  this keeps one code path instead of two.
- An `order` value outside the two literals is coerced to `"spent"` **inside the
  repo** as a defensive default. The API layer never sends one (FastAPI rejects it
  with a 400 first, which is what the test asserts); this only protects a future
  internal caller.

Decisions taken at the gate and honoured, not revisited: the 200-row cap on the
category-filtered list (KD-21 / R4) — no paging added to that path; and R3, the
no-op save marking an expense edited — `update`'s `updated_at` semantics untouched.

## Acceptance criteria mapping

Backend-side; the screens themselves are `implementer-frontend`'s.

- **16.2** — `order=registered` → `ORDER BY e.id DESC`.
  `test_16_2_historial_is_ordered_by_when_it_was_recorded_not_by_its_date` records
  three expenses newest-date-first so the two orderings are exact opposites.
- **16.3** — a backdated expense recorded last comes back first under
  `registered`. `test_16_3_an_expense_dated_in_the_past_is_at_the_top_of_historial`.
- **16.4** — editing touches neither `id` nor the ordering key.
  `test_16_4_editing_an_expense_does_not_move_it_in_historial` patches amount *and*
  `spent_on` on the middle row and asserts the sequence is unchanged.
- **16.8** — keyset termination.
  `test_16_8_repeated_paging_reaches_the_very_first_expense_ever_recorded` pages
  with `limit=2` under a bounded loop (so a non-terminating cursor fails rather
  than hangs), asserts the concatenation equals every id in reverse registration
  order, and that the final id is the first ever recorded.
- **16.9** — `next_before_id is None` on a page that exhausts the rows, on an
  over-large `limit`, and on an empty result.
  `test_16_9_the_last_page_presents_no_cursor`.
- **16.13** — `limit=3` over 9 rows returns 3 items with `total_count == 9`.
  `test_16_13_the_first_screenful_does_not_fetch_every_expense`.
- **18.2** — `month` + `category_id` returns only that category and only that
  month, verified against a decoy in another category and a decoy in another
  month. `test_18_2_a_selected_category_shows_only_it_and_only_the_viewed_month`.
  The 200-row cap remains (R4, accepted at the gate).
- **18.13** — the filtered list keeps the `spent_on DESC` ordering, deliberately
  different from Historial.
  `test_18_13_a_filtered_category_list_is_ordered_by_the_date_it_is_dated_for`.
- **17.4 / 17.5 / 17.10** — no backend work needed and none done: `created_at` and
  `updated_at` are already returned and `update` already rewrites only
  `updated_at`; `source` is already never serialised. The detail screen itself is
  frontend.
- **16.7** — server half only: pages append without overlap and without
  reordering (`test_16_7_paging_appends_older_records_without_repeating_or_reordering`).
  The "does not return to the top" half is frontend.
- **16.1, 16.5, 16.6, 16.10, 16.11, 16.12, 17.1–17.3, 17.6–17.9, 17.11,
  18.1, 18.3–18.12** — frontend criteria; not mine and not claimed. 18.3's *count*
  is served by `total_count`, which is pinned above.

## Verification

`cd /home/david/Proyectos/Autonom-OS/backend && uv run --python 3.12 --extra dev pytest -q`
→ **280 passed, 1 warning** (pre-existing `StarletteDeprecationWarning`). Baseline
before my changes on this working tree: 261 passed. `factory/state.json`'s
`state.verification` was empty at the time of writing, so the count above is from
the run itself, not a claim about a gate.

Also checked by hand against the live schema: `GET /api/expenses` publishes exactly
`{before_id, category_id, date, limit, month, offset, order}` and returns
`{"items": [], "total_count": 0, "next_before_id": null}` on an empty database.

## What to look at hardest

1. The archived-category reading above (`repo/expenses.py:301-303` and its test) —
   it is the one place I chose between two sentences of the contract.
2. `next_before_id`'s exact condition (`repo/expenses.py:327-329`): `order ==
   "registered" and has_more and items`. If any of the three is dropped the cursor
   either lies on the last page (16.9 breaks silently) or appears for `spent`.
3. The three-tuple return: `day_summary` (`repo/expenses.py:334`) is the only
   in-repo caller and now unpacks three values. `month_summary` does **not** call
   `list_expenses` despite what the design's prose says — it runs its own
   aggregate SQL — so nothing there changed.
