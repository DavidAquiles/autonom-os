> **Persisted by the orchestrator, not by the artifact-analyst.**
> The analyst role's `Write` was blocked by the harness for the third time in
> this run, so it returned the complete report as chat text and the
> orchestrator wrote it to this path **unedited** — no summarizing, no
> reordering, no trimming. Treat the body below as the role's own words. The
> analyst is a read-only role and had no write access to this file.
>
> The only change made to the returned text was restoring HTML entities
> (`&lt;` → `<`, `&gt;` → `>`) that the transport had escaped in
> `<select>`, `<placeholder>` and `mkcert <LAN-IP>`. That is a rendering
> repair, not a content edit.
>
> **Pass 1 of this report is preserved at `analysis-pass1.md`** in the same
> directory. It was not overwritten — it is the evidence for the FAIL verdict
> that produced the two architect revisions this pass verifies.

---

# Autonom-OS — Artifact Analysis (second pass)

Re-run after two architect revisions. `spec.md` and `visual-direction.md` are unchanged and were not re-read in full; `design.md` was re-read entirely. Read-only; no artifact was modified.

## Verdict

CONCERNS

Both CRITICALs are genuinely closed. I checked them against the failure pattern I caught the first time — a guarantee re-asserted rather than mechanised — and neither fails it. A1 is now a named component with named rules and a named residual, and the contradicting risk paragraph has been rewritten rather than left standing. A2 reverses the exclusion, freezes the scope, and names what is cached and what is not.

What remains is two HIGH findings, six MEDIUM, two LOW, and the two decisions that were always the human's. None of them is a criterion covered by nothing. Nothing here blocks the gate on its own; three items must be closed before an implementer starts, and I say which.

Nineteen of the twenty-one claimed fixes are real. Two are real but incomplete in a way the fix itself created (B1, B2). The measured benchmarks are faithfully transcribed and the arithmetic built on them checks out.

---

## Verification of claimed dispositions

I verified each claim against the artifact rather than the changelog. "Closed" means I found a mechanism, not a restatement.

### The two CRITICALs, checked hardest

**A1 — 11.17 versus whisper/LLM contention. CLOSED.**

The test is whether the guarantee names a mechanism or repeats itself. It names one, in five places that agree:

- `arbiter/` is a backend module with a stated responsibility — "two priority classes over both sidecars, background preemption, the 60-second quiet period. Every call into `providers/` passes through it."
- The process-topology diagram carries `└ InferenceArbiter ← governs whisper AND Ollama (KD-12)`.
- KD-12 enumerates class membership (interactive: transcription, on-demand questions; background: monthly summary), the preemption rule (background cancelled immediately, re-queued from scratch, interactive does not wait), and the anti-livelock rule (60-second quiet period).
- **R4 has been rewritten.** This is what matters most: the old R4 was the statement that contradicted the guarantee. It now reads "the LLM and whisper never run concurrently by design, which is what makes both 11.17 and 8.8 hold," with a named residual — "the arbiter cannot preempt work already inside Ollama's own request loop instantaneously; expect up to ~1 s of overlap" — absorbed by the 13.6 s measured worst case against a 20 s timeout. The contradiction is gone, not papered over.
- The 11.17 guarantee text now names the exact path it previously omitted: "(2) **Voice** capture does use inference, so the arbiter treats transcription as interactive and cancels any in-flight summary the moment a transcription starts."

Deferred Decisions defers only the cancellation *plumbing* and explicitly fixes the priority rules and quiet period. Rejected alternatives are recorded, including descoping 11.17 — and the note that descoping "would have cost the human a decision to buy a slower answer to a solvable problem" is the right instinct.

This is a mechanism. A1 is closed. It raises one new question it does not answer — see B1 — but that is a gap *in* the new mechanism, not the old defect surviving.

**A2 — 13.2 on a cold open. CLOSED.**

KD-13 reverses "no service worker" explicitly and reproduces the reasoning correctly, including that KD-4 says the machine will be suspended. The scope is frozen rather than gestured at: precaches `index.html`, hashed JS/CSS, the self-hosted font, manifest and icons, generated from the Vite build manifest, cache keyed to build hash, `skipWaiting` + `clients.claim`; `/api/*` is `NetworkOnly` with the reasoning "a stale total is worse than no total in a ledger"; no background sync, no write queue, no offline mutation. The A15/R7 boundary is argued rather than assumed — "caching a static shell so the app can render its own error state stores no user data and queues no writes." Deferred Decisions defers the toolchain and states the scope "may not widen." The client-side contract now says the unreachable state "**renders on a cold open** because the service worker has the shell cached."

One thing I checked and am not raising: iOS's seven-day cap on script-writable storage for unengaged sites would evict the registration, but daily use is the product's premise and R1 already flags the phone OS as unconfirmed. Not a finding.

A2 is closed.

### The remaining claimed fixes

