---
name: autonomos-context
description: Autonom-OS is a single-user Spanish Android PWA built through a phase-gated factory workflow; port 8000 is permanently unavailable on this host
metadata:
  type: project
---

Autonom-OS is a personal life-tracker for one user (David) — gastos, diario, and
a Gimnasio placeholder — in Spanish, phone-first, with a local whisper.cpp +
Ollama stack on his own PC. There is no second user and no cloud service.

**Why it matters for suggestions:** optimise for one person's capture speed, not
for generality. Slow local inference is an accepted trade-off he made with the
measured numbers in front of him (spec.md A21) — proposing a cloud model or
treating slowness as a defect re-litigates a decision he already took.

**How to apply:**
- **The API listens on 8001, not 8000.** Port 8000 is held permanently by
  `trace_erp_api`, a container from David's unrelated `trace_2026_deploy`
  project. It is not ours and must not be stopped or reconfigured. Any dev proxy
  or curl must target 8001.
- Work arrives through a phase-gated factory: PM's `factory/pm/` spec and visual
  brief, Architect's `factory/architect/design.md`, then implementer lanes that
  run concurrently in one working tree. **Never `git add -A`** — stage owned
  paths explicitly; the other lane's in-flight files are in the same tree.
- Design Constraints in `factory/pm/visual-direction.md` are numbered and
  pass/fail; Reviewer and QA check the built UI against them by number.

Related: [[verify-interactive-states]], [[env-chromium-sandbox]].
