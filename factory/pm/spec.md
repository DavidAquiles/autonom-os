# Autonom-OS — Product Spec

**Status: FINAL.** Kickoff gate passed; all three escalated questions answered and
folded in. Assumptions are the human's control surface — read § Assumptions
before § Acceptance Criteria. Criterion numbers are stable and are cited by the
Architect's Interface Contract, Reviewer findings, and QA results; retired
criteria keep their numbers rather than being renumbered.

---

## Problem Statement

David wants to keep a running record of three parts of his life — what he spends,
what he does at the gym, and what he is thinking — but no single place exists to
put them. Today each aspect either lives in a different app, or, more often,
nowhere at all, because the friction of capture exceeds the value of the record
at the moment the thing happens.

The failure is specifically at **capture time**, not at review time. An expense is
made on the street, in seconds, holding a phone; a journal thought arrives at
night, unstructured. Any system that requires opening a laptop, choosing between
seven fields, or thinking about structure loses to not recording anything. The
record is then incomplete, and an incomplete record cannot answer the question
that motivated keeping it — "where is my money actually going?"

A second problem sits on top: even a complete record is inert. Rows of expenses
and pages of journal text do not, by themselves, tell you anything. Reading them
back is work David will not reliably do.

This statement is falsifiable. It is wrong if David is already recording these
things consistently somewhere, or if the barrier is motivation rather than
capture friction, or if he would in fact happily review raw data himself.

## Users

One user: David. He is the only person who will ever open this app, on his own
phone, against a server and database running on his own PC. There is no second
user, no sharing, no roles, no audience. Product decisions should optimise for
one person's speed and comfort, never for generality.

## Decisions taken at the Kickoff gate

Settled by the human; not open to reinterpretation downstream.

- **Away-from-home use is required.** The app must work on mobile data, wherever
  David is, so an expense can be captured the moment it happens. The PC is **not**
  exposed to the public internet; the phone joins a private network with it. The
  mechanism is the Architect's call and is deliberately absent from this spec.
- **Everything stays local.** No audio, no journal text, no expense text, and no
  derived data leaves the PC. No third-party transcription, no third-party LLM,
  no accounts, no quotas — not even for short finance phrases.
- **Insights are both on-demand and periodic.** David asks questions, *and* the
  app produces a short summary on its own.
- **Spanish.** All interface text in Spanish; voice recognition tuned for Spanish
  specifically.

**Measured host hardware** (fact, not estimate): 13 GB RAM (~6.7 GB available),
8 CPU cores, integrated AMD Radeon Vega graphics with no dedicated GPU and no
CUDA, 37 GB free disk.

**The consequence David accepted before choosing:** on this hardware, local voice
transcription runs comfortably, but the local LLM is **noticeably slower and
lower quality than a cloud model**. Insight generation is expected to take
seconds-to-tens-of-seconds, not to feel instant. This is written into the
acceptance criteria below rather than left to be discovered at QA. No criterion in
this spec should be read as requiring an instant AI response.

## Scope

### In scope (this pass)

- **Finances** — record an expense with amount, category, and payment method;
  see today's spending; see this month's spending broken down by category as
  percentages.
- **Journal** — free-text entries, dated, browsable by date.
- **Gym** — a navigational placeholder only.
- **Two input methods across modules** — voice and manual.
- **LLM insights** over the user's own recorded data — on-demand questions and a
  periodic summary — running entirely on the user's PC, at zero cost.
- **Phone-first use, away from home**, against a self-hosted server on the user's
  PC that is never publicly exposed.

### Out of scope (Non-Goals)

Concrete things this pass will explicitly not do:

1. **Gym functionality.** No workout logging, no exercise catalogue, no sets/reps
   /weight model, no gym data of any kind. The Gym module is a labelled,
   inert destination.
2. **Income, balances, budgets, or net worth.** The app records outflows only.
   No account balances, no budget limits, no "you have X left this month", no
   savings goals, no debt tracking.