| Finding | Claim | Verified |
|---|---|---|
| A3 | journal half of the summary | **Closed.** KD-10 stage 2: summaries always `domain="both"`, one excerpt per day, **oldest first spread across the month** with the reasoning that newest-first "would make a summary of a month's writing into a summary of its last week," ~300 chars each, plus three `facts` fields. `/latest` restates it. Better than the finding asked for. |
| A4 | `description` overflow | **Closed.** `0..1000` on POST and PATCH, `too_long` added to the error reasons, draft trimmed on a word boundary with `description_truncated`, full text always in `transcript`. Sizing justified against 32 s of Colombian Spanish at 500-800 chars. |
| A5 | insights entry point | **Closed.** `/finanzas/analisis` inside Finances, with a **second entry from Journal to the same route** because "a journal question discoverable only from Finances is a question nobody asks" (11.9). Navigation stays three. |
| A6 | unresolvable period | **Closed.** Two-pass router: a temporal-cue detector plus the resolver; cue present and unresolved → `period_unrecognised` terminal state; **no cue at all** → current month with `period_assumed: true` so the answer labels itself. Code added to the closed set, to `facts`, and to the job endpoint's terminal codes. The rationale shows the finding was understood, not pattern-matched. |
| A7 | LAN fallback reachability | **Closed** on all three sub-points: second home-screen icon plus a link (a navigation, not a retry) from the unreachable state; `mkcert <LAN-IP> autonomos.local` against a DHCP reservation because "mDNS resolution of `.local` from Android Chrome is unreliable"; microphone granted on **both** origins at setup "precisely so that 15.5's scenario does not begin with a permission prompt." One dependency it surfaces rather than hides — see B7. |
| A9 | 8.8 end-to-end budget | **Closed.** A segment table (decode+resample ≤3 s, upload ≤4 s, sidecar ≤20 s, response+render ≤1 s = 28 s worst case), a **client-side wall clock** firing `transcription_timeout` at 28 s "regardless of what the server is doing," a 30 s client hard stop and a 32 s server cap. The client owning the 8.8 clock is the correct assignment. |
| A10 | latency arithmetic | **Closed by measurement.** See § Benchmarks below; every figure recomputes correctly. Budgets tightened 2,000→1,200 context and 320→220 answer tokens, with the 1,200 marked load-bearing and "must not be raised." |
| A11 | `busy`, 11.12 clock | **Closed.** `409 busy` documented on the only endpoint that emits it, `queued` explained as a sub-second window, and 11.12 measured **from `created_at`** with the reasoning that measuring from generation start "would let the user wait indefinitely while the criterion still passed." `LLM_TIMEOUT_S=110` leaves 10 s. |
| A13 | capture bar on Gym | **Closed** in three places (KD-16, Frontend structure, client-side contract), with the argument that a capture button on Gym "would be a data-entry control, which 1.3 forbids in as many words." |
| A14 | count in `reason` | **Closed.** A `details` object added to the envelope, `in_use` carries `{ "affected_expenses": int }`, and KD-17 states the rule: "A count, limit or identifier goes here — never inside `reason`." |
| A15 | `source` exposure | **Closed.** Removed from both response bodies and both CSVs; request-only; retained in the archival JSON export only. The reasoning — "a field present in the contract is a field a component will eventually display; the fix is to not send it" — is the right generalisation. |
| A16 | silent truncation | **Closed** at the contract level: `journal_entries_considered`, `journal_entries_used`, `journal_truncated`. One softness remains — see B9. |
| A17 | memory budget | **Closed.** A summed table against the corrected denominator, and the sharper consequence drawn: the two upgrade rungs "are each individually affordable within ~1.9 GB of headroom and are **clearly not both**." |
| A18 | constraint 25 for transcription | **Closed.** A phase-plus-elapsed indicator (preparing / uploading / transcribing, seconds counting), justified by the absence of a server progress channel. Now also in the client-side obligations list, claiming 8.8. |
| A19 | bind address | **Closed.** `${LAN_BIND_ADDR}`, "never `0.0.0.0`," runs continuously with the reason ("a listener that must be started by hand during an outage is not a mechanism"), unauthenticated by A6's choice, disabled by config on untrusted networks, README obligation stated, `0.0.0.0` added to rejected options. |
| A20 | `/parse` false claim | **Closed** correctly — `requirements: none` with the rationale, plus a new prohibition: "**The frontend must not expose a typed natural-language expense path**." Removing the claim rather than the endpoint is the right call. |
| A21 | summaries-list endpoint | **Closed by removal.** The endpoint is gone; 11.18 remains claimed by `/latest`; I found no dangling reference to it. |
| A23 | table count | **Closed** — "Seven tables plus two alias tables." |
| A24 | `resolved_by` vocabulary | **Closed.** One `"rules"\|"llm"\|"none"` vocabulary shared with `/suggest-category`; `needs_category_assist` deleted; "there is no separate flag saying the same thing twice." |
| A25 | English route | **Closed** — `/finanzas/analisis`, all segments Spanish, with the reasoning that a URL is visible in the address bar and is "awkward to change once bookmarked." |
| A27 | phantom `pending` | **Closed.** Status set is now `('generating'\|'ready'\|'empty'\|'failed')`, with the explanation that a month with no row *is* pending and that `none` is the only wire state without a row. |
| A12 | 11.1 / 11.7 residual | **Correctly downgraded.** KD-10 now has a section stating plainly that both are prompt-enforced with no guard, naming the exact failure it cannot catch (*"deberías reducir tus gastos en restaurantes"*), identifying this as the one exception to KD-17, and fixing the response if it drifts (the model ladder, not a new guard, because a classifier "would cost a second inference pass inside the same 120 s budget"). This is what I asked for. It stays a residual the human should know about, not a defect. |
| A26 | unmeasured figures | **Superseded by measurement.** Better than stated-as-residual. R9 is rewritten as RESOLVED BY MEASUREMENT with the honest remainder: single-run benchmarks, not p95 under contention, so log `elapsed_ms` from day one. |
| A8 | Tailscale vs 12.4 / 15.3 | **Still open, correctly.** Now R11, stated neutrally, with three alternatives costed (Headscale needs a VPS or solves nothing; plain WireGuard needs a forwarded port that 13.6 forbids; home-only removes 13.4) and the honest conclusion that no option gives away-from-home access with no public exposure and no third party. Carried to the gate. |
| A22 | CSV / snapshots | **Still open, correctly.** Both CSV endpoints now carry `requirements: none` with "**neither satisfies 14.2 alone**," and both items appear under "For the human at Approve Plan." |

