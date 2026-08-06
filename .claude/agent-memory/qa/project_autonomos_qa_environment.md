---
name: autonomos-qa-environment
description: How to actually run and exercise Autonom-OS for QA on this host — ports, sidecars, and the two states the repo's own notes call unreachable but aren't
metadata:
  type: project
---

Autonom-OS is exercised locally: API on **8001** (8000 is permanently held by the unrelated
`trace_erp_api` container — never touch it), whisper-server on 8081, Ollama on 11434.
Run QA against a **separate `DB_PATH`** (e.g. `data/qa-*.db`), never the human's
`data/autonomos.db`; a fresh DB is also the only way to verify first-run seeding (3.1) and the
empty states.

**Why:** the app has one real user and one real database; polluting it to test it would be a
worse outcome than any bug found. A fresh DB additionally unlocks criteria that only exist
before there is data.

**How to apply:** start each server with `DB_PATH=... FRONTEND_DIST=frontend/dist
.venv/bin/python -m autonomos.serve`, and kill it by the PID that `ss -ltnp` reports for the
port — `pkill -f <pattern>` matches the `sh -c` wrapper running the pattern and kills the
calling shell instead.

Two states the repo's notes record as "unreachable in this environment" and which are in fact
reachable — do not accept them as Unverified again:

- **Microphone permission denied (8.5).** Start Chromium *without*
  `--use-fake-ui-for-media-stream` (that flag silently overrides any denial), then CDP
  `Browser.setPermission {origin, permission:{name:'microphone'}, setting:'denied'}`.
  `getUserMedia` then rejects with `NotAllowedError` and the real denial screen renders.
- **The `generating` summary surface (deferred as F4).** It appears for ~30 s during the
  scheduler's own run; set `SCHEDULER_TICK_S=30` on a throwaway DB and poll
  `/api/insights/summaries/latest`.

Data locality (R15) cannot be tested by severing the link — there is no root, no sudo and no
working `unshare` here. Run the API and whisper under `strace -f -e trace=connect` and sample
`ss -tnp` for Ollama instead; every socket should be `127.0.0.1`.

See [[autonomos-qa-verdicts]] for what this found.
