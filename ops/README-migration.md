# Moving Autonom-OS to another machine

Target: a second Linux host with systemd, which **replaces** this PC. Read
`ops/README-setup.md` first — this document only covers what is different when
the host already exists somewhere else.

> **Handing this to a coding agent instead?** Use `ops/AGENT-MIGRATION.md`. It is
> the same move written for an agent to execute — phase gates it must verify,
> explicit HALT points for the browser login, the router, the phone and the old
> machine, and the specific mistakes it must not make. This document is the
> human-readable reference behind it.

Three kinds of thing move, and they move differently:

| | What | How it travels |
| --- | --- | --- |
| **Code** | the repo | `git push` → `git clone` |
| **Data** | `data/autonomos.db` | direct copy, never through GitHub |
| **Host identity** | env, certs, tailnet node | **regenerated on the new host**, not copied |

The third row is the one that bites. `PUBLIC_URL`, `LAN_BIND_ADDR` and the LAN
certificate all name *this* machine. Copying them produces a stack that starts
cleanly and is unreachable.

**Steps 6 and 8 have an old-host half that cannot be done from the new machine.**
`ops/stage-migration.sh` does both in the right order — stops the API, takes the
WAL-safe database copy, verifies it row for row, and gathers it with the mkcert
CA into one folder to carry across. Run it when you actually move, not early: it
cannot tell a fresh copy from a week-old one.

## 0. Before anything else: push

The working tree is clean but the branch is **ahead of `origin/main`**. Until
this runs, most of the work exists on exactly one disk.

```bash
git push origin main
```

## 1. Prerequisites on the new host

`ops/setup.sh --check` names all of these, and none are installed by it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh    # ~/.local/bin/uv
uv python install 3.12                            # pinned; the system python is not used
```

Then, all under `~/.local`, matching the paths the units expect:

* **ollama** → <https://ollama.com/download> into `~/.local/bin/ollama`
* **tailscale** + **tailscaled** → <https://tailscale.com/download> into `~/.local/bin`
* **mkcert** → `~/.local/bin/mkcert` (only needed for the LAN fallback origin)
* **Node** ≥ 20 for the frontend build (this host used v24)
* **whisper.cpp**, built from source at `~/.local/whisper.cpp`:

  ```bash
  git clone https://github.com/ggerganov/whisper.cpp ~/.local/whisper.cpp
  cd ~/.local/whisper.cpp
  git checkout v1.9.2          # the build this host runs; see the -nt flag note below
  cmake -B build && cmake --build build -j --config Release
  sh ./models/download-ggml-model.sh small-q5_1
  ```

  The unit passes `-nt` and **not** `--no-translate` — that flag does not exist
  in this build and makes `whisper-server` print usage and exit 1. If you take a
  newer whisper.cpp, re-check the flags in `ops/systemd/autonomos-whisper.service`
  before assuming the unit is wrong.

Models are re-pulled, not copied:

```bash
ollama serve &                                # or after setup.sh starts the unit
ollama pull qwen2.5:3b-instruct-q4_K_M        # the LLM_MODEL in use
ollama pull qwen3:4b-instruct                 # optional: the R3 ladder rung
```

## 2. Clone to the same path

The systemd units hardcode `%h/Proyectos/Autonom-OS`. `%h` expands to the new
user's `$HOME`, so the **username may differ** — the path under it may not.

```bash
git clone git@github.com:DavidAquiles/autonom-os.git ~/Proyectos/Autonom-OS
cd ~/Proyectos/Autonom-OS
```

If you want it somewhere else, edit `WorkingDirectory`, `EnvironmentFile` and
`ExecStart` in `ops/systemd/autonomos-api.service` — and re-edit them after every
`ops/setup.sh`, which copies the unit files over.

## 3. Build the frontend

`FRONTEND_DIST=frontend/dist` is gitignored and the API serves the SPA from it,
so an unbuilt frontend is a working API with no UI.

```bash
cd frontend && npm ci && npm run build && cd ..
```

## 4. Run setup

```bash
ops/setup.sh --check     # confirm the prerequisites and ports, change nothing
ops/setup.sh
```

**On the port.** 8001 is not sacred and the reason for it does not travel: 8000
is taken *on this PC* by an unrelated `trace_erp_api` container. The new host
probably has 8000 free. Leave `AUTONOMOS_API_PORT=8001` anyway — it costs
nothing, and every other config value and doc already says 8001.

## 5. Fix the four host-specific env values

`ops/setup.sh` creates `ops/autonomos.env` from the example. There are no
secrets in it — only these four lines differ from the committed example, and all
four are about *which machine this is*:

```ini
PUBLIC_URL=            # set in step 7, after `tailscale serve` is up
LAN_BIND_ADDR=         # set in step 6: the NEW host's DHCP-reserved LAN address
TLS_CERTFILE=ops/certs/lan-cert.pem   # keep these RELATIVE — they resolve
TLS_KEYFILE=ops/certs/lan-key.pem     # against the repo root
```

This PC drifted to absolute `/home/david/...` paths for the two TLS values.
Do not carry that over; under a different username it silently breaks the LAN
listener, and `origins.lan` goes `null` with no other symptom.

## 6. LAN certificate — regenerate, but keep the CA

The certificate names a fixed IP (`192.168.1.11` here). It is worthless on a
host with a different address, so it is regenerated:

```bash
ops/mkcert-lan.sh <new-host-LAN-IP>       # make the DHCP reservation first
# then set LAN_BIND_ADDR to that same address in ops/autonomos.env
systemctl --user restart autonomos-api
curl -s http://127.0.0.1:8001/api/health  # origins.lan must be non-null
```

**Copy the mkcert CA before running that**, and the phone needs no changes:

```bash
scp -r ~/.local/share/mkcert <laptop>:~/.local/share/mkcert
```

`mkcert -install` on the new host then reuses that CA instead of minting a new
one, so the root certificate already installed on the phone still validates the
new LAN cert. Skip this and you get an Android certificate install — and the
standing "network may be monitored" notice — a second time.

## 7. Rejoin the tailnet as a new node

The new host is a **different node with a different name**; the tailnet identity
does not move.

```bash
~/.local/bin/tailscale --socket=$HOME/.local/share/tailscale/tailscaled.sock up
# disable key expiry for this node in the admin console (R2)
~/.local/bin/tailscale --socket=$HOME/.local/share/tailscale/tailscaled.sock \
    serve --bg https / http://127.0.0.1:8001
