# Review — Autonom-OS (pass 2)

Re-review of the three blocking findings from pass 1, against the code rather
than the claims. `state.verification` read: all gates pass, `test_integrity`
201 tests / 495 assertions (up from 179 / 437), backend 247 (was 231), frontend
35. `factory/architect/design.md` re-read at 1,518 lines — KD-2 (`:61-154`), the
`GET /api/health` entry (`:958-964`) and the client-side contract's *Arming and
offering the other origin* (`:1194-1209`) are new and are what F2 is now
measured against.

**All three are closed.** Each was checked by reading the mechanism, not the
note; where a fix could have been faked by a passing test, I checked the
quantity the test asserts.

## Findings

### F1 — [closed] The answer deadline now bounds every attempt
Verified, not re-raised. `_generate_answer` takes `deadline: float` — an
absolute epoch time — and the only caller passes the absolute value
(`backend/autonomos/insights/runner.py:138`, signature at `:153-160`). The
budget check is **inside** the `while True:` loop and above every provider call
(`:192-211`): `remaining_s = deadline - time.time()` then
`if remaining_s < settings.llm_min_start_budget_s: … finish_failed(…, "llm_timeout"); return`.
The provider is handed `timeout_s=remaining_s` (`:217`) — a duration derived
fresh each pass — and the old `budget_s = budget_s - 1.0` is gone; the retry now
falls through to the top of the loop with only a `strict = True` (`:251-254`).
I re-ran pass 1's arithmetic: a first generation finishing at t≈80 of a 110 s
deadline leaves `remaining_s = 30`, which is not `< 30`, so the retry starts and
is capped at 30 s, terminating by t=110. Finishing at t≈85 leaves 25, below the
floor, so the job terminates `llm_timeout` **without calling the provider** —
the non-positive case behaves the same way, since any negative remainder is also
`< 30`. Worst case is bounded at the deadline, inside 11.12's 120 s.

The test blindness that let a ~56-year timeout pass 231 tests is closed at the
right level: `backend/tests/conftest.py:37,52-57` records every `timeout_s` the
runner hands the fake, and
`test_the_provider_is_never_handed_a_timestamp_as_a_timeout`
(`backend/tests/test_durability_and_deadline.py:156-173`) asserts the *quantity*
— `0 < timeout <= llm_deadline_answer_s` — which is the only assertion in the
suite that could ever have seen that defect. `:176-192` extends the same
quantity check to the summary path, which still correctly receives
`llm_timeout_summary_s`. The two behavioural tests are complementary rather than
redundant: `:94-129` proves the retry is refused when nothing is left (asserting
`len(fake_llm.calls) == 1` and elapsed within the deadline), and `:132-153`
proves the fix **bounded** the retry rather than disabling it
(`len(fake_llm.calls) == 2` and `fake_llm.timeouts[1] < fake_llm.timeouts[0]`).
That second test is what stops the obvious over-correction.

### F3 — [closed] The guard's allowed set is now scanned out of the prompt it must agree with
Verified. `allowed_values` keeps the hand-listed aggregates and then unions
`_scan(render_facts(facts))` (`backend/autonomos/insights/guard.py:112`, scanner
at `:51-60`), so the permitted set is by construction the figures the model was
shown. The two modules can no longer drift, because there is now one source.

**The core property survives, and I checked it rather than taking the test's
word.** Every line of DATOS comes from a SQL aggregate or the user's own stored
text (`prompts.py:60-103`), so the union adds concrete values, never a range: a
figure absent from DATOS is still rejected. With top expenses and excerpts
present, `test_f3_widening_did_not_weaken_the_core_property`
(`backend/tests/test_insights_router_and_guard.py:181-189`) catches an invented
total, a computed average, an out-of-set percentage and an invented count, and
`:175-178` still rejects `el 19 de julio` — a date the prompt did not show. I
confirmed the negatives are meaningful against `sample_facts()`
(`:71-86`): 312500, 20833, 63 and 88 appear nowhere in that fact set. The union
is also strictly additive — nothing previously allowed became disallowed — so
there is no regression risk in the reject direction.

**The disclosed `"Tienes 7 entradas"` limit is correctly characterised as
pre-existing, and I verified the claim independently.** The pre-F3 guard added
`float(month)` from `period_start`/`period_end`, so for period `2026-07` the
value `7.0` was already in the allowed set before this change touched anything.
`test_the_guard_is_membership_not_meaning_and_this_predates_f3` (`:192-205`)
pins exactly that with `bare = sample_facts()` — the pre-F3 shape, no top
expenses, no excerpts — and asserts `7.0 in guard.allowed_values(bare)`. That is
the honest form: the widening did not create this hole, the test documents it
rather than deleting it, and KD-10 already says a correct figure for the wrong
period is what `period_unrecognised` covers and NumericGuard cannot. **A
widening did not quietly become a weakening.**

