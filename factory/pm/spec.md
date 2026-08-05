# Autonom-OS — Product Spec

**Status: DRAFT pending three open questions (see § Open Questions).** Everything
outside those three items is settled. Assumptions are the human's control surface
at the Approve Plan gate — read § Assumptions before § Acceptance Criteria.

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

## Scope

### In scope (this pass)

- **Finances** — record an expense with amount, category, and payment method;
  see today's spending; see this month's spending broken down by category as
  percentages.
- **Journal** — free-text entries, dated, browsable by date.
- **Gym** — a navigational placeholder only.
- **Two input methods across modules** — voice and manual.
- **LLM insights** over the user's own recorded data, at zero cost.
- **Phone-first use** against a self-hosted server on the user's PC.

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
8. **Journal search.** Entries are reached by date, not by query.
9. **Any paid service, paid tier, trial that converts to paid, or dependency
   that requires payment details.** See Requirement 12.
10. **A public/marketing surface.** No landing page, no sign-up flow, no docs
    site, no app store listing.

---

## Acceptance Criteria

Numbers are stable. If a criterion is retired later, its number is retired with
it rather than reused.

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
    starter set of payment methods.
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

### Requirement 11 — Insights *(shape pending Q3 — see Open Questions)*

As the only user, I want the record to tell me something I did not already know,
so that keeping it is worth the effort.

#### Acceptance Criteria

11.1 WHEN the system produces an insight THEN it SHALL be derived only from the
     user's own recorded expenses and journal entries, and SHALL NOT introduce
     outside facts, advice, or general knowledge presented as being about the user.
11.2 WHEN an insight states a figure THEN that figure SHALL match what the user
     can verify on the corresponding Finances screen.
11.3 WHEN there is too little data to say anything THEN the system SHALL say so
     plainly rather than produce a generic or invented observation.
11.4 WHEN the LLM is unavailable, quota-limited, or slow THEN every other part of
     the app — capture, editing, viewing totals, journal — SHALL continue to work
     normally, and the failure SHALL be visible and explained.
11.5 WHEN an insight is being generated THEN the system SHALL show a visible
     in-progress state, and SHALL either return a result or an explicit failure.
11.6 WHEN insights run THEN the system SHALL NOT create, modify, or delete any
     expense or journal entry as a result — insights are read-only.

*(Further criteria under Requirement 11 will be added once Q3 fixes whether
insights are user-asked, system-offered, or both.)*

### Requirement 12 — Zero cost

As the only user, I want this to cost me nothing, ever, so that a personal habit
does not become a subscription.

#### Acceptance Criteria

12.1 WHEN the system is set up and used by one person for a year THEN it SHALL
     require no paid subscription, licence, metered service, or paid tier.
12.2 WHEN the system is set up THEN it SHALL NOT require entering a credit card,
     billing address, or any payment instrument at any step, including on third
     parties it depends on.
12.3 WHEN a free service the system depends on imposes a usage quota and that
     quota is reached THEN the system SHALL surface a clear message naming the
     limit, and SHALL NOT silently degrade and SHALL NOT auto-upgrade to a paid
     tier.
12.4 WHEN the system reaches a third-party quota THEN capture and viewing of the
     user's own data SHALL remain fully functional.

### Requirement 13 — Reaching it from the phone *(access model pending Q1)*

As the only user, I want the app on my phone to reach the server on my PC, so
that the thing works where I actually am.

#### Acceptance Criteria

13.1 WHEN the user opens the app on their phone THEN the system SHALL be usable
     without installing anything from an app store.
13.2 WHEN the phone cannot reach the server on the PC THEN the system SHALL show
     an explicit "cannot reach your server" state that names the problem, rather
     than a blank screen, an infinite spinner, or a silent failure.
13.3 WHEN the user returns to the app after the server becomes reachable again
     THEN the system SHALL recover without the user reinstalling, clearing data,
     or losing anything previously saved.

*(Whether the app must be reachable away from home, and what access control that
implies, is Q1. Criteria for that will be added once answered.)*

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

