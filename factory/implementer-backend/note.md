# Backend implementation note

## Summary

The backend lane is complete and running. `backend/` is a Python 3.12 FastAPI app
over SQLite (WAL, `synchronous=FULL`, foreign keys on) that serves every endpoint
in Architect's Interface Contract — 30 operations, no more and no fewer — plus the
built SPA from the same origin. The Spanish expense parser is rules-only and
sub-millisecond; the LLM never enters the capture path and never computes a
figure. One `InferenceArbiter` governs both sidecars with the ordering
transcription > question > category assist over background summaries, with
preemption, a 60-second quiet period, and an answer deadline measured from
`created_at`. An in-process scheduler does the boot catch-up scan, the 15-minute
tick and the nightly `VACUUM INTO` snapshot. `ops/` carries four systemd **user**
units, a setup script that runs `loginctl enable-linger`, an `mkcert` helper for
the LAN fallback origin, and a runbook.

231 backend tests pass. Beyond the suite, the stack was exercised live against the
**real** Ollama and whisper.cpp sidecars over HTTP: an expense saved, a 4 s clip
transcribed in 5.9 s, a Spanish answer returned in 16.4 s with correct facts, and
a running question preempted by an arriving transcription. Two live findings
changed code: whisper's `[Música]` non-speech marker is now rejected as
`transcription_failed`, and LLM cancellation is now sub-100 ms instead of ~2 s,
which cut a contended transcription from 17.6 s to 8.5 s.

Two corrections landed after the first pass and are implemented: the loopback API
port is **8001**, because 8000 belongs permanently to an unrelated project's
container on this host; and per the KD-11 revision, **`partial_answer` is no
longer on the wire** — no LLM text reaches a client before NumericGuard has run
on the complete output.

`state.verification` in `factory/state.json` is `{}` — no deterministic gate has
run yet, so nothing here contradicts a gate result. Every number above is from a
command I ran on this host today.

## How to run it

```bash
cd backend
~/.local/bin/uv venv --python ~/.local/bin/python3.12 .venv
~/.local/bin/uv pip install -e ".[dev]"
.venv/bin/python -m pytest -q                      # 231 tests
.venv/bin/python -m autonomos.serve                # both origins, one process
```

Host setup (units, linger, env file): `ops/setup.sh`. Runbook and the two steps a
script cannot do (Tailscale login, `tailscale serve`): `ops/README-setup.md`.

Live checks against the real sidecars:

```bash
.venv/bin/python tools/live_check.py llm
.venv/bin/python tools/live_check.py stt
.venv/bin/python tools/live_check.py endpoint  ~/.local/whisper.cpp/samples/short4s.wav
.venv/bin/python tools/live_check.py contention ~/.local/whisper.cpp/samples/short4s.wav 1.5
```

## Where the design decisions live in the code

| Design | Code | Criteria |
| --- | --- | --- |
| KD-3 one worker, typed models, `/openapi.json` | `autonomos/main.py`, `api/models.py` | R10 |
| KD-4 SQLite WAL/FULL/FKs, migrations, seed | `db/connection.py`, `db/migrations/0001_init.sql`, `db/seed.py` | 3.1, 14.1 |
| KD-4 nightly `VACUUM INTO`, 7 kept | `scheduler.py:60-95` | 14.1 |
| KD-5 whisper sidecar adapter, `-l es` | `providers/whispercpp_http.py` | 8.7 |
| KD-6/KD-7 provider interfaces, OpenAI wire format | `providers/base.py`, `providers/openai_compatible.py` | — |
| KD-8 L1 rules parser, numeral grammar, aliases | `parsing/numerals.py`, `parsing/extractor.py`, `parsing/aliases.py` | 2.4, 9.1, 9.2, 9.6, 9.7 |
| KD-8 L2 category assist, 6 s cap, `max_tokens=8` | `api/expenses.py:82-160` | 9.2, 9.3 |
| KD-9 journal audio never post-processed | `api/voice.py:121-123` (no LLM path exists) | 10.2 |
| KD-10 router / facts / prompts / guard | `insights/router.py`, `facts.py`, `prompts.py`, `guard.py` | 11.1-11.3, 11.7, 11.8, 11.9, 11.11 |
| KD-11 job + polling, deadline from `created_at` | `insights/runner.py:80-200`, `api/insights.py` | 11.12, 11.13 |
| KD-12 the InferenceArbiter | `arbiter.py` | 11.17, 8.8 |
| KD-12 scan predicate, orphan sweep, retries | `repo/summaries.py`, `scheduler.py:36-58`, `runner.py:sweep_on_startup` | 11.14-11.16 |
| KD-15 one WAV format validated server-side | `audio.py` | 8.4 |
| KD-16 no Gym anything | absence; asserted in `tests/test_misc_api.py` | 1.3 |
| KD-17 error envelope, closed code set | `errors.py`, `main.py:validation_exception_handler` | 1.5 |
| KD-2 two origins from one process | `serve.py`, `ops/systemd/autonomos-api.service` | 13.4, 13.6, 15.5 |
| `clock/` sole owner of calendar boundaries | `clock.py` | 4.8 |