Nothing new introduced: the `render_facts` import is function-local
(`guard.py:83`) so there is no import cycle with `prompts.py`, and the extra
render is two string builds per job.

### F2 — [closed] The other origin is now learned while the server answers, in the direction that works
Verified end to end, on both sides of the seam.

*Backend.* `GET /api/health` returns `origins.primary` from `PUBLIC_URL` and
`origins.lan` from `LAN_BIND_ADDR` + `LAN_PORT`
(`backend/autonomos/api/health.py:31-44`), normalised to bare origins by
`as_origin` (`backend/autonomos/config.py:179-191`). The handler signature is
`def health() -> dict:` with **no `Request` parameter at all**, so it is
structurally incapable of deriving anything from the request — a stronger
guarantee than a convention, and pinned anyway by
`test_origins_are_never_derived_from_the_request`
(`backend/tests/test_misc_api.py:100-112`, which sends `Host: 192.168.1.99:8443`
and `X-Forwarded-Host: evil.example.com` and asserts the configured value comes
back). `origins` is on the response model (`api/models.py:44-61`), so
`response_model` cannot silently strip it. The best detail here is that
`lan_origin` reuses `lan_fallback_status` (`config.py:194-220`) — the *same*
predicate `serve.py:53` uses to decide whether to start the listener — so the
advertised origin and the listener that must answer it cannot disagree; all
three disabled cases are asserted at `test_misc_api.py:64-97`.

*Frontend.* `rememberOrigins` is called inside `useHealth`'s `queryFn` on every
successful response (`frontend/src/api/queries.ts:55-59`), gated on nothing —
the inverted `isTailnet` condition is gone, and `main.tsx` no longer imports or
calls the old boot-time function (`frontend/src/main.tsx:1-40`). The write lands
in the storage of whatever origin is being served, which is the direction pass 1
found reversed. `otherOrigins()` (`frontend/src/state/origin.ts:68-88`) returns
every stored entry that parses as a bare origin and differs from
`window.location.origin`, deduped; `usable()` (`:35-43`) rejects anything
carrying a path, so a malformed config yields no link rather than a broken one.
`rememberOrigins` cannot throw — every operation including `JSON.stringify` is
inside the `try` (`:52-59`) and `usable` has its own — which matters, because a
throw in that queryFn would turn a healthy server into a permanent "cannot
reach" state.

**The clause most likely to be lost was not lost.** `SinServidor` builds 13.8's
two clauses separately: the instruction paragraph renders
`servidor.casaAyuda` when `alternativas.length === 0`
(`frontend/src/routes/SinServidor.tsx:64-72`), so the `<p className={s.addr}>`
is never empty — with nothing stored it still says where the home version is and
what has to be true for it to work. `titulo`, `cuerpo1`, `cuerpo2` and the
Reintentar button are all unconditional (`:45-51`), so 13.2 still holds:
explicit, names the problem, not a dead end. Pinned by
`still says in Spanish what to do when nothing has ever been stored`
(`frontend/src/test/origenes.test.tsx:109-121`), which asserts the copy *and*
the retry button *and* that no address was guessed. Reading the store once at
mount via `useState(otherOrigins)` (`SinServidor.tsx:39`) is also the right call
given the re-mount behaviour disclosed below.

**The frontend's judgment call keeps faith with the approved mockup.** I diffed
against `mockups/sin-servidor.html:481`, which renders
`<a …>Abrir la versión de casa</a>` and
`<p class="addr">La versión de casa funciona cuando el teléfono y el computador
están en el mismo wifi, aunque no haya internet.<b>https://192.168.1.24:8443</b></p>`.
On the tailnet origin with a LAN origin stored, the built screen produces that
label (`copy/es.ts:248`), that sentence (`:251-252`) and the address in a `<b>` —
**byte-identical copy to the approved screen**. The new `abrirSiempre` /
`siempreAyuda` strings (`:250,253-254`) appear only on the LAN origin, a
scenario the mockup never depicted, and only because the approved sentence would
otherwise describe the version the user is already on. The original sentence is
preserved verbatim for both the mockup's scenario and the nothing-stored
fallback. This is not an undocumented departure.

The residual KD-2 now names at `:115-133` is real and correctly bounded: the
*primary* origin — where the common failure happens, the everyday icon on a
suspended PC — is armed by ordinary daily use, not by any setup step, since
every successful health poll writes it. Only the rarer reverse direction depends
on setup loading the LAN origin once, which `ops/README-setup.md:78-80` causes
as a side effect of installing the icon and granting microphone permission.

