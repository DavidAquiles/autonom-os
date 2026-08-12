# Agent runbook — bring Autonom-OS up on this machine

**For the human:** clone the repo on the new machine, start Claude Code in it, and say:

> Read `ops/AGENT-MIGRATION.md` and work through it.

**For the agent:** this is an executable runbook, not background reading. Work
through the phases in order. Each ends in a verification gate you must actually
run — do not proceed on the assumption that a step worked. Where a phase is
marked **HALT**, stop and hand back to the human; those steps need a browser
login, a router, a phone, or physical access to the old machine, and you cannot
do them.

Report progress as `Phase N: <result>` after each gate so the human can follow
along without reading your tool calls.

---

## What this system is

A personal expense/journal app the user talks to from their phone in Spanish. It
is entirely self-hosted — no cloud services, no API keys:

| Piece | What it is | Listens on |
| --- | --- | --- |
| `autonomos-api` | FastAPI, one worker, serves the SPA + the REST API | `127.0.0.1:8001`, plus `${LAN_BIND_ADDR}:8443` (TLS) when configured |
| `autonomos-whisper` | whisper.cpp `whisper-server`, `small` q5_1, Spanish | `127.0.0.1:8081` |
| `ollama` | Qwen2.5-3B-Instruct Q4_K_M | `127.0.0.1:11434` |
| `tailscaled` | userspace-networking daemon; `tailscale serve` fronts the API over HTTPS | unix socket |

All four are **systemd user units** — nothing runs as root, everything lives
under `$HOME`. Background on the design is in `ops/README-setup.md`; the move
itself is in `ops/README-migration.md`. Read both before starting.

The user is migrating from a desktop PC to this machine. **The PC is being
retired**, so this machine becomes the only host.

---

## Rules that override your defaults

1. **Never `cp` the database.** `data/autonomos.db` is WAL-mode; the main file
   alone is missing recent writes. The only sanctioned copy path is
   `ops/stage-migration.sh` on the old host, which uses `VACUUM INTO`.
2. **Never install `autonomos.env.oldhost`** as `ops/autonomos.env`. It names the
   *old* machine. It is a reference for reading values out of, nothing more.
3. **Copy the mkcert CA before running `ops/mkcert-lan.sh`.** Order matters and
   is not recoverable cheaply — see Phase 6.
4. **Keep TLS paths relative** in `ops/autonomos.env` (`ops/certs/lan-cert.pem`).
   The old host had absolute `/home/david/...` paths; under a different username
   those break the LAN listener silently — `origins.lan` just reports `null`.
5. **Never `0.0.0.0`** for `LAN_BIND_ADDR`. The API refuses it by design.
6. **Never turn on `tailscale funnel`.** `serve` only. Funnel is public exposure.
7. **If a port is occupied, do not free it.** Something else owns it. Change
   `AUTONOMOS_API_PORT` instead and tell the human.
8. **Do not `git push`** from this runbook. Nothing here should change the repo.

---

## Phase 1 — Survey

Establish where you are before installing anything.

```bash
uname -m && cat /etc/os-release | head -2
systemctl --user is-system-running || true    # user systemd must work
ls ~/.local/bin/{uv,ollama,tailscale,tailscaled,mkcert} 2>&1
ls ~/.local/whisper.cpp/build/bin/whisper-server 2>&1
node -v; npm -v
ss -ltn | grep -E ':(8001|8081|8443|11434)' || echo "target ports free"
free -g | head -2
```

**Gate:** report which prerequisites are present, which are missing, whether the
ports are free, and total RAM. The models need roughly 2.5 GB resident. If this
machine has under 8 GB, say so — it will work but the desktop will feel it.

**HALT if** user systemd is unavailable (a container or a WSL install without
systemd enabled). The whole design is systemd user units; that needs solving
first.

## Phase 2 — Prerequisites

Install only what Phase 1 reported missing. Everything goes under `~/.local`,
because the unit files reference those exact paths.

```bash
# Python — 3.12 is pinned; the system python is deliberately not used
curl -LsSf https://astral.sh/uv/install.sh | sh
~/.local/bin/uv python install 3.12
```

Ollama, Tailscale (both `tailscale` and `tailscaled` binaries) and mkcert:
install to `~/.local/bin` from their official downloads. Prefer the static
tarballs over distro packages — distro packages install system-wide units that
run as root, which is not this design.

Node ≥ 20 for the frontend build. Use the distro package or nvm.

whisper.cpp, built from source:

```bash
git clone https://github.com/ggerganov/whisper.cpp ~/.local/whisper.cpp
cd ~/.local/whisper.cpp
git checkout v1.9.2
cmake -B build && cmake --build build -j --config Release
sh ./models/download-ggml-model.sh small-q5_1
```

Pin `v1.9.2`. `ops/systemd/autonomos-whisper.service` passes `-nt`, and
`--no-translate` does **not** exist in this build — a newer whisper.cpp may
change the flags. If you take a newer tag, verify the flags against
`whisper-server --help` before assuming the unit file is wrong.

