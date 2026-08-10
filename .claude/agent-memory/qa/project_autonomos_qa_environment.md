---
name: autonomos-qa-environment
description: How to actually run and exercise Autonom-OS for QA on this host — ports, a faithful DB copy, browser driving, and states the repo's notes call unreachable but aren't
metadata:
  type: project
---

Autonom-OS is exercised locally: API on **8001** (8000 is permanently held by the unrelated
`trace_erp_api` container — never touch it), whisper-server on 8081, Ollama on 11434.
The user's own server usually already runs on 8001 against `data/autonomos.db`; **leave it
running and never point QA at that database.**

Run QA on a spare port (8011, 8012) against a **copy**:

```
python3 -c "import sqlite3;s=sqlite3.connect('file:data/autonomos.db?mode=ro',uri=True);d=sqlite3.connect('data/qa-run.db');s.backup(d)"
cd backend && DB_PATH=<abs>/data/qa-run.db AUTONOMOS_API_PORT=8011 \
  FRONTEND_DIST=<abs>/frontend/dist ./.venv/bin/python -m autonomos.serve
```

**A plain `cp` of the .db is wrong** — the live server keeps most rows in the `-wal`, so a copied
file looks like an old, smaller database (16 expenses became 13). Use the sqlite backup API.
`DB_PATH` resolves against the repo root, not the process cwd. Kill by the PID `ss -ltnp` reports
for the port; `pkill -f <pattern>` kills the calling shell instead.

**Driving the UI:** `frontend/tools/cdp.mjs` is a dependency-free CDP client (`launch`, `newPage`,
`evaluate`, `forcePseudo`) — import it rather than installing puppeteer. Chromium is a snap, so
the profile dir must live under `$HOME` (use `frontend/tools/out/…` and delete it after).
`frontend/tools/verificar-scroll.mjs [baseURL]` defaults to `http://127.0.0.1:8011` and checks
17.8 on all three lists; it SKIPs Hoy unless expenses are dated today.

**Do not run `npm run shots` against data you care about** — the pre-existing `gasto-guardando`
recipe intermittently writes a real expense into whatever DB it is pointed at.

Two states the repo's notes record as "unreachable in this environment" and which are in fact
reachable — do not accept them as Unverified again:

- **Microphone permission denied (8.5).** Start Chromium *without*
  `--use-fake-ui-for-media-stream`, then CDP `Browser.setPermission {origin,
  permission:{name:'microphone'}, setting:'denied'}`.
- **The `generating` summary surface (deferred as F4).** Set `SCHEDULER_TICK_S=30` on a throwaway
  DB and poll `/api/insights/summaries/latest`.

Useful CDP levers beyond screenshots: `Network.setBlockedURLs` to fail one endpoint while health
still answers (this is how the Run 02 blank-Historial and false-empty-category defects surfaced),
`Emulation.setEmulatedMedia` for `prefers-color-scheme: dark` (constraint 22), and reading
`document.querySelector('main').scrollTop` — the app scrolls `<main>`, not the document.

Data locality (R15) cannot be tested by severing the link — no root, no sudo, no working
`unshare`. Run the API and whisper under `strace -f -e trace=connect` and sample `ss -tnp`.

See [[autonomos-qa-verdicts]] for what this found.
