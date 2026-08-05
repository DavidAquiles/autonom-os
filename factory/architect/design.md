# Autonom-OS — Technical Design

## Summary

A single-user, self-hosted web app: **React + TypeScript SPA** served as static files by a
**Python FastAPI backend** over **SQLite (WAL)**, with two local AI sidecars —
**whisper.cpp `whisper-server`** for Spanish transcription and **Ollama running
Qwen2.5-3B-Instruct Q4_K_M** for insights. Everything is one machine, four processes,
`127.0.0.1`-bound, managed by systemd user units.

Three decisions carry the design:

1. **Tailscale provides HTTPS, and HTTPS is what makes voice possible at all.** `getUserMedia`
   requires a secure context; a plain `http://` LAN or VPN address is not one. `tailscale serve`
   terminates TLS with a real, phone-trusted cert for a `*.ts.net` name that is reachable only
   from David's own devices. This single choice satisfies away-from-home access (13.4), the
   never-public rule (13.6), and phone microphone access simultaneously.
2. **The voice→expense parse is rule-driven first, LLM-assisted only for category.** Amount,
   payment method and description come out of a deterministic Spanish parser in milliseconds, so
   the pre-filled form appears the instant the transcript does. The 3B model is never in the
   capture critical path; it may only fill an otherwise-empty category, asynchronously, with a
   6-second cap.
3. **The LLM never computes a number.** All figures are aggregated in SQL, injected as facts, and
   the generated text is rejected if it contains a figure that is not in the fact set. That is what
   makes 11.2 ("figures match the Finances screen") enforceable rather than hopeful.

Both AI layers sit behind provider interfaces whose default adapters speak the OpenAI-compatible
wire format, so replacing local inference is a base-URL change.

**The biggest risk is mobile voice capture.** Secure context, `MediaRecorder` codec differences
between Android Chrome and iOS Safari, and Tailscale's behaviour with home internet down (15.5)
all converge on one feature. Section *Risks* names the mitigations; test voice on the real phone
before anything else is trusted.

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
- **Self-signed cert + CA installed on the phone.** Works, but is a fiddly one-time setup (iOS
  requires a second "trust" toggle buried in Settings), and the cert expires on a schedule nobody
  will remember. Retained as a *fallback origin only* — see KD-2.
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
| `https://<host>.local:8443` | uvicorn TLS on `0.0.0.0:8443` | LAN fallback with an `mkcert` CA installed once on the phone |

The LAN fallback exists specifically for **15.5** (home internet down, both devices on the private
network). Tailscale nodes that are already up keep working over direct LAN endpoints with cached
peer state, but a cold start without internet can fail to reach the coordination server. One
mechanism failing a hard acceptance criterion is not acceptable, so there are two.

Consequence for the frontend, and it is not optional: **every API call uses a relative path**
(`/api/...`). No base URL constant, no environment-specific origin, no CORS configuration
anywhere. The same bundle must work under both origins unchanged.

Rejected: making Tailscale the only path (fails 15.5 on a cold start); making the LAN path
primary (fails 13.4, away-from-home use).

### KD-3. Backend: Python 3.12 (pinned) + FastAPI + Uvicorn, single worker

Python because the Spanish number grammar, the SQL fact aggregation, and `sqlite3` all live
naturally there. FastAPI because typed request/response models mirror the Interface Contract
below and emit `/openapi.json`, which is a real integration aid for a frontend implementer who
cannot see the backend code.

**The system Python 3.14.4 is not used.** ML- and Rust-backed wheels (`pydantic-core`, `numpy`)
lag new CPython ABIs, and building them on this box is hours of risk for zero benefit. The backend
provisions CPython 3.12 with `uv python install 3.12` into a project venv.

Rejected: **Node/Express** (would gain nothing — the sidecars are HTTP either way — and loses the
text-processing and stdlib-sqlite fit); **Django** (ORM, admin, migrations framework for five
tables); **Flask** (fine, but no typed models or generated schema); **Docker for the whole app**
(RAM and disk overhead, model-path and audio-path friction, and Ollama-in-Docker duplicates model
storage; kept as the documented escape hatch if `uv` fails on this host).

Uvicorn runs with **exactly one worker**. The scheduler and the LLM semaphore are in-process; a
second worker would duplicate both.

### KD-4. Datastore: SQLite, WAL, `synchronous=FULL`, foreign keys on

