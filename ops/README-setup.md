# Autonom-OS — host setup and runbook

Four **systemd user units**, none of them root, all inside `$HOME`:

| Unit | What it is | Bind |
| --- | --- | --- |
| `autonomos-api` | FastAPI, one worker, scheduler + InferenceArbiter in-process | `127.0.0.1:8001` and, when configured, `${LAN_BIND_ADDR}:8443` (TLS) |
| `autonomos-whisper` | whisper.cpp `whisper-server`, `small` q5_1, `-l es`, 6 threads | `127.0.0.1:8081` |
| `ollama` | Qwen2.5-3B-Instruct Q4_K_M, `OLLAMA_KEEP_ALIVE=-1` | `127.0.0.1:11434` |
| `tailscaled` | non-root userspace-networking daemon | socket in `~/.local/share/tailscale` |

## Install

```bash
ops/setup.sh --check     # ports and prerequisites only, changes nothing
ops/setup.sh             # install and start
```

It checks the host, creates `ops/autonomos.env` from the example, provisions the
CPython 3.12 venv with `uv`, installs and starts the four units, and runs
`loginctl enable-linger`. **Lingering is not optional**: user units do not start
at boot without a login session, and 14.1 and 13.7 both require the system to
just be there after a restart.

### The API listens on 8001, not 8000

Port **8000 on this machine belongs to another project** — the `trace_erp_api`
Docker container from `trace_2026_deploy`, published on all interfaces. It is
long-running and **must not be stopped or reconfigured**. So the loopback port
this app listens on is `AUTONOMOS_API_PORT=8001`, and `tailscale serve` points
there.

Nothing about 8001 is sacred; it is configuration. If it is ever taken too, set
`AUTONOMOS_API_PORT` in `ops/autonomos.env`, re-run `ops/setup.sh`, and re-point
`tailscale serve` at the new port. `ops/setup.sh` refuses to install a unit whose
port is already listening rather than leaving you with a crash-looping service
whose failure looks like a bug in this app — run `ops/setup.sh --check` any time
to see the port situation without changing anything.

## The two steps a script cannot do

1. **Join the tailnet** — interactive login:
   ```bash
   ~/.local/bin/tailscale --socket=$HOME/.local/share/tailscale/tailscaled.sock up
   ```
   Then **disable key expiry** for this node in the admin console (R2).
2. **Publish over HTTPS**:
   ```bash
   ~/.local/bin/tailscale --socket=$HOME/.local/share/tailscale/tailscaled.sock \
       serve --bg https / http://127.0.0.1:8001
   ```
   `tailscale funnel` — the public option — stays **off**. This HTTPS origin is
   what makes voice capture possible at all: `getUserMedia` requires a secure
   context, which a plain `http://` LAN address is not.

   Then put that same origin in `ops/autonomos.env` as `PUBLIC_URL` and restart
   the API. `GET /api/health` echoes it, which is how the phone learns the
   *other* origin **while the server is still reachable** — the "cannot reach
   your server" screen needs it at a moment when no request can be made.
   `tailscale status` prints the name.

## The LAN fallback origin (15.5)

For "home internet is down but both devices are on the private network":

```bash
ops/mkcert-lan.sh 192.168.1.50      # your PC's DHCP-reserved LAN address
# set LAN_BIND_ADDR=192.168.1.50 in ops/autonomos.env
systemctl --user restart autonomos-api
curl -s http://127.0.0.1:8001/api/health   # `origins.lan` should now be non-null
```

`origins.lan` stays `null` whenever the fallback listener is not actually
running — no `LAN_BIND_ADDR`, `0.0.0.0` (refused), or a missing certificate.
That is deliberate: advertising an origin nothing listens on would hand the
phone a dead link at exactly the moment it needs a live one.

Then install the mkcert root CA on the phone once, add the origin to the home
screen with a distinct label, and grant microphone permission there — browser
permission is per-origin, and the outage scenario must not begin with a prompt.

**Security note, and it is a real one.** The LAN listener is unauthenticated by
A6's deliberate choice, so the home LAN is its access boundary. If this PC is
ever attached to a network you do not control, **unset `LAN_BIND_ADDR`** and
restart the API; the fallback then simply does not start. `LAN_BIND_ADDR` names
one interface and is never `0.0.0.0` — the API refuses that value rather than
obeying it.

## Everyday operations

```bash
systemctl --user status  autonomos-api autonomos-whisper ollama tailscaled
systemctl --user restart autonomos-api
journalctl --user -u autonomos-api -f
curl -s http://127.0.0.1:8001/api/health
curl -s http://127.0.0.1:8001/api/status     # both sidecars, cached ~30 s
```

`/api/status` answering `"unavailable"` for a sidecar is a normal, visible state:
capture, editing and every view touch SQLite only and keep working (11.4).

## Data, backups and export

* Database: `data/autonomos.db` (WAL, `synchronous=FULL`).
* Nightly `VACUUM INTO data/snapshots/YYYY-MM-DD.sqlite`, last 7 kept. Taken by
  the scheduler after 03:00 local; if the PC was asleep it is taken on the next
  tick after waking.
* Full export: `GET /api/export` → one JSON file with everything. It is the only
  export endpoint; CSV exports were cut at the Approve Plan gate.
* Restore is a file copy: stop `autonomos-api`, copy a snapshot over
  `data/autonomos.db` (remove `-wal`/`-shm` alongside it), start it again.

## Verifying the stack by hand

```bash
cd backend
.venv/bin/python -m pytest -q                       # the unit/API suite
.venv/bin/python tools/live_check.py llm            # real Ollama, end to end
.venv/bin/python tools/live_check.py stt            # real whisper-server
.venv/bin/python tools/live_check.py endpoint FILE.wav
.venv/bin/python tools/live_check.py contention FILE.wav 1.5   # KD-12 preemption
```

## Model ladder (R3/R9)

Both are config changes in `ops/autonomos.env`, and **only one of the two fits**
in the ~2.28 GB of headroom:

* Answers read thin → `LLM_MODEL=qwen3:4b-instruct` (+~0.6 GB) after pulling it.
* Transcription accuracy short → whisper `medium` (+~1.0 GB) in the whisper unit.

Whisper `base` is 3.5× faster but its **Spanish quality is unvalidated**; do not
take that rung until someone transcribes a real Spanish sample containing an
amount and a payment method and confirms 9.6 and 9.7 still hold.
