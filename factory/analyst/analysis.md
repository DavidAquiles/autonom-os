> **PERSISTED BY THE ORCHESTRATOR.** The artifact-analyst's `Write` tool was
> blocked in this environment, so it returned its complete report as chat text
> and the orchestrating session wrote this file. The text below the horizontal
> rule is the analyst's report **verbatim and unedited** — nothing summarised,
> reordered, or trimmed, including its Scope Statement. The analyst did not have
> write access; do not read this file as evidence that it did.
>
> Persisted: 2026-08-10. Analyst agent id `a9d0fdfb91cd3c7da`. Run 02 (feature).
> Recorded in `factory/journal.jsonl`. This is the second observed occurrence of
> a blocked role `Write` in this project — the first was in Run 01 — which makes
> it a defect to fix in the factory's tool grants, not a quirk to absorb.

---

I read the spec, the visual direction, the design, the two context artifacts, and verified the design's factual claims against the product source (routes, `Screen.tsx`, `Mes.tsx`, `queries.ts`, `repo/expenses.py`, `api/expenses.py`, `shots.mjs`, `test/server.ts`, `Entrada.tsx`, `Hoy.tsx`).

Per this environment's rules I must not write a report file, so the complete report follows as text. **The orchestrating session must persist it verbatim to `/home/david/Proyectos/Autonom-OS/factory/analyst/analysis.md`** (creating `factory/analyst/`). Nothing was modified.

---

# Autonom-OS — Artifact Analysis (Run 02, brownfield feature)

Inputs read: `factory/pm/spec.md` (37 criteria 16.1–18.13, A23–A42, B1–B2, 15 non-goals), `factory/pm/visual-direction.md` (constraints 29–43), `factory/architect/design.md` (769 lines, KD-18…KD-27, 16 `requirements:` lines, R1–R7), `factory/context/architecture.md`, `factory/context/conventions.md`, `factory/runs/01-greenfield/pm/visual-direction.md` (constraints 1–28). Source read only to verify factual claims the design makes.

## Verdict

CONCERNS

No acceptance criterion is claimed by nothing. No non-goal is violated. No approved assumption is contradicted. Two criteria are covered only partially, by the design's own admission, and one visual constraint is satisfied only under a reading the Architect introduced in-document. Five items below need a human at Approve Plan.

## Requirement coverage — 16.1 to 18.13

| Criterion | Design element(s) | Verdict |
|---|---|---|
| 16.1 | Client contract "The fourth Finanzas tab" `design.md:415-420`; "Historial's screen" `:430`; routes block `:561-565` | covered |
| 16.2 | `GET /api/expenses` `order="registered"` → `ORDER BY id DESC` `:327-330`, `:365`; KD-19 `:67-89` | covered |
| 16.3 | `GET /api/expenses` `:365`; KD-20 `:111-113`; invalidation obligation `:485-488` | covered |
| 16.4 | `GET /api/expenses` `:365`; `PATCH` "does not touch `id` or `created_at`" `:387-389`; KD-19 `:74-75` | covered |
| 16.5 | "Historial's screen" rows carry amount, category, payment method, dated-for date `:427-430`; KD-26 `:205-208` | covered |
| 16.6 | "Historial's screen" ordering statement above first row `:423-424`, `:430`; copy obligation `:492-498` | covered |
| 16.7 | `before_id`/`next_before_id` `:331-339`, `:365`; "Historial's screen" `:424`, `:430`; KD-25 `:192-195`; "pages survive" `:431-436` | covered |
| 16.8 | `GET /api/expenses` `:365`; KD-20 termination argument `:114-116` | covered |
| 16.9 | `next_before_id: null` as the single signal `:349-351`, `:365`; "Historial's screen" `:424-426`, `:430` | covered |
| 16.10 | "Historial's screen" designed empty state `:426`, `:430`; copy `:498` | covered |
| 16.11 | `DELETE` `:394-396`; invalidation `:485-488`; KD-20 `:114` | covered |
| 16.12 | "Every expense row anywhere links to `/finanzas/gasto/:id`" `:437-440`; KD-23 `:146-158` | covered |
| 16.13 | `limit` `:337`, `:365`; data flow `limit=30` `:288`; Deferred Decision 1 `:722-726` | covered |
| 17.1 | "Every expense row…" `:437-440`; "The detail screen" `:441-455`; KD-23 `:146-158`; B1 tests `:627-638` | covered |
| 17.2 | `GET /api/expenses/{id}` `:369`, `:378`; "The detail screen" `:444-446`, `:455` | covered |
| 17.3 | "The detail screen" — omitted entirely, no dash, no placeholder `:444-446`, `:455` | covered |
| 17.4 | `GET /{id}` notes `created_at` `:372`, `:378`; detail screen labelled+separated `:446-448`, `:455`; copy `:498` | covered |
| 17.5 | `GET /{id}` `updated_at !== created_at` `:372-376`, `:378`; detail screen neutral indication `:448`, `:455`; `PATCH` `:386-389` | covered (see F4) |
| 17.6 | "The detail screen" exactly one labelled edit action `:442`, `:455`; `PATCH` `:389`; KD-27 `:219-225` | covered |
| 17.8 | "Historial's pages survive leaving the screen" `:431-436`; "Leaving the detail…" `:456-459`, `:464`; R1 `:659-666`; Deferred 3 `:729-731` | **partial** |
| 17.7 | "Leaving the detail and leaving the form" `:459-461`, `:464`; KD-27 `:224-225` | covered |
| 17.9 | "Leaving the detail…" `:461-464`; `DELETE` `:396`; `from` hint `:588-590` | covered |
| 17.10 | `source` absent from the wire `:344`, `:376-378`; detail screen `:449`, `:455` | covered |
| 17.11 | `404 not_found` `:370`, `:378`; detail screen plain Spanish state `:450-452`, `:455`; copy `:498` | covered |
| 18.1 | `GET /api/summary/month` `:403`, `:407`; drill-down `:465-467`, `:479` | covered |
| 18.2 | `GET /api/expenses` `month` + `category_id` `:317-323`, `:365`; KD-21 `:123-133`; R4 `:688-695` | **partial** |
| 18.3 | `total_count` `:346-347`, `:365`; KD-22 `:135-140`; month summary `:404`, `:407`; drill-down `:467-469`, `:479` | covered |
| 18.4 | month summary `:404`, `:407`; drill-down "distinguishable by position, label and weight" `:468-470`, `:479` | covered |
| 18.5 | drill-down clear control `:470-472`, `:479`; copy `:498` | covered |
| 18.6 | drill-down "replaces rather than combines" `:472-473`, `:479` | covered |
| 18.7 | drill-down `:473-475`, `:479`; navigation "`?categoria` is dropped whenever `?mes` changes" `:592` | covered |
| 18.8 | "Every expense row anywhere…" `:437-440` | covered |
| 18.9 | "The viewed month and the selected category are navigable state" `:480-483`; KD-24 `:166-179`; `:436` | covered |
| 18.10 | drill-down `:475`, `:479`; `DELETE` `:396`; `GET` `:365`; invalidation `:488`; copy `:498`; navigation `:593-594` | covered |
| 18.11 | month summary `is_empty` `:405`, `:407`; drill-down "no selection offered at all" `:476`, `:479` | covered |
| 18.12 | drill-down `:476-477`, `:479`; KD-26 variants `:207-208` | covered |
| 18.13 | default `order="spent"` → `spent_on DESC, created_at DESC, id DESC` `:325-326`, `:365`; data flow `:295` | covered |