---

## Assumptions

Decisions taken rather than escalated. Object to any of these at Approve Plan;
each is cheap to reverse now and expensive to discover at QA.

- **A1. Expenses only — no income, balances, or budgets.** Every concrete detail
  in the ask concerns spending and its categorisation; nothing mentions money
  coming in.
- **A2. Single currency, Colombian pesos, whole pesos with no cents.** The ask
  says "pesos" and writes `14.000` in Latin-American convention, where cents are
  not used in practice.
- **A3. Interface language is Spanish.** The app is used in a Spanish-speaking
  daily context and the spoken input will be Spanish; the ask being written in
  English is communication with the builder, not a product requirement. *(Flag
  this one if wrong — it touches every string.)*
- **A4. Voice input is Spanish, with the language selectable in settings.** Same
  reason as A3; selectability makes it cheap to be wrong.
- **A5. The app runs in the phone's browser, not as an app-store install.** The
  ask says "connect to it using my phone" and describes a server, not a published
  app; an app store listing would also conflict with Requirement 12.
- **A6. No login or account UI is presented on the user's own home network.** There
  is exactly one user and the ask asks for simplicity. *(Subject to Q1 — an
  away-from-home answer changes this.)*
- **A7. Categories and payment methods ship with a sensible starter list and are
  fully user-editable.** A fixed list invents a constraint the user did not state;
  an empty list makes the first use hostile.
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
- **A15. The app requires the server to be reachable at the moment of capture;
  there is no offline queue on the phone in this pass.** Offline capture is real
  scope and the ask does not ask for it. *(This is the assumption most likely to
  be overturned by the answer to Q1.)*
- **A16. No notifications, reminders, streaks, or any prompt to use the app.** Not
  requested, and it conflicts with the stated wish for something uncomplicated.
- **A17. Insights are read-only and never act on the user's data.** An assistant
  that edits the record silently is a data-integrity risk in a system with no
  second pair of eyes.
- **A18. Light interface only; no dark mode in this pass.** The ask specifies
  "mostly white".

## Open Questions

Three, each of which materially changes scope, cost, or what the user
experiences; each has more than one reasonable reading; and none has a default I
could pick and defend.

**Q1 — Do you need to use this away from home, or only on your own Wi-Fi?**
*(scope + security)*
The ask says the server lives on your PC and you connect with your phone. If that
means only when you are home on the same network, the app stays simple and closed.
But the headline use case — saying "I spent 14.000 on Uber" the moment you get out
of the Uber — happens on the street, on mobile data. Making it work there means
your PC has to be reachable from the internet, which brings in access control (a
passcode or similar on the app) and a real security surface. Answering "home only"
also means expenses get entered later, from memory, which is exactly the friction
this app exists to remove. Which do you want?

**Q2 — May your data leave your PC to a free third-party service, or must
everything stay local?** *(privacy + cost + feasibility)*
Both voice transcription and the LLM insights need to run somewhere. Free options
split into two families: (a) free cloud tiers — your spoken audio and your journal
text get sent to an outside company's servers, costs nothing, works on any
hardware, but has quotas and means personal reflections leave your house; or
(b) fully local on your PC — nothing ever leaves, no quotas, but it depends on
your PC being strong enough and quality will be lower. There is a middle option:
local for the journal (the private part) and cloud for finance parsing. Which line
do you want drawn? If you can tell me your PC's rough specs (RAM, and whether it
has a dedicated GPU) that helps me tell you whether (b) is realistic.

**Q3 — What should the LLM actually do with your information?** *(scope)*
"Insights about my information" reads two different ways and they are different
products. (a) **You ask** — a box where you type or say "how much did I spend on
food this month?" or "what was I worried about in July?" and it answers from your
own records. (b) **It tells you** — the app produces a short written summary on
its own, e.g. at the end of each month, pointing out patterns in your spending and
your journal without you asking. (c) Both. Which one is the thing you pictured?
