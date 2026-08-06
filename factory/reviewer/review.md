# Review — Autonom-OS

Static review of `backend/`, `frontend/` and `ops/` against
`factory/architect/design.md` (Interface Contract and Client-side contract),
`factory/pm/spec.md`, `factory/pm/visual-direction.md` and the approved
`mockups/`. `state.verification` was read: every gate passes
(`frontend:install/build/typecheck/unit`, `backend:unit` 231, `backend:contract`
40, `test_integrity` 179 tests / 437 assertions vs a 0/0 baseline). Nothing below
contradicts a gate result.

## Findings

### F1 — [blocking] The NumericGuard retry escapes the answer deadline, so a question can run past 11.12's 120 s
- location: `backend/autonomos/insights/runner.py:228` (`budget_s = budget_s - 1.0`), feeding the second `llm.generate(..., timeout_s=budget_s)` at `backend/autonomos/insights/runner.py:190`
- injected-at: implementer-backend
- scenario: `_run_question` correctly derives `deadline = created_at + 110` (`runner.py:94-96`), correctly refuses to start under `LLM_MIN_START_BUDGET_S` (`runner.py:116-121, 134-138`), and correctly passes `budget_s = deadline - now` into `_generate_answer`. The retry path then does **not** re-derive it. A journal question (KD-6 measures 55-76 s) created at t=0 starts generation at t≈5 with `budget_s≈105`, completes at t≈80, and NumericGuard rejects it. `attempt` is 1, so the loop sets `strict = True` and `budget_s = 105 - 1 = 104` — a duration, not a deadline — and issues a second generation at t≈80 that may run until t≈184. The guard at `runner.py:229` (`if budget_s < settings.llm_min_start_budget_s`) tests the wrong quantity: it compares the *remaining nominal budget* against 30 s and never looks at elapsed time, so it cannot fire here (104 ≥ 30). Worst case is ~2× the deadline. The client (`frontend/src/routes/finanzas/Analisis.tsx:218-235`) polls indefinitely and has no cutoff of its own, correctly, because KD-11 says the server enforces this. Correct form is `budget_s = deadline - time.time()` re-read before each attempt, with the `< llm_min_start_budget_s` check then meaningful.
- requirement: AC 11.12 ("an answer or an explicit failure within 120 seconds"); KD-11 "the answer budget is a deadline, not a duration… generation must finish by `created_at + LLM_DEADLINE_ANSWER_S`"

### F2 — [blocking] The LAN-fallback link on the "cannot reach your server" screen can never render — the origin is stored in the wrong origin's localStorage
- location: `frontend/src/state/origin.ts:12-32`; consumed at `frontend/src/routes/SinServidor.tsx:18`, `:38-42`, `:44-47`
- injected-at: implementer-frontend
- scenario: `rememberOriginIfHome()` runs at boot (`frontend/src/main.tsx:24`) and writes `window.localStorage.setItem('autonomos.homeOrigin', window.location.origin)` **only when the serving host is not `*.ts.net`**. `localStorage` is partitioned by origin (scheme+host+port). So the value is written into the storage area of `https://<LAN-IP>:8443` and is unreadable from `https://<host>.<tailnet>.ts.net`. On the primary origin the `isTailnet` guard means nothing is ever written, and `rememberedHomeOrigin()` therefore returns `null` every time; `{home && <a className={s.homeLink} href={home}>}` at `SinServidor.tsx:38` and the address at `:45` never render. On the fallback origin itself the link is deliberately suppressed (`stored === window.location.origin` → `null`, `origin.ts:28`). There is consequently **no** state of the app in which the fallback link or address appears. The user who hits 13.2 away from the LAN — or at home with the tailnet down — sees only `servidor.casaAyuda`, which names no address and offers no navigation. The frontend note asserts the opposite (`factory/implementer-frontend/note.md:60`: "remembered from the visit setup makes to the LAN origin"; `:227-235`); the code does not support that claim, and `factory/analyst/analysis-pass1.md:218` already records that `localStorage` is per-origin. Whatever replaces it must get the address from somewhere same-origin — e.g. the backend echoing its configured `LAN_BIND_ADDR`/`LAN_PORT` in `GET /api/health` or `/api/status`, which keeps KD-2's "no origin in the bundle" intact because the string is data, not a build constant. That is a contract addition and needs Architect, not a frontend-only fix.
- requirement: AC 13.8 ("the working alternative SHALL be reachable in no more than one deliberate action from what the user is already looking at"); design § Client-side contract, *Reachability* ("the state also offers a link to the LAN fallback origin (KD-2)"); KD-2 mechanism 1

