---
name: needs-input-affordance
description: In Autonom-OS the "voice could not determine this field" mark is one approved affordance driven only by resolved_by === 'none' — extend it, never invent a second one
metadata:
  type: project
---

The voice review form marks a field the voice pass could not determine with
**one** affordance: a dashed `--violet-line` region on `--violet-wash`
(radius 16, padding 10) plus a `Tag need` in the label reading *Falta
escribirlo* / *Falta elegirla* / *Falta elegirlo*. It is declared twice —
`.missing` in `Chip.module.css` for the chip rows, `.needsInput` in
`Form.module.css` for the amount, which is not a chip row — and a test in
`estilos.test.ts` fails if the two drift apart.

**Why:** criterion 9.2 requires an undetermined field to be empty **and visibly
marked**. QA defect D1 was exactly the failure of shipping the mark on one field
of three. The mark's only input is the Interface Contract's
`resolved_by.<field> === 'none'`; a field the LLM *suggested* is a different
state that keeps its `sugerido` tag, and conflating the two is a defect in the
other direction.

**How to apply:**
- Never infer "needs input" from an empty value, and never add a second visual
  vocabulary for it — extend this one.
- Watch the region's own hover: a chip's `:hover` background is the region's
  fill, so inside the region a hovered chip dissolves unless
  `.missing .chip:hover` keeps the paper fill. Same trap for any control moved
  onto a washed surface. See [[verify-interactive-states]].
- Red (`--danger`) must still win inside the region when the field is rejected —
  declare the error rule after both the region and its `:focus-within`.
- Whether "Otros" for an utterance naming nothing is a suggestion or a default
  is PM's call on the backend's suggestion path, not the UI's marking logic.

Related: [[autonomos-context]].