~/.local/bin/tailscale status          # read the new name
```

Put that origin in `ops/autonomos.env` as `PUBLIC_URL` and restart the API.
`GET /api/health` echoes it, which is how the phone learns the *other* origin
while the server is still reachable. Funnel stays **off**.

## 8. Move the database

Do this **last**, with the API stopped on both machines, so nothing writes to a
database you are about to overwrite or abandon.

`data/autonomos.db` runs in WAL mode and has a live `-wal` alongside it, so
`cp` can capture a torn state. Take a consistent copy the same way the nightly
snapshot does:

```bash
# on THIS PC
systemctl --user stop autonomos-api
cd ~/Proyectos/Autonom-OS
backend/.venv/bin/python -c "import sqlite3; sqlite3.connect('data/autonomos.db').execute(\"VACUUM INTO 'data/transfer.sqlite'\")"
scp data/transfer.sqlite <laptop>:~/Proyectos/Autonom-OS/data/
scp -r data/snapshots     <laptop>:~/Proyectos/Autonom-OS/data/   # optional history
```

```bash
# on the LAPTOP
systemctl --user stop autonomos-api
cd ~/Proyectos/Autonom-OS
rm -f data/autonomos.db data/autonomos.db-wal data/autonomos.db-shm
mv data/transfer.sqlite data/autonomos.db
systemctl --user start autonomos-api
```

`VACUUM INTO` produces a single self-contained file with no `-wal`/`-shm`, which
is exactly what the restore procedure in `ops/README-setup.md` expects. The
`data/qa-*.db` files are QA scratch and do not move.

## 9. Retire this PC

Two hosts running this app means two databases and **no sync between them** —
whichever one the phone is pointed at is the one that gets the entry, and the
other silently falls behind. Once the laptop is verified:

```bash
systemctl --user disable --now autonomos-api autonomos-whisper ollama
~/.local/bin/tailscale --socket=$HOME/.local/share/tailscale/tailscaled.sock serve --https=443 off
systemctl --user disable --now tailscaled
loginctl disable-linger $USER      # only if nothing else here needs lingering
```

Remove the old node from the Tailscale admin console. Keep the repo and
`data/` on disk until the laptop has been running for a few days — the snapshot
history is the only other copy of the data.

## 10. On the phone

Browser permission is **per-origin**, and both origins changed. Re-do the setup
step rather than discovering it during an actual outage:

1. Remove the two old home-screen entries.
2. Add the new tailnet origin, grant microphone permission.
3. Add `https://<new-LAN-IP>:8443`, grant microphone permission, distinct label.

## Verifying the move

```bash
systemctl --user status autonomos-api autonomos-whisper ollama tailscaled
curl -s http://127.0.0.1:8001/api/health    # origins.public AND origins.lan non-null
curl -s http://127.0.0.1:8001/api/status    # both sidecars available
cd backend
.venv/bin/python -m pytest -q
.venv/bin/python tools/live_check.py llm
.venv/bin/python tools/live_check.py stt
```

Then open the tailnet origin on the phone and record one voice expense end to
end. That exercises the secure context, whisper, the LLM and a SQLite write in
one action — the four things this move can break.
