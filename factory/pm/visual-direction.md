# Autonom-OS — Visual Direction

This is the brief, not the design. Design Constraints below are enforced —
Reviewer and QA hold the built UI to them. Feel & Tone is direction, judged at
mockup approval, not pass/fail. Turning this into actual screens is the frontend
implementer's craft.

---

## Visual Intent

One person, on his own phone, usually standing up and usually in a hurry, opening
this app to put something down before he forgets it. Everything visual should
serve that moment. The app should feel like reaching for a **notebook you already
own** — familiar, quiet, no ceremony — rather than logging into a system.

Two different feelings live inside one app and both matter:

- **Finances should feel fast and matter-of-fact.** Record the number, see where
  the money went, leave. It is a ledger, not a report. It should never feel like
  it is judging the spend or asking for reflection.
- **Journal should feel unhurried and roomy.** It is the one place in the app
  where the user is meant to slow down. Text should have space around it and be
  pleasant to read back months later.

The palette carries this: mostly white, with violet as the one colour that means
something. Violet marks what you touch and what the data says. Everything else
gets out of the way. The test of success: David opens it, sees his own month at a
glance, and it looks calm rather than busy.

## Design Constraints (checkable)

Each of these is pass/fail against a real screen.

**Colour**
1. The dominant surface across every screen is white or near-white. Saturated
   violet is not used as a full-page or full-screen background.
2. Violet is the only brand hue in the app. No second decorative accent colour is
   introduced.
3. Exactly one functional colour beyond violet is permitted — a red reserved
   solely for destructive confirmation and validation errors. It appears nowhere
   else.
4. The category breakdown may use tints/shades within the violet family to
   distinguish segments; it may not introduce a rainbow of unrelated hues.
5. All text meets WCAG 2.1 AA contrast against its actual background — 4.5:1 for
   body text, 3:1 for large text — including violet-on-white and white-on-violet.
6. No information is conveyed by colour alone. Every chart segment or
   colour-coded element carries a text label and its numeric value adjacent to it.

**Layout and device**
7. The app is fully usable on a 390×844 phone viewport with no horizontal
   scrolling on any screen and no pinch-zoom required to read or tap anything.
8. No screen uses a fixed desktop width or a desktop-only layout. Wider viewports
   may be handled, but the phone is the design target.
9. The primary capture actions for the current module — start voice capture, and
   open the manual form — are reachable with one thumb in the lower portion of
   the screen.
10. All interactive controls have a touch target of at least 44×44 px.
11. The three top-level destinations (Finances, Journal, Gym) are visible and
    reachable from every screen in one interaction.

**Typography**
12. One typeface family throughout the app; weight and size may vary, families may
    not. Numerals in amounts and totals align consistently in lists.
13. Body text in the journal is set at a size and line length comfortable for
    reading paragraphs, not for scanning table rows.
14. No typeface or icon set requiring a paid licence is used anywhere.

**Required states**
15. Every screen that can be empty has a designed empty state, at minimum:
    Today with no expenses, current month with no expenses, Journal with no
    entries, a selected date with no entries, and insights with too little data.
    None of these renders as a blank screen, an error, or a zeroed-out chart.
16. Every asynchronous action has both a visible in-progress state and a visible
    error state — at minimum voice transcription, insight generation, and saving.
17. Voice capture has an unmistakable, at-a-glance "listening now" indication that
    cannot be confused with the idle state, plus visible stop and cancel controls.
18. A "cannot reach your server" state exists as a designed screen or banner, in
    plain language, not a raw technical error.
19. Every destructive action presents a confirmation step before it is carried
    out.

**Content and mode**
20. The Gym destination is present in the navigation and visibly marked as not
    yet available. It is neither hidden nor made to look broken or empty-by-bug.
21. Amounts everywhere are rendered in Colombian peso convention — `.` thousands
    separator, no cents — e.g. `$14.000`.
22. Light mode only in this pass. No dark mode and no theme toggle in the UI.
23. Interface language is Spanish throughout, with no mixed-language strings on
    any screen. *(Depends on Assumption A3 in the spec.)*

## Feel & Tone (guidance, not pass/fail)

**Aim for**
- Calm and uncluttered. Generous whitespace is the main tool; the app should feel
  emptier than seems necessary.
- Typography-led hierarchy — size, weight, and spacing do the work that boxes,
  borders, and shadows would otherwise do.
- Violet used sparingly enough that when it appears, it means something.
- Soft, rounded, friendly shapes. Personal, not institutional.
- The month breakdown should read as a clear answer to "where did it go", not as
  a data visualisation exercise.
- Journal screens noticeably quieter and roomier than Finances screens.

**Avoid**
- Dense dashboards, data grids, KPI card walls, sidebars.
- Gradients, glassmorphism, heavy shadows, neon glow.
- Gamification: streaks, badges, confetti, congratulation messages, progress rings
  toward goals the user never set.
- Any tone that moralises about spending — no red warnings for spending "too
  much", no frowning faces, no "you're over budget".
- Emoji as interface vocabulary, and stock illustrations of people.
- Marketing copy, taglines, or onboarding tours. The user wrote the ask; he does
  not need to be sold the app.

**Reference feeling:** a well-made paper notebook, and a native phone form that
does exactly what it says.
**Anti-reference:** an enterprise BI dashboard; a neon crypto/fintech app; a
"delightful" habit tracker that celebrates you.

## Visual Non-Goals

- **Not a desktop admin panel.** No sidebar-plus-table layout adapted down to
  mobile.
- **Not a corporate analytics dashboard.** No multi-chart overview screen, no
  filter bars, no date-range pickers with presets.
- **Not a gamified habit app.** Nothing celebrates, rewards, or nags the user.
- **Not a dark neon fintech aesthetic.**
- **No branding work.** No logo, wordmark, brand guidelines, icon system, or
  illustration set is being created here.
- **No theming or customisation surface.** The user does not choose colours,
  fonts, or layouts; there is one look.
- **No marketing or public surface.** No landing page, no screenshots page, no
  onboarding carousel.

## Open Questions

None. The ask specifies the look with enough precision — clean, mostly white,
violet, mobile-oriented — that the remaining decisions are the frontend's craft
rather than the human's intent. Visual decisions I took rather than escalated are
recorded as Assumptions A3 and A18 in `spec.md`; the three questions I am
escalating are all functional.
