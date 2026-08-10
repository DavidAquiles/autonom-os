---
name: scroll-restoration-detached-container
description: Never take a final scrollTop reading in an unmount cleanup — React detaches the container first, so the read returns 0 and destroys the offset already captured; verify scroll restoration by driving a real browser
metadata:
  type: project
---

This app scrolls inside `<main className={scroll}>` (`components/shell/Screen.tsx`),
not the document, so nothing — not the browser's history scroll restoration, not
React Router — restores a list's position. `useScrollMemory` does it: a `scroll`
listener records `location.key → scrollTop` into a module-level Map, and a
`useLayoutEffect` reapplies it on the way back.

**The trap.** Recording a "final" offset in the `useEffect` cleanup looks like
belt-and-braces and is actively destructive. React runs that passive cleanup
*after* detaching the container from the document, and **a detached element
reports `scrollTop === 0`** — so the read does not capture the position, it
overwrites the good value the listener already captured. Every list then silently
returns to the top.

**Why it matters:** this is criterion 17.8 / the design's R1, "the single most
likely criterion to be quietly failed". It passed the whole vitest suite and
every screenshot, because a static render never scrolls first.

**How to apply:**
- The scroll listener is the only writer. Cleanup removes the listener and
  nothing else.
- Guard the restore loop with a `restoring` ref, or the programmatic writes will
  fire `scroll` and record the clamped value on a list that has not finished
  rendering.
- **Verify by driving Chromium**, not by reading: scroll → open a row → back →
  read `document.querySelector('main').scrollTop`. `frontend/tools/verificar-scroll.mjs`
  does exactly this for Hoy, Historial and the filtered month list. A list with
  no rows (Hoy on an empty day) cannot answer the question — it reports SKIP, and
  a real check needs rows created and then deleted.

Related: [[verify-interactive-states]], [[shots-harness-side-effects]].
