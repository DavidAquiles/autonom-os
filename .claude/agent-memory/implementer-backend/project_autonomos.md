---
name: project-autonomos
description: What Autonom-OS is, who it is for, and which factory artifacts are binding on backend work
metadata:
  type: project
---

Autonom-OS is a single-user, self-hosted personal tracker for David: **Finanzas**
(expenses), **Diario** (journal), **Gimnasio** (a labelled placeholder with no
backend at all). Everything runs on his own PC — FastAPI + SQLite, whisper.cpp and
Ollama as loopback sidecars — reached from an Android phone over Tailscale HTTPS.
All UI copy is Spanish; the backend returns closed machine error codes instead.

**Why:** capture friction, not review friction, is the problem — an expense is made
on the street in seconds. Everything local, zero cost, no third-party processing
are hard requirements the human chose at the Kickoff gate, not preferences.

**How to apply:** before backend work, read `factory/architect/design.md` (binding;
its `## Interface Contract` is the frontend's only view of the API) and
`factory/pm/spec.md` (numbered acceptance criteria — the numbers are stable and
cited everywhere; never renumber them). Where design and code disagree, the design
wins until Reviewer says otherwise. Settled at the Approve Plan gate on 2026-08-05
and not to be re-litigated: CSV exports **cut**, nightly snapshots **kept**,
Android only, Tailscale's third-party residual **accepted**.

Related: [[factory-lane-discipline]]
