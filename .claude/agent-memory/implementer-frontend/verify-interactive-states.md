---
name: verify-interactive-states
description: Interactive states must be forced and looked at, not reasoned about — CSS specificity bugs in this project have only ever shown up in a render
metadata:
  type: feedback
---

Render every screen with `:hover`, `:focus-visible`, `:active` and `disabled`
forced, and **look at the images**, before declaring a UI done.

**Why:** in the Phase 5c pilot the only Design Constraint violation that escaped
review lived in a `:hover` rule that no render ever asked for. In this project's
Phase 2 build, looking at renders found three defects that reading the CSS did
not: the active bottom-nav item was not violet and the red error border lost to
`:focus` (both plain specificity — a `.parent a` selector out-specifying a state
class), and one 178×19 touch target. The numeric audit caught only the third.

**How to apply:** prefer CDP `CSS.forcePseudoState` on the real element over a
mirrored `.is-hover` helper class — the helper is a second source of truth that
can drift, and it ships dead CSS. When a state class loses, fix it by writing it
at equal-or-higher specificity **and declaring it after** the rule it must beat,
with a comment saying which rule that is. Then re-render; a passing audit is not
the same as a correct picture. See `frontend/tools/README.md` and
[[env-chromium-sandbox]].

**A forced state can be silently lost, and then the capture is a lie.**
`CSS.forcePseudoState` binds to a node id, so any re-render that replaces the
element drops it and the shot comes out byte-identical to the default while
being filed as hover/focus/active. This happened on the offline screen, which
re-mounts when the health query settles into its error state. Two habits:
`md5sum` the forced shot against its default — identical bytes mean the state
never applied — and let the state settle (a wait) before forcing. `shots.mjs`
now reports this as `ESTADO-PERDIDO`, but only for `forceText` shots.
