---
name: autonomos-qa-verdicts
description: What the first full QA pass on Autonom-OS found (2026-08-06) — four failing criteria and where the fragile surfaces are
metadata:
  type: project
---

First full QA pass, 2026-08-06, against Reviewer-APPROVED code at `528459e`. Four acceptance
criteria failed; everything else passed and all 28 Design Constraints held.

- **9.2** — an undetermined *amount* or *category* is left empty but carries no "needs input"
  marker; only the payment method does (`Tag need` exists for the method alone).
- **11.1 / 11.2** — one root cause: the local 3B model's **prose** is unguarded. In 3 of 7 runs a
  journal answer asserted something the user never wrote; one summary contained a bare figure
  ("(20)") that matches nothing on any screen. NumericGuard checks numeric *membership*, not
  meaning, so a number present for one reason is authorised everywhere.
- **11.15** — a calendar month with no data writes an `empty` summary row that masks the previous
  `ready` one, because `/latest` returns the most recent *finished* row and there is no endpoint
  that lists summaries. One unused month permanently hides the last real summary.

**Why:** these are the surfaces where the app's promise (a record you can trust) is weakest, and
three of the four are invisible to any test suite — they only appear when you run the model
repeatedly against real data.

**How to apply:** on any rework of this project, re-run the journal question **several times**
rather than once (a single clean run proves nothing about grounding), and re-check the
summary-selection rule with a gap month. The deterministic figure path — SQL aggregates,
percentages, month/day boundaries — was correct in every check and does not need re-litigating.

Rework history worth remembering: 11.12 needed two attempts (the first fix passed all 231 tests
while handing the provider a ~1.78e9-second timeout), and 13.8's link had *never* worked despite
the implementer note claiming it did. Both pass now; neither passed cheaply.

Environment and method: [[autonomos-qa-environment]].
