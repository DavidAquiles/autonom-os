---
name: autonomos-qa-verdicts
description: What Autonom-OS QA passes have found — Run 01 (2026-08-06, four failing criteria) and Run 02 (2026-08-10, 37/37 pass, three defects fixed on the first rework)
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

**37/37 criteria pass, 0 implementation rework loops before QA**, constraints 29–43 all pass.
The run's named biggest risk — scroll restoration on all three lists (17.8/R1) — **held from the
start**: Historial 420→420, Hoy 394→394, filtered month list 400→400, and 2400→2400 after paging.

What running it found that reading it did not, and how the one rework cycle went:

- **Reviewer's F2 does not reproduce** (tab switch overwriting the outgoing list's offset) —
  four attempts including wheel-driven scroll and a 200 ms switch. A static "not decidable by
  reading" finding can be closed by execution; say so plainly.
- **Reviewer's F1 was worse than described** (D1): one Back after any delete rendered the deleted
  expense *in full* under the "ya no existe" message with a live edit action. **Fixed first try**
  by popping two history entries and by making the not-found state replace the record instead of
  rendering above it. The forward-button entry survives by construction and is harmless — it
  renders the message alone, with zero actions. Verified.
- **Any failure of `GET /api/expenses` was rendered as data, not as an error** (D2/D3): the
  filtered band claimed "ya no queda nada en «categoría»" and Historial rendered a blank `<main>`.
  **Fixed first try** by one shared failure state ("No pude cargar esta lista… Reintentar") that
  stays silent when the reachability banner already speaks, so a total outage still shows exactly
  one message. The legitimate empty states (16.10, 18.10, 18.11) were **not** swallowed — check
  that specifically, it is the obvious over-correction.

**Why:** these are the surfaces where the app's promise (a record you can trust) is weakest, and
none of them is visible to a suite or to static review; they only appear when you scroll first,
press Back, or fail one request while the app believes it is online.

**How to apply:** on any Autonom-OS rework, re-check (a) scroll offsets *after paging*, not just
on a fresh list, (b) what one Back **and one Forward** do after a destructive action, and (c) each
list screen with only its own endpoint failing. One measurement trap: after deleting a row that
straddles the top of the viewport, the restored offset is one row height smaller (300→231, 350→281,
row = 69 px) — that is Chrome's scroll anchoring keeping the same rows visible, **not** a defect.
Confirm the deleted row's position before filing it.

Environment and method: [[autonomos-qa-environment]].
