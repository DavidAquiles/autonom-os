# Autonom-OS — Visual Direction (Run 02, brownfield feature)

**Status: DRAFT — pending Kickoff gate.** Nothing about the look is open; the one
open question in `spec.md` (OQ1) is functional scope, not visual.

This is the brief, not the design. Design Constraints are enforced — Reviewer and
QA hold the built UI to them, with real screenshots at 390×844. Feel & Tone is
direction, judged at mockup approval, not pass/fail.

## What carries over unchanged

**`factory/runs/01-greenfield/pm/visual-direction.md` remains in force in full.
Constraints 1–28 govern these new screens exactly as they govern every existing
one, and are not renumbered or restated here.** The ones this feature is most
likely to break, named so nobody has to go looking:

- **2, 3** — violet is the only brand hue; the single red is reserved for
  destructive paths and validation errors. A new list, a new detail screen and a
  new filter state introduce three fresh temptations to add a colour. Don't.
- **6** — no information by colour alone; every proportional element carries its
  label and number adjacently. The category rows becoming tappable must not start
  relying on their tint to mean something.
- **7, 8, 10** — 390×844, no horizontal scroll, no pinch-zoom, 44×44 touch
  targets. A fourth tab and a newly tappable breakdown row both land here.
- **15** — every screen that can be empty has a designed empty state. This
  feature adds two more (see constraint 37 below).
- **21, 23, 24** — Colombian peso rendering, Spanish throughout, accents and ñ
  intact at every size.
- **1, 12, 22** — white-dominant surface, one typeface, light mode only.

Constraint numbering continues below at **29**.

## Visual Intent

This feature adds the act of **looking back** to an app that so far has only
supported putting things down. That is a different posture and it should feel
different — slower, more readable, less like a keypad.

Historial is the notebook being flipped backwards: one continuous run of what he
wrote down, in the order he wrote it, quiet enough to scan a long way. The detail
view is the one place in Finanzas where a single expense gets the whole screen —
it should read like a small receipt he is holding up, not like a form with the
inputs switched off. And opening a category in the month view should feel like
lifting the lid on a number he already trusts, not like operating a filter on a
report.

Everything here still has to survive being used one-handed on the street, and it
must not turn Finanzas — which Run 01 defines as *fast and matter-of-fact* — into
something that feels like a reporting tool.

## Design Constraints (checkable)

Each is pass/fail against a real screen. **All of 29–39 are verifiable by
screenshot at a 390×844 viewport, and will be checked that way.**

**The tab strip**

29. The Finanzas tab strip shows four tabs — Hoy, Este mes, Historial, Análisis
    — all fully legible on a 390×844 viewport: no horizontal scrolling, no
    truncation or ellipsis, no wrapping to a second line, and no label rendered
    at a smaller size than its neighbours. Each tab keeps a touch target of at
    least 44×44 px (constraint 10).

**Historial**

30. Historial rows use the same row treatment as the existing Hoy ledger —
    amount on the right, what-it-was on the left — so that a list of expenses
    reads as the same kind of object wherever it appears. Placed side by side,
    the two screenshots differ in content, not in structure.
31. Historial carries a visible statement, in Spanish, of the order it is in,
    positioned where it is read before the first row. A screen full of dates in
    non-descending order with nothing explaining why fails this.
32. While unshown expenses remain, Historial presents a visible control to show
    more. When none remain, no control, label, spinner, or trailing affordance
    implying more exist is present. Both states are distinguishable on sight.
33. Historial is a flat list. It contains no date headings, no day separators, no
    month bands, and no sticky group headers.
34. Historial does not carry a search field, a filter row, a sort control, or a
    chip bar. The screen has a title area and rows, and nothing else operable
    except the control in constraint 32.

**The expense detail screen**

35. The expense detail screen is a reading surface: it contains no text input, no
    editable field, no selectable chip, and no control that changes the expense
    except the single labelled edit action. A disabled-looking form fails this —
    it must not look like a form at all.
36. The detail screen uses the same screen frame as the existing journal-entry
    read screen — a titled bar with a way back, no capture bar — so the app has
    one kind of read screen rather than two.
37. On the detail screen, the date the expense is dated for and the moment it was
    recorded are each labelled, and are never adjacent in a way that lets them be
    read as one date range or as one value. The description is shown in full,
    unclamped, with no "seguir leyendo".