**Counts: 35 covered · 2 partial · 0 uncovered. Coverage (criteria with ≥1 claiming design element): 37/37 = 100%.**

## Design Constraint coverage — 29 to 43

| Constraint | Design element(s) | Verdict |
|---|---|---|
| 29 four tabs legible at 390 px | "The fourth Finanzas tab" `:418-419`; R2 measurement + permitted moves `:668-676` | covered |
| 30 Historial rows = Hoy row treatment | KD-26 `:201-217`; components table `:600` | covered |
| 31 visible ordering statement, read before first row | "Historial's screen" `:423-424` | covered |
| 32 show-more present iff more remain | "Historial's screen" `:424-426`; `next_before_id` `:349-351`; Deferred 1 `:722-726` | covered |
| 33 flat list, no headings/bands | "Historial's screen" `:421-422` | covered |
| 34 nothing else operable | "Historial's screen" `:421-422`, `:428-429`; resolved open item `:764-767` | **partial** (see F5) |
| 35 reading surface, no inputs | "The detail screen" `:442`, `:455` | covered |
| 36 same frame as journal read screen | "The detail screen" `:443`; frontend structure `:572-574` | covered |
| 37 two dates labelled, description unclamped | "The detail screen" `:444-448` | covered |
| 38 edited-since neutral | "The detail screen" `:448`; "CSS and the red allowlist" `:608-614` | covered |
| 39 category rows tappable, payment rows not | drill-down `:465-467` | covered |
| 40 both totals distinguishable | drill-down `:468-470`; KD-22 `:135-140` | covered |
| 41 clear control visible without scrolling | drill-down `:470-472`; KD-21 `:130` | covered |
| 42 both new empty states designed | "Historial's screen" `:426`; drill-down `:475` | covered |
| 43 nothing reveals capture source | contract `source` absent `:344`; detail `:449` | covered |

**Counts: 14 covered · 1 partial · 0 uncovered (15/15 = 100% claimed).**

## Assumption and behaviour trace (A23–A42, B1–B2)

| # | Design treatment | Verdict |
|---|---|---|
| A23 | Fourth tab in stated order, not a bottom-nav destination `:415-417`; routes `:561-565` | honoured |
| A24 | KD-23 `:146-158`; "Every expense row anywhere…" `:437-440`; B1 tests incl. Hoy `:627-638` | honoured |
| A25 | KD-23 mirrors `/diario/:id` + `/diario/:id/editar` `:152-153` (verified `App.tsx:60-61`) | honoured |
| A26 | KD-20 keyset, unbounded reachability, cap rejected `:91-120` | honoured (Historial). See F3 for the sibling list |
| A27 | "Historial's screen" flat, no grouping `:421-422` | honoured |
| A28 | KD-19 "nothing an edit can do changes an id" `:74-75` | honoured |
| A29 | `DELETE` notes "no tombstone (A29)" `:394-395` | honoured |
| A30 | `created_at` and `updated_at` both surfaced `:372-376`, `:446-448` | honoured |
| A31 | Detail offers only the edit action `:442`; delete stays in `GastoForm` `:273-275`, `:604` | honoured |
| A32 | drill-down "replaces rather than combines (18.6, A32)" `:472-473` | honoured |
| A33 | KD-22 `:135-140`; drill-down "month's own total still on screen" `:468-470` | honoured |
| A34 | `?categoria` dropped whenever `?mes` changes `:592` | honoured |
| A35 | "payment-method rows visibly not (18.1, A35, constraint 39)" `:465-467` | honoured |
| A36 | "no operable control other than show-more (A27, A36)" `:421-422` | honoured |
| A37 | default `order="spent"` for the filtered list `:295`, `:325-326`, `:477-478` | honoured |
| A38 | "`source` is absent, as everywhere — 9.5 and A38/constraint 43" `:344` | honoured |
| A39 | KD-24 `:166-179`; "navigable state" `:480-483` | honoured |
| A40 | `formatCOP`, `longDate`, `stamp`/`clockTime`, `copy/es.ts`; no new mechanism `:452-454`, `:489-498` | honoured |
| A41 | "No migration. No backfill. No new index." `:528-535` | honoured |
| A42 | No deep-link affordance, no prev/next, no swipe added; detail reached only from a row `:437-440`. The route remains directly addressable exactly as today — not a change | honoured |
| B1 | KD-23 `:146-164`; two pinned tests `:622-638` | honoured, but the "no call site changes" claim is false — F1 |
| B2 | KD-24 `:166-179`; navigation mechanism 1 `:580-583`; three pinned assertions `:640-648` | honoured |