3. **Multi-currency.** One currency, no conversion, no FX rates.
4. **Bank, card, or receipt integration.** No bank sync, no CSV import from a
   bank, no receipt photo scanning, no OCR.
5. **Any second user.** No sharing, no accounts-as-a-product-feature, no
   collaboration, no export-to-a-friend.
6. **Recurring or scheduled expenses**, and no reminders, notifications, push
   messages, streaks, badges, or gamification of any kind.
7. **Rich journal content.** No photos, attachments, formatting/markdown
   rendering, tags, mood scores, or templates. Plain text only.
8. **Journal search.** Entries are reached by date, not by query. (Asking the
   insights capability about the journal is a different thing and is in scope.)
9. **Any paid service, paid tier, trial that converts to paid, or dependency
   that requires payment details.** See Requirement 12.
10. **Any third-party processing of the user's data**, free tiers included. See
    Requirement 15.
11. **A public/marketing surface.** No landing page, no sign-up flow, no docs
    site, no app store listing.
12. **A second interface language.** Spanish only; no language switcher, no
    translation layer.

---

## Acceptance Criteria

### Requirement 1 — App shell and navigation

As the only user, I want to move between the three aspects of my life in one tap,
so that capture never costs me navigation time.

#### Acceptance Criteria

1.1 WHEN the user opens the app THEN the system SHALL present exactly three
    top-level destinations — Finances, Journal, Gym — reachable from any screen
    in a single interaction.
1.2 WHEN the user opens the app THEN the system SHALL land directly on a usable
    default screen without requiring a selection, a splash step, or a setup step.
1.3 WHEN the user selects Gym THEN the system SHALL show a placeholder screen
    that states in plain language that the module is not available yet, and SHALL
    present no gym data-entry control, no empty gym list, and no error.
1.4 WHEN the user is anywhere in the app THEN the system SHALL make the two
    capture actions available for the current module — start voice capture, and
    open the manual form — without navigating away from the module.
1.5 WHEN any text is shown anywhere in the interface THEN it SHALL be in Spanish,
    with no untranslated or mixed-language strings on any screen, including
    errors, empty states, and validation messages.

### Requirement 2 — Manual expense capture

As the only user, I want to record a spend in seconds on my phone, so that I
actually record it instead of meaning to later.

#### Acceptance Criteria

2.1 WHEN the user submits an expense with an amount, a category, and a payment
    method THEN the system SHALL save it, dated today by default, and SHALL show
    it in the Today list without the user having to refresh or re-navigate.
2.2 WHEN the user submits an expense with an empty, zero, or negative amount THEN
    the system SHALL reject the submission and show an inline error that names the
    offending field.
2.3 WHEN the user submits an expense with no category or no payment method
    selected THEN the system SHALL reject it and name the missing field.
2.4 WHEN the user types an amount as `14.000`, `14000`, or `14 000` THEN the
    system SHALL interpret all three as fourteen thousand pesos.
2.5 WHEN any amount is displayed anywhere in the app THEN the system SHALL format
    it in Colombian peso convention — `.` as thousands separator, no decimal
    cents — e.g. `$14.000`.
2.6 WHEN the user records an expense THEN the system SHALL allow an optional
    free-text description, and SHALL save the expense successfully when that
    description is left empty.
2.7 WHEN the user sets a date other than today THEN the system SHALL accept any
    date up to and including today, and SHALL reject a future date with an
    explanatory message.
2.8 WHEN the user starts from the app's default screen THEN the system SHALL
    allow a complete expense to be saved in no more than four interactions
    (taps/entries) beyond typing the amount itself.

### Requirement 3 — Categories and payment methods

As the only user, I want the lists I pick from to already be right for me, so
that categorising costs no thought.

#### Acceptance Criteria