## Interface Contract Conformance

Implemented exactly as specified. `tests/test_contract_conformance.py` asserts the
generated OpenAPI surface **equals** the contract's set of (method, path) pairs —
so both a missing endpoint and an extra one fail the build.

| Contract entry | Status |
| --- | --- |
| `GET /api/health` | as specified (`status`, `server_time`, `tz`, `version`) |
| `GET /api/status` | as specified; cached 30 s, each probe capped at 2.5 s |
| `GET /api/categories` | as specified, incl. `include_archived`, `in_use_count` |
| `POST /api/categories` | 201 new / **200 un-archive**, `409 conflict`, `blank`/`too_long` |
| `PATCH /api/categories/{id}` | as specified |
| `DELETE /api/categories/{id}` | archive only; `409 in_use` with `details.affected_expenses`; `confirm` gate |
| `GET\|POST\|PATCH\|DELETE /api/payment-methods[/{id}]` | identical in every respect — one router factory, both paths parametrised in the tests |
| `POST /api/expenses` | as specified; `source` accepted, stored, **never returned** |
| `GET /api/expenses` | `date` or `month`, `limit`≤200, `offset`, `total_count`, newest first |
| `GET /api/expenses/{id}` | as specified |
| `PATCH /api/expenses/{id}` | any subset; same validation reasons |
| `DELETE /api/expenses/{id}` | 204, no server-side double confirm |
| `GET /api/summary/day` | as specified; 0 and `[]` for an empty day |
| `GET /api/summary/month` | as specified; largest-remainder percents sum to exactly 100; `is_empty` |
| `POST /api/journal` | as specified; byte-exact text, no maximum, `source` not returned |
| `GET /api/journal` | `date` or `before`, `limit`≤50, `next_before` |
| `GET\|PATCH\|DELETE /api/journal/{id}` | as specified |
| `POST /api/voice/transcribe` | as specified; `415`/`413`/`422`/`504`; never `503 llm_unavailable`; writes nothing |
| `ExpenseDraft` shape | exact, incl. `description_truncated` and `resolved_by` |
| `POST /api/expenses/parse` | rules only, no model |
| `POST /api/expenses/suggest-category` | never fails the caller; `rules`/`llm`/`none`; validated against existing categories |
| `POST /api/insights/questions` | `202`; `400`; `503 llm_unavailable`; `409 busy` only for an active job |
| `GET /api/insights/questions/{job_id}` | full shape incl. `facts` and `elapsed_ms`; **no `partial_answer`** and `answer` null until `done` (KD-11 revision); all terminal `error_code` values reachable |
| `DELETE /api/insights/questions/{job_id}` | 204, cancels generation, touches no data |
| `GET /api/insights/summaries/latest` | all five states: `ready`/`generating`/`empty`/`failed`/`none` |
| `GET /api/export` | JSON attachment, ids **and** names, the only export endpoint |
| Error envelope + closed code set | `errors.py`; every code in the design's list, nothing outside it |
| `fields[].reason` closed vocabulary | asserted by an `assert` in `ValidationError` itself |

**Picked up mid-flight: the KD-11 revision that removes `partial_answer` from the
wire.** The design was amended while I was implementing (`factory/architect/design.md`,
KD-11 and the `GET /api/insights/questions/{job_id}` entry). I implemented it:
the field is gone from the response model and the handler, `answer` stays null
until `done`, and `insight_jobs.partial_answer` remains as a **server-side
diagnostics column** exactly as the revision says — written during generation,
never serialised. Two tests pin it, including one that checks a job *in flight*
carries no generated text. The reasoning is the same as `source`: a field present
in the contract is a field a component will eventually display.

