---
name: autonom-os-project
description: Autonom-OS is a personal life-tracker (Finances, Gym, Journal) for one user; zero-cost and simplicity are hard product constraints, not preferences
metadata:
  type: project
---

Autonom-OS is a single-user personal life tracker with three modules — Finances,
Journal, and Gym (placeholder only in the first pass). Two input methods across
modules: voice and manual. An LLM produces insights over the user's own data.

**Why:** The problem is capture friction, not review. Expenses happen on the
street in seconds; journal thoughts arrive unstructured at night. Any design that
adds a decision at capture time defeats the purpose of the app.

**How to apply:**
- **Zero cost is a first-class requirement**, on the same footing as the features.
  Any dependency, model, or service that has a paid tier, quota-to-paywall, or
  requires payment details is disqualified — say so rather than proposing it with
  a caveat.
- **Simplicity is a requirement too.** When a feature could be richer or simpler,
  the simpler reading is the correct default here.
- Gym is deliberately inert in pass 1 — a labelled navigation destination with no
  data model. Do not let scope creep into it.
- Deployment shape is fixed by the user: server + DB on his PC, phone connects.
  Do not re-litigate it.

Spec and visual brief live at `factory/pm/spec.md` and
`factory/pm/visual-direction.md`. See [[user-profile]].