3.1 WHEN the app is used for the first time with no data THEN the system SHALL
    already offer a non-empty starter set of spend categories and a non-empty
    starter set of payment methods, named in Spanish.
3.2 WHEN the user needs a category or payment method that does not exist THEN the
    system SHALL allow creating it from within the expense form, without
    abandoning the expense being entered.
3.3 WHEN the user renames a category or payment method THEN the system SHALL show
    the new name on all existing expenses that use it.
3.4 WHEN the user removes a category or payment method that is used by existing
    expenses THEN the system SHALL warn that it is in use, SHALL NOT delete or
    orphan those expenses, and SHALL keep them attributed to that name in
    historical views while removing it from future selection.
3.5 WHEN an expense exists THEN it SHALL have exactly one category and exactly one
    payment method — never zero, never several.

### Requirement 4 — Today and this month

As the only user, I want to see what I spent today and where this month's money
went, so that the record answers the question I kept it for.

#### Acceptance Criteria

4.1 WHEN the user opens Finances THEN the system SHALL show the total spent today
    and the list of today's expenses, most recent first, each showing amount,
    category, and payment method.
4.2 WHEN the user views the current month THEN the system SHALL show the total
    spent in that calendar month and a breakdown by category showing, for each
    category, its amount and its percentage of the month total.
4.3 WHEN the category breakdown is shown THEN the percentages SHALL sum to 100%
    (allowing visible rounding of no more than 1 percentage point in total), and
    categories SHALL be ordered from largest to smallest amount.
4.4 WHEN the user views the current month THEN the system SHALL also show the
    total spent per payment method for that month.
4.5 WHEN a month contains no expenses THEN the system SHALL show a plain empty
    state — no error, no `NaN`, no `0%` breakdown of nothing, no blank screen.
4.6 WHEN the user saves, edits, or deletes an expense THEN the Today total, the
    month total, and the category percentages SHALL all reflect the change on
    next view without a manual refresh.
4.7 WHEN the user is viewing the current month THEN the system SHALL allow
    navigating to a previous month and back, showing that month's total and
    breakdown on the same terms.
4.8 WHEN "today" or "this month" is determined THEN the system SHALL use the
    user's own local calendar day and calendar month, so an expense recorded at
    11pm belongs to that day and not the next.

### Requirement 5 — Correcting the record

As the only user, I want to fix what I got wrong, so that a mistake does not
poison the totals I rely on.

#### Acceptance Criteria

5.1 WHEN the user opens an existing expense THEN the system SHALL allow changing
    its amount, category, payment method, date, and description, and SHALL persist
    those changes.
5.2 WHEN the user deletes an expense or a journal entry THEN the system SHALL ask
    for confirmation first, and SHALL remove it only after confirmation.
5.3 WHEN the user opens an existing journal entry THEN the system SHALL allow
    editing its text and SHALL persist the change.

### Requirement 6 — Journal capture

As the only user, I want to write down whatever I am thinking without deciding
anything about structure, so that writing stays effortless.

#### Acceptance Criteria

6.1 WHEN the user submits a journal entry with non-empty text THEN the system
    SHALL save it against today's date and time and SHALL show it at the top of
    the journal list.
6.2 WHEN the user submits a journal entry with empty or whitespace-only text THEN
    the system SHALL reject it and say so inline.
6.3 WHEN the user writes several entries on the same date THEN the system SHALL
    keep each as a separate entry with its own time, and SHALL NOT merge, replace,
    or overwrite the earlier one.
6.4 WHEN a journal entry contains line breaks and paragraphs THEN the system SHALL
    preserve them exactly when the entry is viewed again.
6.5 WHEN a journal entry of at least 5.000 characters is saved THEN the system
    SHALL save it in full and display it in full, with no silent truncation.
6.6 WHEN the user submits a journal entry THEN the system SHALL require nothing
    beyond the text — no title, category, tag, or mood.
6.7 WHEN a journal entry contains Spanish accented characters, ñ, or ¿¡ THEN the
    system SHALL store and redisplay them unchanged.

