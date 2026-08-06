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
