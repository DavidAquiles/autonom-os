# Verification tooling

Development tooling, not application code. Nothing here ships in the bundle.

Chromium on this host is **sandboxed and silently writes no file under `/tmp`**,
so every output path below is inside the project.

## The screenshot matrix and the accessibility audit

```bash
node tools/seed.mjs                 # fill a running backend with sample records
node tools/shots.mjs                # render the matrix + audit → tools/shots/
```

`shots.mjs` drives Chromium over the DevTools Protocol. It:

- renders every screen at 390×844 (plus 360, 320 and 900 px), against the real
  backend where the state can be produced live;
- **forces `:hover`, `:focus-visible` and `:active` through `CSS.forcePseudoState`
  on the real elements** — there is no mirrored `.is-hover` helper class in the
  app's CSS that could drift from the real rule. In the Phase 5c pilot the one
  constraint violation that escaped review lived in a `:hover` rule no render
  ever asked for;
- runs the audit from `audit.mjs` in each state: WCAG 2.1 contrast against the
  background actually painted, every interactive box against 44×44, horizontal
  overflow, and a tripwire for any `prefers-color-scheme` rule (constraint 22).

It exits non-zero if anything is flagged, and writes `tools/shots/audit.json`.

**A forced state that quietly stopped being forced is itself a finding.**
`CSS.forcePseudoState` binds to a node id, so a re-render that replaces the node
drops it and the capture then looks exactly like the default state while being
filed as hover, focus or active — a render that proves nothing while appearing
to prove something. Every `forceText` shot therefore re-checks that its stamped
element is still on the page at capture time and reports `ESTADO-PERDIDO` if it
is not. This fired for real on the "cannot reach your server" shots: the screen
re-mounts when the health query settles into its error state, so those shots wait
for it first.

A shot may seed `localStorage` with `local: { key: value }` (values are
JSON-stringified for you). `autonomos.origins` — the armed alternative origin —
is cleared before every shot, because the profile is shared and a shot that
inherited another's storage would prove nothing about KD-2.

States the server cannot be put into on demand — an empty month, a question
mid-flight, a failed summary, a truncated answer, `409 busy`, the LLM down — are
produced by fulfilling that one request with a **contract-shaped** payload
through CDP. The components under test are still the real ones.

## The service worker's actual job (KD-13, criterion 13.2)

Two steps, because a cold open means a new browser process:

```bash
node tools/sw-warm.mjs              # visit once with the server up; SW installs
kill $(pgrep -f autonomos.serve)    # the suspended PC
node tools/sw-cold.mjs              # cold open → tools/shots/sin-servidor-arranque-en-frio.png
```

The second run must print the Spanish "No puedo alcanzar tu servidor." screen. If
it prints a Chrome network error instead, 13.2's primary case is broken.

The same pair also exercises KD-2 mechanism 1 end to end, which is the only way
to see it: the warm visit is what *arms* the alternative origin from a real
`/api/health`, and the cold open — a new browser process, server stopped — is
what *reads* it. `sw-warm` prints `origins armed:` and `sw-cold` prints
`alternative offered:`, so a break is attributable to the write or to the read
rather than to "the link did not show". `sw-warm` closes the browser through
`Browser.close` rather than a signal on purpose: `localStorage` is flushed on a
clean shutdown, and a SIGTERM can drop the very write the cold open depends on.

## Icons

`icon.html` is the source of `public/icon-*.png`; re-render with

```bash
for spec in "192:0:icon-192.png" "512:0:icon-512.png" "512:22:icon-maskable-512.png"; do
  sz=${spec%%:*}; rest=${spec#*:}; pad=${rest%%:*}; out=${rest#*:}
  chromium-browser --headless --disable-gpu --hide-scrollbars \
    --force-device-scale-factor=1 --window-size=$sz,$sz \
    --screenshot="$PWD/public/$out" "file://$PWD/tools/icon.html?size=$sz&pad=$pad"
done
```