Two contract points where the document left a choice and I made one; neither
changes a shape, a status code, or a field name:

1. **Which row `/latest` returns when several exist.** The contract lists the
   states but not the selection rule. I return the most recent **finished**
   (`ready`/`empty`) row, falling back to the most recent row of any status. The
   alternative — always the newest row — would hide a readable July summary behind
   an August one that is still generating, which reads as a 11.15 failure.
   `tests/test_insights_api.py::test_a_readable_summary_is_not_hidden_by_a_newer_generating_one`.
2. **Timestamp precision.** Timestamps are ISO-8601 with offset at **millisecond**
   precision (`2026-08-05T20:26:17.975-05:00`). `GET /api/journal`'s cursor is a
   `written_at` value, so at seconds precision two entries written in the same
   second stall pagination — I hit this in a test. Residual: two entries inside the
   same millisecond would still collide; that needs an id in the cursor, which the
   contract does not have.

## Escalations / Deviations

No escalation was needed; nothing here changes a component, an interface, a data
flow, or a technology choice. Four things are worth Reviewer's eye.

**1. Two origins, one process — a tension between KD-2 and KD-3, resolved without
changing either.** KD-2 requires a uvicorn TLS listener on `${LAN_BIND_ADDR}:8443`
alongside `127.0.0.1:8001`; KD-3 requires exactly one worker because the scheduler
and the arbiter are in-process and "two arbiters is the same as none". Two uvicorn
*processes* would have produced exactly the two arbiters KD-3 forbids. `serve.py`
runs both listeners as two `uvicorn.Server` instances inside one event loop over
one app object, so there is one arbiter, one scheduler and one DB writer.
Verified live: `http://127.0.0.1:8001/api/health` and `https://<addr>:8443/api/health`
both answered from the same process. `LAN_BIND_ADDR=0.0.0.0` is **refused**, not
obeyed (`serve.py:_lan_enabled`), per KD-2's "one named interface, never all of them".

**2. LLM cancellation was too slow to honour KD-12, and is now fixed.** The first
live contention run showed the arbiter force-taking the slot after its 2 s grace
period and the transcription taking **17.6 s** instead of ~7.5 s. Cause: the
streaming adapter checked the cancel token *between* SSE lines, and prompt
evaluation emits no lines for tens of seconds, so a preempting transcription
waited for the next token. `providers/openai_compatible.py:_cancellable_lines`
now awaits each line *against* the cancel event. Re-measured: preemption lands in
under 100 ms and the contended transcription took **8.5 s**. R4 predicted ~1 s of
residual overlap; before this change it was ~2 s and the cost landed inside 8.8's
budget. The force-take path is kept as the backstop and is tested.

**3. Whisper emits bracketed non-speech markers, and R5 did not name them.** Sending
a tone to the real sidecar returned `[Música]`. Left alone that becomes a journal
entry. `audio.looks_hallucinated` now rejects a transcript that is entirely one
bracketed token (`[Música]`, `[BLANK_AUDIO]`, `(silencio)`) as
`transcription_failed`, alongside the "Subtítulos realizados por…" family R5 does
name. A sentence merely *containing* the word música is unaffected — tested.

**4. The API listens on 8001, because 8000 belongs to another project — permanently.**
I first reported this as "probably the frontend lane's mock"; **that was wrong**, and
the coordinator corrected it with `docker ps`: port 8000 is held by
`trace_erp_api`, a long-running container from David's unrelated
`trace_2026_deploy` project, published on all interfaces. It is not ours and must
not be stopped or reconfigured. That makes the collision permanent rather than
incidental, so a note was not a fix — a default of 8000 would have crash-looped
`autonomos-api` the first time David ran `ops/setup.sh`, on the one machine this
app runs on. The default is now `AUTONOMOS_API_PORT=8001` (verified free, as is
8443) in `config.py`, `ops/autonomos.env.example`, the unit, and the `tailscale
serve` target in both the script and the runbook. It stays configurable; nothing
about 8001 is sacred. `ops/setup.sh` now refuses to install a unit whose port is
already listening, naming the port and telling the user to change
`AUTONOMOS_API_PORT` — and explicitly telling them **not** to stop whatever holds
it. `ops/setup.sh --check` runs that preflight and changes nothing.