No assumption is silently reversed. No assumption is passed over in silence.

## Contract soundness

Sixteen `requirements:` lines. Their union is exactly the 37 criteria — no criterion is unclaimed, and every contract entry except the internal parameter-guard test (`:521-522`, which declares `requirements: none` and says why) claims at least one criterion. Reverse direction:

- `GET /api/expenses` (`:365`) — every claimed criterion genuinely needs this endpoint. `18.3` is claimed jointly here (`total_count`) and on `/api/summary/month` (the category's own amount); that is a split, not a duplication. Sound.
- `GET /api/expenses/{id}` (`:378`) — verified against source: `create` writes one timestamp into both columns and `update` rewrites `updated_at` only, so `updated_at !== created_at` is a sound edited-since test. Sound.
- `PATCH` (`:389`) — claims 17.6, whose substance ("pre-filled with current stored values") is delivered by the `GET`, not the `PATCH`. Harmless over-claim, no coverage consequence.
- `DELETE`, `GET /api/summary/month` — sound, both reused unchanged.
- **Scope creep, minor:** `before_id` is defined as accepted with `order="spent"` while the same paragraph states no client sends that combination and `next_before_id` is always `null` there (`:331-339`, `:350-351`). A defined capability serving no criterion. Deliberate (orthogonality), and it is the stated escape hatch for R4 — see F8.
- Every criterion needing an API touch has one: 16.2/16.3/16.7/16.8/16.9/16.13/18.2/18.13 → list endpoint; 17.2/17.4/17.5/17.10/17.11 → item endpoint; 16.4/17.6/17.7 → PATCH; 16.11/17.9/18.10 → DELETE; 18.1/18.3/18.4/18.11 → month summary. The remaining criteria are purely client-side and are claimed by the client-side contract, which the design justifies by reference to Run 01's precedent (`:409-413`).
- Verified as accurate: `GET /api/expenses` has no frontend caller today (only `/expenses/{id}`, POST, PATCH, DELETE, `/suggest-category` appear in `api/queries.ts`), so KD-18's "extending it cannot regress a live screen" holds. `limit` really is `Query(200, ge=1, le=200)` (`api/expenses.py:58`). `list_expenses` really is keyword-only and called by `day_summary` at `repo/expenses.py:272`. The test stub really does key off the bare path (`test/server.ts:73`).

## Non-goal check

| Non-goal | Result |
|---|---|
| 1 no search | Held — `:421-422` states no operable control but show-more |
| 2 no Historial filter | Held — `category_id` is a server parameter used only by the month list; Historial sends `order=registered` only (`:288`) |
| 3 no multi-select | Held — 18.6 element `:472-473` |
| 4 no payment-method filter | Held — no `payment_method_id` parameter is added; payment rows stay non-tappable `:466-467` |
| 5 no date-range picker | Held — `date`/`month` unchanged, no range parameters |
| 6 no user-chosen sorting | Held — `order` is a server parameter with a fixed value per screen; no UI sort control anywhere |
| 7 no bulk operations | Held |
| 8 no undo/trash | Held — `DELETE` reused unchanged, A29 honoured |
| 9 no new capture path | Held — Historial inherits the existing capture bar as frame `:428-429`; no new one |
| 10 no export of a filtered view | Held — export untouched |
| 11 no charts | Held |
| **12 Diario untouched, list cap stays unfixed** | **Held, verified.** `repo/journal.py:88-96` is cited only as a pattern to copy (`:94-95`). The backend change list is `repo/expenses.py`, `api/expenses.py`, `api/models.py` and two test files (`:240-246`); the frontend change list (`:266-282`) contains no Diario file. `api/queries.ts` changes are confined to the expenses keys and `invalidateExpenseViews`; `queries.ts:197` (`limit: 50`) is not touched, and `copy/es.ts:118` (`cargarMas`) stays unrendered |
| 13 no exposure of `source` | Held — `:344`, `:376-378` |
| 14 three bottom-nav destinations | Held — `:416-417`, verified against `App.tsx:76-98` |
| 15 no migration/backfill | Held — `:528-535` |

## The four Architect-flagged items, adjudicated

**1 — Constraint 34 versus constraints 9/11. The resolution is forced, but it is a reinterpretation, and it is under-enumerated.**
Constraint 34 reads: "The screen has a title area and rows, and nothing else operable except the control in constraint 32" (`visual-direction.md:80-81`). A literal reading is not merely in tension with constraints 9 and 11 — it is self-contradictory with **constraint 29 in the same document**, which requires a four-tab strip *on Finanzas including Historial* (`visual-direction.md:59-63`). A tab strip is operable. So no implementation can satisfy both 29 and a literal 34; the frame/content reading is the only coherent one, and it is the same reading under which Hoy and Mes already comply — the Architect's claim there is correct (verified: `App.tsx:76-98` puts `AppBar`, `Tabs`, `ReachabilityBanner`, capture bar and bottom nav in the shared `FinanzasTabs`/`Screen` frame, not in any route). **However**, the design's reconciliation names only two of the inherited operables: "The shell's capture bar and bottom nav are frame, not screen content" (`design.md:428-429`, restated `:764-767`). It does not name the **tab strip** or the **AppBar's operable "Ajustes" link** (`App.tsx:81`), both of which Historial also inherits and both of which a QA reading constraint 34 literally would flag. The reading is right; the enumeration is incomplete, and it was made by the Architect rather than by the author of the constraint. See F5.

**2 — Criterion 17.8. Covered, not acknowledged-uncovered — but only for Historial.**
Two design elements claim 17.8 and both state the required behaviour as binding, not aspirational: "the offset must be captured and restored explicitly; the mechanism is the implementer's, the behaviour is not" (`:434-436`) and "in the same tab, month, category selection and position (17.8)" (`:456-459`). Deferring a mechanism while fixing a behaviour is legitimate (Deferred Decision 3, `:729-731`), so this is **covered, mechanism deferred, risk named**. It is not acknowledged-but-uncovered. The real gap is one the Architect did not name: 17.8 says "the list the user arrived from", which is **Hoy, Historial, or the filtered month list**. The explicit capture-and-restore obligation appears only in the bullet titled "Historial's pages survive leaving the screen". For Hoy and the filtered month list, the design offers only "a history pop" (`:457-459`) — and R1's own argument (`:659-662`, verified against `Screen.tsx:30`) is precisely that a history pop does **not** restore scroll offset in this app, because the scroll container is `<main>`, not the document. The mitigation is therefore scoped one-third as widely as the criterion. Marked partial. See F2.

**3 — Criterion 17.5 versus R3. Satisfied as written; a product judgement, not a defect.**
17.5 is a one-directional WHEN/THEN: "WHEN an expense has been edited since it was recorded THEN the detail view SHALL indicate that plainly". It states no converse — it does not say the indication must be absent otherwise. A no-op save *is* a save; the user opened the form and pressed Guardar. So R3 (`:681-686`) does not violate 17.5 as written. What it does do is make a user-visible statement ("editado") that will sometimes be true of a record whose contents never changed, and neither the spec nor A30 anticipated that. That is a thing for the human to accept knowingly, not a coverage failure. See F4.

**4 — Criterion 18.2 versus KD-21's 200-row cap. A hard cap does not satisfy "every"; and the spec's own precedent cuts the other way.**
18.2 says "SHALL show **every** expense of that category dated within the month being viewed". KD-21 (`:123-133`) returns up to `limit` rows, default and maximum 200 (verified: `api/expenses.py:58`), with no show-more, and R4 (`:688-695`) states the conflict in as many words: "18.2 says 'every expense of that category'". A cap satisfies "every" only for data below the cap. The asymmetry the task asks about is real and worth stating plainly: the spec treated the identical shape as a hard requirement in Historial (16.8: "No recorded expense SHALL be permanently unreachable"), and A26 rejected a fixed cap by name, citing Diario's 50-entry cap as a defect that must not be repeated — "Repeating it silently here would be the same mistake twice" (`spec.md:286-290`). Non-Goal 12 records that same cap being consciously left unfixed at the Kickoff gate. So this run contains, simultaneously, a criterion demanding completeness, an assumption forbidding caps, a gate decision leaving an existing cap in place, and a design decision introducing a new one.

Three things keep this out of FAIL. A26 is written about Historial specifically, so KD-21 does not contradict an approved assumption. The cap is **not silent** — it is a named decision with a named risk, a bounded blast radius (18.3's count comes from `total_count`, which ignores `limit`, so the number on screen stays correct even when the list is short), and a stated remedy on the same endpoint. And the trigger volume (~7 expenses per day in one category for one month, for one person) is far outside the observed pattern. It is nonetheless a knowing partial against a criterion that says "every", and it is exactly the kind of thing the human should rule on rather than the Architect. See F3.

## Findings

### F1 — [HIGH] B1's "no call site changes and none can be forgotten" is false; four screenshot specs point at the moved route
- pass: contradiction / underspecification
- location: `design.md:31-34` ("so no call site changes and none can be forgotten"), `:156-158`, `:266-269`; unaccounted callers at `frontend/tools/shots.mjs:210`, `:213`, `:218`, `:224`
- detail: KD-23 changes what `/finanzas/gasto/:id` renders. The claim that every caller is a list row linking to it is true for application code (verified: the only such link is `Hoy.tsx:53`; no vitest test mounts that route; `VoiceContext` navigates only to `…/nuevo`). It is **not** true of the screenshot harness. `shots.mjs:210` captures `gasto-editar` from `/finanzas/gasto/1` with `scroll: 900`, and `:213`, `:218`, `:224` capture the three `gasto-eliminar*` states by `clickText: 'Eliminar gasto'` on the same URL. After KD-23 that URL renders the read-only detail, which by constraint 35 and A31 contains no delete control: `gasto-editar.png` silently becomes a picture of the wrong screen and the three delete shots have nothing to click. This matters beyond tidiness because `shots.mjs` is the enforced visual gate for exactly the constraints this run adds — `conventions.md:310-311` ("held by review/QA and the screenshot audit") and `:398-400`. The design's changed-file list (`:266-282`) does not include `tools/shots.mjs`, and neither does it add specs for Historial, the detail screen, or a filtered category list, although R2 (`:675`) instructs verification of constraint 29 "by screenshot (`frontend/tools/shots.mjs`), not by eye" and constraints 29–43 are declared screenshot-checkable (`visual-direction.md:54-55`).
- fixed by: **architect**

### F2 — [HIGH] 17.8's scroll restoration is specified only for Historial, but 17.8 names three lists
- pass: coverage
- location: `spec.md:206-208` (17.8); `design.md:431-436` (bullet is titled and scoped to Historial), `:456-459` (Hoy and the filtered list get only "a history pop"), R1 `:659-666`, Deferred 3 `:729-731`
- detail: R1's own reasoning — verified against `Screen.tsx:30`, where the scroll container is `<main className={s.scroll}>` and not the document — establishes that a history pop restores the location but not the offset. The design applies that conclusion to Historial and requires explicit capture/restore there, then relies on the unaided pop for Hoy and the filtered category list, where the same reasoning applies with the same force. An implementer following the document literally will build restoration for one of the three surfaces 17.8 names, and R1's warning ("the screen will look right in every manual test that does not scroll first") applies to the other two with nothing pointing QA at them.
- fixed by: **architect**

### F3 — [HIGH] 18.2 says "every"; KD-21 caps the filtered list at 200 with no way to reach the rest
- pass: contradiction
- location: `spec.md:228-229` (18.2); `design.md:123-133` (KD-21), `:688-695` (R4); cap verified at `backend/autonomos/api/expenses.py:58` (`limit: int = Query(200, ge=1, le=200)`)
- detail: adjudicated in full above. Not silent, not unbounded, not a violation of any approved assumption — A26 is scoped to Historial (`spec.md:286-290`) — but it is a knowing partial against a criterion whose wording is absolute, in a spec that demanded the opposite for the sibling list (16.8) and that spent Non-Goal 12 explaining why an existing cap of the same shape is a deferred defect. The decision of whether "every" tolerates a bound belongs to the person who wrote "every".
- fixed by: **human** at Approve Plan (accept R4 as written, or rule that 18.2 binds literally, in which case **architect**)

### F4 — [MEDIUM] A save that changes nothing marks the expense "edited"
- pass: contradiction (adjudicated as none, but user-visible)
- location: `spec.md:196-198` (17.5); `design.md:681-686` (R3); verified at `GastoForm.tsx:165-171` (all five fields sent on every submit) and `repo/expenses.py:228-231` (`updated_at` rewritten whenever any settable key is present)
- detail: 17.5 states only the positive direction, so the design does not violate it. But the detail screen will report "edited since recorded" about records the user merely opened and re-saved, and A30 (`spec.md:301-307`) sold this fact to the human as one worth surfacing on the grounds that it explains the record. A human who reads A30 and then meets R3 may want the indication tightened or dropped; the design is right that fixing it server-side would change the semantics of a shipped, tested PATCH.
- fixed by: **human** at Approve Plan (accept R3), or **pm** if 17.5 is to be tightened to exclude no-op saves

### F5 — [MEDIUM] Constraint 34's frame/content reconciliation is correct but under-enumerated, and was made by the Architect
- pass: contradiction / ambiguity
- location: `visual-direction.md:80-81` (34) against `:59-63` (29) and Run 01 `:64-67` (9, 11); `design.md:428-429`, `:764-767`
- detail: a literal reading of 34 cannot be satisfied on any Finanzas tab, because constraint 29 in the same document mandates an operable tab strip on Historial. The frame/content reading is therefore forced, and it matches how Hoy and Mes already comply (`App.tsx:76-98`). The design's statement of it names only the capture bar and the bottom nav. Historial also inherits the four-tab strip and the AppBar's operable "Ajustes" link (`App.tsx:81`), both unmentioned. As written, a QA pass reading constraint 34 literally has two operables the design never excused. The reconciliation should be ratified by the constraint's author rather than resolved in the design document.
- fixed by: **pm** (ratify the reading and its full enumeration at Approve Plan)

### F6 — [MEDIUM] After an edit round trip, the detail's "close by history pop" lands on the detail again, not on the list
- pass: underspecification
- location: `design.md:584-587` (mechanism 2, "the detail can close by popping"), `:459-461` ("mirroring `Entrada.tsx:131`"); verified at `Entrada.tsx:131` (`navigate(\`/diario/${id}\`, { replace: true })`) and `Entrada.tsx:41` (edit is a push)
- detail: the cited journal pattern pushes on edit and replaces on save, giving the stack `[list, detail, editar] → [list, detail, detail]`. The journal survives this because its read screen closes to a **fixed path** (`Entrada.tsx:34`, `back="/diario"`). The expense detail cannot use a fixed path — it must pop, precisely so `?mes=` and `?categoria=` come back (`:585-587`). So after list → detail → editar → save, one pop returns the user to the detail he is already looking at. 17.8 is scoped to "leaves the detail view **without** editing", so nothing is strictly violated, but the design states the pop mechanism unconditionally and Deferred Decision 4 (`:732-734`) considers push-versus-replace only for category switching. An implementer must invent the answer for the edit round trip.
- fixed by: **architect**

### F7 — [MEDIUM] The `from` hint is specified as "the originating list's path" — unclear whether it carries search params
- pass: underspecification
- location: `design.md:588-590`, `:463-464`, `:600`
- detail: `from` exists to give 17.9 a landing place after a delete. If it carries only a pathname, deleting from a detail opened out of a filtered category list lands on `/finanzas/mes` with no `?mes=`/`?categoria=`, i.e. the current month with no selection — the exact reset B2 and 18.9 were introduced to eliminate, arriving through the one path they do not govern. If it carries path plus search, the behaviour is right. The design does not say which, and the distinction is invisible until someone deletes an expense from a past month.
- fixed by: **architect**

### F8 — [LOW] `before_id` with `order="spent"` is a defined capability serving no criterion
- pass: coverage (reverse direction)
- location: `design.md:331-339`, `:350-351`
- detail: the contract defines the combination, then states no client sends it and `next_before_id` is always `null` for it. Justified as orthogonality and as R4's escape hatch (`:694-695`), and cheap; recorded because it is the only contract surface in this run answering to nothing in the spec.
- fixed by: **architect** (accept as documented, or mark explicitly out of scope for this run)

### F9 — [LOW] `keys.expense` and the new `['expenses', …]` prefix differ by one character, and invalidation correctness depends on the difference
- pass: terminology drift
- location: `design.md:276-278`, `:196-200`, `:485-488`, Deferred 7 `:743-744`; verified at `api/queries.ts:31` (`expense: (id) => ['expense', id]`) and `:42-45`
- detail: TanStack matches keys by prefix, and `['expense']` does not match `['expenses', …]`, which is exactly why the design correctly requires `['expenses']` to be added to `invalidateExpenseViews`. The design is right; the naming is one letter from a silent bug, and the failure mode (a deleted expense lingering in Historial, 16.11) is the one KD-25 already flags as a consequence to honour.
- fixed by: **architect** (a distinguishable key name, or an explicit note in the file)

### F10 — [LOW] The router-state hint is named `from` while the design states parameter names are Spanish
- pass: terminology drift
- location: `design.md:181-182` ("Segments and parameter names are Spanish"), `:588-590` (`from`), `:600`
- detail: the Spanish rule is stated for URL segments and search params, and `from` is router state rather than a URL parameter, so this is not a violation — recorded only because the design introduces exactly one new named piece of navigation state and names it in the other language.
- fixed by: **architect**

### F11 — [LOW] `factory/context/architecture.md:237` documents the route mapping this design changes
- pass: contradiction (across artifacts, informational)
- location: `factory/context/architecture.md:237` (`/finanzas/gasto/:id → EditarGasto App.tsx:52`), `:310`; `design.md:146-158`
- detail: a stale context artifact, not a design defect — noted so a later reader does not treat the context map as the current contract for this route.
- fixed by: **architect** (context regeneration after implementation)

### F12 — [LOW] No loading or unreachable state is named for Historial or the filtered category list
- pass: underspecification
- location: `design.md:421-430`, `:465-479`; the design names states for the detail (`:450-452`) and the empty cases (`:426`, `:475`) only
- detail: not a gap that forces invention. The unreachable case is handled by the app-level `ReachabilityBanner` inside `FinanzasTabs` (`App.tsx:94`, `:133-137`), which both new tabbed screens inherit as frame, and the pending case has one obvious in-repo precedent (`Mes.tsx:36`, the `cargando` skeleton). Recorded for completeness against Run 01 constraints 16 and 18, which remain in force.
- fixed by: **architect** (one sentence, or explicitly leave to the existing pattern)

No findings from the ambiguity pass: `design.md` contains no `TODO`, `TBD`, `???`, `XXX` or `<placeholder>`, and no vague adjective standing in for a measurable criterion. Its two uses of "fast" (`:120`) and "simple" are argumentative prose about rejected alternatives, not requirements. Every deferral is enumerated in § Deferred Decisions with the binding part stated and the free part named.

No findings from the principles pass: no `PRINCIPLES.md` exists anywhere in this repository, so there was no stated principle to check the design against. Nothing was inferred in its place.

**13 findings. None omitted.**

## Items for the human at Approve Plan

1. **The filtered category list stops at 200 expenses.** Open a category in a month and you see up to 200 of its expenses; beyond that there is no "show more" and no way to reach the rest, even though the criterion you approved says "every expense of that category". The count shown on screen stays correct either way. You would need roughly seven expenses in one category every day for a month to hit it. (F3)
2. **Coming back from an expense may not return you to where you were scrolled.** The design guarantees this for Historial but leaves it unstated for the Hoy list and for a filtered category list. It will look correct in any test that does not scroll down first. (F2)
3. **Opening an expense, changing nothing, and pressing save will still mark it "edited".** The detail screen will say so. This is a deliberate trade to avoid changing a shipped, tested save path. (F4)
4. **Four existing screenshot recipes point at the screen that is being replaced.** The design says the route move needs no other changes; it does need these four fixed, plus new recipes for the three new screens, or the visual checks that Reviewer and QA rely on will silently photograph the wrong thing. (F1)
5. **One of your visual constraints was reinterpreted inside the design rather than referred back to you.** Constraint 34 says Historial has "nothing else operable" — read literally it forbids the tab strip your own constraint 29 requires, so the design reads it as governing the screen's content and not the app's frame. That reading is the only workable one, but it is your constraint, and the design's list of what counts as "frame" is missing the tab strip and the Ajustes link. (F5)

## Scope Statement

I compared artifacts to each other: spec against design, visual direction against design, and both against the Run 01 artifacts they declare still in force. I did not review code — none exists for this feature — and I did not judge whether the design is good, only whether it is consistent with and complete against what was approved. I read product source only to verify specific factual claims the design makes, and every such claim I checked held: the route table and tab array in `App.tsx:38-98`, the scroll container and frame composition in `Screen.tsx:14-35` and `:58-118`, `useState` at `Mes.tsx:33`, `invalidateExpenseViews` at `api/queries.ts:42-45` and the key shapes at `:24-36`, the absence of any frontend caller of `GET /api/expenses`, the `limit` bounds at `api/expenses.py:58`, the `list_expenses` signature and its `day_summary` caller at `repo/expenses.py:242-272`, the stub's bare-path keying at `test/server.ts:73`, the journal read/edit pattern at `Entrada.tsx:34`, `:41`, `:131`, the row link at `Hoy.tsx:53`, and the screenshot specs at `tools/shots.mjs:210-227`. I did not run the test suite, did not render any screen, and did not verify the constraint 29 tab-width estimate in R2 — that is a screenshot measurement and R2 correctly says so. No `PRINCIPLES.md` exists in this repository, so the principles pass had no input; I did not substitute my own. All other named artifacts were readable in full.

---

**Verdict: CONCERNS.** Counts: **35 covered · 2 partial · 0 uncovered** of 37 acceptance criteria (100% claimed by at least one design element); **14 covered · 1 partial · 0 uncovered** of Design Constraints 29–43. 13 findings — 3 HIGH, 4 MEDIUM, 5 LOW, 1 informational — of which 9 route to **architect**, 1 to **pm**, and 2 to the **human** at the gate. No acceptance criterion is covered by nothing, no non-goal is breached, and no approved assumption is silently reversed, so this does not FAIL. The two partials (18.2's 200-row cap against a criterion that says "every"; 17.8's scroll restoration specified for one of the three lists it names) and the four screenshot recipes pointing at the route KD-23 repurposes are what a human should weigh before approving.

---

> **PERSISTED BY THE ORCHESTRATOR (second time).** The analyst's `Write` was
> blocked again on the re-check, and it said so explicitly. The section below is
> its re-check report **verbatim and unedited**. Persisted 2026-08-10, same
> analyst agent `a9d0fdfb91cd3c7da`, against `design.md` at 970 lines after the
> Architect's revision for F1, F2, F5, F6, F7, F8, F9, F10, F12.

---

This is a re-check only; I did not redo the coverage tables. **My `Write` is still blocked — the text below is for you to persist** (append to `/home/david/Proyectos/Autonom-OS/factory/analyst/analysis.md` as a re-check section). I have no write access; do not read this as a role that had it.

# Re-check of revised `design.md` (970 lines)

## Per-finding verdicts

**F1 — closed.** `tools/shots.mjs` is now in the changed-file list (`:309-312`), the Summary claim is narrowed to "no *row-level* call site changes" with the harness named as the exception (`:33-36`), all four recipes are repointed to `/finanzas/gasto/1/editar` (`:728-733`), and the visual pinning is added to the B1 test section (`:802-805`). Both factual claims check out: `shots.mjs:823,831` computes `path` from `new URL(request.url).pathname` and falls back to `shot.stubs?.[path]`, so one `'/api/expenses'` stub does serve any query string, exactly as `test/server.ts:73` does; and `shots.mjs:891` throws literally `no control labelled "${action.clickText}"`. Recipe-to-constraint coverage is complete for 29, 30, 31, 33, 34, 35, 36, 38, 39, 40, 41, 42, 43 — with two gaps at 32 and 37, below as N1/N2. `finanzas-mes--categoria` at `?categoria=1` resolves to Comida (`db/seed.py:14`, asserted at `test_misc_api.py:213`), which the seeder populates in the current month, so that recipe shows a real filtered list rather than the empty state; and `Page.navigate` takes `BASE + shot.url` (`shots.mjs:961`), so the first query-string recipe in the file works.

**F2 — closed.** The Historial-scoped bullet is replaced by "Every list returns in the state it was left in" (`:479-493`), which names Hoy, Historial and the filtered month list, splits rows (cache) from offset (explicit capture/restore), and binds the offset obligation on all three in as many words — "Hoy is not exempt, and a long day's ledger scrolls… which mechanism is the implementer's (Deferred 3), that it covers all three is not". R1 is rewritten to match (`:826-837`) and directs QA at all three scrolled. This genuinely binds all three.

**F3 — correctly not closed.** KD-21 (`:124-135`) and R4 (`:859-866`) are byte-identical to the prior version. The new "Still open" subsection (`:959-963`) states the conflict verbatim, including "18.2 says 'every expense of that category'" and "no way to reach the rest", and names the remedy. Not softened.

**F4 — correctly not closed.** R3 (`:849-857`) is byte-identical. The "Still open" entry (`:964-967`) concedes the A30 tension rather than resting on the "17.5 states only the positive direction" defence alone. Not softened.

**F5 — closed, and the Architect's fifth operable is real.** Verified against source: `ReachabilityBanner` is rendered inside `FinanzasTabs` at `App.tsx:94`, and the component at `:128-142` carries an operable `<Link to="/sin-servidor">{servidor.verQueHacer}</Link>` at `:136-138`. I missed it; the Architect is right. Its enumeration is correctly qualified as conditional ("when the server is unreachable", `:470-471`) since `:130` returns `null` while healthy. The full five are stated in both places (`:467-477`, `:940-951`), and the reading is explicitly routed to PM for ratification rather than asserted — which is the right disposition.

**F6 — closed.** The push/pop table (`:516-537`) is sound. `[lista, detalle]` → push `editar` → pop returns to the existing detail entry with no duplicate, so a second pop reaches the list; the `Entrada.tsx:131` replace-on-save divergence is stated with the reason (the journal escapes it only because `Entrada.tsx:34` closes to a fixed path, which this detail cannot do). Both 17.7 branches are satisfied by the same pop, and "showing the values currently stored" holds because `useUpdateExpense`'s `onSuccess` calls `invalidateExpenseViews` (verified, `api/queries.ts:180`), which invalidates the `['expense']` prefix that `keys.expense(id)` sits under. The no-entry-to-pop fallback (`:536-537`) targets the detail path, not `…/editar`, so the B1 structural test at `:796-800` remains satisfiable.

**F7 — closed.** `desde` carries pathname *and* search, with the concrete example `/finanzas/mes?mes=2026-07&categoria=3` and the reason (`:540-547`, restated `:687-692`, `:702`).

**F8 — closed.** Status made explicit at `:365-373`: defined, accepted, serves no acceptance criterion, sent by no client, kept because rejecting it would cost a new validation reason outside the closed set at `errors.py:16-49`, and because it is R4's remedy. "Implementers must not build UI against it" is the line that makes it safe.

**F9 — closed; the Architect's correction of my framing is right, and I accept it.** TanStack matches query keys element-wise, so `['expense']` would never have matched `['expenses', …]` — there was no false-positive-match risk, and my headline "one character from a silent bug" overstated it (my own detail line already described the mechanics correctly). The real exposure was a human reading the two prefixes as the same thing and assuming one invalidation covered both. `['expense-list', …]` is applied consistently — `:200`, `:301-304`, `:317`, `:323`, `:580`, `:880`, `:918` — with `['expenses']` surviving only in the two sentences explaining why it was rejected (`:218`, `:304`).

**F10 — closed.** `estado.desde` throughout (`:522`, `:540`, `:687`, `:702`, `:706`), with the Spanish-naming rationale stated at `:545-547`.

**F11 — correctly untouched**, per your routing.

**F12 — closed.** New client-contract bullet at `:549-559`: pending follows `Mes.tsx:36`/`Hoy.tsx:17`'s `.skeleton` + `common.cargando`; unreachable is inherited from `FinanzasTabs`'s `ReachabilityBanner` and nothing new is built; the in-flight "ver más" must live on the control rather than become a bottom spinner, which is the one case with no precedent and the one the visual direction's "avoid" list names. Its `requirements: none` is legitimate — no criterion in 16.1–18.13 asks for a pending state, and 16.10's empty state is claimed elsewhere.

## New findings

### N1 — [MEDIUM] Constraint 32's *present* state is photographed by neither new recipe
- location: `design.md:752-755`; `frontend/tools/seed.mjs:33-38` and `:51-60`; Deferred Decision 1
- detail: the design says `finanzas-historial--ver-mas` stubs `next_before_id: null` to capture the absence, "the live shot above supplies the present state". It does not. The seeder writes 4 expenses for today plus 8 for the month — **12 rows** — against an intended page size of 30, so the live `finanzas-historial` shot returns `next_before_id: null` and renders no control. Both recipes then photograph the same half of a constraint that requires the two states to be "distinguishable on sight". The recipe named `--ver-mas` is the one capturing the absence of "ver más", which is also backwards. The stub that exists in the design's own vocabulary would fix it: give `--ver-mas` a `next_before_id` integer and let the live shot supply the null case.
- fixed by: **architect**

### N2 — [LOW] Constraint 37's "unclamped description" has no recipe that could fail
- location: `design.md:758-763`; `seed.mjs:34` (expense 1 is "Café y pan")
- detail: `gasto-detalle` is live against a short description and `--sin-descripcion` stubs `description: null`. Clamping, line-limiting or a "seguir leyendo" affordance only becomes visible on a long description, and no recipe supplies one. A stubbed long-description shot is the same one line as the two already listed.
- fixed by: **architect**

### N3 — [LOW] The Components heading still says "four existing files change"; the list has eight
- location: `design.md:278` against `:292-312`
- detail: pre-existing (it was seven before) and widened by adding `tools/shots.mjs`. Harmless except to a Reviewer counting changed files against the heading.
- fixed by: **architect**

## Other checks

Coverage is unchanged at **37/37**. There are now 17 `requirements:` lines (was 16); the union is identical plus the new `requirements: none` internal entry, which is legitimately requirement-free. No criterion lost a claimant: the replaced scroll bullet still carries `16.7, 17.8, 18.9` (`:493`) and the split of "Leaving the detail and leaving the form" still carries `17.7, 17.8, 17.9` (`:548`). No scope creep in the 200 added lines — the new material is all specification of behaviour already required, plus the screenshot recipes, plus the `before_id` status paragraph, and no new endpoint, parameter, response field, route or component appears. The contract, KD-18…KD-27, the data-model section and the non-goal position are otherwise unchanged.

CONCERNS