One user, a few thousand rows a year, single writer. SQLite is a file, needs no server, needs no
RAM budget, and survives a restart (14.1). The `sqlite3` CLI is absent from the host; irrelevant,
the Python module is present.

`synchronous=FULL` rather than the usual WAL-plus-`NORMAL`: write volume is a handful of rows a
day, so the durability is free, and the machine is a desktop that will be suspended and
occasionally lose power. A nightly `VACUUM INTO data/snapshots/YYYY-MM-DD.sqlite` keeps the last 7
days.

Rejected: **PostgreSQL** (a server process and ~200 MB of the 6.7 GB for one user, no benefit);
**JSON/NDJSON files** (no atomic multi-row updates, aggregation in Python); **DuckDB** (analytics
engine; the aggregation here is trivial and OLTP durability matters more).

Migrations are numbered plain-SQL files applied in order, with the applied version in a `meta`
table. Rejected Alembic: a dependency and a code-generation step for five tables.

### KD-5. Transcription: whisper.cpp `whisper-server`, model `small` (q5_1), Spanish forced

A sidecar on `127.0.0.1:8081`, started with `-l es --no-translate` (8.7) and 6 threads. The API
process POSTs 16 kHz mono WAV and gets text back.

`small` is the size that fits the 30-second bound in 8.8. On 8 AVX2 cores it runs roughly 4-6×
realtime, so a 30-second utterance lands around 6-10 seconds with headroom for contention.

Rejected:

- **`medium`** — ~1.5 GB resident and roughly 1.5-2× realtime; a 30-second clip lands at 15-20 s
  before any contention, which puts 8.8 one bad moment from failing. Available as a config change
  if accuracy proves short and David accepts the wait.
- **`base`** — faster, noticeably weaker on numerals and proper nouns, which is exactly what 9.6
  and 9.7 depend on. Kept as the documented fallback if 8.8 fails on real audio.
- **faster-whisper (CTranslate2)** — likely faster than whisper.cpp on CPU, but couples model
  memory into the API process and reintroduces the Python-ABI wheel risk KD-3 just removed.
- **openai-whisper (PyTorch)** — ~2.5 GB of dependencies and several times slower on CPU.
- **Vosk** — genuinely fast and streaming, but weaker Spanish accuracy on numbers and no
  punctuation, and 10.2 asks for the user's words back faithfully.
- **Browser Web Speech API** — free and instant, and it ships the audio to Google. Violates 15.1,
  15.3, 15.4 outright. Named here because it is the obvious thing to reach for.

### KD-6. LLM runtime: Ollama serving `qwen2.5:3b-instruct-q4_K_M`

~2.0 GB of weights, ~2.6 GB resident at 4096 context, roughly 8-15 tokens/s on 8 cores. A
250-token answer is therefore 20-35 s including prompt processing — inside the 120 s bound of
11.12 with real margin. Qwen2.5-3B has the strongest Spanish of the models in this size class and
follows "answer only from these facts" instructions reliably.

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

### KD-7. Both AI layers sit behind provider interfaces whose default speaks OpenAI-compatible HTTP

Two internal interfaces, each with exactly one concrete adapter today:

```
LLMProvider:            health() · generate(messages, max_tokens, temperature, on_token, cancel) -> text
TranscriptionProvider:  health() · transcribe(wav_bytes, language, cancel) -> {text, duration_ms, no_speech}
```

Selected at startup from config:

