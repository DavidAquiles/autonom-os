---
name: env-chromium-sandbox
description: Chromium on this host is sandboxed and silently writes no file under /tmp — screenshots and generated HTML must go inside the project or $HOME
metadata:
  type: project
---

Chromium is at `/usr/bin/chromium-browser`. It runs sandboxed: any `--screenshot`
or file it is asked to write **under `/tmp` silently produces nothing** — no
error, no file. Same for HTML it is asked to load from `/tmp`.

**Why:** the sandbox denies writes outside the user's own tree, and Chromium does
not surface the failure. This cost a full render pass before it was noticed.

**How to apply:** when driving Chromium for screenshots, audits or icon
generation, put every input and output path inside the project (or `$HOME`).
The scratchpad directory under `/tmp` is fine for Python venvs and shell
scratch, just not for anything Chromium itself writes or reads.

Driving it over the DevTools Protocol works well with no npm dependency: Node
24 has a global `WebSocket`, so `/json/version` + a socket is enough. See
`frontend/tools/cdp.mjs`. `CSS.forcePseudoState` is what makes `:hover`,
`:focus-visible` and `:active` capturable on real elements — see
[[verify-interactive-states]].