38. The "has been edited" indication is neutral: no red, no warning icon, no
    alarm tone, no badge styled like an error. It reads as a fact about the
    record, not as a problem with it.

**The month view and its filter**

39. In the month breakdown, a category row is visibly tappable at a glance and
    carries the same tap affordance the app already uses for tappable rows. The
    payment-method rows below it remain visibly non-tappable, and the difference
    is apparent without touching either.
40. While a category is selected, the screen shows the category's name and its
    total for that month, and the month's own total remains visible. The two
    figures are distinguishable at a glance — differing in position, label and
    typographic weight — so it is never ambiguous which number belongs to which.
41. While a category is selected, a way to clear it and return to the full
    breakdown is visible on screen without scrolling.

**Required states, extending constraint 15**

42. Both new empty states are designed states, not blank areas: Historial with no
    expenses ever recorded, and a selected category whose expenses in that month
    have all gone. Neither renders as an empty frame, a zero row, an error, or a
    bare screen.
43. Nothing on Historial, the detail screen, or a filtered category list — no
    badge, icon, tint, label, or field — indicates whether an expense was
    captured by voice or typed.

## Feel & Tone (guidance, not pass/fail)

**Aim for**

- Historial should feel like flipping back through a notebook: a long, calm,
  uninterrupted run of entries that is pleasant to scroll past quickly. Restful
  enough that a hundred rows do not feel like a hundred rows.
- The "show more" control should feel like turning a page — unremarkable, low
  contrast, easy to ignore until wanted. Not a call to action.
- The line explaining the order (constraint 31) should sound matter-of-fact and
  brief, in the app's existing voice: patient, not apologetic, not explaining
  itself twice.
- The detail screen should feel like a small receipt or an index card — one thing
  given the whole page, generous whitespace, the amount clearly the headline.
  Roomier than Finanzas usually is; closer to the journal's pace than to the
  form's.
- Opening a category should feel like a drill-down inside the month, not like
  navigating to a different report. The user should never lose the sense of which
  month he is in.
- The two dates on the detail screen (17.4) should be quiet — the expense's own
  date belongs to the record; when it was typed in is a footnote-weight fact.

**Avoid**

- Turning Historial into a data table: no column headers, no rules between every
  cell, no zebra striping, no right-aligned grid of fields.
- Anything that implies pagination as machinery — page numbers, "1 de 12",
  "mostrando 50 de 431" rendered as a status readout, next/previous arrows.
- A loading treadmill: an endless spinner at the bottom of Historial that gives
  no sense of whether anything more is coming.
- Making the detail screen look like the edit form with everything greyed out.
- Filter-tool vocabulary in the month view: chip bars, "filtros", "limpiar
  filtros", dropdowns, an X on a pill borrowed from a search UI. This is opening
  a category, not configuring a query.
- Making the edited-since indication feel like an audit trail or a correction
  notice.
- Any suggestion that older expenses are archived, cold, or less real than recent
  ones — no fading, no dimming with age.

**Reference feeling:** the back pages of a notebook already half-filled; a paper
receipt.
**Anti-reference:** a transaction list in a banking app, with its filter bar,
search icon and month chips; an admin table with pagination controls.

## Visual Non-Goals

- **Not a transactions screen from a banking app.** No search icon, no filter
  bar, no segmented month selector, no "ver todos" chips.
- **Not a data grid.** No columns, no headers, no sortable-looking anything.
- **No timeline graphics.** No vertical rail with dots, no connectors between
  entries, no "activity feed" chrome.
- **No new colour, no new typeface, no new icon family.** Whatever these screens
  need, they build from what the app already has.
- **No dark mode, no theming, no density toggle** — constraint 22 stands.
- **No badges, counters, or "nuevo" markers** on the Historial tab or on rows.
- **No animation as a feature.** Rows do not stagger in, the filter does not
  slide, the detail does not zoom from the row.

## Open Questions

**None.** The ask specifies the look implicitly by being an extension of an
existing, approved product; every remaining decision is the frontend's craft
inside constraints 1–43. Visual decisions I took rather than escalated are
recorded in `spec.md` as assumptions A23, A24, A27, A30, A31 and A33. The single
open question in this run (OQ1) concerns functional scope and has no visual
consequence for the screens described here.