```
LLM_PROVIDER=openai_compatible   LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_MODEL=qwen2.5:3b-instruct-q4_K_M   LLM_TIMEOUT_S=110   LLM_MAX_TOKENS=320
STT_PROVIDER=whispercpp_http     STT_BASE_URL=http://127.0.0.1:8081
STT_MODEL=small                  STT_TIMEOUT_S=25
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

**Layer 0 — transcription** (~6-10 s, unavoidable, bounded by 8.8).

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
- *Description* — the full transcript verbatim.

**Layer 2 — optional LLM category assist**, only when Layer 1 left category null. A separate,
non-blocking request (`POST /api/expenses/suggest-category`) with `max_tokens=8`, a 6-second hard
cap, and a prompt whose only legal outputs are the user's existing category names or `NINGUNA`.
Anything not in that list is discarded and the field stays empty.

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

Rejected: **LLM-only parsing** (adds 8-15 s to every capture and is unreliable on
`catorce mil` — it attacks the app's reason for existing); **rules-only with no assist** (leaves
category empty more often than necessary, costing a tap when the LLM could have saved it for
free); **a fine-tuned local model** (no training capacity on this hardware, and A22-scale data).

### KD-9. Journal audio is never post-processed

For `context=journal` the transcribe endpoint returns the raw transcript and no draft. The LLM is
not consulted, not for cleanup, not for punctuation, not for anything. 10.2 is enforced by the
absence of a code path, not by a prompt instruction.

### KD-10. Insights: the LLM phrases, SQL computes

A question flows through four deterministic stages before any generation:

1. **QuestionRouter** (rules) — resolves the period from a Spanish lexicon (`este mes`, `julio`,
   `la semana pasada`, `ayer`; default = current month) and the domain (finance keywords vs
   journal keywords; both, or neither → both).
2. **FactBuilder** — SQL aggregates for that range: total, per-category amounts and percentages,
   per-method totals, expense count, distinct days, top expenses; and for journal questions, the
   entries in range newest-first, truncated to a **2,000-token budget** (prompt processing on CPU
   is ~100-200 tok/s — an unbounded journal context is the difference between 30 s and 5 minutes).
3. **Insufficiency pre-check** — no expenses and no entries in range → return `insufficient_data`
   without calling the model at all (11.3, and it is instant).
4. **NumericGuard** — after generation, every numeric token in the output must appear in the fact
   set after normalisation. A figure that does not is a hallucination. On violation: one retry with
   a stricter prompt, then an explicit failure (11.2, 11.11).

Rejected: **letting the model read raw rows and do arithmetic** (a 3B model gets column sums wrong,
and 11.2 makes that a defect, not a quirk); **an LLM-based router** (a second inference round trip
inside a 120 s budget, less predictable than a month-name lookup); **RAG with embeddings** (a
second model resident in RAM to search a few hundred journal entries that a date filter already
narrows).

### KD-11. Long insight work is a job with polling, not a streamed connection

`POST /api/insights/questions` returns `202` with a `job_id` immediately (satisfying "working state
within 1 second", 11.12). The client polls once a second; the job row carries `elapsed_ms` and
`partial_answer`, so the UI has something that visibly changes over time (constraint 25) and can
even render text as it arrives. `DELETE` cancels (11.13).

Rejected: **SSE or WebSocket token streaming.** More elegant on a desk, worse on a phone: a
long-lived connection over mobile data drops, and worse, a dropped connection loses the job.
Polling recovers trivially, and because jobs are persisted, David can leave the screen, come back,
and re-attach to a job that is still running (13.3). That is not possible with a stream.

### KD-12. The periodic summary is produced by an in-process scheduler with catch-up on boot

An asyncio task inside the API process ticks every 15 minutes and on startup. Each tick computes
the set of *completed calendar months* between the first recorded data and last month, finds any
without a `summaries` row, and enqueues generation (A19, A20, 11.14).

**If the PC was asleep or off across a month boundary**, the boot scan finds the gap and generates
it in the background. Meanwhile 11.15 still holds, because the *previous* completed summary is a
row in the database and `GET /api/insights/summaries/latest` reads it with no generation. If none
has ever been produced, the endpoint returns an explicit `none` state (11.16).

**LLM access is serialized by one semaphore** (A22). Summary jobs are **preemptible**: an
on-demand question cancels an in-flight summary, which is re-queued from scratch. Without that, a
question arriving mid-summary could wait 40 s before it even starts. Capture, editing and all views
touch neither the LLM nor the semaphore, so 11.17 holds structurally.

Rejected: **cron or a systemd timer** (a separate entry point with its own DB connection that
cannot coordinate with the in-process semaphore — two generations at once on 8 cores is the
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

`MediaRecorder` produces `audio/webm;codecs=opus` on Android Chrome and `audio/mp4` on iOS Safari.
Rather than make the backend deal with both, the frontend decodes the recording with
`AudioContext.decodeAudioData` (which handles each browser's own output), resamples to 16 kHz mono
via `OfflineAudioContext`, and uploads a 16-bit PCM WAV. Thirty seconds is ~960 KB — one to two
seconds on LTE.

This removes an **ffmpeg** dependency that is not verified present on the host, and gives the
backend exactly one input format to validate.

Rejected: **server-side transcode with ffmpeg** (an unverified system binary in the critical path
of the app's headline feature); **streaming audio chunks during recording** (real complexity, and
whisper.cpp is not streaming anyway — the win would be perhaps two seconds).

### KD-16. Gym is a frontend route and nothing else

No table, no endpoint, no model, no seed data. `GET /api/gym` does not exist and must not be
added. The route renders a Spanish placeholder stating the module is not available yet, with no
data-entry control, no empty list, no error (1.3, constraint 20). This is the entire Gym scope, and
any backend work on Gym is scope creep to be rejected at review.

### KD-17. Backend emits error codes; the frontend owns every Spanish string

Error responses carry a machine `code` and, for validation, a `fields` array. The `message` field
is a developer string and **must never be displayed**. All user-visible copy — labels, errors,
empty states, placeholders — lives in the frontend.

This exists because 1.5 and constraint 23 forbid mixed-language strings anywhere, and the single
most common way that fails is a raw backend error surfacing in a toast. The error-code set below is
closed; the frontend maps all of it.

---

## Components / Interfaces

### Process topology

```
   phone browser
        │  HTTPS
        ▼
 ┌─────────────────────┐        (tailscale serve :443 → 127.0.0.1:8000)
 │  autonomos-api      │        (uvicorn TLS 0.0.0.0:8443, LAN fallback)
 │  FastAPI, 1 worker  │
 │  ├ HTTP API /api/*  │
 │  ├ static SPA /     │
 │  ├ scheduler task   │
 │  └ LLM semaphore    │
 └──┬────────┬──────┬──┘
    │        │      │
    │        │      └── SQLite  data/autonomos.db  (WAL)
    │        │
    │        └───────── Ollama          127.0.0.1:11434
    └────────────────── whisper-server  127.0.0.1:8081
```

Both sidecars bind loopback only. Only `tailscale serve` and the LAN TLS port accept off-host
connections (13.6, 15.3). Four systemd **user** units: `autonomos-api`, `autonomos-whisper`,
`ollama`, plus the system `tailscaled`. Rejected `nohup` scripts: they do not survive a reboot,
and 14.1 plus 13.7 require the thing to just be there after a restart.

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
| `insights/` | QuestionRouter, FactBuilder, PromptBuilder, NumericGuard, job runner, LLM semaphore. |
| `scheduler/` | Boot catch-up scan, 15-minute tick, monthly summary enqueue, nightly DB snapshot. |
| `clock/` | Local-day and local-month arithmetic in `APP_TZ`. The **only** place calendar boundaries are computed (4.8). |

### Frontend structure

Route shells: `/finanzas` (default landing, 1.2), `/finanzas/mes`, `/diario`, `/gimnasio`,
`/insights`. Persistent bottom navigation with the three destinations (1.1, constraint 11) and a
per-module capture bar in the thumb zone with *voice* and *manual* (1.4, constraint 9).

Cross-cutting frontend concerns, called out because they are easy to under-scope:

- **`audio/`** — permission handling, recording with a visible elapsed indicator, cancel, the
  `decodeAudioData` → 16 kHz mono → WAV pipeline, and `AbortController` on the upload so 8.9 works.
- **`format/`** — the single Colombian peso formatter (`$14.000`) and the single amount *input*
  parser accepting `14.000` / `14000` / `14 000` (2.4, 2.5, constraint 21). One implementation,
  used everywhere.
- **`copy/`** — every Spanish string, including the error-code → message map. No string literals in
  components (1.5, constraint 23).
- **`state/`** — TanStack Query with an explicit reachability state driving the "no puedo alcanzar
  tu servidor" banner (13.2, constraint 18), and mutation error handling that preserves the user's
  typed text and transcript on failure (13.5).

### Data model

Six tables plus two alias tables. Full DDL is the backend implementer's; the shape is fixed here.

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
  ('pending'|'generating'|'ready'|'empty'|'failed')`, `text`, `facts_json`, `model`,
  `generated_at`, `created_at`.
- **`insight_jobs`** — `id (uuid)`, `question`, `status ('queued'|'running'|'done'|'failed'|
  'cancelled')`, `partial_answer`, `answer`, `facts_json`, `error_code`, `created_at`,
  `started_at`, `finished_at`. Persisted so a job survives a page reload (13.3).
- **`meta`** — `key`/`value`, holds `schema_version`.

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
             "fields": [ { "field": "amount_cop", "reason": "must_be_positive" } ] } }
```

**Closed error-code set** — the frontend maps all of these to Spanish copy:
`validation` · `not_found` · `conflict` · `in_use` · `audio_invalid` · `audio_too_long` ·
`transcription_failed` · `transcription_timeout` · `llm_unavailable` · `llm_timeout` ·
`insufficient_data` · `unverifiable_figures` · `busy` · `internal`.

**Field `reason` values** for `validation`: `required` · `must_be_positive` · `not_an_integer` ·
`too_long` · `future_date` · `blank` · `unknown_id` · `duplicate_name`.

### GET /api/health
- response: `200 { "status": "ok", "server_time": iso8601, "tz": "America/Bogota", "version": string }`
- errors:   none; unreachable server is a transport failure the client renders as the "cannot reach your server" state
- requirements: 13.2, 13.3

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
- errors:   `409 in_use { "error": { "code": "in_use", "fields": [ { "field": "affected_expenses", "reason": "<count>" } ] } }` when in use and `confirm` is not `true`
- notes:    always an archive, never a row deletion; archived categories vanish from selection and stay attached to historical expenses
- requirements: 3.4

### GET|POST|PATCH|DELETE /api/payment-methods[/{id}]
- shapes:   identical to `/api/categories` in every respect, including the un-archive-on-recreate behaviour and the `confirm` gate
- requirements: 3.1, 3.2, 3.3, 3.4

### POST /api/expenses
- request:  `{ "amount_cop": int (>0), "category_id": int, "payment_method_id": int, "spent_on": date? (default: today in APP_TZ), "description": string? (0..500), "source": "manual"|"voice" (default "manual") }`
- response: `201 { "id": int, "amount_cop": int, "category_id": int, "category_name": string, "payment_method_id": int, "payment_method_name": string, "spent_on": date, "description": string|null, "source": string, "created_at": iso8601, "updated_at": iso8601 }`
- errors:   `400 validation` — `amount_cop` `required`/`must_be_positive`/`not_an_integer`; `category_id` `required`/`unknown_id`; `payment_method_id` `required`/`unknown_id`; `spent_on` `future_date`
- notes:    the client sends an integer; it owns parsing `14.000`/`14000`/`14 000` into `14000`. A voice-confirmed expense uses this exact endpoint with `source:"voice"` and is otherwise indistinguishable.
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
- response: `201 { "id": int, "text": string, "written_at": iso8601, "source": string, "created_at": iso8601, "updated_at": iso8601 }`
- errors:   `400 validation` — `text` `blank`
- notes:    text is stored byte-exact: line breaks, blank lines, accents, ñ, ¿ and ¡ all survive round-trip, and there is no truncation at any length. Each submission is a new row; nothing merges with an earlier entry on the same day.
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
  - `audio` — WAV, RIFF PCM 16-bit little-endian, **16000 Hz, mono**, ≤ 40 s, ≤ 2 MB
  - `context` — `"expense"` | `"journal"` | `"question"`
- response: `200 { "transcript": string, "audio_ms": int, "elapsed_ms": int, "draft": ExpenseDraft|null }`
- `ExpenseDraft` (present only when `context="expense"`):
  `{ "amount_cop": int|null, "category_id": int|null, "category_name": string|null, "payment_method_id": int|null, "payment_method_name": string|null, "description": string, "needs_category_assist": bool, "resolved_by": { "amount": "rules"|"none", "category": "rules"|"none", "payment_method": "rules"|"none" } }`
- errors:   `415 audio_invalid` (not the required WAV shape); `413 audio_too_long`; `422 transcription_failed` (nothing usable, silence, or a known whisper silence-hallucination); `504 transcription_timeout`; `503 llm_unavailable` is **never** returned here — this endpoint does not call the LLM
- notes:    audio is held in memory and forwarded to the sidecar; it is never written to disk and never leaves the host. For `journal` and `question` the transcript is returned verbatim with no rewriting, summarising, or translation. A client abort (`AbortController`) cancels sidecar work. **This endpoint writes nothing to the database.**
- requirements: 8.2, 8.3, 8.4, 8.6, 8.7, 8.8, 8.9, 9.1, 9.2, 9.6, 9.7, 10.1, 10.2, 11.10, 15.1

### POST /api/expenses/parse
- request:  `{ "text": string }`
- response: `200 ExpenseDraft` (same shape as above)
- notes:    the rule layer only, no model, sub-millisecond. Exists so a typed sentence takes the same path as a spoken one, and so the parser is testable without audio.
- requirements: 9.1, 9.2, 9.6, 9.7

### POST /api/expenses/suggest-category
- request:  `{ "text": string }`
- response: `200 { "category_id": int|null, "category_name": string|null, "source": "rules"|"llm"|"none" }`
- errors:   never fails the caller — an unavailable or slow model yields `{ "category_id": null, "source": "none" }` with `200`
- notes:    hard 6 s cap, `max_tokens=8`. The result is validated against the user's existing categories; anything else is discarded. The client applies it **only if the category field is still untouched**, labelled *sugerido*.
- requirements: 9.2, 9.3

### POST /api/insights/questions
- request:  `{ "question": string (1..500, non-blank), "source": "text"|"voice" }`
- response: `202 { "job_id": string (uuid), "status": "queued", "created_at": iso8601 }`
- errors:   `400 validation`; `503 llm_unavailable` when the provider health check is failing
- notes:    returns immediately so the client can show a working state inside 1 second. Insights are strictly read-only — no handler on this path writes to `expenses` or `journal_entries`.
- requirements: 11.5, 11.6, 11.8, 11.9, 11.10, 11.12

### GET /api/insights/questions/{job_id}
- response: `200 { "job_id": string, "status": "queued"|"running"|"done"|"failed"|"cancelled",
             "question": string, "elapsed_ms": int, "partial_answer": string|null, "answer": string|null,
             "facts": { "period_label": string, "period_start": date, "period_end": date, "domain": "finances"|"journal"|"both",
                        "total_cop": int|null, "expense_count": int|null,
                        "by_category": [ { "name": string, "amount_cop": int, "percent": int } ]|null,
                        "journal_entry_count": int|null }|null,
             "error_code": string|null, "created_at": iso8601, "finished_at": iso8601|null }`
- errors:   `404 not_found`
- notes:    poll at ~1 s. `elapsed_ms` and `partial_answer` both change over time, so the UI has genuine progress rather than a static spinner. Terminal `error_code` values: `insufficient_data` (too little recorded data to say anything), `unverifiable_figures` (a figure was produced that the recorded data does not support — surfaced as "cannot answer", never as a fabricated number), `llm_timeout` (hard stop at 120 s), `llm_unavailable`. `answer` is always Spanish and derives only from the user's own records. `facts` are the verified figures the answer was built from.
- requirements: 11.1, 11.2, 11.3, 11.5, 11.7, 11.8, 11.9, 11.11, 11.12

### DELETE /api/insights/questions/{job_id}
- response: `204` no body
- errors:   `404 not_found`
- notes:    stops generation and releases the LLM semaphore. Saved data is untouched — there was never anything to touch.
- requirements: 11.6, 11.13

### GET /api/insights/summaries/latest
- response: `200 { "status": "ready", "period_kind": "month", "period_key": "YYYY-MM", "period_label": string, "text": string, "generated_at": iso8601, "model": string, "facts": {…as above} }`
- response: `200 { "status": "generating", "period_key": "YYYY-MM", "period_label": string, "started_at": iso8601 }`
- response: `200 { "status": "empty", "period_key": "YYYY-MM", "period_label": string }` — the period completed with no data
- response: `200 { "status": "none" }` — no summary has ever been produced
- response: `200 { "status": "failed", "period_key": "YYYY-MM", "error_code": string }`
- notes:    **reads a stored row; never triggers generation.** Always returns instantly. The four non-`ready` states are distinct on the wire precisely so the UI can render them as three distinguishable surfaces plus a failure.
- requirements: 11.14, 11.15, 11.16, 11.18, 11.7

### GET /api/insights/summaries
- query:    `limit` int ≤12
- response: `200 { "items": [ summary objects, newest period first ] }`
- requirements: 11.15, 11.18

### GET /api/export
- response: `200 application/json`, `Content-Disposition: attachment` — a lossless dump: `{ "exported_at": iso8601, "schema_version": int, "categories": [...], "payment_methods": [...], "expenses": [...], "journal_entries": [...], "summaries": [...] }`
- requirements: 14.2

### GET /api/export/expenses.csv · GET /api/export/journal.csv
- response: `200 text/csv; charset=utf-8` with a UTF-8 BOM, `Content-Disposition: attachment`
- notes:    expenses columns `id,spent_on,amount_cop,category,payment_method,description,source,created_at`; journal columns `id,written_at,text,source`. Category and payment method are written as **names**, so the file is readable with no reference to this app.
- requirements: 14.2

### Client-side contract (no server endpoint)

These are frontend-only obligations. They are listed here so requirement coverage is computable
across the whole design, not only across the HTTP surface.

- **App shell** — three top-level destinations always visible and one interaction away; the app
  lands on Finances/Today with no splash, selection, or setup step; both capture actions available
  within the current module. `requirements: 1.1, 1.2, 1.4`
- **Gym placeholder** — a route with a Spanish "not available yet" message, no data-entry control,
  no empty list, no error. No API call of any kind. `requirements: 1.3`
- **Spanish everywhere** — all copy in the frontend, including the error-code map; no backend
  `message` field is ever rendered. `requirements: 1.5`
- **Amount input and display** — one parser accepting `14.000` / `14000` / `14 000` → `14000`; one
  formatter emitting `$14.000` everywhere an amount appears. `requirements: 2.4, 2.5`
- **Four-interaction capture budget** — from the default screen, a complete expense saves in ≤4
  taps beyond typing the amount (category, payment method, save — date defaults to today).
  `requirements: 2.8`
- **Destructive confirmation** — expense and journal deletion each present a confirmation step
  before the `DELETE` call. `requirements: 5.2`
- **Voice capture UI** — unmistakable "listening now" state distinct from idle, with stop and
  cancel; cancel discards locally and issues no request; microphone permission denial is explained
  and leaves the manual path fully working; an in-flight transcription can be abandoned for the
  manual form via `AbortController`. `requirements: 8.1, 8.3, 8.5, 8.9`
- **Explicit confirmation before saving voice input** — a transcript or draft becomes a record only
  when the user submits the form. `requirements: 8.6`
- **Edited values win** — a field the user changed is sent as edited; a late category suggestion
  never overwrites a touched field. `requirements: 9.4, 10.3`
- **Live waiting states** — transcription and insight waits show progress that visibly changes;
  waits over ~10 s offer cancel and say the work is happening on the user's own computer; nothing
  implies an instant AI response. `requirements: 11.5, 11.12, 11.13`
- **Reachability** — a designed "no puedo alcanzar tu servidor" state in plain language; automatic
  recovery when the server returns, with nothing lost and no reinstall; a failed save keeps the
  typed text or transcript on screen for retry. `requirements: 13.2, 13.3, 13.5`
- **Browser-only delivery** — a web app plus a web-app manifest for home-screen install; no app
  store, no service worker. `requirements: 13.1`

### Non-endpoint guarantees

Properties of the system with no request/response of their own. QA verifies them by inspection or
by an environment test; they are enumerated so no criterion is left unowned.

- **Zero cost** — every dependency (Tailscale personal, Ollama, whisper.cpp, model weights, fonts,
  npm/PyPI packages) is free and requires no payment instrument or account at any step, and no
  function depends on a remote service that could begin charging or shut down.
  `requirements: 12.1, 12.2, 12.4`
- **Summary generation never gets in the user's way** — capture, editing, and every view read and
  write only SQLite and never acquire the LLM semaphore, so a summary generating in the background
  cannot block, slow, or interrupt them; and an on-demand question preempts an in-flight summary
  rather than queueing behind it. `requirements: 11.17`
- **Never publicly reachable** — sidecars bind `127.0.0.1`; the API binds `127.0.0.1` plus the LAN
  TLS port; `tailscale serve` (not Funnel) is the only remote path, restricted to David's tailnet.
  `requirements: 13.6`
- **One-time setup only** — after joining the tailnet and adding the home-screen icon, daily use
  requires no login, connection step, or manual action. `requirements: 13.7`
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

**R1 — Mobile voice capture is the single most likely thing to be discovered broken at QA.**
Three failure modes stack on one feature: secure context (mitigated by KD-1/KD-2),
`MediaRecorder` output differing between Android Chrome and iOS Safari (mitigated by the
`decodeAudioData` normalisation in KD-15, which handles each browser's own output), and
`OfflineAudioContext` resampling behaviour on older devices. *Mitigation:* build and test voice on
David's actual phone before anything downstream is trusted; treat it as the first integration
checkpoint, not the last. **Which phone OS is unconfirmed** — the design works on both, but
knowing it would let the frontend drop one branch and would sharpen the QA plan.

**R2 — Tailscale cold start with home internet down (15.5).** Already-connected nodes keep working
over direct LAN endpoints with cached peer state, but a cold start needs the coordination server.
*Mitigation:* disable key expiry on both nodes; ship the `mkcert` LAN fallback origin as part of
the setup script; QA should test 15.5 with both nodes already up and separately from a cold boot,
and report the two results separately.

**R3 — A 3B model's Spanish answers may read as thin.** The NumericGuard prevents *wrong* figures,
not *unhelpful* prose. *Mitigation:* the swap to Qwen3-4B-Instruct-2507 is a config change (KD-7);
11.3 and 11.11 make "I cannot answer that" a legitimate, passing outcome rather than a defect.

**R4 — CPU contention between whisper and the LLM.** Both want all 8 cores. A transcription
starting during summary generation slows both. *Mitigation:* 6 threads each rather than 8, the
single LLM semaphore, and summary preemption (KD-12). *Residual:* 8.8's 30 s bound has less
headroom under contention than the 6-10 s typical figure suggests.

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

**R8 — Python 3.14 on the host.** Wheels for it are unreliable. *Mitigation:* KD-3 pins 3.12 via
`uv`. *Residual:* if `uv` cannot provision it, the fallback is running the API in a Docker image
with a pinned Python — an accepted, documented detour that costs an afternoon, not a redesign.

**R9 — 8.8's 30 s and 11.12's 120 s are measured on an unloaded machine.** These are the honest
bars, and they were set knowing the hardware, but they have not been measured on this hardware
with these models. *Mitigation:* the backend implementer should log `elapsed_ms` for every
transcription and generation from day one, so the fallback ladder (whisper `small`→`base`, model
3B→smaller) is driven by numbers rather than by feel at QA time.

**R10 — Two implementers, one contract, no shared code.** The Interface Contract above is the only
thing keeping the lanes in sync. *Mitigation:* the backend must serve `/openapi.json` and its
shapes must match this document; where they diverge, **this document wins** until Reviewer decides
otherwise. The frontend may develop against a local mock that implements this contract.

---

## Deferred Decisions

Left to the Implementers, inside the structural bounds above.

**Backend**
- Table DDL details, index selection, and the exact migration file format.
- The internal shape of the Spanish numeral grammar (a parser, a lookup table, or regexes) — only
  its behaviour on 2.4 and 9.6 is fixed here.
- The wording of every prompt, and the exact normalisation rule inside NumericGuard.
- The alias seed lists' contents beyond the starter sets named above.
- Job and summary retention (nothing prunes user records; job rows are not user records).
- Whether the nightly snapshot runs in the scheduler task or a systemd timer.

**Frontend**
- Component decomposition, the typeface (open licence, self-hosted), spacing and type scale, and
  how the category breakdown renders within constraints 4 and 6.
- Whether the late category suggestion animates in or appears plainly.
- Poll interval tuning around the 1 s baseline, and how "the work is happening on your own
  computer" is phrased.
- The web-app manifest's icon and name.

**Resolved before finalising, and how**
- *Non-HTTPS private-network origins block `getUserMedia`, which would have killed voice on the
  phone.* Resolved by making `tailscale serve`'s Let's Encrypt cert the primary origin (KD-1),
  with an `mkcert` LAN origin as the fallback that keeps 15.5 satisfiable (KD-2). This is why
  Tailscale is a design decision and not an ops detail.
- *Whether the voice parse is LLM-driven.* Resolved as layered, rules-first, with the LLM excluded
  from the capture critical path (KD-8). The deciding argument was latency: an LLM parse would add
  8-15 s to every capture, attacking the exact friction the product exists to remove.
- *What runs the periodic summary and what happens after the PC sleeps.* Resolved as an in-process
  scheduler with a boot catch-up scan over completed months, plus preemptible summary jobs (KD-12).
- *How 11.2 is enforced rather than hoped for.* Resolved by computing every figure in SQL and
  rejecting generated text containing an unverifiable number (KD-10).
- *Audio format across Android and iOS.* Resolved by normalising to 16 kHz mono WAV in the browser,
  which also removes an unverified `ffmpeg` dependency (KD-15).

**Open for verification, not blocking**
- *Which phone OS David uses.* The design covers Android Chrome and iOS Safari; confirming it lets
  the frontend drop one audio branch and lets QA test the real target. See R1.
- *Measured latency of `small` whisper and Qwen2.5-3B on this exact host.* Instrument from day one
  (R9); the fallback ladder is already chosen, only the trigger point is unknown.
