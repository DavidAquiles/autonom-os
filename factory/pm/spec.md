# Autonom-OS — Product Spec (Run 02, brownfield feature)

**Status: FINAL.** Kickoff gate passed; the one escalated question was answered
and is folded in (§ Open Questions, and Non-Goal 12). Everything else I could
responsibly decide is recorded in § Assumptions, which is where the human
exercises control at the Approve Plan gate — read § Assumptions and § Behaviour
That Changes before § Acceptance Criteria.

This spec is **additive** to `factory/runs/01-greenfield/pm/spec.md`, which
remains in force. Requirements 1–15 and their criteria are unchanged and are not
restated here; criterion numbers continue from where that spec stopped, so this
run introduces **Requirements 16, 17 and 18** (criteria 16.1–18.13). Numbers are
stable and are cited by the Architect's Interface Contract, Reviewer findings and
QA results; a retired criterion keeps its number rather than being renumbered.

---

## Problem Statement

David's record of his spending is only reachable through two windows onto it —
**today**, and **this month as category totals**. Neither window answers the two
questions he actually has.

**"What did I just put in?"** Every list in the app is ordered by the date the
money was spent. An expense he records right now but dates to last Tuesday lands
a screenful down, among last Tuesday's rows. He cannot confirm what he just
recorded, and he cannot find the thing he recorded ten minutes ago, without
knowing in advance which day it belongs to. The one ordering that matches how he
actually accumulated the record — the order he typed it in — is the one ordering
the app cannot show him.

**"What was that $506.500 in Comida actually made of?"** The month screen gives
him a category, an amount and a bar, and stops. The individual expenses behind
that number are not reachable from it at all. The breakdown answers "where did it
go" at the level of a word and refuses to answer it at the level of a purchase.

Underneath both sits a third problem. The only way to look at a single expense is
to open the form that edits it. Examining the record and changing the record are
the same act, so a mis-tap while checking something puts him on a live, editable
form over real data — and the form, being a form, shows him less than a reading
surface could: no full date, no record of when he entered it, a description in a
field rather than on the page.

**Falsifiable.** This statement is wrong if David can already reach an arbitrary
past expense in a few taps; or if he never records expenses out of date order, so
that spent-date order and entry order are the same thing for him; or if he is
content to read the month as totals and never wants the purchases behind them.

## Users

Unchanged: one user, David, on his own phone, in Spanish, against his own PC. See
Run 01 § Users. Nothing in this feature is for a second person.

## Non-Goals

Concrete things this pass will explicitly not do.

1. **No search.** Expenses are not searchable by text, amount, or anything else.
   Historial is browsed, not queried.
2. **No filtering of Historial.** The category filter is a month-view capability
   only, as asked. Historial shows everything, in one order, with no controls on
   it.
3. **No multi-select filter.** One category at a time; no "Comida + Transporte",
   no exclusion, no saved filter sets.
4. **No payment-method filter.** The "cómo se pagó" rows in the month view stay
   non-tappable. The ask named categories; the symmetric capability is a cheap
   follow-up, not this pass.
5. **No date-range picker, no custom periods, no presets.** Months are paged the
   way they already are.
6. **No user-chosen sorting.** Historial has exactly one order and no control to
   change it; the month's filtered list has exactly one order.
7. **No bulk operations.** No multi-select, no bulk edit, no bulk delete.
8. **No undo, no recycle bin, no trash.** Deletion stays exactly as destructive
   as it is today, with exactly the confirmation it has today.
9. **No new capture path.** Historial and the detail view do not add a way to
   create an expense; the existing capture bar remains the only one.
10. **No export of a filtered view.** Export stays whole-database, as it is.
11. **No charts.** The month breakdown bars are the only proportional display in
    Finanzas and gain nothing here.
12. **No change to Diario, Gimnasio, voice capture, or Análisis.** In
    particular, **Diario's journal list cap stays unfixed in this run — decided
    at the Kickoff gate, not overlooked.** The journal "Todo" tab shows only the
    50 most recent entries with no way to reach older ones
    (`frontend/src/api/queries.ts:197`, `limit: 50`); the server-side cursor that
    would page it already exists (`backend/autonomos/api/journal.py:21-32`) and
    the Spanish copy for the control is already written and rendered nowhere
    (`frontend/src/copy/es.ts:118`, `cargarMas`). This is Run 01's deferred
    finding **F6** (`factory/runs/01-greenfield/state.json`,
    `reviewer/review.md:163-170`, `walkthrough.md:120`). I raised it as OQ1
    because Historial is being built with exactly the fix F6 needs, next door and
    cheap. **David chose to leave it:** this run stays exactly on the ask, F6
    remains a deferred finding and becomes a candidate follow-up run, and nothing
    is lost in the meantime because export still contains every entry. A later
    run should treat 16.7–16.9 as the pattern to copy.
