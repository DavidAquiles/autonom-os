---
name: autonomos-constraints
description: Autonom-OS host hardware facts and the swappable-AI-layer commitment made to David at the Kickoff gate
metadata:
  type: project
---

Autonom-OS runs on David's own PC: 13.1 GiB RAM, 8 CPU cores, integrated AMD
Radeon Vega (no dedicated GPU, no CUDA/ROCm), 37 GB free disk. **Available RAM is
~5.3 GiB, not the ~6.7 GB the PM spec states** — Ollama's startup log reports
`available="5.3 GiB"`, measured 2026-08-05. Budget against 5.3.

Headless Chromium renders files under the project or `$HOME` but produces nothing
under `/tmp` — any screenshot step must write inside the project or `$HOME`.

**Benchmarked on this host, 2026-08-05 — numbers, not estimates:**
- whisper.cpp `small-q5_1`, 6 threads: encode is a **fixed ~5.5 s per 30-second
  window**, not a multiple of audio length. Hard **~6.4 s floor on every
  transcription**, however short; 33 s of audio crosses into a second window and
  totals ~13.6 s. RSS 476 MB. **`--no-translate` is not a valid flag** in build
  b0f6b6e; `-l es` alone is correct. `base-q5_1` is 3.5× faster but its Spanish
  quality is unvalidated (benchmarked only on English audio).
- `qwen2.5:3b-instruct-q4_K_M` on Ollama, CPU only: prompt eval **26-36 tok/s**,
  generation **10-14 tok/s**. Prompt eval dominates anything carrying journal
  text, so context budgets are the lever that keeps latency bounds satisfiable.
- System Python is 3.14.4, but the project pins CPython 3.12.13 via `uv`, because
  ML and Rust-backed wheels lag new CPython ABIs.

The orchestrating session committed to David that **the LLM layer and the
transcription layer are swappable behind a real interface** — moving off local
inference must be a configuration change, not a re-architecture.

**Why:** David chose fully-local processing (Req 15) after being told the local
LLM would be slow on this hardware. The swappability promise is what made that
choice safe to accept; it is a design requirement, not a nice-to-have.

**How to apply:** Size any model choice to ~5.3 GiB RAM with no GPU and honour
the latency bounds PM wrote (8.8: transcript or explicit failure in 30 s; 11.12:
working state in 1 s, answer or failure in 120 s). Never design as if latency
were free. Any new AI capability goes behind the same provider interface. Prefer
the measured figures above over any arithmetic, and re-measure rather than
re-estimate when a figure is contested — see [[analyst-loop]].