### F8 — [deferred] The screenshot harness detects a dropped forced state only for text-selected shots
- location: `frontend/tools/shots.mjs:887-894` — `forceLost` is computed only inside `if (shot.forceText?.length)`; shots configured with `force:` (a CSS selector) never reach that check and return `forceLost: false` unconditionally at `:902`
- injected-at: implementer-frontend
- scenario: `CSS.forcePseudoState` binds to a node id (`frontend/tools/cdp.mjs:130`), so a React re-render that replaces the node drops the forced state and the capture silently becomes a duplicate of the default while being filed as a passing hover/focus/active shot. The new `ESTADO-PERDIDO` flag closes this for `forceText:` shots but not for the `force:` ones, of which there are many on stable screens — `shots.mjs:88,93,98,111,116,130,139,144,149,162,167` and others. Those particular screens do not re-mount the way the offline screen did, so I have no reason to think a specific capture is currently false, but the detector's coverage is asymmetric and a future re-render could reintroduce the silent pass on a path nothing watches. This is verification tooling, not shipped product behaviour, and it cannot affect the app a user runs — hence deferred, not blocking. Recorded so the asymmetry is not mistaken for full coverage. The frontend disclosed this itself (`frontend/tools/README.md:31-35`) rather than letting it stand, which is the reason it is a bounded note rather than a finding about hidden evidence.

### F9 — [optional] `usable()` drops an origin written with an explicit default port
- location: `frontend/src/state/origin.ts:35-43` — `url.origin === value.replace(/\/$/, '')`
- injected-at: implementer-frontend
- scenario: a configured `PUBLIC_URL=https://host:443` round-trips through the backend's `as_origin` with its netloc intact but fails this equality, because `new URL(...).origin` normalises the default port away. The entry is then silently discarded and no link is offered. It fails closed rather than producing a broken link, and neither `tailscale serve` nor `mkcert-lan.sh` produces such a value, so this is a preference. Said once.

### Pass-1 deferred items — unchanged, not re-raised
F4 (the `generating` summary surface is near-unreachable after the first
finished month), F5 (the red failed-save banner against Design Constraint 3),
F6 (no journal pagination past the newest 50) and F7 (no backoff between summary
retries) were deliberately not fixed and remain recorded as deferred. I re-read
each against the current code and **none has become blocking**: nothing in this
pass touched `api/insights.py:99`, `Panel.module.css`, the journal list, or
`scheduler.py`, and no new criterion has come to bear on them.

## Verdict

APPROVED

## Scope Statement

Static only, second pass, deliberately narrow: I checked whether the three
blocking findings are genuinely closed and whether the fixes introduced anything
new. I did not re-review the parts of the system pass 1 already cleared, beyond
confirming the fixes did not disturb them — specifically I re-confirmed that the
`Health` shape still matches across the seam (`api/models.py:44-61` against
`frontend/src/api/types.ts:53-64`, including `origins` being required on both
sides and the client still tolerating its absence at `state/origin.ts:51`), that
`13.2`'s cold-open branch is untouched (`App.tsx:32-33`), and that the summary
generation path still receives a duration rather than the new absolute deadline.

I did not execute anything: no server, no browser, no sidecar, no test run. All
gate results are taken as given and were not re-litigated.

What that leaves open, stated so this approval is not read as covering it:

- **Every runtime and timing claim.** That the retry actually terminates inside
  110 s of wall clock, that arbiter preemption lands inside R4's ~1 s residual,
  and that a real Ollama respects `timeout_s` are runtime behaviours. I verified
  the *quantity handed to the provider* is a duration inside the answer window;
  I did not observe a generation.
- **Whether NumericGuard's widened set behaves well against a real model.** I
  established the static property — the allowed set is exactly what DATOS
  contains, and figures outside it are still caught. Whether Qwen2.5-3B now
  produces answers that pass more often, and whether the `unverifiable_figures`
  rate actually falls, is a measurement only QA can make.
- **The F2 mechanism on real devices and real origins.** I verified the write
  direction, the read, the storage key, the null handling and the copy. I did
  not observe `localStorage` surviving a real Android Chrome session, a real
  cross-origin navigation, or the mkcert LAN listener answering. The frontend's
  own disclosure that a SIGTERM in `sw-warm.mjs` had been dropping the very
  write the cold-open check depends on is a reminder that this mechanism's
  evidence is environment-sensitive; **QA should verify the link on the phone,
  on both origins, rather than trusting the harness.**
- **Interactive-state screenshot evidence**, per F8: hover/focus/active captures
  for `force:`-selected elements carry no liveness check, so treat that row of
  the matrix as weaker than the `forceText:` rows.
- **Everything measurement-based** that pass 1 also excluded: contrast ratios,
  44×44 hit boxes, the 390 px no-horizontal-scroll claim, transcription
  accuracy, LLM output quality, the systemd units in a live session,
  `tailscale serve`, and the two microphone states that cannot be reached in
  this environment.