13. **No exposure of `source`.** Nothing on any new screen reveals whether an
    expense was spoken or typed; Run 01 criterion 9.5 continues to bind.
14. **No change to the three bottom-nav destinations.** Historial is a tab inside
    Finanzas, not a fourth destination; Run 01 criterion 1.1 continues to bind.
15. **No data migration or backfill.** Registration order is derived from data
    already recorded on every existing expense.

## Behaviour That Changes (regression surface)

Two things that work today will work differently. Both are deliberate; both are
where a regression would hide.

**B1. Tapping an expense no longer opens the edit form.** Today, a row in the
Hoy ledger is a direct link into the editable expense form. From this feature on,
every expense row anywhere — Hoy, Historial, a filtered month list — opens the
read-only detail view, and editing is one further, explicit action from there.

*Why:* the app already has exactly this shape for the journal — an entry opens a
read screen, and editing is a labelled action on it — so this makes the two
modules consistent rather than inventing a pattern. It also makes a mis-tap
harmless, which matters on a phone, one-handed, in the street. The cost is one
extra tap to correct an expense. Correcting is rarer than looking; that is the
trade being made, deliberately. **This is the assumption most worth objecting to
at Approve Plan (A24).**

**B2. The month being viewed survives navigation.** Today the month shown in
"Este mes" is transient screen state: leave the screen and it resets to the
current month. Because this feature makes it possible to leave that screen — into
an expense's detail and back — the month, and the selected category with it, must
now be preserved across that round trip (18.9). Any existing behaviour that
assumed the month resets is affected.

---

## Acceptance Criteria

### Requirement 16 — Historial: every expense, in the order I recorded it

As the only user, I want to see my expenses in the order I entered them, so that
I can confirm what I just recorded and find what I recorded recently, without
first having to remember what date it belongs to.

#### Acceptance Criteria

16.1 WHEN the user opens Finanzas THEN the system SHALL present a tab labelled
     "Historial" alongside the existing Finanzas tabs, reachable from any other
     Finanzas tab in one interaction.
16.2 WHEN the user opens Historial THEN the system SHALL list expenses ordered by
     when each was recorded, most recently recorded first, regardless of the date
     each expense is dated for.
16.3 WHEN the user records an expense dated in the past THEN the system SHALL
     place it at the top of Historial, above expenses that are dated later than
     it.
16.4 WHEN the user edits an existing expense — including changing its date or its
     amount — THEN the system SHALL keep that expense in its original position in
     Historial and SHALL NOT move it to the top.
16.5 WHEN Historial lists an expense THEN the row SHALL show its amount, its
     category, its payment method, and the date the expense is dated for.
16.6 WHEN Historial is shown THEN the system SHALL state on screen, in Spanish,
     that the list is in the order the expenses were recorded, so that a list
     whose dates are not in descending order cannot be mistaken for a fault.
16.7 WHEN more recorded expenses exist than are currently shown THEN the system
     SHALL offer a visible control to show more, and using it SHALL append older
     records without changing the order of what is already on screen and without
     returning the user to the top of the list.
16.8 WHEN the user uses that control repeatedly THEN the system SHALL eventually
     reach the very first expense ever recorded. No recorded expense SHALL be
     permanently unreachable from Historial.
16.9 WHEN every recorded expense is already shown THEN the system SHALL present
     no control, label, or affordance implying more exist.
16.10 WHEN no expense has ever been recorded THEN Historial SHALL show a designed
      empty state — not a blank screen, not an error, not an empty list frame.
16.11 WHEN the user deletes an expense THEN the system SHALL remove it from
      Historial entirely, leaving no gap, placeholder, or "deleted" entry.
16.12 WHEN the user taps an expense in Historial THEN the system SHALL open that
      expense's detail view as described in Requirement 17.
16.13 WHEN the user opens Historial THEN the system SHALL show the first
      screenful of recent expenses without first fetching every expense ever
      recorded.

### Requirement 17 — Seeing one expense before changing it

As the only user, I want to look at an expense and read what I recorded, so that
checking the record is not the same act as editing it and a mis-tap cannot put me
on a live form over real data.

#### Acceptance Criteria

17.1 WHEN the user taps an expense anywhere it is listed — Hoy, Historial, or a
     filtered month list — THEN the system SHALL open a read-only detail view of
     that expense and SHALL NOT open an editable form. *(Changes existing
     behaviour — see B1.)*