Not a deviation, but stated so nobody has to reconstruct it: `config.py` holds the
provider defaults (`LLM_MODEL=qwen2.5:3b-instruct-q4_K_M`, the whisper base URL),
which are the exact env values KD-7 itself writes out. The boundary-rule test
(`test_no_vendor_name_outside_providers`) exempts that one file and enforces the
rule on every other module — a provider swap is still a config change with no code.

## Acceptance Criteria Mapping

Frontend-owned criteria are named as such and are not claimed here. "Tested" means
a named test in `backend/tests/`; "live" means I ran it against the real sidecars.

### Requirement 1 — shell (frontend lane)
1.1, 1.2, 1.4, 1.5 — frontend. 1.5's backend half is KD-17: the API returns closed
machine codes and never a Spanish sentence (`errors.py`); the only Spanish the
backend emits is LLM insight text, which KD-10 names as the one exception.
**1.3 (Gym)** — frontend, and the backend's obligation is the *absence* of Gym:
no table, no model, no endpoint. Tested (`test_kd16_there_is_no_gym_endpoint`).

### Requirement 2 — manual expense capture
- 2.1 saved, dated today, in the Today list — tested; `repo/expenses.py:create`.
- 2.2 empty/zero/negative rejected with the field named — tested (`required`,
  `must_be_positive`).
- 2.3 missing category or method named — tested.
- 2.4 `14.000`/`14000`/`14 000` — the *input parser* is the frontend's per the
  contract; the same three forms are handled server-side in the numeral grammar so
  voice and `/parse` agree. Tested.
- 2.5 display formatting — frontend.
- 2.6 optional description, incl. empty — tested.
- 2.7 backdating allowed, future rejected (`future_date`) — tested.
- 2.8 four-interaction budget — frontend.

### Requirement 3 — categories and payment methods
- 3.1 non-empty Spanish starter sets — seeded on first run; tested for both tables.
- 3.2 create from inside the form — endpoint exists and is order-independent;
  "without abandoning the draft" is frontend.
- 3.3 rename shows on existing expenses — expenses hold ids, so no backfill. Tested.
- 3.4 warn when in use, never orphan, keep historical attribution, remove from
  selection — `409 in_use` with the count in `details`, archive not delete,
  archived rows still resolve in month totals. Tested (four assertions).
- 3.5 exactly one category and one method — `NOT NULL` FKs in the schema. Tested.

### Requirement 4 — today and this month
- 4.1 today total + list newest first — tested.
- 4.2, 4.3 breakdown, percentages summing to 100, ordered — largest-remainder
  rounding in `repo/expenses.py:largest_remainder_percents`. Tested.
- 4.4 per-payment-method totals — tested.
- 4.5 empty month is an explicit empty state (`is_empty`, `[]`, 0) — tested.
- 4.6 totals reflect saves/edits/deletes — server always recomputes; tested. The
  "without manual refresh" half is TanStack invalidation, frontend.
- 4.7 previous months on the same terms — tested.
- 4.8 local calendar day/month — every boundary in `clock.py` in `APP_TZ`; the
  server is authoritative. Tested via `-05:00` timestamps and month bounds.

### Requirement 5 — correcting the record
- 5.1 all five fields editable and persisted — tested.
- 5.2 confirmation before delete — the confirm step is the client's (constraint 19);
  the server deletes on request and 404s otherwise. Tested.
- 5.3 journal edit persists — tested.

### Requirement 6 — journal capture
6.1 tested · 6.2 blank rejected, tested · 6.3 separate rows, tested · 6.4 line
breaks preserved, tested · 6.5 5,000+ characters stored and returned in full,
tested · 6.6 nothing but text required, tested · 6.7 accents/ñ/¿¡ round-trip,
tested. Storage is byte-exact; only the blank check trims.

### Requirement 7 — journal browsing
- 7.1 newest first — tested. The date grouping/labels are frontend.
- 7.2 a queried day with nothing returns `items: []` — tested.
- 7.3 empty state — the API returns an empty list, not an error; the invitation is
  frontend.

### Requirement 8 — voice capture
- 8.1, 8.5 listening state, permission handling — frontend.
- 8.2 show what was heard before anything is written — the endpoint returns a
  transcript and writes nothing; tested (`test_8_3_transcribing_writes_nothing`).
- 8.3 cancel discards — no write path exists to discard from.
- 8.4 failure/timeout/nothing-usable says so and saves nothing — `422
  transcription_failed`, `504 transcription_timeout`, silence and hallucination
  rejection. Tested, and the `[Música]` case came from a live run.
