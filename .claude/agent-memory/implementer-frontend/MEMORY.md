# Memory index

- [Autonom-OS context](autonomos-context.md) — one Spanish-speaking user, local AI, phase-gated factory lanes; API is on 8001 because 8000 is permanently taken.
- [Verify interactive states by rendering](verify-interactive-states.md) — force hover/focus/active and look; specificity bugs here never show up in a code read.
- [Chromium sandbox writes nothing under /tmp](env-chromium-sandbox.md) — screenshots and generated HTML must live inside the project or $HOME.
- [Failed is not empty](failed-vs-empty-states.md) — one shared `ListFailure`; gate empty-state copy on `isSuccess` and a record's render on `!missing`.
- [The "needs input" affordance](needs-input-affordance.md) — one mark for an undetermined field, driven only by `resolved_by === 'none'`; extend it, never invent a second.
- [Build mockups on Run 01's stylesheet](mockups-extend-run01-css.md) — import `mockups/_build/css.py`, append a delta; plus the tab strip's measured capacity (wraps ≤330px).
