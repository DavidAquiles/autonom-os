---
name: analyst-loop
description: How to handle an artifact-analyst FAIL on design.md, and the standing rule about correcting performance estimates
metadata:
  type: feedback
---

An artifact-analyst FAIL routed back by the orchestrator is the normal loop, not a
rejection. Fix findings **in place** in `design.md`; never renumber PM criteria or
KD/Interface-Contract identifiers, because the analyst report, Reviewer and QA all
cite them.

**Standing rule from the orchestrator: correct performance numbers rather than
defending them.** If an analyst's arithmetic on a stated throughput or latency
figure is sound, restate the honest larger number and tighten the budgets that
depended on the optimistic one.

**Why:** David already accepted that local inference is slow, so an honest larger
figure costs nothing with him and costs a lot if QA discovers the gap. Downstream
roles plan against whatever number the design states.

**How to apply:** label estimates as estimates; when a figure moves, check whether
the budgets derived from it (context size, token caps, timeouts) still fit the
criterion, and move them too. Findings routed to **human** — technology choices
with a cost/privacy trade — get one short *neutral* paragraph stating the residual
and what the realistic alternative costs, with no advocacy for the existing choice.
See [[autonomos-constraints]] and [[factory-artifacts]].
