> **Persisted by the orchestrator, not by the artifact-analyst.**
> The analyst role's `Write` was blocked by the harness, so it returned the
> complete report as chat text and the orchestrator wrote it to this path
> **unedited** — no summarizing, no reordering, no trimming. Treat the body
> below as the role's own words. The analyst is a read-only role and had no
> write access to this file.
>
> Orchestrator-established fact the analyst could not check for itself, kept
> here rather than folded into its prose: the analyst notes `PRINCIPLES.md` is
> absent from this tree. That is correct for the *project* repo. A
> `PRINCIPLES.md` does exist in the factory's own repo at
> `/home/david/Proyectos/software_factory/PRINCIPLES.md`, which was never
> supplied to the role and governs the factory, not this product. Pass 6 being
> unrun is therefore expected and not a gap in this analysis.

---

# Autonom-OS — Artifact Analysis

Read-only cross-artifact check of `factory/pm/spec.md`, `factory/pm/visual-direction.md` and `factory/architect/design.md`, run before the Approve Plan gate. No code was read; no artifact was modified.

## Verdict

FAIL

Two CRITICAL findings. Both are contradictions inside the design itself — a criterion the design claims, against a mechanism the design also states. Neither requires a redesign; both require a decision that nothing currently records, and both are cheaper to settle now than at QA.

This is a strong design. Nominal coverage is complete, the `requirements:` annotations are unusually disciplined, and the three load-bearing decisions (rules-first parse, SQL-computes/LLM-phrases, job-plus-polling) are the right shape for the hardware. The FAIL is narrow and specific, not a rejection of the approach.

---

## Coverage

Coverage is computed against every numbered criterion in `spec.md`. 12.3 is retired at the Kickoff gate and is excluded from the denominator; its number is shown but not counted.

"Covered by" cites the design element whose `requirements:` line names the criterion. "Verified" marks claims I read the entry against the criterion text rather than trusting the annotation — see § Claim verification below.