---

## Benchmarks — verification against your measurements

The design transcribes your figures exactly: whisper 4.0 s → 5,652 ms encode / 6.4 s total; 11.0 s → 5,776 ms / 7.0 s; 33.0 s → 11,089 ms (2 × 5,544) / 13.6 s; RSS 476 MB. Ollama 113-tok → 35.8 / 13.9 tok/s / 6.9 s; 1,915-tok → 25.7 / 10.0 tok/s / 82.1 s. Denominator 5.3 GiB from `total="13.1 GiB" available="5.3 GiB"`. No number is inflated, rounded favourably, or quietly widened.

**The derived tables recompute correctly.** I checked all three rows of KD-6's rebuilt table against the measured rates:

- finance-only, ~500-token prompt: 500 ÷ 36 = 13.9 s to 500 ÷ 26 = 19.2 s → design says 14-19 s ✓; 220 ÷ 14 = 15.7 s to 220 ÷ 10 = 22 s → says 16-22 s ✓; total 30-41 s ✓
- journal, ~1,400-token prompt: 38.9-53.8 s → says 39-54 s ✓; total 55-76 s ✓
- summary, ~1,800-token prompt: 50.0-69.2 s → says 50-69 s ✓; 320 ÷ 14 = 22.9 to 320 ÷ 10 = 32 → says 23-32 s ✓; total 73-101 s ✓

Your own 1,915-token run is internally consistent with this: 1,915 ÷ 25.7 = 74.5 s of prompt, leaving 7.6 s of the 82.1 s wall, ≈ 76 generated tokens at 10.0 tok/s.

**One thing the design does not draw out.** Your two data points show prompt-eval throughput *degrading with prompt length* — 35.8 tok/s at 113 tokens, 25.7 tok/s at 1,915. The design applies the flat band 26-36 tok/s to all three workloads. For the two long-prompt cases the applicable rate is the slow end, so the realistic figures are the **tops** of the stated ranges (journal ≈ 76 s, summary ≈ 101 s), not their midpoints. The journal question at 76 s against a 110 s timeout is comfortable. The summary at 101 s against the same 110 s is not — that is B3.

**The `base` caveat is handled correctly and I am not flagging it.** You asked me to check whether the design leans on that number for anything beyond a labelled, unvalidated fallback rung. It does not. KD-5 states the speed win is "real and language-independent," the quality "**unvalidated for Spanish**," names the reason ("the only sample benchmarked was English audio forced through `-l es`, which produced garbage from both models and is therefore no evidence at all about Spanish accuracy"), keeps `small` as the default, and gates the rung: "someone must transcribe a real Spanish sample containing an amount and a payment method and confirm 9.6 and 9.7 still hold." R9 repeats it and "Open for verification" repeats it a third time. That is exactly the disposition you described, restated three times so it cannot be lost. Nothing downstream depends on it.

The `--no-translate` correction is also right: whisper.cpp translates only on `--translate`, so `-l es` alone satisfies 8.7.

---

## The ~6.4 s floor — does any criterion become unsatisfiable?

**No. None.** The floor is a product property, not a defect, and the design is honest about it: "For short input the effective throughput is *below* 1× realtime. No UI copy, animation, or affordance may imply otherwise (constraint 28)."

- **2.8 is untouched.** It counts *interactions*, not seconds — "no more than four interactions (taps/entries) beyond typing the amount." A 6.4 s wait costs zero taps. PM wrote the criterion in the one unit that latency cannot affect, which turns out to have been fortunate. (2.8 has a different problem, unrelated to latency — B4.)
- **8.8 holds with margin.** Budgeted worst case 28 s against a 30 s criterion, and that 28 s sums every segment *maximum* including the 20 s sidecar timeout rather than the 13.6 s measured worst case. Realistic worst case is ~21.6 s. The client-side clock delivers an explicit failure at 28 s, which is inside 30 s, satisfying 8.8's "explicit failure" branch rather than relying on the happy path.
- **Constraint 25 is satisfied and is now universal rather than conditional.** Every transcription exceeds two seconds by physics; the phase-plus-elapsed indicator covers it.
- **Constraint 27** is unaffected; `/latest`'s five wire states still map to three distinguishable surfaces plus a failure.
- **Constraint 28** is strengthened — KD-5 turns it into an explicit prohibition on the implementers.
- **Constraint 26 is the one that moved**, and the brief has not caught up. See B6.

