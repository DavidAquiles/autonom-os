---
name: autonomos-spec-continuity
description: Autonom-OS specs accumulate across factory runs — criterion numbers continue, they never restart at 1, and old artifacts stay in force
metadata:
  type: project
---

Autonom-OS runs the AI Software Factory repeatedly on the same shipped product.
Each run archives its artifacts under `factory/runs/NN-<name>/` and writes the
new ones to `factory/pm/`.

**The rule: acceptance-criterion and visual-constraint numbers are global to the
product, not to the run.** Run 01 (greenfield) ended at Requirement 15 (with
12.3 retired, not reused) and visual constraint 28. Run 02 (Historial / expense
detail / month category filter) therefore starts at Requirement 16 and
constraint 29.

**Why:** Architect's Interface Contract entries, Reviewer findings and QA
results all cite these numbers by address (`2.3`, `constraint 10`). Restarting
at 1 in a later run silently collides every citation and destroys the "is every
requirement built?" regex check that the numbering exists to enable.

**How to apply:** before writing a spec for any new run, read the most recent
`factory/runs/*/pm/spec.md` and `visual-direction.md` to find the highest number
used, and state in the new file that the earlier artifacts remain in force and
are not restated. Write the *additive* requirements only — do not copy forward
Requirements 1–15 or constraints 1–28.

See [[autonom-os-project]].