### Requirement 7 — Journal browsing

As the only user, I want to find what I wrote on a given day, so that the journal
is re-readable rather than write-only.

#### Acceptance Criteria

7.1 WHEN the user opens Journal THEN the system SHALL list entries newest first,
    visibly grouped or labelled by date.
7.2 WHEN the user selects a specific date THEN the system SHALL show that date's
    entries, or an explicit "nothing written on this day" state.
7.3 WHEN the journal contains no entries at all THEN the system SHALL show an
    inviting empty state rather than a blank screen.

### Requirement 8 — Voice capture (shared behaviour)

As the only user, I want to talk to the app instead of typing, so that recording
costs nothing while I am walking down the street.

#### Acceptance Criteria

8.1 WHEN the user starts voice capture THEN the system SHALL show an unmistakable
    "listening now" indication and SHALL offer both a stop and a cancel action.
8.2 WHEN voice capture finishes THEN the system SHALL show the user what it heard,
    as text, before anything is written to the record.
8.3 WHEN the user cancels a capture THEN the system SHALL discard it entirely and
    SHALL write nothing.
8.4 WHEN transcription fails, times out, or returns nothing usable THEN the system
    SHALL say so in plain language and offer both retry and switching to the
    manual form, and SHALL NOT save an empty or partial record.
8.5 WHEN microphone permission is unavailable or denied THEN the system SHALL
    explain why voice cannot be used and SHALL leave the manual path fully
    working.
8.6 WHEN anything is captured by voice THEN the system SHALL require an explicit
    user confirmation before it becomes a saved expense or journal entry.
8.7 WHEN the user speaks in Colombian Spanish THEN the system SHALL transcribe it
    as Spanish, including accented characters and ñ, and SHALL NOT translate it
    into another language.
8.8 WHEN voice capture ends THEN the system SHALL show a visible working state
    within 1 second and SHALL present either a transcript or an explicit failure
    within 30 seconds, for an utterance of up to 30 seconds of speech.
8.9 WHEN transcription is in progress THEN the system SHALL allow the user to
    abandon it and switch to the manual form without waiting for it to finish.

### Requirement 9 — Voice to expense

As the only user, I want to say what I spent in one natural sentence, so that
capture matches how I actually think about the spend.

#### Acceptance Criteria

9.1 WHEN the user speaks a sentence containing an amount, what it was for, and a
    payment method — e.g. "gasté 14.000 pesos en Uber con la tarjeta de crédito" —
    THEN the system SHALL present a pre-filled expense form containing the amount,
    a suggested category, the payment method, and a description, for confirmation.
9.2 WHEN a field cannot be determined from what was said THEN the system SHALL
    leave that field empty and visibly marked as needing input, and SHALL NOT
    invent, guess, or default a value for it.
9.3 WHEN the system suggests a category THEN it SHALL be one of the user's
    existing categories, never a newly invented one.
9.4 WHEN the user edits a pre-filled field before confirming THEN the system SHALL
    save the edited value, not the originally suggested one.
9.5 WHEN a voice-captured expense is confirmed THEN it SHALL behave identically to
    a manually entered expense — same fields, same appearance in Today and month
    totals, same editability.
9.6 WHEN the spoken amount uses Latin-American spoken forms ("catorce mil",
    "14 mil", "14.000") THEN the system SHALL resolve it to the same numeric
    value for confirmation.
