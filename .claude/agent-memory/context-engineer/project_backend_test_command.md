---
name: backend-test-command-needs-dev-extra
description: Autonom-OS backend tests only run with `uv run --python 3.12 --extra dev pytest -q`; the repo's own README and the usual invocation both fail
metadata:
  type: project
---

The working backend test command is, from `backend/`:

`uv run --python 3.12 --extra dev pytest -q`  (261 passed at 418d7b3)

**Why:** pytest lives in the optional `dev` extra of `backend/pyproject.toml`, not
the base dependency list. Two documented-looking alternatives are both broken:
`uv run --python 3.12 pytest -q` (no `--extra dev`) dies with
`Failed to spawn: pytest`, and `ops/README-setup.md`'s
`.venv/bin/python -m pytest -q` fails with `No module named pytest` because the
checked-in `backend/.venv` has no dev deps installed.

**How to apply:** whenever running or quoting the backend verification gate — in
factory packs, QA runs, or when a caller hands me a command to use. Do not trust
the ops README on this one. Frontend gates are fine as documented:
`npm run test` (vitest) and `npm run build` (runs `tsc --noEmit` first).
