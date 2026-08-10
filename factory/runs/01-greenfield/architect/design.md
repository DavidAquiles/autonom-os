# Autonom-OS — Technical Design

## Summary

A single-user, self-hosted web app: **React + TypeScript SPA** served as static files by a **Python
FastAPI backend** over **SQLite (WAL)**, with two local AI sidecars — **whisper.cpp** for Spanish
transcription and **Ollama running Qwen2.5-3B-Instruct Q4_K_M** for insights. One machine, four
processes, loopback-bound, systemd user units. Three decisions carry it:

1. **Tailscale provides HTTPS, and HTTPS is what makes voice possible at all.** `getUserMedia`
   needs a secure context, which a plain `http://` LAN or VPN address is not. `tailscale serve`
   terminates TLS with a phone-trusted `*.ts.net` cert reachable only from David's devices —
   satisfying away-from-home access (13.4), the never-public rule (13.6), and the microphone at once.
2. **The voice→expense parse is rules-first; the LLM assists only with category.** A deterministic
   Spanish parser fills amount, payment method and description in milliseconds, so the pre-filled
   form appears the instant the transcript does. The model is never in the capture path.
3. **The LLM never computes a number.** Figures come from SQL, are injected as facts, and generated
   text carrying a figure outside the fact set is rejected — which makes 11.2 enforceable.

Both AI layers sit behind provider interfaces speaking the OpenAI-compatible wire format, so
replacing local inference is a base-URL change. One **InferenceArbiter** governs both sidecars:
transcription and questions preempt the background monthly summary, so the runtimes never contend.

**The biggest risk is mobile voice capture** — secure context, on-device resampling, and Tailscale
with home internet down (15.5) converge on one feature; test it on the real phone first. Approved
at the gate on 2026-08-05: **Android only**, Tailscale kept with its third-party residual accepted
(R11), CSV exports cut, nightly snapshots kept.

---

## Key Decisions

### KD-1. How the app reaches the phone: Tailscale + `tailscale serve` (HTTPS)

`tailscale serve https / http://127.0.0.1:8000` publishes the app at
`https://<host>.<tailnet>.ts.net`, with a Let's Encrypt certificate that every phone already
trusts, reachable only by devices signed into David's tailnet. Tailscale Funnel (the public
option) is **not** enabled.

This is load-bearing beyond convenience: `navigator.mediaDevices.getUserMedia` and
`MediaRecorder` are gated on a *secure context*. Only `https://` and `localhost` qualify. Without
a trusted cert on the phone, voice capture — half the product — cannot exist.

Rejected:

- **Plain HTTP over LAN or a hand-rolled WireGuard tunnel.** Cheapest to set up, and it kills
  voice on the phone. Also no stable hostname, no cert, manual NAT traversal.
- **Self-signed cert + CA installed on the phone.** Works, but is a fiddly one-time setup — on
  Android the CA goes in through Settings → Security → Encryption & credentials and leaves a
  standing "network may be monitored" warning — and the cert expires on a schedule nobody will
  remember. Retained as a *fallback origin only* — see KD-2.
- **Port-forward + Let's Encrypt HTTP-01.** Directly violates 13.6.
- **Cloudflare Tunnel / ngrok.** Free tiers exist, but David's requests would traverse a third
  party's edge — a 15.3 hazard — and a free tier that can start charging is a 12.4 hazard.
- **Native app / app store.** Excluded by 13.1 and A5.

Tailscale's personal plan is free, needs no card (12.1, 12.2), and carries no user data — it
carries encrypted traffic between two of David's own devices, which is not third-party
*processing* (15.3).

### KD-2. Two origins, one app; the frontend hardcodes no origin

The app is served on two origins simultaneously:

| Origin | Bind | Purpose |
| --- | --- | --- |
| `https://<host>.<tailnet>.ts.net` | `tailscale serve` → `127.0.0.1:8000` | primary; anywhere, any network |
| `https://<LAN-IP>:8443` | uvicorn TLS bound to `${LAN_BIND_ADDR}:8443` | LAN fallback with an `mkcert` CA installed once on the phone |

The LAN fallback exists specifically for **15.5** (home internet down, both devices on the private
network). Tailscale nodes that are already up keep working over direct LAN endpoints with cached
peer state, but a cold start without internet can fail to reach the coordination server. One
mechanism failing a hard acceptance criterion is not acceptable, so there are two.

Consequence for the frontend, and it is not optional: **every API call uses a relative path**
(`/api/...`). No base URL constant, no environment-specific origin, no CORS configuration
anywhere. The same bundle must work under both origins unchanged.

**How the fallback is actually reached.** No transparent failover is possible — a page served from
origin A cannot silently retry origin B — so this is decided, not left to the implementer:

1. **A second home-screen icon**, installed during setup, labelled distinctly (the frontend owns
   the Spanish label; something that reads as "at home"). In addition, the "cannot reach your
   server" state offers a plain link to the *other* origin — a navigation, not a retry, which is
   the only thing that can cross an origin boundary.

   **The link is armed while the server is reachable, never at the moment it is needed.** This is
   the whole mechanism and it is easy to get backwards, so it is stated as a rule: the server
   advertises both of its origins on `GET /api/health`; the client persists them in the storage of
   **whatever origin it is currently being served from**, on every successful response; and the
   unreachable state renders from that origin's own stored copy. There is no fetch while offline —
   by definition nothing would answer — and no cross-origin read, because there is no such thing.

   The failure this replaces is worth recording so it is not reinvented: `localStorage` is
   partitioned by origin, so an implementation that writes the address *while on the LAN origin*
   puts it somewhere the tailnet origin can never read, and the tailnet origin is the one that
   renders the failure. The mechanism must run in the direction of the origin that will need it,
   which means every origin stores the set for itself.

   **KD-2's no-hardcoded-origin rule survives intact.** The bundle still contains no origin, host
   or port; it learns one at runtime as data from the machine that knows its own addresses. A build
   constant would have to be rebuilt when the LAN address changed; this refreshes on the next
   successful load.
2. **The certificate names a fixed LAN IP, not `.local`.** mDNS resolution of `.local` from Android
   Chrome is unreliable, so the setup script requires a DHCP reservation on the router and runs
   `mkcert <LAN-IP> autonomos.local`, putting the IP in the SAN and the hostname in as a
   convenience only. The address is stable because the reservation makes it stable.
3. **Browser state is per-origin, and two things depend on it.** Setup grants microphone access on
   *both* origins once, at setup time, precisely so that 15.5's scenario does not begin with a
   permission prompt — and, by loading the app successfully on each origin, it is also what arms
   the cross-origin link in mechanism 1. Both are the same one-time act. Nothing else is at stake:
   A15 puts no user data in the client, so a cold TanStack cache on the fallback origin costs one
   fetch.

**Named residual: an origin that has never once reached the server cannot offer the alternative.**
Before an origin has had a single successful `/api/health` response it has nothing stored, so the
unreachable state there renders without a link. 13.8 has two clauses and they fare differently:

- *"tell the user in plain Spanish, at the moment they hit it, what to do instead"* — **holds
  always.** This is copy, not data: the state says to join the home network and open the local
  access. It does not depend on knowing the address.
- *"the working alternative SHALL be reachable in no more than one deliberate action"* — **does not
  hold in that window**, and no mechanism would. A page cannot learn a peer origin's address
  without having once talked to the server, and baking it into the bundle is the hardcoded origin
  this design refuses.

**13.2 holds throughout** — the state is explicit, names the problem, and offers retry; it is not a
dead end, and the link was always an addition to it rather than the whole of it.

The window is bounded by setup, which loads the app on both origins, so it does not arise in
operation — but it is a real gap between install and setup completion and is recorded rather than
argued away. **The setup script owns closing it**: loading each origin once is not optional polish,
it is what makes 13.8's second clause true.

**Reading of 13.7 this depends on, stated so PM can object:** 13.7 governs *routine daily use*,
which runs on the primary origin with no extra step. Switching origins is a recovery action during
an outage, not routine use. If PM reads 13.7 as covering outage recovery too, this design fails it
and there is no mechanism that would not — origins cannot fail over transparently.

**Two config values name the two origins**, and they are what `GET /api/health` echoes: `PUBLIC_URL`
(the `https://<host>.<tailnet>.ts.net` origin) and `LAN_BIND_ADDR` plus the TLS port. Both are
server configuration and neither is ever inferred from a request `Host` header — a client that can
reach one origin must be told the *other* one, which the request cannot supply.

**The fallback listener binds one interface, not all of them.** `LAN_BIND_ADDR` is the host's LAN
address; it is never `0.0.0.0`. It runs continuously, because 15.5 can occur at any moment and a
listener that must be started by hand during an outage is not a mechanism. It is unauthenticated
by A6's deliberate choice, which makes the home LAN the access boundary for this port — so if the
PC is ever attached to a network David does not control, `LAN_BIND_ADDR` should be unset and the
fallback disabled. That is a config line, and the setup README must say so.

Rejected: making Tailscale the only path (fails 15.5 on a cold start); making the LAN path
primary (fails 13.4, away-from-home use); binding the fallback to `0.0.0.0` (widens an
unauthenticated surface onto every interface for no gain).

### KD-3. Backend: Python 3.12 (pinned) + FastAPI + Uvicorn, single worker

Python because the Spanish number grammar, the SQL fact aggregation, and `sqlite3` all live
naturally there. FastAPI because typed request/response models mirror the Interface Contract
below and emit `/openapi.json`, which is a real integration aid for a frontend implementer who
cannot see the backend code.

**The system Python 3.14.4 is not used.** ML- and Rust-backed wheels (`pydantic-core`, `numpy`)
lag new CPython ABIs, and building them on this box is hours of risk for zero benefit. The backend
provisions CPython 3.12 with `uv python install 3.12` into a project venv. **Done on this host,
2026-08-05:** `uv 0.12.2`, CPython 3.12.13. R8 is closed — the Docker fallback is not needed.

Rejected: **Node/Express** (would gain nothing — the sidecars are HTTP either way — and loses the
text-processing and stdlib-sqlite fit); **Django** (ORM, admin, migrations framework for five
tables); **Flask** (fine, but no typed models or generated schema); **Docker for the whole app**
(RAM and disk overhead, model-path and audio-path friction, and Ollama-in-Docker duplicates model
storage; kept as the documented escape hatch if `uv` fails on this host).

Uvicorn runs with **exactly one worker**. The scheduler and the InferenceArbiter are in-process; a
second worker would duplicate both, and two arbiters is the same as none.

### KD-4. Datastore: SQLite, WAL, `synchronous=FULL`, foreign keys on

One user, a few thousand rows a year, single writer. SQLite is a file, needs no server, needs no
RAM budget, and survives a restart (14.1). The `sqlite3` CLI is absent from the host; irrelevant,
the Python module is present.

`synchronous=FULL` rather than the usual WAL-plus-`NORMAL`: write volume is a handful of rows a
day, so the durability is free, and the machine is a desktop that will be suspended and
occasionally lose power. A nightly `VACUUM INTO data/snapshots/YYYY-MM-DD.sqlite` keeps the last 7
days.

**The nightly snapshots were approved by the human at the Approve Plan gate on 2026-08-05** and
are in scope. They exceed what 14.1 strictly requires — survival across a restart — and were kept
deliberately, on the reasoning that backups protect against data loss, which is the failure that
actually hurts in a system holding years of irreplaceable personal writing. They are not unmandated
work and are not to be cut later as scope creep.

Rejected: **PostgreSQL** (a server process and ~200 MB of the 5.3 GiB for one user, no benefit);
**JSON/NDJSON files** (no atomic multi-row updates, aggregation in Python); **DuckDB** (analytics
engine; the aggregation here is trivial and OLTP durability matters more).

Migrations are numbered plain-SQL files applied in order, with the applied version in a `meta`
table. Rejected Alembic: a dependency and a code-generation step for five tables.

### KD-5. Transcription: whisper.cpp `whisper-server`, model `small` (q5_1), Spanish forced

A sidecar on `127.0.0.1:8081`, started with **`-l es`** and 6 threads. The API process POSTs 16 kHz
mono WAV and gets text back. Translation is off by default; there is **no `--no-translate` flag**
in the current build (b0f6b6e, ggml 0.18.1) — passing it prints usage and exits 1. `-l es` alone
is what satisfies 8.7.

