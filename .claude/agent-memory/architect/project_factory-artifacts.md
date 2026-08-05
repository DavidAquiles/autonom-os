---
name: factory-artifacts
description: Where the AI Software Factory role artifacts live in Autonom-OS and which are authoritative for the Architect
metadata:
  type: reference
---

Autonom-OS uses the AI Software Factory role pipeline. Artifacts:

- `factory/pm/spec.md` — numbered requirements with two-level acceptance
  criteria (1.1, 11.12, ...). Criterion numbers are **stable**; retired criteria
  keep their number rather than being renumbered (e.g. 12.3 is retired).
- `factory/pm/visual-direction.md` — numbered Design Constraints (1-28), which
  Reviewer and QA enforce pass/fail. Not the Architect's to change, but a
  constraint there can rule a technical choice in or out.
- `factory/architect/design.md` — the Architect's single output.

**How to apply:** cite criteria by number in every Interface Contract entry's
`requirements:` line — the artifact-analyst computes coverage from those lines,
so an entry without one is a defect. Read the PM Assumptions section before the
criteria; it is the human's control surface and resolves things the criteria
leave implicit. See [[autonomos-constraints]].