17.2 WHEN the detail view is shown THEN it SHALL show the expense's amount, its
     category, its payment method, the date it is dated for, and its description
     in full — no truncation, no clamping, no "seguir leyendo".
17.3 WHEN the expense has no description THEN the detail view SHALL omit it
     rather than showing an empty field, a placeholder dash, or a word standing
     in for "nothing".
17.4 WHEN the detail view is shown THEN it SHALL show when the expense was
     recorded; and WHEN that differs from the date the expense is dated for THEN
     both SHALL be shown, each labelled so the two cannot be confused.
17.5 WHEN an expense has been edited since it was recorded THEN the detail view
     SHALL indicate that plainly, without implying an error, a warning, or a
     problem.
17.6 WHEN the detail view is shown THEN it SHALL present exactly one clearly
     labelled action to edit that expense, and taking it SHALL open the existing
     expense form pre-filled with that expense's current stored values.
17.7 WHEN the user leaves the edit form that was opened from a detail view —
     whether by saving the change or by closing without saving — THEN the system
     SHALL return to that expense's detail view, showing the values currently
     stored.
17.8 WHEN the user leaves the detail view without editing THEN the system SHALL
     return to the list the user arrived from, in the same state: same tab, same
     month, same category selection, same position in the list.
17.9 WHEN the user deletes the expense from within the edit form THEN the system
     SHALL NOT leave the user on a detail view of a record that no longer exists.
17.10 WHEN the detail view shows an expense THEN nothing on it SHALL reveal
      whether that expense was captured by voice or typed.
17.11 WHEN the user opens a detail view for an expense that does not exist THEN
      the system SHALL say so plainly in Spanish, rather than showing a blank
      screen, a spinner that never ends, or a raw technical error.

### Requirement 18 — This month, one category at a time

As the only user, I want to open a category in the month breakdown and see the
actual purchases behind its number, so that "where did it go" is answerable at
the level of a purchase and not only at the level of a word.

#### Acceptance Criteria

18.1 WHEN the user views a month's category breakdown THEN the system SHALL allow
     any listed category to be selected in one interaction.
18.2 WHEN a category is selected THEN the system SHALL show every expense of that
     category dated within the month being viewed, and no expense of any other
     category and no expense of any other month.
18.3 WHEN a category is selected THEN the system SHALL show the category's name,
     that category's total for that month, and how many expenses it contains.
18.4 WHEN a category is selected THEN the month's own total SHALL remain visible
     and SHALL be distinguishable from the category's total.
18.5 WHEN a category is selected THEN the system SHALL offer a visible,
     single-interaction way to clear the selection and return to the month's full
     breakdown.
18.6 WHEN a category is selected and the user selects a different one THEN the
     system SHALL show only the newly selected category, replacing the previous
     selection rather than combining the two.
18.7 WHEN the user moves to a different month while a category is selected THEN
     the system SHALL clear the selection and show the new month's full
     breakdown. At no point SHALL one month's heading appear over another
     month's expenses.
18.8 WHEN the user taps an expense in a filtered category list THEN the system
     SHALL open that expense's detail view as described in Requirement 17.
18.9 WHEN the user returns from that detail view THEN the system SHALL show the
     same month and the same selected category as before, not a reset view of the
     current month. *(Tightens existing behaviour — see B2.)*
18.10 WHEN the selected category's list becomes empty — because its last expense
      in that month was deleted, recategorised, or redated out of the month —
      THEN the system SHALL show a plain state saying there is nothing left in
      that category for that month, rather than a blank area or a zero row.
18.11 WHEN a month contains no expenses at all THEN the existing empty state
      (Run 01 criterion 4.5) SHALL continue to apply and no category selection
      SHALL be offered.
18.12 WHEN a filtered category list is shown THEN each row SHALL show the
      expense's amount, its payment method, the date it is dated for, and its
      description when it has one.
18.13 WHEN a filtered category list is shown THEN its expenses SHALL be ordered
      by the date they are dated for, most recent first — this list answers a
      question about a month, not about the order things were recorded, and is
      deliberately ordered differently from Historial (16.2).

---

## Assumptions

Decisions I took rather than escalating. Each is cheap to reverse now and
expensive to discover at QA. **A24 is the one most worth objecting to** — it
changes behaviour David uses every day.

- **A23.** Historial is a fourth tab inside Finanzas, ordered
  *Hoy · Este mes · Historial · Análisis*. The three views of the record sit
  together and Análisis, which is derived rather than recorded, stays last. It is
  not a fourth bottom-nav destination, because Run 01 criterion 1.1 fixes those
  at three.