**Measured on this host, 2026-08-05** — `small-q5_1`, 6 threads, greedy (`-bo 1 -bs 1`), resident
RSS **476 MB**:

| Audio | Encode | Total |
| --- | --- | --- |
| 4.0 s | 5,652 ms | **6.4 s** |
| 11.0 s | 5,776 ms | **7.0 s** |
| 33.0 s | 11,089 ms (2 × 5,544 ms) | **13.6 s** |

**Encode is a fixed cost per 30-second window, not a multiple of the audio length.** Whisper pads
to a full 30 s window regardless of how much speech is in it, so the right unit is *windows*, not
"× realtime" — that framing is deleted from this design because it misleads for exactly the
utterances this app is built around. Three consequences the implementers must design to:

- **Every transcription has a hard ~6.4 s floor.** "Gasté 14 mil en Uber con la tarjeta" is a
  3-second utterance and costs the same ~6 s as a 28-second one. For short input the effective
  throughput is *below* 1× realtime. No UI copy, animation, or affordance may imply otherwise
  (constraint 28), and the phase indicator during transcription (Frontend structure) is what makes
  that floor feel intentional rather than broken.
- **The 32 s audio cap deliberately crosses into a second window**, doubling encode to ~11 s and
  landing a 33 s clip at ~13.6 s. That is inside `STT_TIMEOUT_S=20` with room to spare. The cap is
  **not** reduced to 30 s to stay in one window: that would trade real capability for a cosmetic
  number, and 8.8 already passes at 32 s.
- **8.8 is not at risk.** Worst measured sidecar time is 13.6 s against a 20 s timeout.

**The 8.8 budget is end-to-end, and the client owns the clock.** 8.8 starts when capture ends, so
the sidecar is only one term:

| Segment | Budget |
| --- | --- |
| `decodeAudioData` + `OfflineAudioContext` resample + WAV encode on the phone | ≤ 3 s |
| upload of ~960 KB over LTE | ≤ 4 s |
| whisper sidecar (measured 6.4-13.6 s; `STT_TIMEOUT_S=20`) | ≤ 20 s |
| response + render | ≤ 1 s |
| **worst case** | **28 s** |

The client starts a wall clock at capture end and shows an explicit `transcription_timeout` failure
at **28 s** regardless of what the server is doing (8.4, 8.8). Recording is hard-stopped at 30 s
client-side; the server rejects audio over 32 s.

Rejected:

- **`medium`** — ~1.5 GB resident (estimate; not benchmarked here) and roughly 3× the encode cost
  per window, which against the 5.5 s measured for `small` puts a two-window clip near the 20 s
  timeout. Available as a config change if accuracy proves short and David accepts the wait — but
  see the resident-memory table in KD-6 before choosing it.
- **`base`** — **measured 1.8 s on the same 4 s clip against `small`'s 6.4 s**, so the speed win is
  real and language-independent. Its *quality* is **unvalidated for Spanish**: the only sample
  benchmarked was English audio forced through `-l es`, which produced garbage from both models and
  is therefore no evidence at all about Spanish accuracy. `small` stays the default. Before this
  rung of R9's ladder may be used, someone must transcribe a real Spanish sample containing an
  amount and a payment method and confirm 9.6 and 9.7 still hold.
- **faster-whisper (CTranslate2)** — likely faster than whisper.cpp on CPU, but couples model
  memory into the API process and reintroduces the Python-ABI wheel risk KD-3 just removed.
- **openai-whisper (PyTorch)** — ~2.5 GB of dependencies and several times slower on CPU.
- **Vosk** — genuinely fast and streaming, but weaker Spanish accuracy on numbers and no
  punctuation, and 10.2 asks for the user's words back faithfully.
- **Browser Web Speech API** — free and instant, and it ships the audio to Google. Violates 15.1,
  15.3, 15.4 outright. Named here because it is the obvious thing to reach for.

### KD-6. LLM runtime: Ollama serving `qwen2.5:3b-instruct-q4_K_M`

~2.0 GB of weights, ~2.6 GB resident at 4096 context. Qwen2.5-3B has the strongest Spanish of the
models in this size class and follows "answer only from these facts" instructions reliably.

**Measured on this host, 2026-08-05** — Ollama 0.32.6, CPU only (`total_vram = 0 B`):

| Case | Prompt eval | Generation | Wall |
| --- | --- | --- | --- |
| 113-token prompt | 35.8 tok/s | 13.9 tok/s | **6.9 s** |
| 1,915-token prompt | 25.7 tok/s | 10.0 tok/s | **82.1 s** |

Generation is **10-14 tok/s**. **Prompt evaluation is 26-36 tok/s** — below the 40-100 tok/s this
design previously estimated, and it is the dominant cost on anything carrying journal text. Rebuilt
against the context budgets in KD-10:

| Work | Prompt | Generate | Total |
| --- | --- | --- | --- |
| finance-only question (~500-token prompt, 220 out) | 14-19 s | 16-22 s | **~30-41 s** |
| journal question (1,200-token context, ~1,400 total, 220 out) | 39-54 s | 16-22 s | **~55-76 s** |
| monthly summary (~1,800-token prompt, 320 out) | 50-69 s | 23-32 s | **~73-101 s** |

**Read these as the tops of their ranges, not the midpoints.** The two measured points show prompt
evaluation degrading with prompt length — 35.8 tok/s at 113 tokens, 25.7 tok/s at 1,915 — so for
the two long-prompt workloads the applicable rate is the slow end. Plan on ~76 s for a journal
question and ~101 s for a summary.

**The two workloads therefore get different budgets, not one.** Questions run against a 110 s
deadline from `created_at` (KD-11), which 76 s clears. Summaries run against
`LLM_TIMEOUT_SUMMARY_S=300`, because **the summary has no deadline in the spec at all** — 11.15 is
served by the previous month's stored row however long the current one takes, and 11.17 is
guaranteed structurally by the arbiter. Holding a 101-second worst case against a 110-second cutoff
bought nothing and manufactured `failed` rows for an 8% overshoot on single-run benchmarks that R9
itself says are not a p95. It was the same number applied to a criterion that does not govern it.

Two more things follow that downstream roles must not undo:

- **The 1,200-token journal budget is load-bearing, not a round number.** At 26 tok/s the original
  2,000-token budget would have been ~77 s of prompt evaluation *before the first token*, putting a
  journal question near 100 s against a 110 s timeout. Raising it back is the fastest way to break
  11.12.
- **The 120-second bound is a journal-question bound, not a general one.** A finance question —
  which is most of what gets asked — measures near 7 s at short prompt lengths and ~30-41 s at the
  budgeted size. That is genuinely good, and no copy should apologise for it.

Rejected:

- **Qwen2.5-7B / Llama-3.1-8B at Q4** — ~4.7-5 GB resident leaves almost nothing for whisper, and
  at ~4 tok/s a monthly summary takes over a minute. Better answers, but it breaks the RAM budget
  and crowds 11.12.
- **Llama-3.2-3B-Instruct** — same footprint, weaker Spanish.
- **Phi-3.5-mini** — strong reasoning, noticeably weaker Spanish output quality.
- **Gemma-2-2b-it** — smaller and good Spanish, but weaker at holding a table of figures without
  drifting.
- **Qwen3-4B-Instruct-2507 Q4_K_M (~2.5 GB)** — the documented upgrade if 3B answers read as
  vague. Not the default only because thinking-variant confusion and a larger footprint are
  avoidable risk on day one.
- **llama.cpp `llama-server` directly** — equivalent quality and more control over threads and
  context, but Ollama gives model management, resident-model keep-alive, and an OpenAI-compatible
  endpoint out of the box. It is a drop-in alternative behind the same interface (KD-7).

`OLLAMA_KEEP_ALIVE=-1` keeps the model resident: a reload on this hardware costs several seconds
and would land inside the user's wait.

**Total resident-memory budget. The denominator is 5.3 GiB, not 6.7 GB.** Ollama's own startup log
on this host reports `total="13.1 GiB" available="5.3 GiB"` — the spec's ~6.7 GB figure was
measured at a different moment and is the more optimistic of the two. Budget against the smaller
one. Both models are pinned simultaneously and permanently, so this must add up rather than be
reasoned about component by component:

| Process | Resident |
| --- | --- |
| Ollama + Qwen2.5-3B Q4_K_M @ 4096 ctx (`KEEP_ALIVE=-1`) | ~2.6 GB |
| whisper-server + `small` q5_1 | **476 MB (measured)** |
| API process (CPython 3.12, FastAPI, SQLite page cache) | ~0.25 GB |
| `tailscaled` | ~0.08 GB |
| **total** | **~3.41 GB of 5.69 GB (= 5.3 GiB), leaving ~2.28 GB** |

Units, because this table is what the model ladder will be planned against: **5.3 GiB is 5.69 GB**,
and the subtraction is done in GB throughout. The reading is also a **pre-load** one — it comes
from Ollama's startup log, before either model is resident — which makes the table self-checking:
once both are loaded, `available` should read roughly 2.3 GB, and if it does not, one of these
rows is wrong.

The consequence is sharper than it looked at a 6.7 GB denominator: the two documented upgrade
paths — whisper `medium` (+~1.0 GB) and Qwen3-4B-Instruct-2507 (+~0.6 GB) — are each individually
affordable within ~2.28 GB of headroom and are **not both** affordable alongside a browser and a
desktop session. If R3 and R9 both bite, exactly one of the two gets upgraded.

### KD-7. Both AI layers sit behind provider interfaces whose default speaks OpenAI-compatible HTTP

Two internal interfaces, each with exactly one concrete adapter today:

```
LLMProvider:            health() · generate(messages, max_tokens, temperature, on_token, cancel) -> text
TranscriptionProvider:  health() · transcribe(wav_bytes, language, cancel) -> {text, duration_ms, no_speech}
```

Selected at startup from config:

```
LLM_PROVIDER=openai_compatible   LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_MODEL=qwen2.5:3b-instruct-q4_K_M
LLM_DEADLINE_ANSWER_S=110        LLM_MIN_START_BUDGET_S=30      # deadline from job created_at
LLM_TIMEOUT_SUMMARY_S=300        # wall-clock; the summary has no spec deadline
LLM_MAX_TOKENS_ANSWER=220        LLM_MAX_TOKENS_SUMMARY=320
STT_PROVIDER=whispercpp_http     STT_BASE_URL=http://127.0.0.1:8081
STT_MODEL=small                  STT_TIMEOUT_S=20        MAX_AUDIO_S=32
```

Because the default LLM adapter speaks the OpenAI chat-completions shape, Ollama, llama.cpp
`llama-server`, LM Studio and vLLM are all reachable by changing `LLM_BASE_URL` and `LLM_MODEL` —
no code. A genuinely different API needs one new adapter module and nothing else.

**The boundary rule, which Reviewer should check:** no module outside `providers/` may reference
Ollama, whisper.cpp, a model name, or a provider-specific field. Callers see only the two
interfaces above.