- 8.6 explicit confirmation — structural: there is no endpoint that turns audio
  into a record.
- 8.7 Spanish, not translated — `-l es` in the unit and per request; no translate
  flag anywhere. Live: the sidecar returned Spanish text.
- 8.8 the 30 s bound — the client owns the clock (KD-5). The server's terms:
  `STT_TIMEOUT_S=20`, and measured live **5.9-8.0 s** for a 4 s clip end to end
  through the endpoint, 8.5 s when contended. 32 s audio is accepted, 33 s is
  `413`. Tested.
- 8.9 abandon in flight — `AbortController` disconnect is watched and cancels the
  sidecar work rather than holding the arbiter slot (`api/voice.py:38-51`).

### Requirement 9 — voice to expense
- 9.1 pre-filled form from one sentence — tested end to end:
  "gasté 14.000 pesos en Uber con la tarjeta de crédito" →
  14000 / Transporte / Tarjeta de crédito / description.
- 9.2 undetermined fields left empty, never guessed — `resolved_by.<field> ==
  "none"`; two equally-cued amounts yield `null` rather than a pick. Tested.
- 9.3 suggestions are always existing categories — true by construction (aliases
  point at rows) and the LLM assist discards anything not in the list. Tested.
- 9.4 edited values win — frontend.
- 9.5 a voice expense is indistinguishable — `source` is request-only and appears
  in no response body. Tested.
- 9.6 `catorce mil` / `14 mil` / `14.000` → one value — tested, 15 numeral forms.
- 9.7 everyday payment phrases matched or left empty — tested.

### Requirement 10 — voice to journal
- 10.1 full transcript into the entry text — returned verbatim; tested.
- 10.2 no rewriting or translation — enforced by the absence of a code path (KD-9);
  the journal context returns `draft: null` and never calls the LLM. Tested.
- 10.3 edits win — frontend.
- 10.4 indistinguishable from typed — `source` never returned. Tested.

### Requirement 11 — insights
- 11.1 only the user's own data, no outside facts or advice — **prompt-enforced,
  not guarded**, exactly as KD-10 states. `insights/prompts.py` rules 2, 4, 5.
  QA should test this as judgement; nothing detects it mechanically.
- 11.2 figures match the Finances screens — every figure is a SQL aggregate;
  NumericGuard rejects any numeric token outside the fact set, retries once with a
  stricter prompt, then fails `unverifiable_figures`. Tested (invented figure,
  computed average, out-of-set percentage) and live.
- 11.3 too little data said plainly — insufficiency pre-check before any model
  call; tested, including that the model was never called.
- 11.4 everything else keeps working — capture, editing and views touch SQLite only
  and never enter the arbiter; `503 llm_unavailable` on ask, `/api/status` reports
  it. Tested with the model down.
- 11.5 visible in-progress state, result or explicit failure — `elapsed_ms` is the
  only progress signal on the wire and changes every poll; no generated text is
  returned before NumericGuard has passed on the whole output (KD-11 revision).
- 11.6 read-only — no handler on the insights path writes to `expenses` or
  `journal_entries`. Tested (the expense survives a cancel).
