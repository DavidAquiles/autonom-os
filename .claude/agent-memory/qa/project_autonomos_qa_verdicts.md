---
name: autonomos-qa-verdicts
description: What Autonom-OS QA passes have found — Run 01 (2026-08-06, four failing criteria) and Run 02 (2026-08-10, 37/37 pass with six non-blocking defects)
metadata:
  type: project
---

## Run 01 — first full pass, 2026-08-06, at `528459e`

Four acceptance criteria failed; everything else passed and all 28 Design Constraints held.

- **9.2** — an undetermined *amount* or *category* is left empty but carries no "needs input"
  marker; only the payment method does.
- **11.1 / 11.2** — one root cause: the local 3B model's **prose** is unguarded. In 3 of 7 runs a
  journal answer asserted something the user never wrote. NumericGuard checks numeric
  *membership*, not meaning.
- **11.15** — a calendar month with no data writes an `empty` summary row that masks the previous
  `ready` one. One unused month permanently hides the last real summary.

Rework worth remembering: 11.12 needed two attempts; 13.8's link had *never* worked despite the
implementer note claiming it did.

## Run 02 — brownfield feature, 2026-08-10 (Historial, expense detail, month by category)

**37/37 criteria pass, 0 rework loops** (`state.loops` was `{0,0}`), constraints 29–43 all pass.
The run's named biggest risk — scroll restoration on all three lists (17.8/R1) — **holds**:
Historial 420→420, Hoy 394→394, filtered month list 400→400, and 2400→2400 after paging.

What running it found that reading it did not:

- **Reviewer's F2 does not reproduce** (tab switch overwriting the outgoing list's offset) —
  four attempts including wheel-driven scroll and a 200 ms switch. A static "not decidable by
  reading" finding can be closed by execution; say so plainly.
- **Reviewer's F1 is worse than described.** One Back after any delete renders the deleted
  expense *in full* under the "ya no existe" message, with a live edit action; saving from there
  reports "no alcanzo tu servidor" while the API answers `404 not_found`.
- **Any failure of `GET /api/expenses` is rendered as data, not as an error**: the filtered
  category band shows "ya no queda nada en «categoría»" (contradicting the breakdown above it),
  and Historial renders a completely blank `<main>`. A *total* outage is handled correctly; it is
  the partial failure — one endpoint down, `/api/health` still green — that is unhandled.

**Why:** three of these four are invisible to any suite and to static review; they only appear
when you scroll first, press Back, or fail one request while the app believes it is online.

**How to apply:** on any Autonom-OS rework, re-check (a) scroll offsets *after paging*, not just
on a fresh list, (b) what one Back tap does after a destructive action, and (c) each list screen
with only its own endpoint failing — `Network.setBlockedURLs ['*/api/expenses*']` while health
still answers is the cheapest way to produce it.

Environment and method: [[autonomos-qa-environment]].