Rejected: **calling the sidecars inline from request handlers** (fast to write, and it welds the
app to today's runtime — the exact thing this design was asked to prevent); **a plugin/entry-point
registry** (indirection for a set of two).

### KD-8. Voice → structured expense: deterministic parser first, LLM only for category

This is where the product's core promise is won or lost. Layers:

**Layer 0 — transcription** (measured 6.4-13.6 s, with a hard ~6.4 s floor even for a three-second
sentence — see KD-5 — and bounded end-to-end by the 8.8 budget there).

**Layer 1 — deterministic Spanish extractor**, sub-millisecond, no model:

- *Amount* — digit forms with Colombian grouping (`14.000`, `14000`, `14 000`, `14,000`) and
  spoken forms (`catorce mil`, `14 mil`, `mil quinientos`, `un millón doscientos mil`), resolved by
  a Spanish numeral grammar covering 0-999,999,999. This **must** be rules: 2.4 and 9.6 are
  pass/fail criteria and an LLM is flaky on precisely this.
- *Payment method* — accent- and case-insensitive matching of the transcript against the user's
  *actual* payment-method names plus a seeded alias table ("con la tarjeta de crédito" → `Tarjeta
  de crédito`, "en efectivo"/"en plata" → `Efectivo`). Never invents a method (9.7, 9.2).
- *Category* — the same matching against the user's *actual* categories plus a seeded Spanish
  lexicon (`uber`, `taxi`, `bus`, `gasolina` → `Transporte`; `almuerzo`, `café`, `restaurante` →
  `Comida`). Constrained to existing categories by construction (9.3).
- *Description* — the transcript verbatim, trimmed on a word boundary to the 1,000-character
  contract limit if longer, with `description_truncated: true` set on the draft. **Why this rather
  than a bigger field:** 32 s of Colombian Spanish runs 500-800 characters and the old 500-cap
  would have rejected a confirmed voice expense at the final step, on a field the user never
  typed. The full transcript is always returned separately in `transcript`, so nothing is lost —
  the user can paste back or edit before confirming.

**Layer 2 — optional LLM category assist**, only when Layer 1 left category null. A separate,
non-blocking request (`POST /api/expenses/suggest-category`) with `max_tokens=8`, a 6-second hard
cap, and a prompt whose only legal outputs are the user's existing category names or `NINGUNA`.
Anything not in that list is discarded and the field stays empty.

Layer 1 and Layer 2 report provenance through **one** vocabulary — `"rules" | "llm" | "none"` —
used identically by `ExpenseDraft.resolved_by` and by `/suggest-category`'s `source`. The client
calls the assist endpoint exactly when `resolved_by.category == "none"`; there is no separate
flag saying the same thing twice.

**Latency consequence, which is the whole point:** the transcribe response carries the transcript
*and* the rule-derived draft together. The user sees a filled form the moment the transcript
appears. The LLM is never between David and his pre-filled form.

**When it is ambiguous or wrong:**

- Two or more amount candidates with equal cue strength → amount is `null`, not a guess (9.2).
- Nothing matched for method or category → `null`, visibly marked as needing input (9.2).
- Layer 2 returns a suggestion → the frontend auto-fills it **only if the user has not touched
  that field**, visibly labelled *sugerido*. It never overwrites an edit (9.4).
- Anything wrong → the user fixes it in the confirmation form, which is mandatory (8.6). Nothing
  is saved without it.

**Structural guarantee:** there is no endpoint that turns audio into a saved record. `/api/voice/
transcribe` only returns text and a draft; creation goes through `POST /api/expenses` or `POST
/api/journal` exactly as the manual path does (9.5, 10.4, 8.3, 8.6).

Rejected: **LLM-only parsing** (at the measured 26-36 tok/s prompt and 10-14 tok/s generation, a
parse prompt plus a JSON field extraction adds **~10-14 s** to every capture, on top of the ~6.4 s
transcription floor, and is unreliable on
`catorce mil` — it attacks the app's reason for existing); **rules-only with no assist** (leaves
category empty more often than necessary, costing a tap when the LLM could have saved it for
free); **a fine-tuned local model** (no training capacity on this hardware, and A22-scale data).

### KD-9. Journal audio is never post-processed

For `context=journal` the transcribe endpoint returns the raw transcript and no draft. The LLM is
not consulted, not for cleanup, not for punctuation, not for anything. 10.2 is enforced by the
absence of a code path, not by a prompt instruction.

### KD-10. Insights: the LLM phrases, SQL computes

A question flows through four deterministic stages before any generation:

1. **QuestionRouter** (rules) — resolves the period from a Spanish lexicon (`este mes`, `el mes
   pasado`, `julio`, `julio de 2025`, `esta semana`, `la semana pasada`, `hoy`, `ayer`, `este
   año`) and the domain (finance keywords vs journal keywords; both, or neither → both).

   **A period it cannot resolve is a failure, not a default.** The router runs two passes: a
   *temporal-cue detector* (month names, `semana`, `mes`, `año`, `día`, `quincena`, `trimestre`,
   `desde`, `hasta`, `últimos`, `pasado`, `anterior`, any `20\d\d`) and the resolver above. If a
   cue is present but nothing resolves — "en los últimos tres meses", "desde que empecé", "la
   primera quincena" — the job terminates with `period_unrecognised` and the UI asks him to
   rephrase. Only a question with **no** temporal cue at all defaults to the current month, and in
   that case `facts.period_label` states the assumed period so the answer labels itself.

   This exists because a correct figure for the wrong period is exactly the failure 11.11 guards
   against, and NumericGuard cannot catch it — the number *is* in the fact set. Silently
   answering about March when he asked about the last three months is the worst outcome available
   to this feature, and it would look like a good answer.
2. **FactBuilder** — SQL aggregates for that range: total, per-category amounts and percentages,
   per-method totals, expense count, distinct days, top expenses; plus journal excerpts when the
   domain includes the journal, under a **1,200-token budget** (prompt evaluation measures 26-36
   tok/s on this host, so every 100 tokens of context costs ~3-4 s before generation starts — an
   unbounded journal context is the difference between a minute and never). See KD-6: this budget
   is what keeps a journal question inside 11.12 and must not be raised.

   **Journal selection differs by job kind, and truncation is never silent:**
   - *Questions* — entries in range, newest first, until the budget is spent.
   - *Monthly summaries* — `domain="both"` always (11.14 requires spending **and** journal). One
     excerpt per day, oldest first, spread across the whole month, each entry trimmed to ~300
     characters, until the budget is spent. Newest-first would make a summary of a month's writing
     into a summary of its last week.
   - Both record `journal_entries_considered`, `journal_entries_used` and `journal_truncated` in
     `facts`. When `journal_truncated` is true the prompt requires the text to say it read part of
     the period's writing, and the client **must** surface the two counts (client-side contract) —
     a confidently partial answer that does not admit it is partial is the failure mode here, and
     an obligation stated in one section and offered as an option in another is not a mechanism.
3. **Insufficiency pre-check** — no expenses and no entries in range → return `insufficient_data`
   without calling the model at all (11.3, and it is instant).
4. **NumericGuard** — after generation, every numeric token in the output must appear in the fact
   set after normalisation. A figure that does not is a hallucination. On violation: one retry with
   a stricter prompt, then an explicit failure (11.2, 11.11).

**What is prompt-enforced rather than guarded, stated plainly so QA tests it as judgement.**
NumericGuard covers wrong *numbers*. Two criteria have no mechanism behind them and are carried by
the system prompt alone:

- **11.1** — "no outside facts, advice, or general knowledge presented as being about the user."
  Nothing detects *"deberías reducir tus gastos en restaurantes"*, which is a clean 11.1 failure
  containing no number at all.
- **11.7** — Spanish output. Nothing detects an English-drifting answer.

Both are accepted as prompt-enforced. This is also the **one exception to KD-17**: LLM-generated
text is the only user-visible string the frontend does not own, and it is the only place a
non-Spanish string can reach a screen. If either drifts in practice, the response is the model
ladder in KD-6, not a new guard — a classifier to police a 3B model would cost a second inference
pass inside the same 120 s budget.

Rejected: **letting the model read raw rows and do arithmetic** (a 3B model gets column sums wrong,
and 11.2 makes that a defect, not a quirk); **an LLM-based router** (a second inference round trip
inside a 120 s budget, less predictable than a month-name lookup); **RAG with embeddings** (a
second model resident in RAM to search a few hundred journal entries that a date filter already
narrows).

### KD-11. Long insight work is a job with polling, not a streamed connection

`POST /api/insights/questions` returns `202` with a `job_id` immediately (satisfying "working state
within 1 second", 11.12). The client polls once a second; the job carries `elapsed_ms`, which
visibly changes over time and satisfies constraint 25 on its own. `DELETE` cancels (11.13).

**No LLM-generated text reaches a client before NumericGuard has passed on the complete output.**
`partial_answer` is therefore **not** on the wire. It was, and it was wrong: the guard runs after
generation while a live preview renders during it, so a figure could be shown for forty seconds and
then retracted when the finished text failed validation and the job terminated
`unverifiable_figures`. A number shown and withdrawn was still shown, and 11.2 says figures the
user sees must match the Finances screen.

This is the same ruling as `source` in the Data model, for the same reason: **a field present in
the contract is a field a component will eventually display, so the fix is to not send it.** The
mockup rendered a live unvalidated total precisely because the contract permitted it.

Rejected: **masking numeric runs in the partial** (ships deliberately mangled prose and still
streams unvalidated claims — "gastaste mucho más en Mercado" needs no digits to be wrong);
**running the guard incrementally** (a half-streamed token is not yet a number, so the guard would
have to hold back a tail it cannot size, adding real complexity to the streaming path to rescue a
nice-to-have). `insight_jobs.partial_answer` **stays as a column** for server-side diagnostics —
stored, never serialised.

**Consequence for progress display, which the frontend should keep as it has it.** The API exposes
no completion fraction for generation and cannot: token counts do not map to remaining time at
these rates. So a **bounded** wait whose endpoint is known — recording, hard-stopped at 30 s — may
show a determinate meter, and an **unbounded** wait — transcription, insight generation — shows
elapsed time only. Never a determinate bar for the latter; constraint 28 forbids implying a
completion time nobody knows, and this design has no number to give one.

**A second question is rejected, not queued.** A22 allows one insight at a time and there is one
user; if a question is already `queued` or `running`, `POST` returns `409 busy` and the client
offers to cancel the running one. That is the only condition under which `busy` is emitted. The
`queued` status therefore covers only the sub-second window between `202` and the arbiter picking
the job up — never a wait behind another question.

**11.12's clock starts at request receipt**, not at generation start, and the server enforces it
from `insight_jobs.created_at`. Measuring from generation start would let the user wait
indefinitely while the criterion still passed, which is the kind of compliance that fails a user.

**Because the clock starts there, the answer budget is a deadline, not a duration.** A question's
generation must finish by `created_at + LLM_DEADLINE_ANSWER_S (110 s)`, and time spent waiting in
the arbiter is subtracted from it rather than added to it. Two rules follow, and they are what
close the arithmetic hole a flat 110 s timeout left open:

- The arbiter never starts generation it cannot finish. If the remaining budget when a job reaches
  the front is below **30 s** — the floor for a useful answer at the measured rates — the job
  terminates immediately with `llm_timeout` rather than starting a doomed generation.
- The worst case is therefore bounded at 110 s of *elapsed* time whatever the job waited behind,
  leaving ten seconds for the response. A question queued behind a 13.6 s transcription gets 96 s,
  not 110 s on top of 13.6.

Rejected: **SSE or WebSocket token streaming.** More elegant on a desk, worse on a phone: a
long-lived connection over mobile data drops, and worse, a dropped connection loses the job.
Polling recovers trivially, and because jobs are persisted, David can leave the screen, come back,
and re-attach to a job that is still running (13.3). That is not possible with a stream.

### KD-12. The periodic summary is produced by an in-process scheduler with catch-up on boot

An asyncio task inside the API process ticks every 15 minutes and on startup. Each tick computes
the set of *completed calendar months* between the first recorded data and last month, and enqueues
generation for any that lack a finished summary (A19, A20, 11.14).

**"Lacks a finished summary" is the scan predicate, not "has no row."** Keying on row absence
leaves two months permanently unsummarised, and preemption made both routine rather than rare. A
completed month needs generation when it has **no row**, or a row with `status = 'failed'` and
`attempts < 3`:

- **A cancelled summary deletes its row.** Preemption by interactive work is now the normal
  interruption, and it is not a failure — deleting the row returns the month to the row-absent
  state the scan already handles, and it burns no retry attempt.
- **Startup deletes orphaned `generating` rows.** The arbiter is in-process, so nothing can still
  be generating across a restart; a row left at `generating` by a crash is indistinguishable from
  a cancellation and is treated identically. This is what stops `/latest` reporting "currently
  being produced" forever about work that stopped days ago — reporting progress that is not
  happening is worse than reporting failure (constraint 27).
- **Real failures retry up to three times**, tracked by `attempts` and `last_attempt_at` on the
  row. After the third, the row stays `failed`, `/latest` reports it honestly, and nothing loops.

**If the PC was asleep or off across a month boundary**, the boot scan finds the gap and generates
it in the background. Meanwhile 11.15 still holds, because the *previous* completed summary is a
row in the database and `GET /api/insights/summaries/latest` reads it with no generation. If none
has ever been produced, the endpoint returns an explicit `none` state (11.16).

**An InferenceArbiter, not a bare semaphore, and it covers transcription too.** This is the
correction that makes 11.17 true rather than asserted. A single arbiter in the API process governs
*all* local inference — the LLM and whisper — in two priority classes:

- **Interactive**: voice transcription, on-demand insight questions, category assist. Never waits
  behind background work.
- **Background**: monthly summary generation. Runs only when nothing interactive is active.

When an interactive job arrives, any in-flight **background** job is cancelled immediately and
re-queued from scratch; the interactive job starts without waiting for it to finish. Summaries are
monthly, restartable, and read by nobody at the moment they run, so throwing away partial work
costs nothing a user can perceive.

**Interactive is itself ordered, because three things live in it.** Priority runs
**transcription > question > category assist**, and each pair has one stated outcome:

- **Transcription never waits, and preempts a running question.** 11.4 requires capture to keep
  working normally while insights are loading, and voice capture *is* capture — a transcription
  queued behind a 110-second answer would fail that, and the client's 28-second clock would fire a
  `transcription_timeout` for work never attempted. The preempted question terminates with an
  explicit `preempted` failure, which is a legitimate 11.12 outcome ("an answer **or an explicit
  failure**"), not a silent loss. It is not restarted automatically; the user re-asks.
- **A question waits for a running transcription** — at most the 20 s sidecar timeout, measured
  6.4-13.6 s — and that wait is subtracted from its 110 s deadline rather than added to it (KD-11).
  Transcription is short and bounded; preempting it to start a 76-second answer would trade a
  guaranteed small wait for a broken 8.8.
- **Category assist yields to everything.** Its 6-second cap runs from request receipt, so waiting
  simply produces the `null` result it is already designed to produce (KD-8 Layer 2). It never
  preempts and is never preempted — it is abandoned.
- **Two jobs of the same kind cannot arise.** `409 busy` already prevents a second question, and
  there is one capture session at a time.

This ordering is fixed, not deferred. Two implementers could not otherwise guess the same answer,
and the frontend's timeout handling depends on which one holds.

**Why this is not optional.** The earlier design serialized LLM against LLM only, which left
whisper and Ollama competing for the same 8 cores. Voice expense capture *is* expense capture, so
a summary that slows a transcription is a plain 11.17 failure — and, because the two share one
cause, it is also the most likely way 8.8's budget breaks. One mechanism fixes both.

**Restart thrashing is bounded.** A cancelled summary waits for a **60-second quiet period** — no
transcription and no question — before restarting, so a run of back-to-back captures does not
livelock it. A monthly job that starts an hour late is invisible; 11.15 is served by the
*previous* month's stored row regardless.

Capture, editing and all views touch SQLite only — no inference, no arbiter — so nothing in the
read/write path can be blocked by generation at all.

Rejected: **letting the two runtimes contend and calling it acceptable** (it is a descope of
11.17, which is written as pass/fail, and it would have to go to the human as one); **thread
partitioning instead of preemption** (4 threads each halves interactive speed permanently to solve
a collision that happens a few times a month); **cron or a systemd timer** (a separate entry point
with its own DB connection that cannot see the arbiter — two generations at once on 8 cores is the
failure A22 exists to prevent); **APScheduler** (a dependency for one rule); **generate-on-open**
(explicitly forbidden by 11.15).

### KD-13. Frontend: React + TypeScript + Vite, built to static files the backend serves

One origin, no CORS, no second process in production. TanStack Query for server state — the cache
invalidation it gives is exactly what 4.6 asks for (totals reflect a change without a manual
refresh), and its error/retry states map onto 13.2/13.3/13.5. React Router for the three
destinations.

Rejected: **Next.js / SSR** (a Node server alongside a Python one, for an app with one user and no
SEO surface); **Svelte or vanilla** (fine choices; React wins on the implementer's likely
familiarity and on TanStack Query specifically); **a separately-hosted frontend** (a second origin,
CORS, and a second thing to keep running).

**A shell-only service worker is required — this reverses an earlier "no service worker".** 13.2
says that when the phone cannot reach the server the system shows an explicit "cannot reach your
server" state rather than a blank screen or a silent failure. A TanStack reachability banner only
exists once the SPA has loaded. The most common real instance of 13.2 is David tapping the
home-screen icon while the PC is suspended — and KD-4 says outright that it will be suspended —
which without a cached shell produces Chrome's own network error page. That is precisely what 13.2
forbids, and no other mechanism covers it: Vite's hashed filenames make incidental HTTP-cache
survival unreliable.

Its scope is fixed here and is deliberately narrow:

- **Precaches the built shell only** — `index.html`, hashed JS/CSS, the self-hosted font, the
  manifest and icons. Generated from the Vite build manifest, cache name keyed to the build hash,
  `skipWaiting` + `clients.claim` so a new build takes effect on the next open.
- **`/api/*` is `NetworkOnly`.** No API response is ever cached, ever served stale, ever
  replayed. A stale total is worse than no total in a ledger.
- **No background sync, no write queue, no offline mutation.** A capture attempted while
  unreachable fails and keeps the text on screen (13.5), exactly as before.

**This does not reopen R7 or contradict A15.** A15 rules out an *offline queue* — client-side
storage of unsaved captures and the conflict resolution that follows. Caching a static shell so
the app can render its own error state stores no user data and queues no writes. The app is
exactly as offline-incapable as A15 intends; it just says so in Spanish instead of showing a
browser error page.

Rejected: **no service worker** (fails 13.2's primary case, as above); **a full offline-capable
PWA with a write queue** (that is R7/A15 scope and would need conflict resolution this design does
not have); **relying on HTTP cache headers** (hashed asset names and `index.html` revalidation
make it unreliable exactly when it is needed).

### KD-14. Styling: CSS custom properties + CSS Modules; no UI framework, no chart library

The visual direction is a two-colour palette (white surfaces, violet, and one red reserved for
destruction), one typeface, typography-led hierarchy. A single `tokens.css` makes constraints 1-5,
12, 21 and 22 auditable in one file that Reviewer can read in a minute.

Rejected: **Tailwind** (faster to write, and it disperses a palette constraint across a thousand
class attributes where nobody can check it, and it invites the utility-dense dashboard look
constraint 8 and the Visual Non-Goals rule out); **MUI / Chakra / shadcn** (each brings a design
language that would have to be fought back to "a well-made paper notebook", plus bundle weight on
mobile data); **Recharts / Chart.js for the category breakdown** (constraint 6 requires a text
label and numeric value adjacent to every segment, and constraint 4 forbids a rainbow — that is a
ranked list with proportional violet-tinted bars, which is ~40 lines of CSS and passes contrast
checks that canvas text does not).

The typeface is the frontend's choice, with two hard constraints: an open licence (constraint 14)
and **self-hosted in the repo**. A Google Fonts link would be an external request on every page
load — a 15.3 hazard and a hard failure when the internet is down (15.5).

### KD-15. Audio is converted to canonical WAV in the browser

**The target platform is Android only** (confirmed 2026-08-05, R1), so `MediaRecorder` produces
`audio/webm;codecs=opus` and nothing else. The frontend still decodes the recording with
`AudioContext.decodeAudioData`, resamples to 16 kHz mono via `OfflineAudioContext`, and uploads a
16-bit PCM WAV. Thirty seconds is ~960 KB — one to two seconds on LTE.

The normalisation earns its place on one platform for two reasons that have nothing to do with
container divergence: it removes an **ffmpeg** dependency that is not verified present on the host,
and it gives the backend exactly one input format to validate. No iOS-specific branch is to be
written; whatever robustness falls out of using the standard APIs is free and may stay.

Rejected: **server-side transcode with ffmpeg** (an unverified system binary in the critical path
of the app's headline feature); **streaming audio chunks during recording** (real complexity, and
whisper.cpp is not streaming anyway — the win would be perhaps two seconds).

### KD-16. Gym is a frontend route and nothing else

No table, no endpoint, no model, no seed data. `GET /api/gym` does not exist and must not be
added. The route renders a Spanish placeholder stating the module is not available yet, with no
data-entry control, no empty list, no error (1.3, constraint 20). This is the entire Gym scope, and
any backend work on Gym is scope creep to be rejected at review.

**The capture bar is not rendered on `/gimnasio`.** 1.4 makes the two capture actions available
"for the current module"; Gym has no capture, no endpoint and nothing to send. A voice or manual
button there would be a data-entry control, which 1.3 forbids in as many words. The bottom
navigation stays (constraint 11); the capture bar is a Finances-and-Journal affordance only.

### KD-17. Backend emits error codes; the frontend owns every Spanish string

Error responses carry a machine `code`, a `fields` array for validation failures, and a `details`
object for code-specific machine values that the frontend needs to compose a message (the count in
an `in_use` warning is the only current case). The `message` field is a developer string and
**must never be displayed**. All user-visible copy — labels, errors, empty states, placeholders —
lives in the frontend.

`fields[].reason` draws from a closed set of *reasons*; it never carries a value. A count, an
identifier or a limit goes in `details`, never smuggled through `reason` where the frontend's
reason→Spanish map cannot reach it.

This exists because 1.5 and constraint 23 forbid mixed-language strings anywhere, and the single
most common way that fails is a raw backend error surfacing in a toast. The error-code set below is
closed; the frontend maps all of it. The one string the frontend does not own is LLM-generated
insight text — see the end of KD-10.

---

## Components / Interfaces

### Process topology

```
   phone browser
        │  HTTPS
        ▼
 ┌─────────────────────┐        (tailscale serve :443 → 127.0.0.1:8000)
 │  autonomos-api      │        (uvicorn TLS ${LAN_BIND_ADDR}:8443, LAN fallback)
 │  FastAPI, 1 worker  │
 │  ├ HTTP API /api/*  │
 │  ├ static SPA /     │
 │  ├ scheduler task   │
 │  └ InferenceArbiter │  ← governs whisper AND Ollama (KD-12)
 └──┬────────┬──────┬──┘
    │        │      │
    │        │      └── SQLite  data/autonomos.db  (WAL)
    │        │
    │        └───────── Ollama          127.0.0.1:11434
    └────────────────── whisper-server  127.0.0.1:8081
```

Both sidecars bind loopback only. Only `tailscale serve` and the LAN TLS port accept off-host
connections (13.6, 15.3).

**Four systemd *user* units, none of them root:** `autonomos-api`, `autonomos-whisper`, `ollama`,
and `tailscaled`. Tailscale 1.102.2 is installed as a **non-root userspace-networking daemon**
rather than a system service, because this app needs `tailscale serve` and not full tunnel
routing — which keeps the entire stack inside `$HOME` with nothing owned by root, consistent with
the other three units. **Runbook consequence:** user units need `loginctl enable-linger` to start
at boot without a login session, and that applies to all four including `tailscaled`. Rejected
`nohup` scripts: they do not survive a reboot, and 14.1 plus 13.7 require the thing to just be
there after a restart.

### Repository layout

```
backend/    FastAPI app, SQL migrations, providers/, parsing/, insights/
frontend/   React SPA; builds to frontend/dist, served by the backend
ops/        systemd units, setup scripts, mkcert helper, README-setup.md
models/     gitignored — whisper + GGUF weights
data/       gitignored — autonomos.db, snapshots/
```

`frontend/dist` is the single integration point between the two lanes. `FRONTEND_DIST` is a
backend env var so the frontend implementer never needs to touch backend code, and vice versa.

### Backend modules

| Module | Responsibility |
| --- | --- |
| `api/` | FastAPI routers; request/response models; the error envelope. Contains no business logic. |
| `db/` | Connection setup (WAL, FKs, `synchronous=FULL`), numbered SQL migrations, seed data, nightly snapshot. |
| `repo/` | Query layer for expenses, journal, categories, payment methods, summaries, jobs. Owns the month/day aggregation and largest-remainder percentage rounding. |
| `parsing/` | Spanish numeral grammar, amount extraction, alias matching for categories and payment methods. Pure functions, no I/O, no model. |
| `providers/` | `LLMProvider` and `TranscriptionProvider` interfaces plus the `openai_compatible` and `whispercpp_http` adapters. **The only place vendor names appear.** |
| `insights/` | QuestionRouter, FactBuilder, PromptBuilder, NumericGuard, job runner. |
| `arbiter/` | The InferenceArbiter (KD-12): two priority classes over both sidecars, the interactive ordering transcription > question > category assist, background preemption, the 60-second quiet period, and the answer deadline derived from `created_at`. Every call into `providers/` passes through it. |
| `scheduler/` | Boot catch-up scan, 15-minute tick, monthly summary enqueue, nightly DB snapshot. |
| `clock/` | Local-day and local-month arithmetic in `APP_TZ`. The **only** place calendar boundaries are computed (4.8). |

### Frontend structure

Route shells: `/finanzas` (default landing, 1.2), `/finanzas/mes`, `/finanzas/analisis`,
`/finanzas/ajustes`, `/diario`, `/gimnasio`. Persistent bottom navigation with the three
destinations (1.1, constraint 11) and a per-module capture bar in the thumb zone with *voice* and
*manual* (1.4, constraint 9) — on Finances and Journal only, never on `/gimnasio` (KD-16).

**`/finanzas/ajustes` is where three criteria that had endpoints but no screen live.** `PATCH` and
`DELETE` on categories and payment methods, and `GET /api/export`, all existed in the contract with
nowhere in the UI to invoke them — a gap the mockup pass caught. Renaming (3.3), removing with the
in-use warning (3.4) and exporting (14.2) belong on one quiet settings sub-route inside Finances,
on the same precedent as `/finanzas/analisis`: a sub-route, not a fourth tab, so 1.1's "exactly
three" holds. Creating a category mid-expense (3.2) stays in the form where it is needed; ajustes
is for the maintenance that is not part of capture.

**The insights area lives inside Finances; it is not a fourth destination.** 1.1 requires *exactly*
three top-level destinations and constraint 11 requires those three from every screen, so insights
cannot be a tab. It is `/finanzas/analisis`, reached by a labelled control on the Finances screens
— **and** by a second control in Journal that navigates to the same route, because 11.9 makes
journal questions a first-class use and a journal question discoverable only from Finances is a
question nobody asks. Both are in-module affordances; the navigation stays three.

Route segments are Spanish throughout. A URL is visible in the phone's address bar, and 1.5 covers
text shown anywhere in the interface; one English segment among four Spanish ones is free to avoid
now and awkward to change once bookmarked.

Cross-cutting frontend concerns, called out because they are easy to under-scope:

- **`audio/`** — permission handling, recording with a visible elapsed indicator and a hard stop at
  30 s, cancel, the `decodeAudioData` → 16 kHz mono → WAV pipeline, `AbortController` on the upload
  so 8.9 works, and the client-side 28-second failure clock from KD-5. During transcription it runs
  a **phase-plus-elapsed indicator** — preparing audio, uploading, transcribing, with seconds
  counting — because the request is one blocking round trip with no server-side progress channel,
  and constraint 25 rejects a spinner that could equally mean "hung".
- **`format/`** — the single Colombian peso formatter (`$14.000`) and the single amount *input*
  parser accepting `14.000` / `14000` / `14 000` (2.4, 2.5, constraint 21). One implementation,
  used everywhere.
- **`copy/`** — every Spanish string, including the error-code → message map. No string literals in
  components (1.5, constraint 23).
- **`state/`** — TanStack Query with an explicit reachability state driving the "no puedo alcanzar
  tu servidor" banner (13.2, constraint 18), and mutation error handling that preserves the user's
  typed text and transcript on failure (13.5).

### Data model

Seven tables plus two alias tables. Full DDL is the backend implementer's; the shape is fixed here.

- **`categories`** / **`payment_methods`** — `id`, `name`, `sort_order`, `archived_at`,
  `created_at`. Uniqueness on `name` **among non-archived rows only**.
- **`category_aliases`** / **`payment_method_aliases`** — `(target_id, alias)`, seeded at first
  run, no UI surface. This is what makes 9.7 work on everyday Spanish, and it keeps 9.3 true by
  construction: every alias points at a category that already exists.
- **`expenses`** — `id`, `amount_cop INTEGER NOT NULL CHECK(amount_cop > 0)`, `category_id NOT NULL
  REFERENCES`, `payment_method_id NOT NULL REFERENCES`, `spent_on TEXT (YYYY-MM-DD, local)`,
  `description TEXT NULL`, `source TEXT ('manual'|'voice')`, `created_at`, `updated_at`. The two
  `NOT NULL` FKs are 3.5 enforced by the schema.
- **`journal_entries`** — `id`, `text TEXT NOT NULL`, `written_at TEXT (ISO-8601 local with
  offset)`, `source`, `created_at`, `updated_at`. Separate rows always; nothing merges (6.3).
- **`summaries`** — `id`, `period_kind ('month')`, `period_key ('YYYY-MM')` UNIQUE, `status
  ('generating'|'ready'|'empty'|'failed')`, `text`, `facts_json`, `model`, `generated_at`,
  `attempts INTEGER NOT NULL DEFAULT 0`, `last_attempt_at`, `created_at`. There is no `pending`
  status: a month that should have a summary and has no row *is* pending, which is what the
  scheduler's catch-up scan looks for. A cancelled or crash-orphaned run **deletes** its row rather
  than leaving it at `generating`, returning the month to that pending state; only genuine failures
  persist, and only three times (KD-12). On the wire, `status: "none"` from `/latest` means "no row
  exists at all" and is the only response state without a corresponding row.
- **`insight_jobs`** — `id (uuid)`, `question`, `status ('queued'|'running'|'done'|'failed'|
  'cancelled')`, `partial_answer`, `answer`, `facts_json`, `error_code`, `created_at`,
  `started_at`, `finished_at`. Persisted so a job survives a page reload (13.3).
  `partial_answer` is **server-side diagnostics only and is never serialised to a client** — it
  holds text that NumericGuard has not yet validated (KD-11).
- **`meta`** — `key`/`value`, holds `schema_version`.

**`source` is stored but never rendered.** 9.5 and 10.4 require a voice-captured record to be
indistinguishable from a typed one. `source` is accepted on `POST` and kept for diagnostics, and
it is **omitted from every expense and journal response body** — it appears only in the full JSON
export, which is an archival dump and not a rendered list. A field present in the contract is a
field a component will eventually display; the fix is to not send it.

**Nothing is ever hard-deleted by the system.** Categories and payment methods archive (3.4);
expenses and journal entries are deleted only by explicit user action (14.3). Because categories
are never removed, an expense can never be orphaned and a historical view always resolves the
name it was filed under.

Seed data (3.1): categories *Comida, Transporte, Mercado, Servicios, Salud, Ocio, Hogar, Ropa,
Educación, Otros*; payment methods *Efectivo, Tarjeta de crédito, Tarjeta débito, Transferencia,
Nequi, Daviplata*.

### Time

`APP_TZ=America/Bogota` (UTC-5, no DST). **The server is authoritative for "today" and "this
month"** and computes every boundary in `clock/`. The frontend never derives a day or month
boundary from the device clock — a phone in another timezone would otherwise silently file an
11 pm expense on the wrong day (4.8).

---

## Interface Contract

Base path `/api`. JSON in and out, UTF-8. Amounts are **integers of Colombian pesos, no cents**.
Dates are `YYYY-MM-DD` (local). Timestamps are ISO-8601 with offset (local). All frontend requests
use **relative paths** (KD-2).

**Error envelope**, every non-2xx response:

```json
{ "error": { "code": "validation",
             "message": "developer string, never displayed",
             "fields": [ { "field": "amount_cop", "reason": "must_be_positive" } ],
             "details": {} } }
```

`fields` is present only for `validation`. `details` is an optional object of code-specific machine
values the frontend needs to compose Spanish copy; today its only use is `in_use`, which carries
`{ "affected_expenses": int }`. A count, limit or identifier goes here — never inside `reason`,
whose values are a closed vocabulary the frontend maps directly.

**Closed error-code set** — the frontend maps all of these to Spanish copy:
`validation` · `not_found` · `conflict` · `in_use` · `audio_invalid` · `audio_too_long` ·
`transcription_failed` · `transcription_timeout` · `llm_unavailable` · `llm_timeout` ·
`insufficient_data` · `unverifiable_figures` · `period_unrecognised` · `preempted` · `busy` ·
`internal`.

**Field `reason` values** for `validation`: `required` · `must_be_positive` · `not_an_integer` ·
`too_long` · `future_date` · `blank` · `unknown_id` · `duplicate_name`.

### GET /api/health
- response: `200 { "status": "ok", "server_time": iso8601, "tz": "America/Bogota", "version": string,
             "origins": { "primary": string|null, "lan": string|null } }`
- errors:   none; unreachable server is a transport failure the client renders as the "cannot reach your server" state
- notes:    `origins` are **absolute origins** (scheme + host + port, no trailing path — e.g. `"https://autonomos.tail1a2b3c.ts.net"`, `"https://192.168.1.42:8443"`), read from server configuration (`PUBLIC_URL`, and `LAN_BIND_ADDR` + the TLS port), **never derived from the request**. Either is `null` when that origin is not configured — `lan` is `null` whenever the fallback listener is disabled (KD-2), and a client must treat `null` as "no alternative exists", not as an error.
            This field exists so the client can learn the *other* origin **while the server is reachable**. It is read on success and used on failure; it is never fetched at the moment it is needed, because at that moment nothing is answering. See KD-2 mechanism 1 — including why storing it from the LAN origin cannot work.
- requirements: 13.2, 13.3, 13.8

### GET /api/status
- response: `200 { "transcription": "ok"|"unavailable", "llm": "ok"|"unavailable", "checked_at": iso8601 }`
- notes:    cached ~30 s; never blocks. Drives the visible, explained AI-unavailable state while the rest of the app keeps working.
- requirements: 11.4, 8.4

### GET /api/categories
- query:    `include_archived` boolean, default `false`
- response: `200 { "items": [ { "id": int, "name": string, "sort_order": int, "archived": bool, "in_use_count": int } ] }`
- notes:    seeded non-empty on first run
- requirements: 3.1, 3.4

### POST /api/categories
- request:  `{ "name": string (1..40, trimmed, non-blank) }`
- response: `201 { "id": int, "name": string, "sort_order": int, "archived": false, "in_use_count": int }`
- response: `200` same body, when the name matches an archived row — it is un-archived rather than duplicated
- errors:   `400 validation` (`blank`, `too_long`); `409 conflict` when an active category has that name
- notes:    callable from inside the expense form; creating one must not disturb the draft
- requirements: 3.2

### PATCH /api/categories/{id}
- request:  `{ "name": string (1..40) }`
- response: `200` category object
- errors:   `400 validation`; `404 not_found`; `409 conflict`
- notes:    expenses reference the id, so existing expenses show the new name with no backfill
- requirements: 3.3

### DELETE /api/categories/{id}
- query:    `confirm` boolean, default `false`
- response: `200 { "archived": true, "affected_expenses": int }`
- errors:   `409 { "error": { "code": "in_use", "details": { "affected_expenses": int } } }` when in use and `confirm` is not `true` — the count lives in `details` so the frontend can compose the warning 3.4 requires
- notes:    always an archive, never a row deletion; archived categories vanish from selection and stay attached to historical expenses
- requirements: 3.4

### GET|POST|PATCH|DELETE /api/payment-methods[/{id}]
- shapes:   identical to `/api/categories` in every respect, including the un-archive-on-recreate behaviour and the `confirm` gate
- requirements: 3.1, 3.2, 3.3, 3.4

### POST /api/expenses
- request:  `{ "amount_cop": int (>0), "category_id": int, "payment_method_id": int, "spent_on": date? (default: today in APP_TZ), "description": string? (0..1000), "source": "manual"|"voice" (default "manual") }`
- response: `201 { "id": int, "amount_cop": int, "category_id": int, "category_name": string, "payment_method_id": int, "payment_method_name": string, "spent_on": date, "description": string|null, "created_at": iso8601, "updated_at": iso8601 }`
- errors:   `400 validation` — `amount_cop` `required`/`must_be_positive`/`not_an_integer`; `category_id` `required`/`unknown_id`; `payment_method_id` `required`/`unknown_id`; `spent_on` `future_date`; `description` `too_long`
- notes:    the client sends an integer; it owns parsing `14.000`/`14000`/`14 000` into `14000`. `description` is 1000 characters so a full spoken sentence survives confirmation (KD-8) rather than failing validation on a field the user never typed. `source` is **request-only**: it is stored and never returned, so a voice expense is indistinguishable from a manual one in every response body.
- requirements: 2.1, 2.2, 2.3, 2.4, 2.6, 2.7, 3.5, 9.5

### GET /api/expenses
- query:    `date` (a single day) **or** `month` (`YYYY-MM`); `limit` int ≤200, `offset` int
- response: `200 { "items": [ expense ], "total_count": int }` — newest first, ties broken by `created_at` descending
- requirements: 4.1

### GET /api/expenses/{id}
- response: `200` expense object
- errors:   `404 not_found`
- requirements: 5.1

### PATCH /api/expenses/{id}
- request:  any subset of `{ "amount_cop", "category_id", "payment_method_id", "spent_on", "description" }`
- response: `200` expense object
- errors:   `400 validation` (same reasons as POST); `404 not_found`
- requirements: 5.1, 4.6

### DELETE /api/expenses/{id}
- response: `204` no body
- errors:   `404 not_found`
- notes:    the confirmation step is the client's (constraint 19); the server does not double-confirm
- requirements: 5.2, 4.6

### GET /api/summary/day
- query:    `date` (default: today in `APP_TZ`)
- response: `200 { "date": date, "total_cop": int, "expense_count": int, "items": [ expense ] }`
- notes:    `total_cop` is 0 and `items` empty for a day with nothing — a valid state, not an error
- requirements: 4.1, 4.6, 4.8

### GET /api/summary/month
- query:    `month` (`YYYY-MM`, default: current month in `APP_TZ`)
- response: `200 { "month": "YYYY-MM", "total_cop": int, "expense_count": int, "is_empty": bool,
             "by_category": [ { "category_id": int, "name": string, "amount_cop": int, "percent": int } ],
             "by_payment_method": [ { "payment_method_id": int, "name": string, "amount_cop": int } ] }`
- errors:   `400 validation` on a malformed `month`
- notes:    `by_category` is ordered by `amount_cop` descending, and `percent` values are integers computed by largest-remainder so they sum to **exactly 100** whenever `total_cop > 0`. When `is_empty` is true both arrays are `[]` and `total_cop` is `0` — the client renders an empty state, never a zeroed chart. Archived categories still appear here under the name they were filed under.
- requirements: 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 3.4

### POST /api/journal
- request:  `{ "text": string (non-blank after trim, no maximum), "source": "manual"|"voice" (default "manual") }`
- response: `201 { "id": int, "text": string, "written_at": iso8601, "created_at": iso8601, "updated_at": iso8601 }`
- errors:   `400 validation` — `text` `blank`
- notes:    text is stored byte-exact: line breaks, blank lines, accents, ñ, ¿ and ¡ all survive round-trip, and there is no truncation at any length. Each submission is a new row; nothing merges with an earlier entry on the same day. `source` is request-only and never returned, so a spoken entry is indistinguishable from a typed one in the list (10.4).
- requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 10.4

### GET /api/journal
- query:    `date` (single day) **or** `before` (iso8601 cursor); `limit` int ≤50
- response: `200 { "items": [ journal_entry ], "next_before": iso8601|null }`
- notes:    newest first by `written_at`. An empty `items` for a queried date is the "nothing written on this day" state.
- requirements: 7.1, 7.2, 7.3

### GET|PATCH|DELETE /api/journal/{id}
- PATCH request:  `{ "text": string (non-blank) }`
- PATCH response: `200` journal entry; DELETE response: `204`
- errors:   `400 validation`; `404 not_found`
- requirements: 5.2, 5.3

### POST /api/voice/transcribe
- request:  `multipart/form-data`
  - `audio` — WAV, RIFF PCM 16-bit little-endian, **16000 Hz, mono**, ≤ 32 s (`MAX_AUDIO_S`), ≤ 2 MB
  - `context` — `"expense"` | `"journal"` | `"question"`
- response: `200 { "transcript": string, "audio_ms": int, "elapsed_ms": int, "draft": ExpenseDraft|null }`
- `ExpenseDraft` (present only when `context="expense"`):
  `{ "amount_cop": int|null, "category_id": int|null, "category_name": string|null, "payment_method_id": int|null, "payment_method_name": string|null, "description": string (≤1000), "description_truncated": bool, "resolved_by": { "amount": "rules"|"llm"|"none", "category": "rules"|"llm"|"none", "payment_method": "rules"|"llm"|"none" } }`
- errors:   `415 audio_invalid` (not the required WAV shape); `413 audio_too_long`; `422 transcription_failed` (nothing usable, silence, or a known whisper silence-hallucination); `504 transcription_timeout`; `503 llm_unavailable` is **never** returned here — this endpoint does not call the LLM
- notes:    audio is held in memory and forwarded to the sidecar; it is never written to disk and never leaves the host. For `journal` and `question` the transcript is returned verbatim with no rewriting, summarising, or translation. A client abort (`AbortController`) cancels sidecar work. **This endpoint writes nothing to the database.** `draft.description` is the transcript trimmed to 1000 characters on a word boundary, with `description_truncated` set — the untrimmed text is always in `transcript`. `resolved_by.<field> == "none"` is the single signal that a field needs input; the client calls `/suggest-category` when `resolved_by.category == "none"`. The client's own 28-second clock (KD-5) governs 8.8, not this response.
- requirements: 8.2, 8.3, 8.4, 8.6, 8.7, 8.8, 8.9, 9.1, 9.2, 9.6, 9.7, 10.1, 10.2, 11.10, 15.1

### POST /api/expenses/parse
- request:  `{ "text": string }`
- response: `200 ExpenseDraft` (same shape as above)
- notes:    the rule layer only, no model, sub-millisecond. It exists as a test seam: the Spanish numeral grammar and alias matching behind 9.1/9.2/9.6/9.7 must be testable without audio, and QA needs a way to exercise `catorce mil` without recording it. **The frontend must not expose a typed natural-language expense path** — every criterion in Requirement 9 begins "WHEN the user *speaks*", and a second, untested capture mode is not in scope.
- requirements: none — internal test seam for the parser behind 9.1, 9.2, 9.6, 9.7; those criteria are served by `/api/voice/transcribe`

### POST /api/expenses/suggest-category
- request:  `{ "text": string }`
- response: `200 { "category_id": int|null, "category_name": string|null, "source": "rules"|"llm"|"none" }`
- errors:   never fails the caller — an unavailable or slow model yields `{ "category_id": null, "source": "none" }` with `200`
- notes:    hard 6 s cap, `max_tokens=8`. `source` uses the same `"rules"|"llm"|"none"` vocabulary as `ExpenseDraft.resolved_by`, so the client can merge the result into the draft without translating between two spellings of one concept. The result is validated against the user's existing categories; anything else is discarded. The client applies it **only if the category field is still untouched**, labelled *sugerido*. This call runs at interactive priority (KD-12) and does not wait behind a summary.
- requirements: 9.2, 9.3

### POST /api/insights/questions
- request:  `{ "question": string (1..500, non-blank), "source": "text"|"voice" }`
- response: `202 { "job_id": string (uuid), "status": "queued", "created_at": iso8601 }`
- errors:   `400 validation`; `503 llm_unavailable` when the provider health check is failing; `409 busy` when a question is already `queued` or `running` — the only condition that emits `busy`
- notes:    returns immediately so the client can show a working state inside 1 second. A22 allows one question at a time, so a second is rejected rather than queued and the client offers to cancel the running one. **The 120-second bound of 11.12 is measured from `created_at`, not from generation start**, and the server enforces it. Insights are strictly read-only — no handler on this path writes to `expenses` or `journal_entries`.
- requirements: 11.5, 11.6, 11.8, 11.9, 11.10, 11.12

### GET /api/insights/questions/{job_id}
- response: `200 { "job_id": string, "status": "queued"|"running"|"done"|"failed"|"cancelled",
             "question": string, "elapsed_ms": int, "answer": string|null,
             "facts": { "period_label": string, "period_start": date, "period_end": date, "period_assumed": bool,
                        "domain": "finances"|"journal"|"both",
                        "total_cop": int|null, "expense_count": int|null,
                        "by_category": [ { "name": string, "amount_cop": int, "percent": int } ]|null,
                        "journal_entries_considered": int|null, "journal_entries_used": int|null,
                        "journal_truncated": bool }|null,
             "error_code": string|null, "created_at": iso8601, "finished_at": iso8601|null }`
- errors:   `404 not_found`
- notes:    poll at ~1 s. `elapsed_ms` changes over time, which is what gives the UI genuine progress rather than a static spinner; it is the **only** progress signal, and no completion fraction exists or may be implied. **`answer` is `null` until the job is `done`** — no generated text is ever returned mid-flight, because NumericGuard has not yet run on it (KD-11). Terminal `error_code` values: `insufficient_data` (too little recorded data to say anything), `period_unrecognised` (the question names a period the router cannot resolve — answering about a different period would be exactly the fabrication 11.11 forbids), `unverifiable_figures` (a figure was produced that the recorded data does not support — surfaced as "cannot answer", never as a fabricated number), `llm_timeout` (the 110 s deadline from `created_at` elapsed, or too little of it remained to start), `preempted` (a voice capture took priority — KD-12; the job is not restarted automatically and the client should invite re-asking), `llm_unavailable`. `period_assumed` is true when the question named no period and the current month was used, so the client can label what it answered about. `journal_truncated` with the two counts says the context was cut; the client **must** surface it and the answer text is also required to admit it. `answer` being Spanish and free of outside facts (11.7, 11.1) is **prompt-enforced, not guarded** — see the end of KD-10.
- requirements: 11.1, 11.2, 11.3, 11.5, 11.7, 11.8, 11.9, 11.11, 11.12

### DELETE /api/insights/questions/{job_id}
- response: `204` no body
- errors:   `404 not_found`
- notes:    stops generation and releases the arbiter. Saved data is untouched — there was never anything to touch.
- requirements: 11.6, 11.13

### GET /api/insights/summaries/latest
- response: `200 { "status": "ready", "period_kind": "month", "period_key": "YYYY-MM", "period_label": string, "text": string, "generated_at": iso8601, "model": string, "facts": {…as above} }`
- response: `200 { "status": "generating", "period_key": "YYYY-MM", "period_label": string, "started_at": iso8601 }`
- response: `200 { "status": "empty", "period_key": "YYYY-MM", "period_label": string }` — the period completed with no data
- response: `200 { "status": "none" }` — no summary has ever been produced
- response: `200 { "status": "failed", "period_key": "YYYY-MM", "error_code": string }`
- notes:    **reads a stored row; never triggers generation.** Always returns instantly. The four non-`ready` states are distinct on the wire precisely so the UI can render them as three distinguishable surfaces plus a failure. `status: "none"` is the only state with no corresponding row. The summary always covers spending **and** journal (`facts.domain` is always `"both"`, journal excerpts selected per KD-10 stage 2), and `facts.journal_truncated` says when a month's writing did not fit.
- requirements: 11.14, 11.15, 11.16, 11.18, 11.7

### GET /api/export
- response: `200 application/json`, `Content-Disposition: attachment` — a lossless dump: `{ "exported_at": iso8601, "schema_version": int, "categories": [...], "payment_methods": [...], "expenses": [...], "journal_entries": [...], "summaries": [...] }`
- notes:    **the only export endpoint.** Category and payment method appear as ids *and* names, so the file is readable in any text editor with no reference to this app. CSV exports were cut at the Approve Plan gate on 2026-08-05 — the JSON dump already satisfies 14.2 and each CSV would have held only half the data.
- requirements: 14.2

### Client-side contract (no server endpoint)

These are frontend-only obligations. They are listed here so requirement coverage is computable
across the whole design, not only across the HTTP surface.

- **App shell** — exactly three top-level destinations, always visible and one interaction away;
  the app lands on Finances/Today with no splash, selection, or setup step; both capture actions
  available within the current module, on Finances and Journal. The insights area is reached from
  inside Finances and Journal at `/finanzas/analisis` and is **not** a fourth destination.
  `requirements: 1.1, 1.2, 1.4, 11.15`
- **Gym placeholder** — a route with a Spanish "not available yet" message, no data-entry control,
  no empty list, no error, **and no capture bar**. No API call of any kind. `requirements: 1.3`
- **Spanish everywhere** — all copy in the frontend, including the error-code map; no backend
  `message` field is ever rendered. `requirements: 1.5`
- **Amount input and display** — one parser accepting `14.000` / `14000` / `14 000` → `14000`; one
  formatter emitting `$14.000` everywhere an amount appears. `requirements: 2.4, 2.5`
- **Four-interaction capture budget, and the control pattern that makes it reachable** — from the
  default screen the sequence is: open the manual form (1), type the amount, choose a category (2),
  choose a payment method (3), save (4). Exactly four, with **zero slack**, so the pattern is
  prescribed rather than left to discovery: category and payment method are **inline single-tap
  chips**, laid out as wrapping rows inside the form. A native `<select>`, a modal picker, or a
  bottom sheet is two interactions each (open, then choose), which makes the total six and fails a
  pass/fail criterion — this is the obvious way to build the form and it is the wrong one.
  The chips must fit ten seeded categories and six payment methods at ≥44×44 px inside a 390 px
  viewport with no horizontal scrolling (constraints 7, 10); wrapping rows with vertical scroll is
  how that resolves. The "create new" affordance (3.2) is an extra chip opening an inline field —
  it is outside the four, being the exceptional path, not the daily one. If an implementer needs
  slack, the one interaction available to reclaim is the form-opening tap: putting the amount field
  directly on the default screen removes it. `requirements: 2.8, 3.2`
- **Destructive confirmation** — expense and journal deletion each present a confirmation step
  before the `DELETE` call. `requirements: 5.2`
- **Settings screen (`/finanzas/ajustes`)** — the screen for maintenance that is not capture:
  rename a category or payment method and see the new name on existing expenses; remove one, with
  the in-use warning composed from `error.details.affected_expenses` and a confirmation before the
  `confirm=true` retry; and download the full export. A sub-route inside Finances, reached from the
  Finances screens; the bottom navigation still carries exactly three destinations.
  `requirements: 3.3, 3.4, 14.2`
- **Voice capture UI** — unmistakable "listening now" state distinct from idle, with stop and
  cancel; cancel discards locally and issues no request; microphone permission denial is explained
  and leaves the manual path fully working; an in-flight transcription can be abandoned for the
  manual form via `AbortController`. `requirements: 8.1, 8.3, 8.5, 8.9`
- **Explicit confirmation before saving voice input** — a transcript or draft becomes a record only
  when the user submits the form. `requirements: 8.6`
- **Edited values win** — a field the user changed is sent as edited; a late category suggestion
  never overwrites a touched field. `requirements: 9.4, 10.3`
- **Live waiting states** — insight waits render `elapsed_ms` from the poll; transcription waits
  render a **client-side** phase-plus-elapsed indicator, since that request has no server progress
  channel; both visibly change rather than spinning. **No generated text is displayed before the
  job is `done`** — there is none on the wire to display (KD-11). A wait with a known endpoint
  (recording, capped at 30 s) may use a determinate meter; an unbounded wait (transcription,
  generation) shows elapsed time only and never a determinate bar. Waits over ~10 s offer cancel
  and say the work is happening on the user's own computer; nothing implies an instant AI response.
  `requirements: 8.8, 11.5, 11.12, 11.13`
- **Partial answers say they are partial** — when `facts.journal_truncated` is true the client
  **must** surface it alongside the answer, using `journal_entries_used` and
  `journal_entries_considered`. This is an obligation, not an option: the prompt is required to make
  the text admit partiality, and this is the only non-prompt mechanism against a confidently
  partial answer. How it is shown is the frontend's craft; whether it is shown is not.
  `requirements: 11.9, 11.11`
- **Reachability** — a designed "no puedo alcanzar tu servidor" state in plain language, which
  **renders on a cold open** because the service worker has the shell cached; automatic recovery
  when the server returns, with nothing lost and no reinstall; a failed save keeps the typed text
  or transcript on screen for retry. `requirements: 13.2, 13.3, 13.5`
- **Arming and offering the other origin** — two obligations that must not be separated:
  1. **On every successful `GET /api/health`**, persist the response's `origins` object in the
     storage of the origin currently being served. Overwrite each time, so a changed LAN address
     self-heals on the next successful load. The write is unconditional — it must **not** be gated
     on which origin is serving, which is the inversion that made the link unreachable in the first
     implementation (`localStorage` is per-origin; writing it from the LAN origin puts it where the
     tailnet origin can never read it).
  2. **On the unreachable state**, read that stored object and offer, as a plain link, every entry
     that is non-null and differs from `window.location.origin`. One tap from the screen the user
     is already looking at (13.8, second clause). When nothing is stored, or every entry matches
     the current origin, render the state without a link — never a broken link, never a guessed
     address, never a fabricated one.
  The **plain-Spanish instruction is unconditional** and does not depend on any of this: the state
  always says what to do instead — join the home network, open the local access — because 13.8's
  first clause is copy, not data, and must hold on first run too.
  `requirements: 13.2, 13.8`
- **Browser-only delivery** — a web app plus a web-app manifest for home-screen install; no app
  store; a **shell-only service worker** that precaches the built assets and treats `/api/*` as
  `NetworkOnly`, with no write queue and no cached API responses (KD-13). `requirements: 13.1`

### Non-endpoint guarantees

Properties of the system with no request/response of their own. QA verifies them by inspection or
by an environment test; they are enumerated so no criterion is left unowned.

- **Zero cost** — every dependency (Tailscale personal, Ollama, whisper.cpp, model weights, fonts,
  npm/PyPI packages) is free and requires no payment instrument or account at any step, and no
  function depends on a remote service that could begin charging or shut down.
  `requirements: 12.1, 12.2, 12.4`
- **Summary generation never gets in the user's way** — two mechanisms, because two things could
  get in the way. (1) Capture, editing and every view touch SQLite only; they never enter the
  InferenceArbiter, so nothing in the read/write path can be blocked by generation at all. (2)
  **Voice** capture does use inference, so the arbiter treats transcription as interactive and
  cancels any in-flight summary the moment a transcription starts — a summary can therefore never
  slow a spoken expense or journal entry either. The cancelled summary re-queues after a
  60-second quiet period (KD-12). `requirements: 11.17`
- **Never publicly reachable** — sidecars bind `127.0.0.1`; the API binds `127.0.0.1:8000` plus
  `${LAN_BIND_ADDR}:8443`, a single named LAN interface and never `0.0.0.0`; `tailscale serve`
  (not Funnel) is the only remote path, restricted to David's tailnet. The LAN listener is
  unauthenticated by A6's design, so the home LAN is its access boundary and it is disabled by
  config on any network David does not control. `requirements: 13.6`
- **One-time setup only** — after joining the tailnet and adding the home-screen icon, daily use
  on the primary origin requires no login, connection step, or manual action. Setup also installs
  the fallback icon and grants microphone permission on both origins, so the 15.5 path needs no
  permission prompt when it is needed. Switching to the fallback origin is an outage-recovery
  action, not routine use — see the reading of 13.7 stated in KD-2. `requirements: 13.7`
- **Away-from-home parity** — the same origin and the same endpoints serve mobile data and home
  Wi-Fi; no feature, including insights, is gated on being at home. `requirements: 13.4`
- **Durability** — SQLite WAL with `synchronous=FULL` plus nightly `VACUUM INTO` snapshots; every
  record survives a server or PC restart. `requirements: 14.1`
- **No automatic deletion** — no expiry, archival, or pruning job exists for expenses or journal
  entries. `requirements: 14.3`
- **All processing local** — audio and record content go only to `127.0.0.1` sidecars; the app
  makes no outbound request carrying user data; the frontend loads no remote asset (fonts and
  icons are in the bundle); no account or API key is required to transcribe or to generate; with
  home internet down, both devices on the private network, voice and insights still work.
  `requirements: 15.1, 15.2, 15.3, 15.4, 15.5`

---

## Risks / Tradeoffs

**R1 — Mobile voice capture, REDUCED at the Approve Plan gate on 2026-08-05: the target is
Android only.** This was the top unconfirmed risk and one of its three failure modes is now gone.
What remains: secure context (mitigated by KD-1/KD-2) and `OfflineAudioContext` resampling
behaviour on the actual device. What closed:

- **Container-format divergence.** Android Chrome records `audio/webm;codecs=opus`, one format
  rather than two. KD-15's `decodeAudioData` normalisation stays — it still removes the ffmpeg
  dependency and still guarantees the 16 kHz mono WAV the sidecar wants — but it no longer has to
  straddle two containers, and no iOS-specific handling is to be written.
- **The iOS seven-day eviction of script-writable storage**, which would have dropped KD-13's
  service-worker registration for an unengaged site, cannot apply on Android. Recorded so nobody
  re-litigates it.

*Mitigation, unchanged in priority:* build and test voice on David's Android phone before anything
downstream is trusted — first integration checkpoint, not the last. **QA's matrix is one platform:
Android Chrome.** Cross-platform robustness that costs nothing stays; iOS-specific work stops.

**R2 — Tailscale cold start with home internet down (15.5).** Already-connected nodes keep working
over direct LAN endpoints with cached peer state, but a cold start needs the coordination server.
*Mitigation:* disable key expiry on both nodes; ship the `mkcert` LAN fallback origin as part of
the setup script; QA should test 15.5 with both nodes already up and separately from a cold boot,
and report the two results separately.

**R3 — A 3B model's Spanish answers may read as thin.** The NumericGuard prevents *wrong* figures,
not *unhelpful* prose. *Mitigation:* the swap to Qwen3-4B-Instruct-2507 is a config change (KD-7);
11.3 and 11.11 make "I cannot answer that" a legitimate, passing outcome rather than a defect.

**R4 — CPU contention between whisper and the LLM.** Both want all 8 cores. *Mitigation:* the
InferenceArbiter (KD-12) makes transcription and on-demand questions interactive and summaries
background, and cancels a running summary the moment either arrives — so the LLM and whisper never
run concurrently by design, which is what makes both 11.17 and 8.8 hold. Threads are capped at 6
each so neither starves the desktop session. *Residual:* the arbiter cannot preempt work already
inside Ollama's own request loop instantaneously; expect up to ~1 s of overlap while the
cancellation lands. KD-5's measured worst case of 13.6 s against a 20 s sidecar timeout absorbs
that comfortably.

**R5 — Whisper hallucinates on silence.** Spanish whisper models are known to emit boilerplate
("Subtítulos realizados por…") when given near-silence. Left unhandled, that becomes a journal
entry or a nonsense expense description. *Mitigation:* enforce a minimum speech duration, use the
sidecar's no-speech threshold, and reject known hallucination patterns as `transcription_failed`
(8.4) rather than returning them as a transcript.

**R6 — The rule-based parser will miss phrasings.** Real Colombian speech will produce sentences
the alias tables do not cover, and the answer is an empty field the user fills by hand — correct
per 9.2, but felt as friction. *Mitigation:* the alias tables are data, not code, so coverage
improves by editing seed rows; the LLM assist covers category, the field with the widest surface.
*Accepted tradeoff:* an occasional extra tap in exchange for never waiting on a model to record a
spend.

**R7 — No offline queue (A15).** A dropped connection mid-capture means the save fails. 13.5 keeps
the text on screen, but David must retry while still connected. *Mitigation:* none in this pass —
this is PM's flagged assumption, not an oversight; a real offline queue is separate scope and would
pull in conflict resolution the design deliberately does not have.

**R8 — CLOSED, 2026-08-05.** The Python 3.14 wheel risk is gone: `uv 0.12.2` provisioned CPython
3.12.13 on this host and the stack builds against it. The Docker fallback is not needed.

**R9 — RESOLVED BY MEASUREMENT, 2026-08-05.** The throughput figures behind 8.8 and 11.12 were
estimates; they have now been benchmarked on this host with this stack (Ollama 0.32.6,
whisper.cpp b0f6b6e, both models installed), and KD-5, KD-6 and KD-10 carry the measured numbers.
Both bounds hold with margin: transcription worst case 13.6 s against 20 s, journal question
~55-76 s against 110 s. *What remains:* the numbers are single-run benchmarks, not a p95 under
contention, so the backend implementer should still log `elapsed_ms` for every transcription and
generation from day one. *What changed in the ladder:* whisper `base` is 3.5× faster and its
Spanish quality is **unvalidated** — the benchmark used English audio forced through `-l es`, which
is no evidence about Spanish. That rung needs a real Spanish sample before it may be pulled.

**R10 — Two implementers, one contract, no shared code.** The Interface Contract above is the only
thing keeping the lanes in sync. *Mitigation:* the backend must serve `/openapi.json` and its
shapes must match this document; where they diverge, **this document wins** until Reviewer decides
otherwise. The frontend may develop against a local mock that implements this contract.

**R11 — Tailscale is a third party. RESIDUAL ACCEPTED by the human at the Approve Plan gate on
2026-08-05.** He was shown this section in full — the free tier that could begin charging, the
DERP relay under a literal 15.3 — alongside the costed alternatives below, and chose to keep
Tailscale. This is a decision on the record, not an open risk. The alternatives stay written down
because they are the ladder that gets used if Tailscale ever changes its terms; nothing about
KD-1 or KD-2 changes.

Away-from-home access (13.4) depends on Tailscale, whose personal tier is a free tier of a
commercial service. 12.4 forbids any functionality depending on a remote service that could begin
charging, rate-limiting, or shutting down; that hazard is the reason Cloudflare Tunnel and ngrok
were disqualified, and it applies to Tailscale in the same form. Separately, 15.3 forbids any
request to an external service carrying the user's data; Tailscale traffic is end-to-end encrypted
and its coordination server never holds plaintext, but when a direct peer connection cannot be
established the encrypted stream is relayed through Tailscale's DERP servers. Reading 12.4 and
15.3 literally, this is the one place the design accepts a third party.

What the alternatives cost, so the trade is visible:

- **Self-hosted coordination (Headscale) instead of Tailscale's.** Removes the commercial
  dependency, and the coordination server must itself be reachable from outside the house — which
  means a VPS (a recurring cost, failing 12.1) or the PC itself (unreachable from outside, so it
  solves nothing).
- **Plain WireGuard with a fixed endpoint.** No third party at all, and it needs a public IP or a
  forwarded port on the home router, which 13.6 forbids.
- **Home-network-only.** No third party, no port forwarding, no recurring cost. The app then works
  at home and not on the street, which removes 13.4 — a decision the human took at the Kickoff
  gate, and the one thing here that only he can reverse.

There is no known option that provides away-from-home access with no public exposure and no
third-party coordination. The choice is between accepting a third party for transit, and giving up
13.4.

---

## Deferred Decisions

Left to the Implementers, inside the structural bounds above.

**Backend**
- Table DDL details, index selection, and the exact migration file format.
- The internal shape of the Spanish numeral grammar (a parser, a lookup table, or regexes) — only
  its behaviour on 2.4 and 9.6 is fixed here.
- The wording of every prompt, and the exact normalisation rule inside NumericGuard.
- The alias seed lists' contents beyond the starter sets named above, and the temporal-cue word
  list behind the QuestionRouter's `period_unrecognised` path — only its *behaviour* is fixed.
- Job and summary retention (nothing prunes user records; job rows are not user records).
- Whether the nightly snapshot runs in the scheduler task or a systemd timer.
- How the InferenceArbiter signals cancellation to each sidecar (request abort, or a provider-level
  cancel token) — the priority rules, the interactive ordering, the 60-second quiet period and the
  answer deadline are all fixed; only the plumbing is not.
- Retry backoff shape for a `failed` summary within the three-attempt limit.

**Frontend**
- Component decomposition, the typeface (open licence, self-hosted), spacing and type scale, and
  how the category breakdown renders within constraints 4 and 6.
- Whether the late category suggestion animates in or appears plainly.
- Poll interval tuning around the 1 s baseline, and how "the work is happening on your own
  computer" is phrased.
- The web-app manifest's icon and name, and the Spanish labels for the two home-screen entries.
- The service-worker toolchain (`vite-plugin-pwa` or a hand-written worker) — its *scope* is fixed
  in KD-13 and may not widen.
- The phase labels shown during transcription, and *how* `journal_truncated` is surfaced — *that*
  it is surfaced is an obligation in the client-side contract, not a choice.
- Chip layout, wrapping and ordering within the prescribed inline-chip pattern for category and
  payment method — the pattern itself is fixed by 2.8's zero-slack budget and may not be traded for
  a `<select>`, modal or bottom sheet.

**Resolved before finalising, and how**
- *Non-HTTPS private-network origins block `getUserMedia`, which would have killed voice on the
  phone.* Resolved by making `tailscale serve`'s Let's Encrypt cert the primary origin (KD-1),
  with an `mkcert` LAN origin as the fallback that keeps 15.5 satisfiable (KD-2). This is why
  Tailscale is a design decision and not an ops detail.
- *Whether the voice parse is LLM-driven.* Resolved as layered, rules-first, with the LLM excluded
  from the capture critical path (KD-8). The deciding argument was latency, and the measured rates
  strengthened it: an LLM parse would add ~10-14 s on top of a ~6.4 s transcription floor,
  attacking the exact friction the product exists to remove.
- *What runs the periodic summary and what happens after the PC sleeps.* Resolved as an in-process
  scheduler with a boot catch-up scan over completed months, plus preemptible summary jobs (KD-12).
- *How 11.2 is enforced rather than hoped for.* Resolved by computing every figure in SQL and
  rejecting generated text containing an unverifiable number (KD-10).
- *Audio format on the phone.* Resolved by normalising to 16 kHz mono WAV in the browser, which
  removes an unverified `ffmpeg` dependency and gives the backend one format to validate (KD-15).
  Since the platform was confirmed as Android-only, this is a single-container path.

**Resolved in revision, after artifact analysis**
- *11.17 versus whisper/LLM core contention.* The original semaphore serialized LLM against LLM
  only, leaving voice capture — which is expense capture — exposed to a running summary. Resolved
  by promoting the semaphore to an InferenceArbiter covering both sidecars, with transcription as
  interactive work that preempts summaries (KD-12). Chosen over descoping 11.17, which would have
  cost the human a decision to buy a slower answer to a solvable problem.
- *13.2 on a cold open while the PC is suspended.* Resolved by requiring a shell-only service
  worker (KD-13), reversing the earlier "no service worker". Caching a static shell is not an
  offline queue, so A15 and R7 are untouched.
- *The journal half of the monthly summary.* Resolved: summaries always run `domain="both"`, with
  one excerpt per day spread across the month rather than newest-first, and truncation reported in
  `facts` rather than hidden (KD-10).
- *A voice description longer than the field allowed.* Resolved by raising `description` to 1000
  characters and trimming the draft on a word boundary with `description_truncated`, rather than
  letting a confirmed voice expense fail validation on a field the user never typed (KD-8).
- *Where the insights area lives, given "exactly three destinations".* Resolved as
  `/finanzas/analisis` inside Finances, with a second entry point from Journal so 11.9 is
  discoverable (Frontend structure).
- *An unresolvable period in a question.* Resolved by adding a temporal-cue detector and the
  `period_unrecognised` terminal state, because a correct figure for the wrong period is the exact
  fabrication 11.11 forbids and NumericGuard cannot see it (KD-10).
- *How the LAN fallback origin is actually reached.* Resolved as a second home-screen icon plus a
  link from the unreachable-server state, a certificate naming a DHCP-reserved IP rather than
  `.local`, and microphone permission granted on both origins at setup (KD-2).
- *Whether 11.1 and 11.7 have mechanisms.* Resolved by admitting they do not: both are
  prompt-enforced, stated as such, and are the one exception to KD-17's "frontend owns every
  Spanish string" (KD-10).
- *Corrected latency and memory arithmetic.* KD-5, KD-6 and KD-10 now carry end-to-end budgets and
  a summed resident-memory table, with the context and output budgets tightened (2,000→1,200
  tokens, 320→220 answer tokens) so the corrected figures still fit 11.12.

**Replaced by measurement on this host, 2026-08-05**
- Every throughput and memory figure in KD-5, KD-6 and KD-10 is now **measured, not estimated**,
  on the installed stack (Ollama 0.32.6, whisper.cpp b0f6b6e, `qwen2.5:3b-instruct-q4_K_M`,
  `ggml-small-q5_1.bin`). The three corrections that changed a design fact rather than a number:
  whisper encode is a **fixed cost per 30 s window** (~5.5 s) rather than a multiple of audio
  length, so every transcription has a ~6.4 s floor; prompt evaluation is **26-36 tok/s**, below
  even the corrected estimate, which is what makes KD-10's 1,200-token budget load-bearing; and
  the RAM denominator is **5.3 GiB**, not 6.7 GB.
- `whisper-cli --no-translate` **does not exist** in the current build. KD-5 now specifies `-l es`
  alone, which is what 8.7 needs.

**Resolved in revision 3, after artifact analysis pass 2**
- *Two interactive jobs contending.* The arbiter's classes covered interactive-versus-background
  only. Resolved by ordering interactive itself — transcription > question > category assist — with
  a stated outcome for each pair, and by making the answer budget a **deadline from `created_at`**
  so queueing subtracts from it. That closes the 116-130 s arithmetic a flat 110 s timeout allowed
  against 11.12's 120 s (KD-11, KD-12). Adds the terminal code `preempted`.
- *Summaries that fail or are orphaned are never retried.* Resolved by changing the catch-up scan
  predicate from "no row" to "no finished summary", deleting rows on cancellation and on startup
  sweep, and retrying genuine failures three times (KD-12). The preemption added in revision 2 made
  mid-flight interruption routine, which is what turned this from latent into likely.
- *One timeout for two workloads.* Resolved by splitting it: questions keep the 110 s deadline;
  summaries get `LLM_TIMEOUT_SUMMARY_S=300`, because the summary has no deadline in the spec and
  the tight value only manufactured permanent `failed` rows (KD-6, KD-7).
- *2.8's four-tap budget asserted rather than designed.* Resolved by prescribing inline single-tap
  chips and naming the three patterns that break it, with the viewport and touch-target constraints
  that follow and the one interaction available to reclaim as slack (client-side contract).
- *`journal_truncated` capability versus obligation.* Resolved as an obligation.
- *GiB/GB mixed in the memory subtraction.* Corrected to ~2.28 GB of headroom, with the units
  stated and the pre-load nature of the reading noted so the table checks itself.

**Resolved in revision 4, after the mockup pass**
- *`partial_answer` bypassed NumericGuard.* The guard runs after generation; the contract streamed
  generated text during it, and the mockup rendered an unvalidated peso total exactly as permitted.
  Resolved by removing `partial_answer` from the wire entirely — no LLM-generated text reaches a
  client before the guard has passed on the complete output (KD-11). The column stays for
  server-side diagnostics. Masking digits and incremental validation were both rejected; the
  reasoning is in KD-11.
- *Three criteria had endpoints but no screen.* 3.3, 3.4 and 14.2 were marked covered because
  `PATCH`/`DELETE` on categories and `GET /api/export` exist, and nobody had checked they were
  reachable in the UI. Resolved by recording `/finanzas/ajustes` as a sub-route inside Finances,
  on the `/finanzas/analisis` precedent, with the bottom navigation still carrying exactly three
  destinations. Found by the frontend at mockup time, which is the cheapest place it could have
  been found.

**Resolved in revision 5, after Reviewer CHANGES_REQUESTED (F2)**
- *The LAN-fallback link could never render.* The design asked the unreachable state to offer a
  link to the other origin but never said how that origin's address arrives, and the implementation
  stored it from the LAN origin — where, `localStorage` being per-origin, the tailnet origin that
  renders the failure can never read it. Resolved by putting `origins: { primary, lan }` on
  `GET /api/health`, read on **success** during ordinary use and persisted by whatever origin is
  being served, then read from local storage when the failure renders. The trap that shaped the
  ruling: reading it at failure time is a fetch to a machine that by definition is not answering,
  so the reviewer's suggested shape only works once moved in time (KD-2 mechanism 1).
  A first-run residual is named rather than argued away: 13.8's second clause cannot hold on an
  origin that has never reached the server, and setup owns closing that window.

**Open for verification, not blocking**
- *Spanish accuracy of whisper `base`.* Its speed advantage is measured (1.8 s vs 6.4 s on the
  same clip) but its quality was benchmarked only on English audio forced through `-l es`, so
  nothing is known about its Spanish. The R9 ladder may not use that rung until someone transcribes
  a real Spanish sample containing an amount and a payment method and confirms 9.6 and 9.7.
- *p95 under contention.* The KD-5/KD-6 figures are single-run benchmarks on an otherwise idle
  machine. Log `elapsed_ms` from day one.

**Settled by the human at the Approve Plan gate, 2026-08-05**
- *Tailscale as a third-party dependency* against a literal reading of 12.4 and 15.3 — **kept**,
  residual accepted knowingly. See R11.
- *CSV exports* — **cut.** The JSON dump satisfies 14.2 on its own and each CSV held only half the
  data. `GET /api/export/expenses.csv` and `/journal.csv` no longer exist and must not be built.
- *Nightly `VACUUM INTO` snapshots* (KD-4) — **kept**, with explicit approval. In scope; not to be
  cut later as unmandated work.
- *The target phone is Android.* R1 reduced accordingly; no iOS-specific handling is to be written
  and QA's matrix is Android Chrome only.
- *The ~6.4 s voice floor* (analysis B8) — acknowledged. Voice is the hands-free path, not the
  faster one for a simple expense; KD-5 already forbids any copy implying otherwise.