- 11.7 Spanish — prompt-enforced, as KD-10 states. Live answers were Spanish.
- 11.8 finance questions — tested and live ("Gastaste 14.000 pesos hoy en
  Transporte", 16.4 s).
- 11.9 journal questions, with the two counts and `journal_truncated` in `facts` —
  tested, including truncation under the 1,200-token budget.
- 11.10 typed or spoken — `source: "text"|"voice"`, and `context=question` on the
  transcribe endpoint.
- 11.11 cannot answer rather than fabricate — three mechanisms:
  `period_unrecognised` for an unresolvable period, `insufficient_data`,
  `unverifiable_figures`. Tested.
- 11.12 working state inside 1 s, alive while working, answer or explicit failure
  inside 120 s — `202` returns immediately (measured <1 s); the deadline is
  enforced from `created_at`, and a job that cannot start with 30 s left terminates
  `llm_timeout` rather than starting. Tested; live answers took 4.6-39.6 s.
- 11.13 cancel, leave, no data affected — tested.
- 11.14 summary covers spending **and** journal — `domain="both"` always. Tested.
- 11.15 previous summary readable immediately, no generation on open — `/latest`
  reads a row and nothing else. Tested (<1 s, and no provider call).
- 11.16 never produced / period empty are explicit states — `none` and `empty`.
  Tested.
- 11.17 a summary never blocks or slows capture — the arbiter cancels a running
  summary the moment interactive work arrives, and the read/write path never enters
  the arbiter at all. Tested at unit level and end to end (transcription preempted
  a running question; a summary is strictly weaker).
- 11.18 states its period and when it was produced — `period_key`, `period_label`,
  `generated_at`. Tested.

### Requirement 12 — zero cost
12.1, 12.2, 12.4 — no dependency in `pyproject.toml` is paid; nothing calls a
remote service; no key, no account. Verified by inspection.

### Requirement 13 — reaching it from the phone
- 13.1 no app store — frontend/delivery.
- 13.2, 13.3, 13.5, 13.8 — frontend states; the backend's part is `/api/health`
  for reachability and persisted jobs so a reload re-attaches (13.3). Tested.
- 13.4 away-from-home parity — the same endpoints on both origins; no feature is
  gated on the network.
- 13.6 never publicly reachable — API binds `127.0.0.1` plus one named LAN
  interface (`0.0.0.0` refused); both sidecar units bind loopback; the runbook says
  Funnel stays off.
- 13.7 no step before capture — no auth anywhere by A6.

### Requirement 14 — the record survives
- 14.1 survives a restart — WAL + `synchronous=FULL` + FKs, asserted by PRAGMA in a
  test, plus a test that drops every connection and re-reads. Nightly `VACUUM INTO`
  snapshots, 7 kept, verified by reading a snapshot back.
- 14.2 export readable without the app — `GET /api/export`, ids and names. Tested.
- 14.3 nothing auto-deletes — no expiry or pruning job exists for user records;
  a test greps the scheduler for a delete against those tables. Snapshot pruning
  touches only `data/snapshots`.

### Requirement 15 — the data never leaves the PC
- 15.1 audio processed only here — forwarded in memory to `127.0.0.1:8081`, never
  written to disk.
- 15.2, 15.3 — the only outbound HTTP the backend makes is to the two loopback
  sidecars; no other host appears in `providers/`.
- 15.4 no account or key — none anywhere.
- 15.5 works with home internet down — the LAN fallback origin; the sidecars and
  the DB are local. The end-to-end proof needs the phone and is QA's.

## What I deliberately did not do

- **I did not install or start the systemd units.** `ops/setup.sh` does that,
  including `loginctl enable-linger`. I verified the units' syntax with
  `systemd-analyze --user verify` (all four clean) and ran each unit's `ExecStart`
  command by hand — the API through `python -m autonomos.serve`, whisper-server
  with exactly the unit's flags, Ollama already serving. I did not enable them
  because installing user units and enabling linger changes the human's session
  state. (The port-8000 collision that first blocked this is now designed out:
  the default is 8001 and `ops/setup.sh` preflights it.)
- **Tailscale login and `tailscale serve`** — interactive, the human's, as briefed.
- **The LAN certificate** — needs the DHCP-reserved LAN IP. `ops/mkcert-lan.sh`
  takes it as an argument; I proved the TLS listener works with a throwaway cert
  for `127.0.0.1`, then deleted it.
- **Spanish transcription accuracy is still unverified**, and this is R9's open
  item, not something I could close: the host has no TTS and no recording device,
  so there is no real Spanish speech sample here. I verified the whisper round trip
  and language forcing with the repo's English sample through `-l es` (it returns
  Spanish words, i.e. no translation to English) and verified 9.6/9.7 through the
  parser with text. Someone with a microphone must still say
  "gasté catorce mil pesos en Uber con la tarjeta de crédito" once.
- **`GET /api/gym`, `expenses.csv`, `journal.csv`** — do not exist, and a test
  fails if they ever do.

## Measurements from this host, 2026-08-05

| What | Measured |
| --- | --- |
| `POST /api/voice/transcribe`, 4 s clip, real sidecar | 5.9-8.0 s end to end |
| same, while Ollama was generating (after the cancel fix) | 8.5 s |
| same, before the cancel fix | 17.6 s |
| finance question, real Ollama, HTTP + polling | 16.4 s |
| three questions in `live_check llm` | 4.6 s, 17.0 s, 39.6 s |
| backend test suite | 231 tests, ~8 s |

`elapsed_ms` is logged for every transcription and every job, as R9 asks.