- **A24.** *(the one to look at twice)* Tapping an expense row anywhere now opens
  the detail view, not the edit form — including in Hoy, where it works the other
  way today. Chosen for consistency with the journal's existing read-then-edit
  shape and to make a mis-tap harmless; the price is one extra tap to correct
  something. *Reversible — say so if you'd rather Hoy keep jumping straight to
  edit and only the two new lists go via the detail.*
- **A25.** The detail-then-edit relationship for an expense mirrors the one the
  journal already has for an entry, rather than inventing a second shape for the
  same idea.
- **A26.** Historial covers **every expense ever recorded**, loaded a screenful
  at a time with an explicit control to show more (16.7–16.9). A fixed cap was
  rejected on purpose: the previous run shipped exactly that in Diario (50
  entries, no control) and it was deferred as a defect. Repeating it silently
  here would be the same mistake twice.
- **A27.** Historial is a flat, continuous stream with no grouping by day or
  month. The user's own words were "no matter the date"; date headings would
  reintroduce exactly the ordering he asked to get away from. Each row carries
  its own date instead (16.5), and the screen says what its order is (16.6).
- **A28.** Editing an expense does not move it in Historial (16.4). "Order of
  registration" means when it was recorded, and that does not change when the
  contents do.
- **A29.** A deleted expense simply disappears from Historial — no tombstone, no
  gap, no "eliminado" row. Deletion in this product is already permanent and
  confirmed; a visible ghost would be a new concept nobody asked for.
- **A30.** The detail view surfaces two facts the app has never shown anywhere:
  **when the expense was recorded** (17.4) and **whether it has been edited
  since** (17.5). Both are already stored on every expense. Without them the
  detail view is only a slower version of the list row, and in a
  registration-ordered list the recording time is the thing that explains why a
  row sits where it sits. *Reversible — say so if you'd rather the detail stayed
  strictly to what you entered.*
- **A31.** Deleting stays inside the edit form, where it lives today, with its
  existing confirmation. The detail view offers only "editar". This diverges
  from the journal's read screen, which offers both, and does so deliberately:
  one delete path per expense, and deletion should stay slightly effortful.
- **A32.** One category at a time in the month view. Multi-select was not asked
  for and makes the "which total am I looking at" question harder in the exact
  place this feature is trying to make it easier.
- **A33.** Selecting a category does **not** change the big month total; the
  category's own total is shown separately and labelled (18.3, 18.4). Swapping
  the hero number under the user would make it impossible to tell at a glance
  which figure is on screen.
- **A34.** Paging to another month clears the category selection (18.7). Keeping
  it would mean silently showing a different category's month, or an empty
  filter, with no obvious cause.
- **A35.** The category rows in the breakdown become the selection affordance;
  the payment-method rows stay non-tappable. The ask named categories.
- **A36.** Historial has no controls on it at all — no search, no filter, no
  sort. It has exactly one job: everything, newest-recorded first.
- **A37.** The filtered month list is ordered by spent date, newest first
  (18.13), not by registration order. It is answering a question about a month.
  The two lists ordering differently is intentional and each says which it is.
- **A38.** Nothing on any new surface distinguishes a voice-captured expense from
  a typed one, extending Run 01 criterion 9.5 to the new screens by construction
  — the API still does not return `source`.
- **A39.** The month being viewed and the selected category become part of the
  app's navigable state, so that returning from a detail view restores them
  (18.9). Today the month is transient screen state; this feature is what makes
  that a defect rather than a detail.
- **A40.** No new formatting, date rendering, or copy mechanism. New screens use
  the single peso formatter, the single date renderer, and the single Spanish
  copy module the product already has. The word "Historial" is the user's own and
  is used as the tab label.
- **A41.** No migration and no backfill. Every existing expense already carries
  the timestamp that registration order is derived from, so Historial is correct
  for records created before this feature existed.
- **A42.** The detail view is reachable only by tapping an expense in a list. No
  deep link, no "previous / next expense" navigation, no swiping between
  expenses.

## Open Questions

**None.**

One question was escalated at Kickoff and has been answered.

**OQ1 — Should Diario's list cap (Run 01 finding F6) be fixed in the same pass?
— Answered: no. Option B, leave it.** David's reasoning as given: the run stays
exactly on the ask; F6 stays a deferred finding and can be a follow-up run later;
nothing is lost because export still contains everything. Folded into Non-Goal 12
with the citations, so a later reader can see it was considered and consciously
excluded at a gate rather than missed.

The uncertainties I chose not to escalate are recorded above as Assumptions.
**A24** (every expense row now opens the detail view rather than the edit form,
including in Hoy) is by some distance the one most worth a second look at Approve
Plan, followed by **A30** and **A31**.