### F3 — [blocking] NumericGuard rejects figures the prompt itself authorises, terminating correct answers as `unverifiable_figures`
- location: `backend/autonomos/insights/guard.py:51-76` (`allowed_values`) against `backend/autonomos/insights/prompts.py:81-86` and `:97-98` (`render_facts`)
- injected-at: implementer-backend
- scenario: `render_facts` writes the top-expense rows into DATOS as `- Gasto grande: 45.000 pesos el 2025-07-14 en Comida — <description>` (`prompts.py:81-86`) and the journal excerpts as `- Diario 2025-07-14: "<text>"` (`prompts.py:98`), while `SYSTEM_ANSWER` rule 3 tells the model "Solo puedes repetir cifras que aparecen literalmente en DATOS" (`prompts.py:25-27`). `allowed_values` builds its set from totals, counts, distinct days, `by_category` amounts and percents, `by_payment_method` amounts, `top_expenses[].amount_cop`, the journal counts, and the year/month/day components of `period_start`/`period_end` only. It never adds `top_expenses[].spent_on` components, digits inside `top_expenses[].description`, journal-excerpt dates, or digits inside excerpt text. `check()` (`guard.py:84-90`) tokenises every digit run, so an answer to "¿en qué gasté más en julio?" that says "el gasto más grande fue de $45.000 el **14** de julio" produces the token `14`, which is absent from `allowed` unless it coincidentally matches an amount or count. The job then burns its one strict retry and terminates `unverifiable_figures`, and the UI tells the user "No puedo responder eso con lo que tienes anotado" (`frontend/src/copy/es.ts:277-278`) about a question that was answered correctly. This is a static contradiction between two modules, not a guess about model behaviour: the prompt permits exactly what the guard forbids. KD-10 stage 4 defines the rule as membership in *the fact set*, and `spent_on` and the excerpts are in the fact set (KD-10 stage 2 lists "top expenses" and journal excerpts).
- requirement: AC 11.8, AC 11.9; KD-10 stage 4

### F4 — [deferred] The `generating` summary surface becomes effectively unreachable after the first successful month
- location: `backend/autonomos/api/insights.py:99` (`row = summaries_repo.latest_ready(conn) or summaries_repo.latest(conn)`), with `latest_ready` selecting `status IN ('ready','empty')` at `backend/autonomos/repo/summaries.py:33-37`
- injected-at: implementer-backend
- scenario: once any month has a `ready` or `empty` row, `/api/insights/summaries/latest` prefers it over a newer row that is `generating`, so the response can no longer be `{"status":"generating"}` and `SummaryCard`'s generating branch (`frontend/src/routes/finanzas/Analisis.tsx:321-332`) renders only before the very first finished summary exists. Design Constraint 27 asks the summary surface to distinguish "a summary currently being produced" on sight; the surface exists and is well built, but the wire state that drives it is near-unreachable in steady use. The choice is documented (`factory/implementer-backend/note.md:130-135`) and pinned by a test, and it is defensible under KD-12 ("11.15 still holds, because the previous completed summary is a row in the database and `/latest` reads it"), which is why this is not blocking. A resolution — e.g. carrying a `generating` marker alongside the ready row — is a contract change for Architect, not implementer rework in this pass.
- requirement: Design Constraint 27; AC 11.15