The thing worth putting in front of the human is not a criterion failure. It is that a 6.4 s floor on a three-second sentence means voice capture is, in wall-clock terms, **slower than manual entry** for a simple expense — and that fact did not exist when PM wrote Requirement 8. Voice is still justified on its actual merits (one-handed, walking, not looking at the screen, which is what 8's user story says), and the design never claims otherwise. But it is new information about the app's most-used path and the human should accept it knowingly rather than discover it. That is B8.

---

## Coverage

95 active criteria (12.3 retired at Kickoff, excluded from the denominator).

| Criterion | Covered by | Notes |
|---|---|---|
| 1.1 | Client-side contract — App shell; Frontend structure | **now verified** — insights is `/finanzas/analisis`, not a fourth destination (A5) |
| 1.2 | Client-side contract — App shell | verified |
| 1.3 | Gym placeholder; KD-16 | **now verified** — no capture bar on `/gimnasio` (A13) |
| 1.4 | App shell; Frontend structure | **now verified** — capture bar is Finances-and-Journal only |
| 1.5 | Spanish everywhere; KD-17; Frontend structure | verified; routes now all Spanish (A25); LLM text is the one stated exception |
| 2.1 | POST /api/expenses | verified |
| 2.2 | POST /api/expenses | verified |
| 2.3 | POST /api/expenses | verified |
| 2.4 | POST /api/expenses; Amount input; KD-8 Layer 1 | verified |
| 2.5 | Client-side — Amount input and display | verified |
| 2.6 | POST /api/expenses (`description` 0..1000) | **now verified** (A4) |
| 2.7 | POST /api/expenses (`future_date`) | verified |
| 2.8 | Client-side — Four-interaction capture budget | partial — asserted, control pattern unrecorded (B4) |
| 3.1 | GET /api/categories; payment-methods; Seed data | verified |
| 3.2 | POST /api/categories | verified |
| 3.3 | PATCH /api/categories/{id} | verified |
| 3.4 | DELETE /api/categories/{id}; summary/month; Data model | **now verified** — count moved to `details` (A14) |
| 3.5 | POST /api/expenses; NOT NULL FKs | verified |
| 4.1 | GET /api/expenses; GET /api/summary/day | verified |
| 4.2 | GET /api/summary/month | verified |
| 4.3 | GET /api/summary/month (largest-remainder) | verified — stricter than the criterion |
| 4.4 | GET /api/summary/month | verified |
| 4.5 | GET /api/summary/month (`is_empty`) | verified |
| 4.6 | PATCH/DELETE expenses; summary endpoints; KD-13 | verified |
| 4.7 | GET /api/summary/month (`month` param) | verified |
| 4.8 | summary endpoints; `clock/`; Time | verified |
| 5.1 | GET/PATCH /api/expenses/{id} | verified |
| 5.2 | DELETE endpoints; Destructive confirmation | verified |
| 5.3 | PATCH /api/journal/{id} | verified |
| 6.1 | POST /api/journal | verified |
| 6.2 | POST /api/journal (`blank`) | verified |
| 6.3 | POST /api/journal; Data model | verified |
| 6.4 | POST /api/journal (byte-exact) | verified |
| 6.5 | POST /api/journal (`no maximum`) | verified |
| 6.6 | POST /api/journal | verified |
| 6.7 | POST /api/journal | verified |
| 7.1 | GET /api/journal | verified |
| 7.2 | GET /api/journal (`date`) | verified |
| 7.3 | GET /api/journal | verified |
| 8.1 | Client-side — Voice capture UI | verified |
| 8.2 | POST /api/voice/transcribe | verified |
| 8.3 | POST /api/voice/transcribe; Voice capture UI | verified |
| 8.4 | transcribe errors; GET /api/status; R5; KD-5 clock | verified |
| 8.5 | Client-side — Voice capture UI | verified |
| 8.6 | transcribe; Explicit confirmation; KD-8 | verified — structural |
| 8.7 | KD-5 (`-l es`, translate off by default) | **now verified** — the non-existent flag corrected |
| 8.8 | KD-5 end-to-end budget table + 28 s client clock; Live waiting states | **now verified** (A9) |
| 8.9 | transcribe; Voice capture UI (`AbortController`) | verified |
| 9.1 | POST /api/voice/transcribe (`ExpenseDraft`) | **now verified** — 1000-char description (A4) |
| 9.2 | transcribe; /suggest-category; KD-8 | verified |
| 9.3 | /suggest-category; alias tables | verified — by construction |
| 9.4 | Client-side — Edited values win | verified |
| 9.5 | POST /api/expenses (`source` request-only) | **now verified** (A15) |
| 9.6 | transcribe; KD-8 Layer 1 | verified |
| 9.7 | transcribe; `payment_method_aliases` | verified |
| 10.1 | POST /api/voice/transcribe | verified |
| 10.2 | transcribe; KD-9 | verified — absence of a code path |
| 10.3 | Client-side — Edited values win | verified |
| 10.4 | POST /api/journal (`source` request-only) | **now verified** (A15) |
| 11.1 | GET job endpoint; KD-10 | covered, **prompt-enforced and stated as such** (A12) |
| 11.2 | KD-10 NumericGuard | verified |
| 11.3 | KD-10 insufficiency pre-check | verified |
| 11.4 | GET /api/status | partial — contention during a running question is unspecified (B1) |
| 11.5 | POST/GET questions; Live waiting states | verified |
| 11.6 | POST/DELETE questions | verified |
| 11.7 | GET job; /latest; KD-10 | covered, **prompt-enforced and stated as such** (A12) |
| 11.8 | POST/GET questions; KD-10 router | **now verified** (A6) |
| 11.9 | POST/GET questions; FactBuilder; Journal entry point | **now verified** (A6, A16, A5) |
| 11.10 | transcribe (`context="question"`); POST questions | verified |
| 11.11 | GET job (`period_unrecognised`, `unverifiable_figures`) | **now verified** (A6) |
| 11.12 | KD-11 (`202`, clock from `created_at`); KD-6 budgets | partial — intra-interactive arithmetic (B1) |
| 11.13 | DELETE /api/insights/questions/{job_id} | verified |
| 11.14 | KD-12 scheduler; KD-10 stage 2 (`domain="both"`) | partial — no recovery for `failed`/orphaned rows (B2) |
| 11.15 | GET /latest ("reads a stored row; never triggers generation") | verified |
| 11.16 | GET /latest (`none`, `empty`) | verified |
| 11.17 | Non-endpoint guarantee; KD-12 InferenceArbiter; R4 | **now verified — was CRITICAL (A1)** |
| 11.18 | GET /latest (`period_label`, `generated_at`) | verified |
| 12.1 | Zero cost; KD-1 | verified |
| 12.2 | Zero cost; KD-1 | verified |
| 12.4 | Zero cost; R11 | contested — the human's call (A8) |
| 13.1 | Browser-only delivery; KD-1 | verified |
| 13.2 | GET /api/health; Reachability; **KD-13 service worker** | **now verified — was CRITICAL (A2)** |
| 13.3 | health; Reachability; persisted `insight_jobs` | verified |
| 13.4 | Away-from-home parity; KD-1 | verified |
| 13.5 | Client-side — Reachability | verified |
| 13.6 | Never publicly reachable; KD-2 (`LAN_BIND_ADDR`) | **now verified** (A19) |
| 13.7 | One-time setup only; KD-2 | partial — rests on a reading PM has not confirmed (B7) |
| 14.1 | Durability; KD-4 | verified |
| 14.2 | GET /api/export | verified — CSVs correctly disclaimed |
| 14.3 | No automatic deletion | verified |
| 15.1 | transcribe notes; All processing local | verified |
| 15.2 | All processing local | verified |
| 15.3 | All processing local; KD-14; R11 | contested — the human's call (A8) |
| 15.4 | All processing local | verified |
| 15.5 | KD-2 fallback origin (icon, IP-SAN cert, mic on both origins); R2 | **now verified** (A7) |

**Coverage: 95/95 criteria claimed (100%) · 0 uncovered · verified coverage 90/95 (95%, up from 91%) · 5 criteria partially delivered (was 9) · 0 design elements carrying an unearned `requirements:` line.**

Both elements that previously carried false claims now carry `requirements: none` with a rationale, which is the honest disposition; the one unmandated endpoint was cut. On the reverse direction, only the nightly snapshots (KD-4) and the provider abstraction (KD-7) remain unmandated, and both are bought by named risks or routed to the human.

---

## Findings

Ten findings, two carried forward. Findings first raised in this pass are B-numbered; A-numbers are preserved so you can match them to the first report.

### B1 — [HIGH] The arbiter has no rule for two *interactive* jobs
- pass: underspecification
- location: design.md KD-12 (two priority classes); `arbiter/` module row; R4 ("the LLM and whisper never run concurrently by design"); KD-11 (11.12's clock from `created_at`, `LLM_TIMEOUT_S=110`, "ten seconds for arbitration"); against spec.md 11.4, 11.12
- detail: The arbiter's stated rules govern **interactive versus background** only. Interactive contains three things — voice transcription, on-demand questions, and `/suggest-category` — and nothing says what happens when two of them want inference at once. Three mutually exclusive answers are available and the design picks none:
  1. *They run concurrently* — contradicts R4's "never run concurrently by design," which is the sentence that closed A1.
  2. *The later one waits* — then a voice capture starting during a running question waits up to 110 s, and the client's 28 s clock fires a `transcription_timeout` for a transcription that was never attempted. 11.4 requires that while insights is "still loading," capture "SHALL continue to work normally." Manual capture is untouched; voice capture is not.
  3. *The later one preempts* — throws away a question the user is waiting on, with no rule for what he sees.

  There is also arithmetic. If interactive work serializes, a question arriving during a transcription waits 6.4-13.6 s (up to the 20 s sidecar timeout) and then gets `LLM_TIMEOUT_S=110`. Measured from `created_at` as KD-11 requires, that is 116-130 s against 11.12's 120 s. KD-11's ten seconds of slack for "arbitration and the response" does not cover a transcription.

  Realistically the exposure is small — one user does one thing at a time, and A22 says so. But Deferred Decisions states that "the priority rules and the 60-second quiet period are fixed; the plumbing is not," and this priority rule is not fixed. Two implementers cannot both guess the same answer, and the frontend's timeout handling depends on which one is chosen.
- fixed by: **architect**
- blocks the gate: **no.** Must be closed before the backend lane starts.

### B2 — [HIGH] A `failed` or orphaned `generating` summary is never regenerated
- pass: contradiction
- location: design.md KD-12 — each tick "finds any without a `summaries` row, and enqueues generation"; against the `summaries.status` set `('generating'|'ready'|'empty'|'failed')`, `GET /api/insights/summaries/latest`, spec.md 11.14, visual-direction.md constraint 27
- detail: The catch-up scan keys on **row absence**. A month whose summary generation failed has a row with `status='failed'`, so the scan will never pick it up again, and that month never gets the summary 11.14 requires. The same is true of a row stuck at `generating`: the arbiter's cancel path re-queues in process, but a process restart or crash mid-generation leaves the row at `generating` with nothing to re-queue it — and `/latest` then reports `status: "generating"` indefinitely, which constraint 27 requires to be distinguishable as "currently being produced." Reporting work in progress that is not in progress is worse than reporting failure.

  This existed before the revision, but the revision raised the exposure materially: summaries are now cancelled and restarted routinely by design, so mid-flight interruption is the normal case rather than the rare one, and B3's tight timeout makes `failed` a more likely terminal state than it was.
- fixed by: **architect**
- blocks the gate: **no.** Must be closed before the backend lane starts.

### B3 — [MEDIUM] One `LLM_TIMEOUT_S` for two workloads, and the summary sits 9 s under it
- pass: contradiction
- location: design.md KD-7 (`LLM_TIMEOUT_S=110`, single value); KD-6 ("All three fit inside 11.12's 120 s and inside `LLM_TIMEOUT_S=110`", summary modelled at 73-101 s) and KD-6's own "**The 120-second bound is a journal-question bound, not a general one**"
- detail: KD-6 argues correctly that the 120 s bound belongs to questions, then configures a single timeout that applies it to summaries too. The monthly summary's modelled worst case is 101 s against a 110 s cutoff — 8% margin, on single-run benchmarks that R9 itself says are "not a p95 under contention." And per your measurements the applicable prompt-eval rate for an 1,800-token prompt is the *slow* end of the 26-36 tok/s band, not its middle, so 101 s is the realistic figure rather than a pessimistic one.

  The summary has **no deadline in the spec at all** — 11.15 is served by the *previous* month's stored row regardless of how long the current one takes, and 11.17 is now structurally guaranteed by the arbiter. So the tight timeout buys nothing and costs a `failed` row, which B2 then makes permanent.
- fixed by: **architect**
- blocks the gate: no.

### B4 — [MEDIUM] 2.8's four-interaction budget is asserted, not designed
- pass: underspecification
- location: design.md § Client-side contract — "a complete expense saves in ≤4 taps beyond typing the amount (category, payment method, save — date defaults to today)"; against spec.md 2.8, Seed data (10 categories, 6 payment methods), visual-direction.md constraints 7 and 10
- detail: The budget is stated as an arithmetic claim and nothing records the control pattern that makes it reachable. From the default screen the sequence is: open the manual form (1), type the amount, choose a category (2), choose a payment method (3), save (4) — exactly 4, with zero slack. That holds only if category and payment method are each **one** interaction. A native `<select>`, a modal picker, or a bottom sheet is two (open, choose), which puts the total at 6 and fails a pass/fail criterion.

  One-tap selection means inline chips, which then has to fit ten seeded categories and six payment methods into a 390 px viewport with 44 × 44 px targets and no horizontal scrolling. That is achievable — wrapping chip rows — but it is a real constraint on the form's design that no artifact records, and it is the kind of thing a frontend implementer discovers after building the form the obvious way.

  I did not raise this in the first pass and am raising it now; it is pre-existing rather than a regression.
- fixed by: **architect**
- blocks the gate: **no.** Must be closed before the frontend lane builds the expense form.

### B5 — [MEDIUM] The spec's "~6.7 GB available (fact, not estimate)" is contradicted by the measurement the design now uses
- pass: contradiction
- location: spec.md § Decisions taken at the Kickoff gate — "**Measured host hardware** (fact, not estimate): 13 GB RAM (~6.7 GB available)"; against design.md KD-6 — "The denominator is 5.3 GiB, not 6.7 GB", KD-4 ("~200 MB of the 5.3 GiB")
- detail: You asked whether this needs a PM correction or is fine as a design-side footnote. **It needs a PM correction, and it does not block the gate.**

  The design's handling is correct engineering: it names the source (Ollama's own startup log on this host), explains the choice ("budget against the smaller one"), and draws a sharper consequence than the optimistic number would have allowed — that whisper `medium` and Qwen3-4B are individually affordable and clearly not both. Nothing in the design needs changing.

  The problem is the spec's label. Available RAM is a moment-in-time reading that moves with the page cache and the desktop session; both 6.7 and 5.3 can be true hours apart. Presenting it as "fact, not estimate" freezes a fluctuating quantity, and the spec is what the human approves and QA reads. Left as it stands, a downstream reader sizing against 6.7 GB concludes that ~2.9 GB of headroom exists and that *both* upgrade rungs are affordable — which is precisely the wrong conclusion, and the one the design just spent a paragraph ruling out.
- fixed by: **pm** — restate as a measured range with the reading's date and the note that available RAM is a moment-in-time figure, and name 5.3 GiB as the planning denominator so the design and the spec agree.
- blocks the gate: no.

### B6 — [MEDIUM] Visual constraint 26 names only insight generation, and transcription now routinely crosses ten seconds
- pass: coverage
- location: visual-direction.md constraint 26 — "Any wait that can exceed roughly ten seconds — insight generation — presents a visible way to cancel or leave, and says in plain language that the work is happening on the user's own computer"; against design.md KD-5 (13.6 s measured sidecar, ~21 s realistic end-to-end)
- detail: When the brief was written, transcription was assumed to be a 6-10 s wait, so constraint 26's worked example names insight generation alone. The measurements move it: a two-window clip is 13.6 s in the sidecar and up to ~21 s end-to-end, so **transcription is now the app's most frequent wait over ten seconds** — many times a day, against an insight question that might be asked weekly.

  The design covers it anyway; its client-side contract states the rule generically ("waits over ~10 s offer cancel and say the work is happening on the user's own computer") and 8.9 already provides abandon-to-manual. So there is no build gap. The gap is in **enforcement**: the brief says Reviewer and QA hold the built UI to the Design Constraints, and constraint 26 as written does not reach transcription. A transcription wait shipped without a cancel affordance or the "on your own computer" explanation would pass a literal reading of the constraint it should fail.
- fixed by: **pm** — widen constraint 26's example to name voice transcription alongside insight generation.
- blocks the gate: no.

### B7 — [MEDIUM] KD-2's reading of 13.7 needs PM's explicit confirmation
- pass: ambiguity
- location: design.md KD-2 — "13.7 governs *routine daily use* … Switching origins is a recovery action during an outage, not routine use. If PM reads 13.7 as covering outage recovery too, this design fails it and there is no mechanism that would not"; § Non-endpoint guarantees — One-time setup only; against spec.md 13.7
- detail: This descends from A7, which is otherwise closed. The architect resolved the mechanism and then did the right thing with the residual: surfaced the interpretation it depends on instead of assuming it. I am carrying it forward only because an interpretation stated for PM to object to needs PM to actually respond, or it becomes an assumption by silence — and this one decides whether 13.7 passes or is unsatisfiable.

  The architect's claim that no alternative mechanism exists is correct: origins cannot fail over transparently, so if 13.7 covers outage recovery, no design satisfies it and the criterion has to change. That makes this a spec question with a one-line answer, not a design problem.
- fixed by: **pm** (confirm the reading, or narrow 13.7's wording to say it governs routine use on the primary origin)
- blocks the gate: no — but it is a one-line confirmation that should happen at the gate rather than after it.

### B8 — [MEDIUM] The mandatory ~6.4 s voice floor is a product property the human has not yet seen
- pass: coverage
- location: design.md KD-5 — "**Every transcription has a hard ~6.4 s floor** … For short input the effective throughput is *below* 1× realtime"; against spec.md § Problem Statement, Requirement 8's user story
- detail: Not a defect, and no criterion fails. I am raising it because it is new information about the app's headline feature that did not exist when the spec was written, and the Approve Plan gate is where the human sees it.

  Whisper pads every clip to a full 30-second window, so *"gasté 14 mil en Uber con la tarjeta"* — a three-second sentence and the canonical example in 9.1 — costs the same ~6.4 s as a 28-second one. Against a manual entry of roughly 5-8 seconds of uninterrupted tapping, **voice is not the faster path for a simple expense**; it is the hands-free one. That is still a good reason to have it — Requirement 8's story is "recording costs nothing while I am walking down the street," and one-handed capture without looking at the screen is exactly that — but it is a different reason than "it is quicker," and the spec's Problem Statement frames the whole product around capture friction.

  The design is honest about this throughout and forbids any copy implying otherwise. Nothing needs fixing. The human needs to have seen it.
- fixed by: **human** (acknowledge at Approve Plan; no artifact change required)
- blocks the gate: no — it *is* gate material.

### B9 — [LOW] `journal_truncated` is a capability, not an obligation
- pass: underspecification
- location: design.md KD-10 stage 2 — "the client **can** surface the two counts"; against the § Client-side contract obligations list, which omits it entirely
- detail: A16 is otherwise closed — the three machine fields exist and the prompt is required to make the text admit partiality. But the design's own words are that "a confidently partial answer that does not admit it is partial is the failure mode here," and the only non-prompt mechanism against that failure is described as something the client *can* do. The client-side contract section is explicitly "frontend-only obligations … listed here so requirement coverage is computable," and this is not in it. Deferred Decisions defers "*how* `journal_truncated` is surfaced," which implies *that* it is surfaced is settled — so the two sections disagree about whether it is required.
- fixed by: **architect** (one line in the client-side contract)
- blocks the gate: no.

### B10 — [LOW] GiB and GB are mixed in the resident-memory subtraction
- pass: ambiguity
- location: design.md KD-6 — "**~3.4 GB of 5.3 GiB, leaving ~1.9 GB**"
- detail: 5.3 GiB is 5.69 GB, so 5.69 − 3.41 gives 2.28 GB, not 1.9. The stated 1.9 comes from subtracting in GB from a GiB figure. The error runs in the safe direction — it *understates* headroom by ~0.4 GB — and the conclusion (one upgrade rung, not both) holds under either reading, which is why this is LOW rather than higher. It is worth fixing only because this table is the number downstream will plan the model ladder against, and a budget table that mixes units invites someone to re-derive it and reach a different answer.

  The figure is also correct under the reading that 5.3 GiB is a *pre-load* measurement — which it is, being an Ollama startup log — and saying so would make the table self-checking.
- fixed by: **architect**
- blocks the gate: no.

### Carried forward, unchanged in status

**A8 — [HIGH] Tailscale against a literal reading of 12.4 and 15.3. Fixed by: human. Does not block the gate; it *is* the gate.** Now R11, and materially better than a finding requires: neutral framing, three alternatives costed, and the honest bottom line that "there is no known option that provides away-from-home access with no public exposure and no third-party coordination. The choice is between accepting a third party for transit, and giving up 13.4." The architect has done everything an architect can do here. The remaining decision is the human's and only his, because reversing it means reversing a Kickoff decision.

**A22 — [LOW] CSV exports and nightly snapshots. Fixed by: human. Does not block the gate.** Both now carry `requirements: none`, the CSVs explicitly disclaim satisfying 14.2 alone, and both appear under "For the human at Approve Plan" as keep-or-cut.

---

## Pass summary

| Pass | Result |
|---|---|
| 1 — Coverage | 0 criteria claimed by nothing. 5 partially delivered, down from 9 (2.8, 11.4, 11.12, 11.14, 13.7). Both previously-false `requirements:` lines are now honest `requirements: none`. |
| 2 — Underspecification | 4 findings: B1, B4, B7, B9. |
| 3 — Ambiguity | 2 findings: B7, B10. No `TODO`, `TBD`, `???`, `XXX` or `<placeholder>` anywhere in the revised design. |
| 4 — Contradiction | 3 findings: B2, B3, B5. The two contradictions that made the first pass a FAIL (A1's R4 conflict, A2's service-worker exclusion) are both resolved at the source rather than papered over. |
| 5 — Terminology drift | **None.** All four drift findings closed: one provenance vocabulary (A24), Spanish routes throughout (A25), the phantom `pending` status removed (A27), the table count corrected (A23). `source`, `resolved_by`, `period_*`, `journal_*` are now used identically wherever they appear. |
| 6 — Principles alignment | **Not run — no `PRINCIPLES.md` exists in this tree.** No path was supplied and none was found. No finding raised; nothing in the artifacts cites it. |

**Visual constraints 1-28:** re-checked. None is made impossible; two are now better served than before (25 by the phase-plus-elapsed indicator, 28 by KD-5's explicit prohibition). Constraint 26 is the only one whose *text* has fallen behind the measurements — B6.

---

## Scope Statement

**What I read this pass.** `design.md` in full, twice through the changed sections. `spec.md` and `visual-direction.md` were not re-read in full, as you said they are unchanged; I re-read the specific passages a finding turned on — 2.8, 8.8, 11.4, 11.12, 11.14, 13.7, 15.5, the Kickoff hardware paragraph, and constraints 7, 10, 25-28 — from my first-pass reading of those files.

**What I did not check.**

- **Code.** None exists and it is not my subject.
- **The benchmarks themselves.** I verified that the design transcribes your figures without distortion and that every number derived from them recomputes correctly. I did not re-run anything and cannot speak to how the measurements were taken, beyond noting where the design generalises two data points into a flat band (§ Benchmarks) and that R9 correctly labels them single-run rather than p95.
- **Design quality.** Coverage and consistency only. Whether the InferenceArbiter is the *best* way to satisfy 11.17 is not mine; whether it satisfies it, and whether an implementer can build it from what is written, is.
- **`PRINCIPLES.md`.** Absent. Pass 6 could not run either time.

**Determinism.** A-numbers are preserved from the first report so dispositions can be matched. Findings first raised in this pass are B1-B10, ordered by severity then pass. B4 is a pre-existing issue I missed in the first pass and have labelled as newly raised rather than presented as a regression.

---

## What to hand the human

Three things go to Approve Plan as decisions: **A8** (Tailscale — the only one that could change the shape of the product), **A22** (CSV and snapshots — keep or cut), and **B8** (the 6.4 s voice floor — acknowledge). **B5**, **B6** and **B7** are three short PM edits that can be made before or at the gate and change no design.

Three things must be closed before implementers start, none of which blocks the gate: **B1** and **B2** before the backend lane, **B4** before the frontend builds the expense form.
