---
name: autonomos-constraints
description: Autonom-OS host hardware facts and the swappable-AI-layer commitment made to David at the Kickoff gate
metadata:
  type: project
---

Autonom-OS runs on David's own PC: 13 GB RAM (~6.7 GB actually available), 8 CPU
cores, integrated AMD Radeon Vega (no dedicated GPU, no CUDA/ROCm), 37 GB free
disk. Installed: git 2.53, python3 3.14.4, node v24.18.1, npm 11.16, docker
29.6.2, chromium 150. Not installed: pytest, playwright, sqlite3 CLI (Python
`sqlite3` module is present). Headless Chromium renders files under the project
or `$HOME` but produces nothing under `/tmp`.

The orchestrating session committed to David that **the LLM layer and the
transcription layer are swappable behind a real interface** — moving off local
inference must be a configuration change, not a re-architecture.

**Why:** David chose fully-local processing (Req 15) after being told the local
LLM would be slow on this hardware. The swappability promise is what made that
choice safe to accept; it is a design requirement, not a nice-to-have.

**How to apply:** Size any model choice to ~6.7 GB RAM with no GPU and honour
the latency bounds PM wrote (8.8: transcript or explicit failure in 30 s; 11.12:
working state in 1 s, answer or failure in 120 s). Never design as if latency
were free. Any new AI capability goes behind the same provider interface.