### F5 — [deferred] The failed-save banner is red, which Design Constraint 3 reserves for destructive confirmation and validation errors
- location: `frontend/src/components/ui/Panel.module.css:59-65` (`.alarm` → `--danger-wash`, `--danger-line`, `--danger`), applied at `frontend/src/routes/finanzas/GastoForm.tsx:199-205` and `frontend/src/routes/diario/Entrada.tsx:140-146`
- injected-at: pm
- scenario: a save that fails because the server is unreachable is neither a destructive confirmation nor a validation error, so constraint 3's "It appears nowhere else" is not met as written. The built UI is faithful to what the human approved: `mockups/gasto-guardar-fallo.html:481` renders the same banner with `style="background:var(--danger-wash);border-color:#F0C3C8"` and a `--danger`-coloured icon. Repainting it now would move the shipped app *away* from the approved mockup, and the constraint as written has no colour for "the write failed and nothing was lost". This wants PM to widen constraint 3 to cover a failed write, or an explicit instruction to repaint — it is not implementer rework. Flagged honestly by the frontend at `factory/implementer-frontend/note.md:81` and `:237-238` rather than changed quietly; that disclosure is the right behaviour and is why this is `deferred` rather than an undocumented mockup departure.
- requirement: Design Constraint 3

### F6 — [deferred] The journal "Todo" list stops at the 50 newest entries with no way to load older ones
- location: `frontend/src/routes/diario/Diario.tsx:14` (`useJournal()`), `frontend/src/api/queries.ts:186-191` (`limit: 50`, response `next_before` never read), `frontend/src/api/types.ts:111-114`, orphaned copy at `frontend/src/copy/es.ts:118` (`cargarMas: 'Ver entradas más antiguas'`, defined and rendered nowhere — `rg cargarMas` returns only its definition)
- injected-at: implementer-frontend
- scenario: with 51 or more entries the "Todo" tab renders only the newest 50 and offers no control to page further; the contract's `before` cursor and `next_before` field (`backend/autonomos/api/journal.py:21-32`) are implemented server-side and unused client-side. Older entries stay reachable a day at a time through `/diario/fecha` (`Diario.tsx:47-97`), and 7.1 as written only requires listing entries newest first and labelled by date, so this is not a criterion failure — but the orphaned copy string shows the affordance was intended and dropped.
- requirement: AC 7.1 (letter met), design § Interface Contract `GET /api/journal`

### F7 — [optional] A `failed` summary is retried immediately, up to three times back to back
- location: `backend/autonomos/scheduler.py:134-154` — `_drain_summaries` re-runs `pending_summary_months()` and re-enters `run_summary` for the same month with no delay; only `cancelled` outcomes are counted (`MAX_CANCEL_RETRIES`)
- injected-at: implementer-backend
- scenario: three consecutive `llm_unavailable` failures against `LLM_TIMEOUT_SUMMARY_S=300` burn all three attempts within one tick while Ollama is simply down, leaving the month permanently `failed`. Backoff shape is explicitly the implementer's under design § Deferred Decisions, so this is a preference, not a defect. Mentioned once.

## Verdict

CHANGES_REQUESTED

## Scope Statement

Static only. I did not execute anything — no server, no browser, no sidecar — and
I did not re-run or re-litigate the deterministic gates, which all pass.

What I checked by reading, and what that does and does not establish:

- **Backend/frontend drift.** I compared `backend/autonomos/api/models.py`,
  `repo/` and the routers against `frontend/src/api/types.ts`, `queries.ts` and
  `client.ts`, field by field, against the Interface Contract. **No shape, field
  name, status code or error code diverges.** `source` appears in no expense or
  journal response (`repo/expenses.py:28-40`, `repo/journal.py`, `api/models.py:84-95,151-157`)
  and only in `GET /api/export` (`api/export.py:47,55`), as the design requires.
  `partial_answer` is written for diagnostics (`repo/jobs.py:68-71`) and appears
  in no response model or handler (`api/models.py:238-255`, `api/insights.py:63-75`);
  `answer` is populated only by `finish_done`. All sixteen closed error codes are
  emitted by the backend (`errors.py:16-35`) and mapped to Spanish
  (`copy/es.ts:264-285`), and `journal_truncated` is surfaced with both counts
  (`Analisis.tsx:266-299`, `copy/es.ts:189-190`), as the client-side contract
  makes obligatory.