**Gate:** re-run the Phase 1 `ls` checks; every path must now exist.

## Phase 3 — The app

The repo must live at `~/Proyectos/Autonom-OS`. The unit files hardcode
`%h/Proyectos/Autonom-OS` (`%h` = `$HOME`, so a different *username* is fine, a
different *path* is not). If it is elsewhere, either move it or edit
`WorkingDirectory`, `EnvironmentFile` and `ExecStart` in
`ops/systemd/autonomos-api.service` — and re-apply that edit after every
`ops/setup.sh`, which overwrites the unit files.

```bash
cd ~/Proyectos/Autonom-OS
cd frontend && npm ci && npm run build && cd ..   # FRONTEND_DIST is gitignored
ops/setup.sh --check                              # must be clean before you continue
ops/setup.sh
```

`setup.sh` creates `ops/autonomos.env` from the example, provisions the venv,
installs and starts the four units, and enables lingering. It does not touch
`ops/autonomos.env` if one already exists.

Then pull the model:

```bash
~/.local/bin/ollama pull qwen2.5:3b-instruct-q4_K_M
systemctl --user restart autonomos-api
```

**Note on port 8001:** the old PC had port 8000 permanently held by an unrelated
Docker container, which is why this app uses 8001. That reason does not travel —
8000 is probably free here. Leave it on 8001 anyway; every config value and doc
already says 8001 and there is nothing to gain from changing it.

**Gate:**

```bash
systemctl --user status autonomos-api autonomos-whisper ollama --no-pager --lines=0
curl -s http://127.0.0.1:8001/api/health
curl -s http://127.0.0.1:8001/api/status
```

`/api/health` must return `status: ok`. `/api/status` must show both sidecars
available. At this point `origins.primary` and `origins.lan` are both `null` —
correct, they are configured in Phases 4 and 6.

## Phase 4 — Tailnet — **HALT**

The login is interactive and browser-based. You cannot do it. Print this for the
human and stop:

```
Run this yourself (in Claude Code, prefix with ! to run it here):

  ~/.local/bin/tailscale --socket=$HOME/.local/share/tailscale/tailscaled.sock up

Then, in the Tailscale admin console, DISABLE KEY EXPIRY for this new node.
Without that it silently drops off the tailnet in a few months and the phone
stops reaching it.

Tell me when that's done.
```

Once the human confirms, you can do the rest:

```bash
~/.local/bin/tailscale --socket=$HOME/.local/share/tailscale/tailscaled.sock \
    serve --bg https / http://127.0.0.1:8001
~/.local/bin/tailscale status      # read this machine's tailnet hostname
```

Set `PUBLIC_URL` in `ops/autonomos.env` to `https://<that-hostname>` — no
trailing slash — and `systemctl --user restart autonomos-api`.

`PUBLIC_URL` is echoed by `/api/health` so the phone can learn the *other* origin
while the server is still reachable. It is never inferred from a request, which
is why it must be set by hand.

**Gate:** `curl -s http://127.0.0.1:8001/api/health` shows `origins.primary` as
the tailnet URL. Ask the human to open it on their phone and confirm the app
loads.

## Phase 5 — Verification with an empty database

Prove the stack before any data is at stake. The PC is still live, so everything
so far is reversible.

```bash
cd backend
.venv/bin/python -m pytest -q
.venv/bin/python tools/live_check.py llm
.venv/bin/python tools/live_check.py stt
```

**Gate:** the suite passes and both live checks succeed against the real
sidecars. Then ask the human to record one voice expense from their phone over
the tailnet origin — that exercises the secure context, whisper, the LLM and a
SQLite write in one action. It lands in this machine's empty database; that is
expected and gets replaced in Phase 6.

**Do not continue until this passes.** Everything after this point starts
retiring the old machine.

## Phase 6 — Cutover — **HALT, then execute**

Two things exist only on the old PC and cannot be fetched from here: the
database, and the mkcert CA that the user's phone already trusts.

Tell the human:

```
On the OLD PC, run:

    cd ~/Proyectos/Autonom-OS
    ops/stage-migration.sh --retire

That stops its API, takes a WAL-safe copy of the database, verifies it row for
row, and gathers it with the mkcert CA into ~/autonomos-migration.

Then copy that folder to this machine (scp or a USB stick) and tell me the path.

Run it LAST — the copy is only as fresh as the moment you run it, and --retire
leaves the old API stopped so nothing writes after the snapshot.
```

Once the folder is here, with `$STAGED` as its path:

```bash
cd ~/Proyectos/Autonom-OS
systemctl --user stop autonomos-api

# The CA FIRST — before mkcert has ever run on this machine.
rm -rf ~/.local/share/mkcert
cp -a "$STAGED/mkcert-CA" ~/.local/share/mkcert

# Then the data. Remove the -wal/-shm alongside, or SQLite will try to
# reconcile this machine's leftovers against the incoming file.
rm -f data/autonomos.db data/autonomos.db-wal data/autonomos.db-shm
cp "$STAGED/autonomos.db" data/autonomos.db
cp -a "$STAGED/snapshots" data/snapshots

systemctl --user start autonomos-api
```

