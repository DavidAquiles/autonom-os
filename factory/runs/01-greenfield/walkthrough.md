# Autonom-OS — walkthrough

A Spanish, mobile-first personal tracker that runs entirely on your own PC:
**Finanzas**, **Diario**, and a **Gimnasio** placeholder. Capture by typing or by
voice; ask a local AI questions about your own records.

Built from `description.md` in one factory run. Baseline `247f6b044` → `HEAD`.

---

## What was built

- **`backend/`** — FastAPI + SQLite (WAL, `synchronous=FULL`). Every Interface
  Contract operation, no more and no fewer — a conformance test asserts the
  generated OpenAPI surface *equals* the contract, so a missing endpoint and an
  extra endpoint both fail the build. **261 tests.**
- **`frontend/`** — React 18 + TypeScript + Vite, served as static files by the
  backend from one origin. Six routes; three bottom-nav destinations. **41 tests.**
- **`ops/`** — four systemd **user** units (api, ollama, whisper, tailscaled),
  `setup.sh`, `mkcert-lan.sh`, `README-setup.md`.
- **AI, all local** — whisper.cpp `small-q5_1` for Spanish speech, Ollama running
  `qwen2.5:3b-instruct-q4_K_M` for insights. No account, no API key, no cloud.

## How to run it

```bash
cd /home/david/Proyectos/Autonom-OS/ops
./setup.sh --check        # refuses if the API port is occupied; changes nothing
./setup.sh                # installs the user units + loginctl enable-linger
```

Then, the two steps only you can do:

1. `~/.local/bin/tailscale --socket=$HOME/.local/share/tailscale/tailscaled.sock login`
   — links the daemon to your Tailscale account in a browser.
2. Open the app on your phone once **on each origin** (tailnet and LAN). This is
   not optional polish: it is what arms the offline fallback link and grants the
   microphone on both origins.

**The API listens on 8001, not 8000.** Port 8000 is permanently held by
`trace_erp_api`, a Docker container from your unrelated `trace_2026_deploy`
project. Nothing here touches it.

## How to verify it

```bash
python3 /home/david/Proyectos/software_factory/tools/verify.py --project /home/david/Proyectos/Autonom-OS
```

All gates pass at HEAD: frontend install/build/typecheck/unit, backend
unit + contract, and `test_integrity` at **221 tests / 565 assertions** (vs
179/437 at first review — tests were strengthened at every rework, never weakened).

Full QA evidence: `/home/david/qa-shots/` (60 screenshots) and
`/home/david/qa-evidence/` (QA database, JSON export, `strace` capture).

## What is proven, not just claimed

- **"Nothing leaves my PC."** Under `strace`, across a full session with live
  transcription and insight generation, the API made 6 `connect()` calls — **all
  to `127.0.0.1`**. whisper made zero. The browser requested nothing but
  localhost: no CDN, no font host, no telemetry.
- **Four taps to save an expense.** Counted in the running UI, criterion 2.8
  met exactly, with zero `<select>` elements.
- **All 28 Design Constraints pass**, measured against the live DOM: 0 contrast
  failures, 0 touch targets under 44×44, no horizontal overflow at 390 or 320 px.
- **The record survives.** 9 server restarts, one ungraceful; fingerprint identical.

## Measured performance — this is how it will feel

| Action | Time |
|---|---|
| Any voice capture | **~6.4 s floor** (whisper pads to a fixed 30 s window) |
| Finance question | ~7 s |
| Journal question over a month | 55–76 s |
| Monthly summary | pre-generated in background; opens instantly |

A three-second sentence costs the same as a twenty-eight-second one. **Voice is
the hands-free path, not the faster one** — for a simple expense, typing is
quicker. You accepted this at the plan gate.

## Still unverified — nobody has tested these

- **Spanish transcription accuracy.** This machine has no microphone and no
  text-to-speech, so *no one has ever spoken to this app*. The parser is verified
  with text; the speech→text step is not. **Say one sentence into it** — e.g.
  *"gasté catorce mil pesos en Uber con la tarjeta de crédito"* — and confirm.
  QA was explicitly told not to synthesize audio and call it a pass.
- **The real away-from-home path**, because Tailscale is not logged in yet.
- **Microphone-denied and MediaRecorder-unsupported** on a real Android device
  (both verified in headless Chromium).

## One criterion not fully closed

**11.1 — the AI must not assert things you did not record.** QA found 3 of 7
journal answers inventing content. The root cause was structural and is fixed:
`preocupado` was missing from the router's journal vocabulary, so journal
questions were routed as *finance* questions and the model was handed spending
data to weave from. After the fix, measured 0/7 (backend) and 0/5 (orchestrator,
two question types, both models).

**The residual is real:** a 3B model at Q4_K_M still occasionally infers — writing
*"tu bienestar emocional"* where you wrote something more specific. More prompt
text stops helping, because the prompt is already long enough that a 3B starts
dropping instructions from it.

**The model upgrade is not the answer, and this was measured, not guessed.**
`qwen3:4b-instruct` was pulled and A/B'd: no better grounded (0/5 both), warm
7–8 s vs 2–8 s, cold first load **94 s**, +0.6 GB RAM, and it introduces Spanish
person-agreement errors (*"fui al mercado"* where it means *"fuiste"*). We stayed
on the 3B. The 4B is on disk if you want to compare; `ollama rm qwen3:4b-instruct`
reclaims 2.5 GB.

## Deferred — recorded with evidence, none lost

| | Finding |
|---|---|
| **F4** | **Now closed** by the D3 fix — verified end-to-end after the fix |
| F5 | Failed-save banner is red; Constraint 3 reserves red for destructive/validation. It is red in the **mockup you approved** — the constraint needs widening, not the UI repainting |
| F6 | Journal "Todo" list caps at 50 newest; the server-side cursor exists and is unused |
| F7 | A failed summary retries 3× back-to-back with no backoff |
| F8 | The screenshot harness's liveness check skips `force:`-selector shots — **this fired for real**, reporting "0 findings" on a run where three captures had nothing to photograph |
| D4 | Amounts inside AI-written prose can use a comma (`346,000`) — the app's own formatter is never wrong |
| D6 | A 21-digit amount echoes as `1e.+21`; submitting is correctly refused, nothing saved |

## Two things worth knowing about how this was built

**A partial fix was reverted for being worse than the bug.** A backend agent died
mid-edit leaving code that would have handed the AI a **56-year timeout** — and
all 231 tests passed against it. The suite could see outcomes but not quantities.
The fix now asserts the quantity itself.

**The frontend's transcript was lost twice.** Both times the work was rebuilt
from artifacts on disk with nothing lost, which is what those artifacts are for.