| Criterion | Covered by | Notes |
|---|---|---|
| 1.1 | Client-side contract — App shell | partial — see A5, the insights area has no home among "exactly three" |
| 1.2 | Client-side contract — App shell | |
| 1.3 | Client-side contract — Gym placeholder; KD-16 | |
| 1.4 | Client-side contract — App shell; Frontend structure | see A13, interaction with 1.3 on the Gym route |
| 1.5 | Client-side contract — Spanish everywhere; KD-17 | see A12 (LLM output) and A25 (route names) |
| 2.1 | POST /api/expenses | verified |
| 2.2 | POST /api/expenses (`must_be_positive`, `required`) | verified |
| 2.3 | POST /api/expenses (`unknown_id`, `required`) | verified |
| 2.4 | POST /api/expenses notes; Client-side — Amount input; KD-8 Layer 1 | verified |
| 2.5 | Client-side contract — Amount input and display | verified |
| 2.6 | POST /api/expenses (`description` optional) | verified — but see A4 |
| 2.7 | POST /api/expenses (`future_date`) | verified |
| 2.8 | Client-side contract — Four-interaction capture budget | |
| 3.1 | GET /api/categories; payment-methods; Seed data | verified |
| 3.2 | POST /api/categories; payment-methods | verified |
| 3.3 | PATCH /api/categories/{id} | verified — FK reference makes it structural |
| 3.4 | DELETE /api/categories/{id}; GET /api/summary/month; Data model | verified — archive, never delete; see A14 on the error shape |
| 3.5 | POST /api/expenses; Data model (`NOT NULL` FKs) | verified |
| 4.1 | GET /api/expenses; GET /api/summary/day | verified |
| 4.2 | GET /api/summary/month | verified |
| 4.3 | GET /api/summary/month (largest-remainder) | verified — design is stricter than the criterion |
| 4.4 | GET /api/summary/month (`by_payment_method`) | verified |
| 4.5 | GET /api/summary/month (`is_empty`) | verified |
| 4.6 | PATCH/DELETE expenses; summary endpoints; KD-13 | |
| 4.7 | GET /api/summary/month (`month` param) | verified |
| 4.8 | GET /api/summary/day, /month; `clock/`; Time | verified — server authoritative |
| 5.1 | GET/PATCH /api/expenses/{id} | verified |
| 5.2 | DELETE expenses/{id}; DELETE journal/{id}; Client-side — Destructive confirmation | verified |
| 5.3 | PATCH /api/journal/{id} | verified |
| 6.1 | POST /api/journal | verified |
| 6.2 | POST /api/journal (`blank`) | verified |
| 6.3 | POST /api/journal notes; Data model | verified |
| 6.4 | POST /api/journal notes (byte-exact) | verified |
| 6.5 | POST /api/journal (`no maximum`) | verified |
| 6.6 | POST /api/journal (text only) | verified |
| 6.7 | POST /api/journal notes | verified |
| 7.1 | GET /api/journal | verified |
| 7.2 | GET /api/journal (`date`) | verified |
| 7.3 | GET /api/journal | |
| 8.1 | Client-side contract — Voice capture UI | |
| 8.2 | POST /api/voice/transcribe | verified — endpoint writes nothing |
| 8.3 | POST /api/voice/transcribe; Client-side — Voice capture UI | verified |
| 8.4 | POST /api/voice/transcribe errors; GET /api/status; R5 | verified |
| 8.5 | Client-side contract — Voice capture UI | |
| 8.6 | POST /api/voice/transcribe; Client-side — Explicit confirmation; KD-8 | verified — structural, no audio→record endpoint |
| 8.7 | POST /api/voice/transcribe; KD-5 (`-l es --no-translate`) | verified |
| 8.8 | POST /api/voice/transcribe; KD-5 | partial — see A9, budget counts sidecar time only |
| 8.9 | POST /api/voice/transcribe; Client-side — Voice capture UI | verified |
| 9.1 | POST /api/voice/transcribe (`ExpenseDraft`); POST /api/expenses/parse | partial — see A4 |
| 9.2 | POST /api/voice/transcribe; /parse; /suggest-category; KD-8 | verified — nulls, never guesses |
| 9.3 | POST /api/expenses/suggest-category; alias tables | verified — constrained by construction |
| 9.4 | Client-side contract — Edited values win | verified |
| 9.5 | POST /api/expenses notes | partial — see A15 (`source` field) |
| 9.6 | POST /api/voice/transcribe; /parse; KD-8 Layer 1 | verified |
| 9.7 | POST /api/voice/transcribe; /parse; `payment_method_aliases` | verified |
| 10.1 | POST /api/voice/transcribe | verified |
| 10.2 | POST /api/voice/transcribe notes; KD-9 | verified — enforced by absence of a code path |
| 10.3 | Client-side contract — Edited values win | |
| 10.4 | POST /api/journal | partial — see A15 (`source` field) |
| 11.1 | GET /api/insights/questions/{job_id} notes | **claim, no mechanism — see A12** |
| 11.2 | GET job endpoint; KD-10 NumericGuard | verified — real mechanism, numeric only |
| 11.3 | GET job endpoint; KD-10 insufficiency pre-check | verified |
| 11.4 | GET /api/status | verified |
| 11.5 | POST/GET insights questions; Client-side — Live waiting states | verified |
| 11.6 | POST/DELETE insights questions | verified |
| 11.7 | GET job endpoint; GET summaries/latest | **claim, no mechanism — see A12** |
| 11.8 | POST/GET insights questions; KD-10 | partial — see A6 |
| 11.9 | POST/GET insights questions; KD-10 FactBuilder | partial — see A6, A16 |
| 11.10 | POST /api/voice/transcribe (`context="question"`); POST questions | verified |
| 11.11 | GET job endpoint (`unverifiable_figures`) | partial — see A6, wrong-period answers |
| 11.12 | POST questions (`202`); GET job (`elapsed_ms`); KD-11 | partial — see A10, A11 |
| 11.13 | DELETE /api/insights/questions/{job_id} | verified |
| 11.14 | GET summaries/latest; KD-12 scheduler | **partial — the journal half is unspecified, see A3** |
| 11.15 | GET summaries/latest ("reads a stored row; never triggers generation") | verified — the strongest part of the design |
| 11.16 | GET summaries/latest (`none`, `empty`) | verified |
| 11.17 | Non-endpoint guarantees — Summary generation never gets in the user's way | **claim contradicted by R4 — see A1** |
| 11.18 | GET summaries/latest (`period_label`, `generated_at`) | verified |
| 12.1 | Non-endpoint guarantees — Zero cost; KD-1 | |
| 12.2 | Non-endpoint guarantees — Zero cost; KD-1 | |
| 12.3 | *(retired at Kickoff — not counted)* | |
| 12.4 | Non-endpoint guarantees — Zero cost | contested — see A8 |
| 13.1 | Client-side contract — Browser-only delivery; KD-1 | verified |
| 13.2 | GET /api/health; Client-side — Reachability | **partial, and foreclosed by "no service worker" — see A2** |
| 13.3 | GET /api/health; Client-side — Reachability; `insight_jobs` persisted | verified |
| 13.4 | Non-endpoint guarantees — Away-from-home parity; KD-1 | verified |
| 13.5 | Client-side contract — Reachability | verified |
| 13.6 | Non-endpoint guarantees — Never publicly reachable; KD-1 (Funnel off) | verified — see A19 on the bind address |
| 13.7 | Non-endpoint guarantees — One-time setup only | partial — see A7 (fallback origin) |
| 14.1 | Non-endpoint guarantees — Durability; KD-4 | verified |
| 14.2 | GET /api/export; CSV exports | verified — see A22 |
| 14.3 | Non-endpoint guarantees — No automatic deletion; Data model | verified |
| 15.1 | POST /api/voice/transcribe notes; Non-endpoint — All processing local | verified — memory only, loopback sidecar |
| 15.2 | Non-endpoint guarantees — All processing local | verified |
| 15.3 | Non-endpoint guarantees — All processing local; KD-14 (self-hosted fonts) | contested — see A8 |
| 15.4 | Non-endpoint guarantees — All processing local | verified |
| 15.5 | KD-2 (LAN fallback origin); R2 | partial — see A7 |

**Coverage: 95/95 criteria claimed (100%) · 0 uncovered · verified coverage 86/95 (91%) · 9 criteria whose claiming element does not fully deliver · 4 design elements serving no criterion.**

Nominal coverage is 100% — every numbered criterion is named by at least one `requirements:` line, including all of 11, 13 and 15, the three expanded after Kickoff. Requirement 11 in particular is covered criterion-by-criterion with real mechanisms behind most of it. The gap is not omission; it is nine claims that do not survive reading the entry against the criterion.