Why the CA order: the phone has a root certificate installed that anchors trust
for the LAN fallback origin. It was generated on the old PC. If `mkcert -install`
runs here first it mints a *new* CA, and the user has to install a certificate on
Android again — including its permanent "network may be monitored" notice. Copy
the CA first and the phone needs no changes at all.

**Gate:** `curl -s http://127.0.0.1:8001/api/health` still returns ok, and the
user's real expense history is visible in the app. Report the row count:

```bash
backend/.venv/bin/python -c "import sqlite3;print(sqlite3.connect('data/autonomos.db').execute('select count(*) from expenses').fetchone())"
```

## Phase 7 — LAN fallback — **HALT**

This origin exists for "home internet is down but both devices are on the
private network". It needs a LAN IP that will not change, which means a DHCP
reservation on the router — the human's job.

```bash
ip -4 addr show scope global | grep inet    # this machine's current LAN address
```

Print for the human:

```
Reserve <that address> for this machine on your router (DHCP reservation), or
tell me a different reserved address to use. The certificate names a fixed IP,
so it breaks if the address moves.
```

Then, with `$LAN_IP` confirmed:

```bash
ops/mkcert-lan.sh "$LAN_IP"
# set LAN_BIND_ADDR=$LAN_IP in ops/autonomos.env  (never 0.0.0.0)
# confirm TLS_CERTFILE / TLS_KEYFILE are RELATIVE: ops/certs/lan-cert.pem
systemctl --user restart autonomos-api
```

**Gate:** `origins.lan` in `/api/health` is non-null. If it is still `null`, the
listener did not start — check, in this order: `LAN_BIND_ADDR` set and not
`0.0.0.0`; the cert files exist at the configured paths; the paths are relative;
port 8443 free.

**Security note, and it is real.** The LAN listener is unauthenticated by
deliberate design, so the home LAN is its access boundary. If this machine is a
laptop that leaves the house, say so explicitly: on any untrusted network,
`LAN_BIND_ADDR` should be unset and the API restarted, and the fallback then
simply does not start. This matters more on a laptop than it did on the desktop.

## Phase 8 — Phone — **HALT**

You cannot do any of this. Print it:

```
On your phone — browser microphone permission is per-origin, and both origins
just changed. Do this now, not during an actual outage:

  1. Remove the two old home-screen entries.
  2. Open <PUBLIC_URL>, add to home screen, grant microphone permission.
  3. Open https://<LAN_IP>:8443, add to home screen with a DISTINCT label,
     grant microphone permission.

The mkcert CA came across in Phase 6, so step 3 should not prompt you to
install any certificate. If it warns about the certificate, stop and tell me —
it means the CA copy did not take.
```

## Phase 9 — Retire the old machine — **HALT**

`--retire` already left the old API stopped. Print:

```
On the OLD PC, once you're happy with this machine:

    systemctl --user disable --now autonomos-api autonomos-whisper ollama
    ~/.local/bin/tailscale --socket=$HOME/.local/share/tailscale/tailscaled.sock serve --https=443 off
    systemctl --user disable --now tailscaled

Then remove the old node from the Tailscale admin console.

KEEP the repo and data/ on that disk for a couple of weeks. Until this machine
has accumulated its own nightly snapshots, the old PC is the only backup.
```

Never run two hosts of this app at once. There is no sync between them —
whichever origin the phone points at gets the entry, and the other silently
falls behind.

---

## Final report

```bash
systemctl --user status autonomos-api autonomos-whisper ollama tailscaled --no-pager --lines=0
curl -s http://127.0.0.1:8001/api/health
curl -s http://127.0.0.1:8001/api/status
ls -la data/autonomos.db data/snapshots | head
```

State plainly: both origins live, both sidecars available, the expense count
matching the old host, and anything left undone. If a phase was skipped or
partially completed, say which and why — do not report a migration as finished
when part of it is outstanding.

## If something breaks

| Symptom | Cause |
| --- | --- |
| Unit crash-loops immediately | Port occupied. `ss -ltnp`. Change the port, don't free it. |
| API up, blank page | `frontend/dist` missing — `npm ci && npm run build`. |
| `origins.lan` is `null` | No `LAN_BIND_ADDR`, it's `0.0.0.0`, or the cert path is wrong/absolute. |
| Sidecar `unavailable` | Normal and visible by design — capture and all views keep working on SQLite alone. Check the unit, but it is not an outage. |
| Phone won't record | Not a secure context. Voice needs HTTPS; `http://` LAN addresses cannot do `getUserMedia`. |
| Phone warns about the certificate | The mkcert CA copy in Phase 6 did not take. |
| Units die at reboot/logout | Lingering off — `loginctl enable-linger $USER`. |

`journalctl --user -u autonomos-api -n 100 --no-pager` is the first thing to read
for anything API-side.
