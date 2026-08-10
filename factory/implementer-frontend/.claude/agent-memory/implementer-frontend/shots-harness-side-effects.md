---
name: shots-harness-side-effects
description: Two traps when rendering the screenshot matrix — a reused Chromium profile serves a cached index.html so a fixed build looks broken, and the matrix writes a real expense into the live database
metadata:
  type: project
---

`frontend/tools/shots.mjs` renders against the **real running backend**, not
fixtures. Two consequences that each cost a wrong conclusion:

**1. A reused Chromium profile hides a rebuild.** Vite emits content-hashed
bundles, but `index.html` itself is cached by the profile, so a profile from an
earlier run keeps loading the *previous* bundle. A fix that was already correct
looked broken for two rounds because of this. Use a fresh profile directory per
verification run (`tools/verificar-scroll.mjs` deletes and recreates one per
case). The matrix itself is fine — it navigates fresh targets — but any ad-hoc
CDP script must start clean.

**2. Running the matrix mutates the database it photographs.** A pre-existing
recipe (`gasto-guardando`, which *delays* the POST rather than failing it)
intermittently writes a real `$14.000 Transporte` expense per run. Check
`GET /api/expenses?order=registered&limit=5` before and after, and delete what
the run created. Do not "fix" the recipe on the way past — it belongs to an
earlier run's slice.

**How to apply:** before rendering, note the month total; after, compare and
clean up. If a screen needs data the live DB lacks (Hoy on an empty day), create
rows through the API, verify, and delete exactly those ids — then confirm the
totals match what you started with.

Also: the API port is 8001 and a long-running dev server may predate the current
backend code — check `/api/openapi.json` for the parameters you expect before
concluding the frontend is wrong. Starting a second instance on another port
(`AUTONOMOS_API_PORT=8011`) is safer than restarting the user's process.

Related: [[env-chromium-sandbox]], [[autonomos-context]], [[scroll-restoration-detached-container]].