- **The InferenceArbiter (KD-12).** The class ordering is correct:
  `TRANSCRIPTION(0) < QUESTION(1) < ASSIST(2) < SUMMARY(10)` sorted at
  `arbiter.py:215`; transcription preempts a running question with
  `REASON_PREEMPTED` (`arbiter.py:183-185`) which becomes terminal `preempted`
  (`runner.py:197-206`); a question waits for a running transcription and that
  wait is *subtracted* from the deadline (`runner.py:121`, `wait_budget = remaining - 30`);
  assist yields and is abandoned to a `null` result (`api/expenses.py:113-118`);
  the 60-second quiet period gates only `SUMMARY` waiters (`arbiter.py:110-114,217-221`)
  and is armed from interactive release (`arbiter.py:165-172`). Cancellation is
  awaited *against* each SSE line rather than checked between them
  (`providers/openai_compatible.py:28-58`), with a 2 s force-take backstop
  (`arbiter.py:198-204`). I read this as correct; whether preemption actually
  lands inside R4's ~1 s residual is a runtime claim I cannot verify.
- **The four-interaction budget (2.8).** Inline single-tap chips only
  (`components/ui/Chip.tsx:38-53`), no `<select>`, modal or bottom sheet on the
  capture path; asserted through the real component tree at
  `src/test/captura.test.tsx:28-78`.
- **Navigation and Gym.** Exactly three bottom-nav destinations, part of the
  frame rather than any route (`components/shell/Screen.tsx:120-142`); Análisis
  and Ajustes are sub-routes (`App.tsx:43-52`); no capture bar on `/gimnasio`
  (`routes/Gimnasio.tsx:12-17`, `capture={null}`) and no Gym endpoint anywhere.
- **Service worker scope (KD-13).** Precaches shell/hashed assets/manifest/icons
  from the real build manifest (`vite.config.ts:13-40`); `/api/*` returns before
  any cache lookup (`sw/sw-template.js:44`); non-GET is untouched (`:38`); no
  sync handler, no IndexedDB, no queue. Scope has not widened.
- **KD-2, no origin in the bundle.** I grepped the built output: the only
  absolute URLs in `frontend/dist/assets/index-D-Rzcqig.js` are React's error-decoder
  link and W3C XML namespaces. No `8001`, `8443`, `ts.net`, `127.0.0.1` or
  `localhost`.
- **Design Constraints.** I confirmed each *checkable* constraint is **expressed
  in the code** — one violet hue and one red in `styles/tokens.css`, no
  `prefers-color-scheme` anywhere, one self-hosted OFL typeface, empty and error
  states present for every screen that can have them, elapsed-only progress with
  no `total` prop on `Tally`, cancel offered from t=0 on transcription. I did
  **not** confirm they *render* that way: contrast ratios, 44×44 hit boxes, the
  390 px no-horizontal-scroll claim and the "0 findings" screenshot audit are
  browser measurements and belong to QA. Constraint 3 is the one constraint the
  source does not satisfy as written (F5). Feel & Tone I read as consistent with
  the direction and did not turn into a pass/fail finding.
- **Mockup fidelity.** I diffed the built shell against `mockups/finanzas-hoy.html`
  and `mockups/gasto-guardar-fallo.html` and found the structure, chips, capture
  bar, tabs and nav carried across faithfully. The six departures the frontend
  lists (`factory/implementer-frontend/note.md:57-64`) are documented and
  reasonable; I found no *undocumented* departure. I did not diff all 40 screens
  or look at the 57 renders in `shots/` — QA owns pixel comparison.
- **The two unreachable states.** I read them rather than ran them.
  `getUserMedia` rejection is caught and routed to `{ kind: 'denied' }`
  (`voice/VoiceContext.tsx:210-217`), and the feature test for
  `navigator.mediaDevices?.getUserMedia` / `typeof MediaRecorder` precedes any
  permission request (`:205-208`) so `{ kind: 'unsupported' }` cannot be
  shadowed by a permission prompt. Both render distinct Spanish screens that
  keep the manual path one tap away (`voice/VoiceScreen.tsx:163-196`), and
  neither issues a request. **Both paths read as correct.** That they behave
  correctly on a real Android device with the permission actually denied is QA's
  to establish; I cannot.
- **Not checked at all:** runtime behaviour of any kind, the systemd units in a
  live session, `tailscale serve`, the mkcert LAN listener, transcription
  accuracy, LLM output quality, and every criterion whose evidence is a
  measurement rather than a line of code.