9.7 WHEN the user names a payment method aloud in everyday Spanish ("con la
    tarjeta de crédito", "en efectivo") THEN the system SHALL match it to one of
    the user's existing payment methods, or leave the field empty per 9.2 if it
    cannot.

### Requirement 10 — Voice to journal

As the only user, I want to speak a journal entry and have my own words kept, so
that the journal stays mine.

#### Acceptance Criteria

10.1 WHEN the user captures voice in the Journal module THEN the system SHALL put
     the full transcript into the entry text for review.
10.2 WHEN the transcript is presented THEN the system SHALL NOT summarise, rewrite,
     rephrase, translate, or "improve" the user's words; only literal transcription
     and ordinary punctuation are permitted.
10.3 WHEN the user edits the transcript before confirming THEN the system SHALL
     save the edited text.
10.4 WHEN a voice journal entry is confirmed THEN it SHALL be indistinguishable
     from a typed entry in the journal list and equally editable.

### Requirement 11 — Insights

As the only user, I want the record to tell me something I did not already know —
both when I ask and without my asking — so that keeping it is worth the effort.

#### Acceptance Criteria

**Shared behaviour**

11.1 WHEN the system produces an insight THEN it SHALL be derived only from the
     user's own recorded expenses and journal entries, and SHALL NOT introduce
     outside facts, advice, or general knowledge presented as being about the user.
11.2 WHEN an insight states a figure THEN that figure SHALL match what the user
     can verify on the corresponding Finances screen.
11.3 WHEN there is too little data to say anything THEN the system SHALL say so
     plainly rather than produce a generic or invented observation.
11.4 WHEN the insights capability is unavailable, still loading, or failing THEN
     every other part of the app — capture, editing, viewing totals, journal —
     SHALL continue to work normally, and the failure SHALL be visible and
     explained.
11.5 WHEN an insight is being generated THEN the system SHALL show a visible
     in-progress state, and SHALL either return a result or an explicit failure.
11.6 WHEN insights run THEN the system SHALL NOT create, modify, or delete any
     expense or journal entry as a result — insights are read-only.
11.7 WHEN any insight text is produced THEN it SHALL be in Spanish.

**On-demand questions**

11.8 WHEN the user asks a question in Spanish about their finances — e.g. "¿cuánto
     gasté en comida este mes?" — THEN the system SHALL answer from the user's own
     recorded expenses for the period the question names.
11.9 WHEN the user asks a question in Spanish about their journal — e.g. "¿qué me
     preocupaba en julio?" — THEN the system SHALL answer from the user's own
     journal entries for the period the question names.
11.10 WHEN the user asks a question THEN the system SHALL accept it either typed
      or by voice, using the same voice behaviour as Requirement 8.
11.11 WHEN a question cannot be answered from the recorded data THEN the system
      SHALL say that it cannot answer, and SHALL NOT fabricate a figure, a date,
      or a quotation from an entry that does not exist.
11.12 WHEN the user asks a question THEN the system SHALL show a working state
      within 1 second, SHALL keep that state visibly alive (not a frozen spinner)
      while it works, and SHALL return either an answer or an explicit failure
      within 120 seconds.
11.13 WHEN an answer is taking time to generate THEN the user SHALL be able to
      cancel it and leave the screen, and doing so SHALL NOT affect any saved data.

**Periodic summary**

11.14 WHEN a period completes THEN the system SHALL produce, without the user
      asking, a short written summary covering that period's spending and journal.
11.15 WHEN the user opens the insights area THEN the most recent completed summary
      SHALL be readable immediately, without waiting for anything to be generated
      at that moment.
11.16 WHEN a summary has never yet been produced, or the period contains no data
      THEN the system SHALL show an explicit state saying so, rather than a blank
      area or a fabricated summary.
11.17 WHEN a summary is being produced THEN it SHALL NOT block, slow, or interrupt
      expense capture, journal capture, or any view of the user's data.
11.18 WHEN a summary is shown THEN it SHALL state which period it covers and when
      it was produced.

*(Note for QA, not a criterion: on the measured hardware the local model is
expected to take seconds-to-tens-of-seconds. The 120-second bound in 11.12 and the
"already produced" requirement in 11.15 exist because of that, and are the honest
bar — a slow but bounded, visible, cancellable answer passes. A fast one is a
bonus, not the requirement.)*

### Requirement 12 — Zero cost

As the only user, I want this to cost me nothing, ever, so that a personal habit
does not become a subscription.

#### Acceptance Criteria

12.1 WHEN the system is set up and used by one person for a year THEN it SHALL
     require no paid subscription, licence, metered service, or paid tier.
12.2 WHEN the system is set up THEN it SHALL NOT require entering a credit card,
     billing address, or any payment instrument at any step, including on any
     third party it depends on.
12.3 *(Retired at the Kickoff gate — superseded by Requirement 15. With no
     third-party services there are no third-party quotas to surface. Number
     retired, not reused.)*
12.4 WHEN the system runs THEN no functionality SHALL depend on a remote service
     that could later begin charging, rate-limiting, or shutting down.

### Requirement 13 — Reaching it from the phone

As the only user, I want the app on my phone to reach the server on my PC from
wherever I am, so that I can record the spend the moment I make it.

#### Acceptance Criteria

13.1 WHEN the user opens the app on their phone THEN the system SHALL be usable
     without installing anything from an app store.
13.2 WHEN the phone cannot reach the server on the PC THEN the system SHALL show
     an explicit "cannot reach your server" state that names the problem, rather
     than a blank screen, an infinite spinner, or a silent failure.
13.3 WHEN the user returns to the app after the server becomes reachable again
     THEN the system SHALL recover without the user reinstalling, clearing data,
     or losing anything previously saved.
13.4 WHEN the user is away from home and on mobile data THEN the system SHALL be
     fully usable — every capture, every view, and the insights capability behave
     as they do at home.
13.5 WHEN a save is attempted and the server cannot be reached THEN the system
     SHALL keep the user's typed text or transcript on screen so it can be retried,
     and SHALL NOT discard what the user just entered.
13.6 WHEN the system is running THEN the server and the database on the PC SHALL
     NOT be reachable from the public internet — only from the user's own private
     network.
13.7 WHEN the user has completed the one-time setup on their phone THEN routine
     daily use SHALL require no additional connection step, login, or manual
     action before capturing something.

### Requirement 14 — The record survives

As the only user, I want my data to still be there tomorrow, so that a journal I
keep for years is not one crash from gone.

#### Acceptance Criteria

14.1 WHEN the server or the PC is restarted THEN every previously saved expense
     and journal entry SHALL still be present and unchanged.
14.2 WHEN the user asks to export THEN the system SHALL produce a file containing
     all expenses and all journal entries in a format readable without this app.
14.3 WHEN the user deletes nothing THEN the system SHALL delete nothing — no
     automatic expiry, archival, or pruning of old expenses or entries.

### Requirement 15 — The data never leaves the PC

As the only user, I want my spending and my private writing to stay in my house,
so that using this costs me no privacy.

#### Acceptance Criteria

15.1 WHEN the user records anything by voice THEN the audio SHALL be processed only
     on the user's own PC, and SHALL NOT be transmitted to any third party.
15.2 WHEN insights are generated, on demand or periodically THEN the expense and
     journal content used SHALL be processed only on the user's own PC, and SHALL
     NOT be transmitted to any third party.
15.3 WHEN the system runs normally THEN it SHALL make no request to any external
     service carrying the user's expenses, journal text, audio, or anything
     derived from them.
15.4 WHEN the system is set up or used THEN it SHALL NOT require creating an
     account with, authenticating to, or holding an API key for any external
     service in order to transcribe voice or generate insights.
15.5 WHEN the user's home internet connection is down but the phone and the PC are
     both on the private network THEN voice capture and insights SHALL still work.

---

## Assumptions

Decisions taken rather than escalated. Object to any of these at Approve Plan;
each is cheap to reverse now and expensive to discover at QA. Items marked
**[confirmed]** were assumptions I made that the human has since confirmed at the
Kickoff gate; **[revised]** items changed as a result of his answers.

- **A1. Expenses only — no income, balances, or budgets.** Every concrete detail
  in the ask concerns spending and its categorisation.
- **A2. Single currency, Colombian pesos, whole pesos with no cents.** The ask
  says "pesos" and writes `14.000` in Latin-American convention, where cents are
  not used in practice.
- **A3. [confirmed] Interface language is Spanish.**
- **A4. [revised] Voice input is Spanish only; no language switcher.** Spanish was
  confirmed, so a selector became unused scope that conflicts with the stated wish
  for something uncomplicated.
- **A5. The app runs in the phone's browser, not as an app-store install.** The
  ask describes a server and a phone, not a published app; an app store listing
  would also conflict with Requirement 12.
- **A6. [revised] There is no in-app login or passcode.** The private network is
  the access boundary (13.6), the phone is David's own, and an unlock step before
  every capture is exactly the friction this app exists to remove. *Reversible —
  say so if you want the app itself locked in case the phone is lost or lent.*
- **A7. Categories and payment methods ship with a sensible starter list, in
  Spanish, and are fully user-editable.** A fixed list would invent a constraint
  the user did not state; an empty list makes first use hostile.
- **A8. Per-payment-method totals are shown alongside the category percentages.**
  The ask records payment method deliberately and states no other use for it.
- **A9. Expenses default to today and may be backdated but not future-dated.** This
  is a record of what happened, not a planner.
- **A10. One category and one payment method per expense; no split expenses.** No
  split spend is described and splitting would add a decision at capture time.
- **A11. Journal entries are plain text with no title, tags, mood, photos, or
  formatting.** The ask says "any text I want to put, simple as that".
- **A12. Month view can navigate to previous months.** A tracker whose history is
  unreachable stops being worth keeping after thirty days.
- **A13. Gym is a visible, labelled, inert destination with no data model behind
  it.** The ask says to leave the space only.
- **A14. Full data export is included in this pass.** The journal is irreplaceable
  personal writing and the ask specifies no backup mechanism at all.
- **A15. [revised] There is no offline queue on the phone; the private network
  must be reachable at the moment of capture.** Away-from-home use is now required
  (13.4), but it is served by the private network rather than by storing captures
  on the phone. Criterion 13.5 covers the residual risk — a failed save keeps your
  text on screen instead of losing it. *A true offline queue is real scope; say so
  if a dropped connection mid-Uber is something you expect to hit often.*
- **A16. No notifications, reminders, streaks, or any prompt to use the app.** Not
  requested, and it conflicts with the stated wish for something uncomplicated.
- **A17. Insights are read-only and never act on the user's data.** An assistant
  that edits the record silently is a data-integrity risk in a system with no
  second pair of eyes.
- **A18. Light interface only; no dark mode in this pass.** The ask specifies
  "mostly white".
- **A19. The periodic summary covers a calendar month and is produced when the
  month ends.** The ask's only stated time horizons are "today" and "this month",
  so the summary matches the unit the user already thinks in. *Say so if you'd
  rather have it weekly.*
- **A20. The summary is produced in the background and read later, never generated
  while the user waits.** On the measured hardware, generating on open would mean
  watching a spinner for tens of seconds; hence 11.15.
- **A21. Insight answers may be slow, but must be bounded, visible, and
  cancellable** (11.12, 11.13). This is the honest bar given the hardware
  trade-off David accepted with the facts in front of him; treating slowness
  itself as a defect would be re-litigating a decision he already made.
- **A22. Only one insight question is answered at a time.** With 8 CPU cores and no
  GPU, concurrent generation makes every answer slower, and there is one user, who
  asks one question at a time.

## Open Questions

**None.** All three escalated questions were answered at the Kickoff gate and are
folded into § Decisions taken at the Kickoff gate and into the criteria above. The
uncertainties I chose not to escalate are recorded as Assumptions; **A6, A15, and
A19** are the three most worth a second look at Approve Plan.