### Claim verification

I checked 41 of the ~95 individual claims against the criterion text rather than trusting the annotation. Sampling was weighted toward Requirements 11, 13 and 15 as instructed, plus every claim asserted by the two non-endpoint blocks (which are the easiest place for an unbacked assertion to hide, since they have no request/response to inspect).

Claims verified as genuinely delivered, worth naming because they are load-bearing:

- **11.2** — `NumericGuard` is a real mechanism, not a prompt instruction. Every figure comes from SQL, and generated text carrying a number outside the fact set is rejected. This is the design's best work.
- **11.15** — `GET /api/insights/summaries/latest` reads a stored row and is documented as never triggering generation. A20 and 11.15 are structurally satisfied.
- **10.2** — enforced by the absence of a code path (KD-9), not by asking the model nicely. Correct approach.
- **9.3 / 9.7** — the alias tables point at existing category rows, so "never a newly invented category" is true by construction.
- **4.3** — largest-remainder integer percentages summing to exactly 100 is stricter than the criterion's 1-point tolerance.
- **8.6 / 8.3** — no endpoint turns audio into a saved record. Structural.
- **4.8** — the server is authoritative for day and month boundaries and `clock/` is the single place they are computed. This correctly resists the obvious phone-timezone bug.

Claims verified as **not** delivered: 11.17 (A1), 13.2 (A2), 11.14 journal half (A3), 9.1/2.6 description overflow (A4), 1.1 (A5), 11.8/11.9/11.11 period handling (A6), 15.5 and 13.7 fallback path (A7), 11.1 and 11.7 (A12), 9.5/10.4 (A15).

### Reverse direction — design without a mandate

Four design elements deliver capability no criterion asked for. None is large, none is harmful, and I am not asking for any of them to be cut — but they should be visible before the human approves the plan.

1. `POST /api/expenses/parse` — parses a **typed** sentence into an expense draft. Requirement 9 is entirely about speech. See A20.
2. `GET /api/insights/summaries` (up to 12 past summaries) — nothing asks for browsing summary history. See A21.
3. `GET /api/export/expenses.csv` and `/journal.csv` — 14.2 is satisfied by the JSON dump alone. See A22.
4. Nightly `VACUUM INTO` snapshots with 7-day retention (KD-4) — 14.1 asks only that records survive a restart. Cheap and defensible; still unmandated.

The `LLMProvider` / `TranscriptionProvider` abstraction (KD-7) is also unmandated by any criterion, but I do not count it as scope creep: R3 and R9 make the swap ladder a live mitigation, so the seam is bought by a named risk.

Every Interface Contract entry carries a `requirements:` line. There are no orphan entries.

---

## Findings

27 findings. None omitted; the cap of 50 was not reached.

### A1 — [CRITICAL] The design's 11.17 guarantee is contradicted by its own R4
- pass: contradiction
- location: design.md § Non-endpoint guarantees, "Summary generation never gets in the user's way" (`requirements: 11.17`); against design.md R4; spec.md 11.17
- detail: The guarantee reads "capture, editing, and every view read and write only SQLite and never acquire the LLM semaphore, so a summary generating in the background cannot block, slow, or interrupt them." That enumeration omits **voice** capture, which goes through whisper-server. R4 states the opposite in plain terms: "Both want all 8 cores. A transcription starting during summary generation slows both," with the residual that "8.8's 30 s bound has less headroom under contention than the 6-10 s typical figure suggests." Spec 11.17 says a summary being produced "SHALL NOT block, slow, or interrupt expense capture, journal capture, or any view." Voice expense capture is expense capture. The two statements cannot both hold, and no mechanism in the design reconciles them — the semaphore serializes LLM against LLM, never LLM against whisper. The existing summary-preemption machinery in KD-12 is the natural place to fix this (preempt or pause a summary when a transcription starts, exactly as an on-demand question already does), but the design does not say so, so an implementer would have to invent it. This is the single most likely 11.17 failure at QA and it is also the most likely 8.8 failure, since the two share one cause.
- fixed by: **architect** (extend preemption to transcription, or state the residual explicitly). If the architect judges the slowdown acceptable, **pm** must narrow 11.17, because as written it is pass/fail and the design fails it.

### A2 — [CRITICAL] 13.2's primary failure case is foreclosed by "no service worker"
- pass: contradiction
- location: design.md § Client-side contract, "Browser-only delivery" (`requirements: 13.1`) — "a web app plus a web-app manifest for home-screen install; no app store, **no service worker**"; against § Client-side contract "Reachability" (`requirements: 13.2, 13.3, 13.5`) and spec.md 13.2
- detail: 13.2 requires that when the phone cannot reach the server, the system shows an explicit "cannot reach your server" state "rather than a blank screen, an infinite spinner, or a silent failure." The design's mechanism is a TanStack Query reachability state driving a banner — which only exists once the SPA has loaded. With no service worker and no cached app shell, the most common real instance of this criterion (David taps the home-screen icon while the PC is asleep — and KD-4 says the machine "will be suspended") produces the browser's own network error page. That is precisely the outcome 13.2 forbids, and the design has ruled out the one mechanism that would cover it. Note the exclusion is not required by A15: a shell-caching service worker is not an offline queue and would not introduce the conflict-resolution scope R7 rejects. Vite's hashed asset filenames make incidental HTTP-cache survival unreliable, so nothing else covers this.
- fixed by: **architect** (either allow a shell-only service worker and say so, or state that cold-open-while-unreachable is out of 13.2's scope and let **pm** confirm that reading).

### A3 — [HIGH] The journal half of the monthly summary is specified nowhere
- pass: underspecification
- location: spec.md 11.14; design.md KD-12; § Interface Contract `GET /api/insights/summaries/latest` (`requirements: 11.14, …`)
- detail: 11.14 requires a summary "covering that period's spending **and journal**." KD-12 describes when a summary is scheduled and enqueued but never what is in it. KD-10's FactBuilder builds journal facts only "for journal questions," and the `facts` shape returned by the summary endpoint (shared with the job endpoint) carries `journal_entry_count` — a count — and no journal text. An implementer must invent whether the monthly summary runs with `domain="both"`, what journal token budget applies over a whole month (the 2,000-token figure is specified for questions), and how a month of entries is selected down to that budget. The spending half is fully specified; the journal half is not.
- fixed by: **architect**

### A4 — [HIGH] The voice draft's verbatim description can exceed the contract's 500-char limit
- pass: contradiction
- location: design.md KD-8 Layer 1, "*Description* — the full transcript verbatim"; against `POST /api/expenses` request `"description": string? (0..500)` and `POST /api/voice/transcribe` `audio … ≤ 40 s`
- detail: The draft returned by `/api/voice/transcribe` puts the entire transcript in `description`. The endpoint accepts up to 40 seconds of audio; 40 s of Colombian Spanish is roughly 600-800 characters, and even a 30 s utterance lands near 400-550 — at or over the boundary. Confirming such a draft sends it straight to `POST /api/expenses`, which rejects `description` over 500 with `validation` / `too_long`. The user's voice capture then fails at the final step with a validation error on a field he never typed. An implementer will have to choose between truncating silently, raising the cap, or trimming the draft — three different products, none recorded.
- fixed by: **architect**

### A5 — [HIGH] The insights area has no entry point, and 1.1 says "exactly three"
- pass: underspecification
- location: design.md § Frontend structure, route list including `/insights`; against spec.md 1.1, 11.15; visual-direction.md constraint 11
- detail: The design lists five routes — `/finanzas`, `/finanzas/mes`, `/diario`, `/gimnasio`, `/insights` — and a persistent bottom navigation carrying "the three destinations." Nothing says how the user reaches `/insights`. 1.1 requires *exactly* three top-level destinations and constraint 11 requires those three visible from every screen, so insights cannot become a fourth tab; it must live inside one of the three, and the design does not say which, or what the affordance is. 11.15 ("when the user opens the insights area") presupposes an entry point that no artifact defines. This is a navigation decision with a pass/fail criterion attached, left to an implementer.
- fixed by: **architect**

### A6 — [HIGH] The QuestionRouter has no "I did not understand the period" path
- pass: underspecification
- location: design.md KD-10 stage 1; against spec.md 11.8, 11.9, 11.11
- detail: The router "resolves the period from a Spanish lexicon (`este mes`, `julio`, `la semana pasada`, `ayer`; **default = current month**)." A question naming a period outside the lexicon — "en los últimos tres meses", "el año pasado", "desde que empecé", "en la primera quincena" — silently becomes a current-month question and gets a fluent, confident answer about the wrong period. 11.8 and 11.9 require the answer to cover "the period the question names," and 11.11 requires the system to say it cannot answer rather than produce a figure the data does not support for the question asked. A correct number for the wrong period is exactly the failure 11.11 exists to prevent, and NumericGuard cannot catch it — the figure *is* in the fact set. There is no `period_unrecognised` state in the closed error-code set and no fallback behaviour described.
- fixed by: **architect**

### A7 — [HIGH] Reaching the LAN fallback origin is undefined, and it is a second origin
- pass: underspecification
- location: design.md KD-2 (`https://<host>.local:8443`); R2; against spec.md 15.5, 13.7
- detail: The mkcert LAN origin is the design's answer to 15.5 (home internet down), a Kickoff-settled hard criterion. Three things an implementer must invent:
  1. **How the user gets there.** No automatic failover is possible — a page served from origin A cannot transparently retry origin B. So it is a second URL, a second home-screen icon, or a manual address edit while standing in a house with no internet. 13.7 says routine use requires "no additional connection step, login, or manual action"; nothing describes what this step is or when it is acceptable.
  2. **How `<host>.local` resolves on the phone.** mDNS resolution of `.local` from Android Chrome is historically unreliable, and the certificate name is fixed at mkcert time, so falling back to a raw LAN IP requires that IP in the cert SAN and a DHCP reservation. None of this is stated.
  3. **Per-origin browser state.** Microphone permission, `localStorage`, and the TanStack cache are scoped per origin. The user must grant mic access a second time on the fallback origin — during the exact scenario (15.5) where voice must work.
- fixed by: **architect**

### A8 — [HIGH] 12.4 disqualifies the rejected tunnels but is never applied to Tailscale
- pass: contradiction
- location: design.md KD-1 — "Cloudflare Tunnel / ngrok. Free tiers exist, but … a free tier that can start charging is a 12.4 hazard"; then "Tailscale's personal plan is free, needs no card (12.1, 12.2)"; against spec.md 12.4, 15.3, and § Decisions taken at the Kickoff gate
- detail: The same hazard class is applied as a disqualifier to one candidate and left unaddressed for the one chosen. Tailscale's personal tier is also a free tier of a remote commercial service that could begin charging, rate-limiting, or shutting down — which is what 12.4 forbids any functionality from depending on. Away-from-home use (13.4), a Kickoff-settled hard requirement, depends on it entirely; the LAN fallback covers only the home network. Separately, 15.3 forbids "any request to any external service carrying the user's expenses, journal text, audio, or anything derived from them"; when direct peer-to-peer fails, Tailscale relays traffic through third-party DERP servers. The design's answer — encrypted transit "is not third-party *processing*" — is a reasonable reading of the *intent*, and Kickoff did put the mechanism in the architect's hands. But 12.4 and 15.3 are written as absolutes, the Kickoff record lists zero recurring cost as a hard requirement separate from data locality, and this is the one place the design accepts a third party. The human should accept this knowingly at Approve Plan rather than have it discovered by QA reading 12.4 literally.
- fixed by: **human** (accept the residual and have **pm** record the acceptance against 12.4 and 15.3, or direct **architect** to a mechanism with no third-party coordination)

### A9 — [MEDIUM] 8.8's 30-second budget counts only sidecar time
- pass: underspecification
- location: design.md KD-5 ("a 30-second utterance lands around 6-10 seconds"), `STT_TIMEOUT_S=25`, KD-15; against spec.md 8.8
- detail: 8.8 starts the clock when **voice capture ends** and demands a transcript or an explicit failure within 30 s. The design budgets only whisper's own time. Between those two points also sit: `decodeAudioData` plus `OfflineAudioContext` resampling on a phone CPU, a ~960 KB upload over LTE (KD-15 says one to two seconds), the sidecar round trip, and the response. With `STT_TIMEOUT_S=25` the worst case is 25 s of sidecar plus everything else, which crosses 30 s. No end-to-end budget is stated anywhere, so nothing tells the implementer that the client-side work is inside the criterion's window.
- fixed by: **architect**

### A10 — [MEDIUM] The insight latency figure does not survive the design's own arithmetic
- pass: contradiction
- location: design.md KD-6 ("A 250-token answer is therefore 20-35 s including prompt processing"); against KD-10 stage 2 (2,000-token journal budget, "prompt processing on CPU is ~100-200 tok/s") and `LLM_MAX_TOKENS=320`
- detail: Using the design's own numbers: a 2,000-token journal context at 100-200 tok/s is 10-20 s of prompt processing, and 250 tokens at 8-15 tok/s is 17-31 s. That totals 27-51 s, not 20-35 s. At `LLM_MAX_TOKENS=320` the ceiling rises further. This still fits inside 11.12's 120 s and inside `LLM_TIMEOUT_S=110`, so the criterion is not broken — but the stated headroom is roughly half what the design claims, and both input rates are optimistic for a 3B Q4_K_M on a memory-bandwidth-bound Vega APU with 6 threads. Real-world CPU prompt eval for this class of model is often nearer 40-80 tok/s, which would put a full-context journal question at 40-70 s. The design's fallback ladder and R9 already exist; the correction needed is to the stated number, so that nobody downstream plans against 35 s.
- fixed by: **architect**

### A11 — [MEDIUM] `busy` is emitted by no endpoint, and 11.12's clock start is undefined
- pass: underspecification
- location: design.md § Interface Contract, closed error-code set (`busy`); `POST /api/insights/questions` errors (`400 validation`; `503 llm_unavailable` only); `insight_jobs.status` including `queued`; against spec.md 11.12, A22
- detail: Three connected gaps. (1) `busy` is in the closed error-code set that KD-17 requires the frontend to map to Spanish copy, but no endpoint documents returning it and no condition is named. (2) A22 allows one insight at a time; the job status enum includes `queued`, implying a second question waits — but nothing says whether a second question queues or is rejected with `busy`. (3) If it queues, 11.12's 120-second bound is measured from an undefined point: request time (in which case queueing can blow the bound) or generation start (in which case the user can wait longer than 120 s and the criterion is still nominally met). KD-12 solves the summary-versus-question collision with preemption but says nothing about question-versus-question.
- fixed by: **architect**

### A12 — [MEDIUM] 11.1 and 11.7 rest on prompt text alone, in a design that elsewhere refuses to
- pass: underspecification
- location: design.md `GET /api/insights/questions/{job_id}` notes — "`answer` is always Spanish and derives only from the user's own records" (`requirements: 11.1, …, 11.7`); against spec.md 11.1, 11.7, 1.5 and KD-17
- detail: The design is admirably mechanism-driven where it counts — 11.2 has NumericGuard, 10.2 has the absence of a code path, 9.3 has construction. 11.1 ("SHALL NOT introduce outside facts, advice, or general knowledge presented as being about the user") and 11.7 ("SHALL be in Spanish") have neither guard nor structure, only an assertion in a notes line. NumericGuard catches wrong *numbers*; it does not catch "deberías reducir tus gastos en restaurantes", which is general advice presented as being about the user and is a clean 11.1 failure. Nor does anything detect an English-drifting answer, which 1.5 and constraint 23 forbid while KD-17 places all user-visible Spanish in the frontend — a rule the LLM's output is the sole exception to, unstated. I am not asking for a second guard; I am asking that the design say these two are prompt-enforced and accepted, so QA tests them as judgement calls rather than assuming a mechanism exists.
- fixed by: **architect**

### A13 — [MEDIUM] The per-module capture bar on the Gym route collides with 1.3
- pass: contradiction
- location: design.md § Frontend structure — "a per-module capture bar in the thumb zone with *voice* and *manual* (1.4, constraint 9)"; against spec.md 1.3 and 1.4
- detail: 1.4 requires the two capture actions available "for the current module." 1.3 requires the Gym screen to present "no gym data-entry control, no empty gym list, and no error." KD-16 makes Gym a route and nothing else — no endpoint, no model — so a capture bar there would have nowhere to send anything. The design never says the capture bar is absent on `/gimnasio`, and an implementer reading "per-module capture bar" plus "persistent bottom navigation" could reasonably render it and fail 1.3.
- fixed by: **architect**

### A14 — [MEDIUM] The `in_use` error puts a count where the closed `reason` set has no value
- pass: contradiction
- location: design.md `DELETE /api/categories/{id}` — `"fields": [ { "field": "affected_expenses", "reason": "<count>" } ]`; against the declared closed `reason` set for `validation`
- detail: The contract declares a closed set of `reason` values: `required`, `must_be_positive`, `not_an_integer`, `too_long`, `future_date`, `blank`, `unknown_id`, `duplicate_name`. The `in_use` response smuggles a numeric count through the same field, which is neither in the set nor a reason. KD-17 requires the frontend to map the closed set to Spanish copy; a stringified integer cannot be mapped, and 3.4 needs that count to warn the user how many expenses are affected. The `409` body also already carries `affected_expenses` in the success shape — the error shape should say where the count lives.
- fixed by: **architect**

### A15 — [MEDIUM] `source: "manual"|"voice"` is exposed by the API while 9.5 and 10.4 demand indistinguishability
- pass: contradiction
- location: design.md Data model (`expenses.source`, `journal_entries.source`); expense and journal response objects; `GET /api/export/*.csv` columns; against spec.md 9.5, 10.4
- detail: 10.4 requires a voice journal entry to be "indistinguishable from a typed entry in the journal list," and 9.5 requires a voice expense to behave identically to a manual one. The design stores `source`, returns it in every expense and journal response body, and writes it into both CSV exports. Storing it is defensible for the architect's own diagnostics; returning it to a client that renders lists makes 10.4 one careless component away from failing. The design should state that `source` is never surfaced in any list or detail view — otherwise the frontend implementer, seeing a field in the contract, has no reason not to use it.
- fixed by: **architect**

### A16 — [MEDIUM] Journal fact truncation is silent
- pass: underspecification
- location: design.md KD-10 stage 2 — journal entries "truncated to a **2,000-token budget**"; against spec.md 11.9, 11.3, 11.11
- detail: A question like "¿qué me preocupaba en julio?" over a month of substantial journalling will exceed 2,000 tokens, and the newest-first truncation silently drops the oldest entries in the period — which for a "what was worrying me in July" question are as relevant as any. The answer is then confidently partial with nothing signalling it. The truncation is the right call for latency (the design's reasoning is sound); the gap is that neither the contract's `facts` object nor the UI has any field indicating the context was cut. `facts` carries `journal_entry_count` but not how many entries actually reached the model.
- fixed by: **architect**

### A17 — [MEDIUM] No total resident-memory budget is stated against the measured 6.7 GB
- pass: underspecification
- location: design.md KD-6 ("~2.6 GB resident", `OLLAMA_KEEP_ALIVE=-1`), KD-5 (whisper `small` footprint never stated — only `medium`'s ~1.5 GB), KD-3, KD-4; against spec.md § Measured host hardware
- detail: The design reasons about memory per component and never sums it. With `OLLAMA_KEEP_ALIVE=-1` the 3B model is permanently resident (~2.6 GB), whisper-server holds `small` resident alongside it (~0.5-0.7 GB, a figure the design never gives), plus the Python 3.12 API process, plus SQLite page cache, plus `tailscaled`. That is roughly 3.5-4 GB of the 6.7 GB available, permanently — which fits, and the point is that the design should say it fits rather than leave four separate estimates for a reader to add up. This matters because the documented upgrade paths (whisper `medium` at ~1.5 GB in R9's ladder, Qwen3-4B at ~2.5 GB in KD-6) are each individually reasonable and are not both affordable, and nothing records that.
- fixed by: **architect**

### A18 — [MEDIUM] Constraint 25 has a named mechanism for insights and none for transcription
- pass: coverage
- location: visual-direction.md constraint 25; design.md KD-11 (`elapsed_ms`, `partial_answer`) versus `POST /api/voice/transcribe`
- detail: Constraint 25 applies to "any wait that can exceed roughly two seconds — voice transcription, an insight answer." For insights the design supplies genuine server-side progress. Transcription is a single blocking multipart request with no progress channel; the frontend `audio/` module is described as showing "a visible elapsed indicator" during **recording**, not during transcription. The constraint is satisfiable — a client-side elapsed counter during a 6-10 s wait visibly changes — but the design does not say so, and constraint 25 explicitly rejects "a static spinner that could equally mean 'hung'". The design makes it possible; it does not make it determined.
- fixed by: **architect**

### A19 — [MEDIUM] The LAN origin binds all interfaces and has no authentication
- pass: contradiction
- location: design.md KD-2 ("uvicorn TLS on `0.0.0.0:8443`") versus § Non-endpoint guarantees ("the API binds `127.0.0.1` plus the LAN TLS port", `requirements: 13.6`); spec.md 13.6, A6
- detail: Two descriptions of the same bind, one looser than the other. `0.0.0.0:8443` is every interface on the host, on whatever network the machine is attached to, with no authentication at all (A6 deliberately removed any login, on the reasoning that the private network *is* the access boundary). Behind a home router this satisfies 13.6. The design should state which interface the fallback listener actually binds and whether it is enabled continuously or only when needed, because A6's reasoning depends on an access boundary this listener widens.
- fixed by: **architect**

### A20 — [LOW] `POST /api/expenses/parse` claims four criteria it does not serve
- pass: coverage
- location: design.md `POST /api/expenses/parse` — `requirements: 9.1, 9.2, 9.6, 9.7`
- detail: All four cited criteria begin "WHEN the user **speaks**…" and are already served by `POST /api/voice/transcribe`. The parse endpoint takes typed text. Its stated justification is real (a test seam, and parity between typed and spoken sentences), but as annotated it inflates the coverage of Requirement 9 and, more practically, exposes a natural-language typed-expense path that no criterion asks for and that QA has no basis to test.
- fixed by: **architect**

### A21 — [LOW] `GET /api/insights/summaries` is unmandated and claims 11.15
- pass: coverage
- location: design.md `GET /api/insights/summaries` — `requirements: 11.15, 11.18`
- detail: 11.15 concerns *the most recent* completed summary being readable immediately, which `/latest` delivers on its own. Browsing up to twelve past summaries is a feature no criterion requests. Small and harmless; listed so it is a decision rather than a default.
- fixed by: **architect**

### A22 — [LOW] CSV exports and nightly snapshots exceed what 14.2 and 14.1 ask
- pass: coverage
- location: design.md `GET /api/export/expenses.csv`, `/journal.csv` (`requirements: 14.2`); KD-4 nightly `VACUUM INTO` with 7-day retention
- detail: 14.2 asks for "a file containing all expenses and all journal entries in a format readable without this app" — the JSON dump satisfies it alone, and note that each CSV contains only half the data, so neither individually meets 14.2's "all expenses **and** all journal entries." The snapshots serve no criterion; 14.1 requires only survival across restart. Both are cheap and both are good engineering. They are listed because they are build time nobody asked for.
- fixed by: **human** (keep or cut at Approve Plan)

### A23 — [LOW] "Six tables" precedes a list of seven
- pass: contradiction
- location: design.md § Data model — "Six tables plus two alias tables"
- detail: The list is `categories`, `payment_methods`, `expenses`, `journal_entries`, `summaries`, `insight_jobs`, `meta` — seven, plus the two alias tables.
- fixed by: **architect**

### A24 — [LOW] `resolved_by` cannot express an LLM-sourced category, and duplicates a flag
- pass: terminology drift
- location: design.md `ExpenseDraft.resolved_by` (`"rules"|"none"`) and `needs_category_assist`; against `POST /api/expenses/suggest-category` response `"source": "rules"|"llm"|"none"`
- detail: Two shapes describe the same concept — how a field was resolved — with different vocabularies. `resolved_by.category` has no `"llm"` value even though KD-8 Layer 2 exists precisely to produce one, so a client that merges the suggestion into the draft cannot record its provenance in the draft's own field. Separately, `needs_category_assist` carries the same information as `resolved_by.category == "none"`; two encodings of one fact will diverge.
- fixed by: **architect**

### A25 — [LOW] `/insights` is an English route among Spanish ones
- pass: terminology drift
- location: design.md § Frontend structure — `/finanzas`, `/finanzas/mes`, `/diario`, `/gimnasio`, `/insights`; against spec.md 1.5 and visual-direction.md constraint 23
- detail: Four Spanish route segments and one English. A URL is visible in the phone browser's address bar, and 1.5 covers "any text … shown anywhere in the interface" with "no untranslated or mixed-language strings on any screen." Marginal, and arguably a URL is not interface text — but the drift is free to fix now and the spec itself never names the feature "insights" in Spanish, so PM's vocabulary and the design's diverge.
- fixed by: **architect**

### A26 — [LOW] The two headline throughput figures are unmeasured and sit at the optimistic end
- pass: ambiguity
- location: design.md KD-5 ("roughly 4-6× realtime"), KD-6 ("roughly 8-15 tokens/s"), KD-10 ("~100-200 tok/s" prompt processing); mitigated by R9
- detail: whisper.cpp `small` q5_1 at **6 threads** (KD-5 and R4 both specify 6, not 8) on a Vega-class APU commonly lands nearer 2-4× realtime than 4-6×, putting a 30 s utterance at 10-20 s rather than 6-10 s — which, combined with A9's uncounted client work and A1's contention, is where 8.8 gets tight. Qwen2.5-3B Q4_K_M generation on dual-channel DDR4 is bandwidth-bound at roughly 6-12 tok/s. None of this breaks a criterion; the bounds hold. R9 already flags all of it as unmeasured and specifies logging `elapsed_ms` from day one, and the fallback ladder is pre-chosen, which is the right mitigation. Recorded so the numbers are not quoted downstream as measurements. They are estimates, as R9 says.
- fixed by: **architect** (no action needed beyond R9 — labelled, not silent)

### A27 — [LOW] `summaries.status` includes a value that never appears on the wire
- pass: terminology drift
- location: design.md Data model `summaries.status ('pending'|'generating'|'ready'|'empty'|'failed')` against `GET /api/insights/summaries/latest` (`ready`, `generating`, `empty`, `none`, `failed`)
- detail: `pending` exists in the table and in no response; `none` exists in responses and in no row (it means "no row"). Both are defensible, and neither is documented as such, so an implementer mapping the two sets has to guess whether `pending` is meant to surface.
- fixed by: **architect**

---

## Pass summary

| Pass | Result |
|---|---|
| 1 — Coverage | 0 criteria claimed by nothing. 9 criteria whose claiming element does not deliver (A1-A7, A12, A15). 4 design elements serving no criterion (A20-A22). |
| 2 — Underspecification | 9 findings: A3, A5, A6, A7, A9, A11, A12, A16, A17. |
| 3 — Ambiguity | 1 finding (A26). **No `TODO`, `TBD`, `???`, `XXX`, or `<placeholder>` appears in any of the three artifacts.** Both Open Questions sections read "None" and are honest — the escalated questions really are folded into the criteria. The design's Deferred Decisions section is a model of the form: each deferral names its bounds. |
| 4 — Contradiction | 10 findings: A1, A2, A4, A8, A10, A13, A14, A15, A19, A23. |
| 5 — Terminology drift | 4 findings: A24, A25, A27, and the naming half of A15. Otherwise the vocabulary is remarkably tight — `amount_cop`, `spent_on`, `category`, `payment_method`, `journal_entry`, `summary`, `job` are used consistently across all three artifacts, and the spec's `14.000` convention survives into the contract intact. |
| 6 — Principles alignment | **Not run — no `PRINCIPLES.md` exists in this tree.** No path was given and none was found. No finding is raised: nothing in the three artifacts depends on it. |

### Visual constraints 1-28

Checked for the narrow question the design owes them — does any decision make a constraint *impossible*? **No constraint is made impossible.** Several are actively helped:

- **4, 6** — KD-14's rejection of Recharts/Chart.js in favour of violet-tinted CSS bars with adjacent labels is a direct, correct read of constraints 4 and 6.
- **14** — KD-14 requires an open-licence, self-hosted typeface, and correctly derives the self-hosting requirement from 15.3 and 15.5 rather than from the constraint alone.
- **22, 1-5, 12, 21** — a single `tokens.css` makes them auditable in one file.
- **27** — the four distinct wire states of `/api/insights/summaries/latest` are explicitly designed so the three surfaces constraint 27 demands are distinguishable. This is the clearest example in the design of a visual constraint reaching back into the API shape, which is exactly right.
- **26, 28** — carried by the client-side contract's "Live waiting states".
- **19, 18, 15, 16, 17, 20, 23, 24** — each has a named home.

Two interactions with the latency constraints are recorded above rather than here: constraint 25 against transcription (A18), and constraint 11 against the fifth route (A5).

---

## Scope Statement

**What I read.** Only `/home/david/Proyectos/Autonom-OS/factory/pm/spec.md`, `/home/david/Proyectos/Autonom-OS/factory/pm/visual-direction.md` and `/home/david/Proyectos/Autonom-OS/factory/architect/design.md`, in full. Nothing else exists under `factory/`.

**What I did not check.**

- **Code.** None exists, and it is not my subject. If it did exist, comparing it to the design is the Reviewer's job.
- **Design quality.** I judged coverage and consistency only. Whether SQLite over Postgres, React over Svelte, Ollama over llama.cpp, or Tailscale over any alternative is the *right* choice is not mine — I only checked that the choices do not contradict a criterion. A8 is the one place a technology choice appears, and it appears because the design applies a criterion inconsistently across candidates, not because I disagree with the pick.
- **Product questions.** A6, A15 and A19 in the spec are PM's flagged assumptions and the human's to weigh. I flagged A15's consequence only where the design's own reachability handling meets it (A2).
- **`PRINCIPLES.md`.** Absent from this repository; no path was supplied. Pass 6 could not run. I raise no finding for its absence because nothing in the three artifacts cites it.
- **Hardware measurement.** I reasoned about the design's performance claims against the measured hardware stated in the spec (13 GB RAM / ~6.7 GB free, 8 cores, Vega integrated, no CUDA, 37 GB free disk). I ran no benchmark. A10, A17 and A26 are arithmetic and comparison against known behaviour of these model classes on CPU, not measurements, and R9 already commits the implementer to measuring.

**Determinism.** Finding IDs A1-A27 are assigned by pass order then severity, and are stable for these three files unchanged.

---

**Routing summary for the orchestrator:** 24 findings to **architect**, 2 to **human** (A8, A22), 0 to **pm** alone — though A1 has a pm alternative (narrow 11.17) if the architect judges the whisper/LLM contention unavoidable, and A8 needs pm to record whatever the human accepts.
