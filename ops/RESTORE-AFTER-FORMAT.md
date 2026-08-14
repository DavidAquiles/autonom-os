# Restoring Autonom-OS after formatting this PC

**Situation this covers:** the *same* machine, wiped and reinstalled. The backup
archive (`autonomos-backup-YYYY-MM-DD.tar.gz`, produced by
`ops/stage-format-backup.sh`) is the only thing that survived the format besides
the GitHub repo.

> **This is not `ops/README-migration.md`.** That document moves the stack to a
> *different* host and tells you to **regenerate** the env, the certificate and
> the node identity, because they name the old machine. Here the machine is the
> same one, so most of that inverts:
>
> | | Migration (new host) | This (same host, wiped) |
> | --- | --- | --- |
> | `ops/autonomos.env` | regenerate; never install the old one | **install as-is**, then re-check `PUBLIC_URL` |
> | LAN IP / `LAN_BIND_ADDR` | new address | unchanged (same NIC, same DHCP reservation) |
> | LAN certificate | regenerate for the new IP | reusable if the IP is unchanged; regenerate is also fine |
> | mkcert CA | copy so the phone keeps trusting it | same — restore it **before** `mkcert -install` |
> | tailnet node | new node | new node here too: the old node key was on the wiped disk |

Everything below assumes the archive is extracted to `~/autonomos-backup/`.

---

## Phase 0 — Extract and read the manifest

```bash
tar xzf autonomos-backup-*.tar.gz -C ~
cd ~/autonomos-backup
cat MANIFEST.txt        # versions this host was running, and a checksum per file
sha256sum -c SHA256SUMS # every file arrived intact
```

**Gate:** `sha256sum -c` prints `OK` for every line. A corrupt `autonomos.db`
here is a corrupt database forever — there is no other copy.

---

## Phase 1 — Prerequisites

None of these are installed by `ops/setup.sh`; it only checks for them. Versions
in brackets are what this host was running at backup time — newer is usually
fine, the whisper.cpp one is not (see below).

```bash
# uv, and the pinned CPython (the system python is NOT used)     [uv 0.12.3]
curl -LsSf https://astral.sh/uv/install.sh | sh
~/.local/bin/uv python install 3.12                              # [3.12.13]
```

Then, all under `~/.local`, because the systemd units hardcode those paths:

* **ollama** → <https://ollama.com/download> into `~/.local/bin/ollama` [0.32.9]
* **tailscale** + **tailscaled** → <https://tailscale.com/download> into `~/.local/bin` [1.102.2]
* **mkcert** → `~/.local/bin/mkcert` [v1.4.4] — only needed for the LAN fallback origin
* **Node** for the frontend build [v22.23.2, npm 10.9.8]
* **whisper.cpp** at `~/.local/whisper.cpp`:

  ```bash
  git clone https://github.com/ggerganov/whisper.cpp ~/.local/whisper.cpp
  cd ~/.local/whisper.cpp
  git checkout v1.9.2
  cmake -B build && cmake --build build -j --config Release
  sh ./models/download-ggml-model.sh small-q5_1     # ~190 MB, the model the unit names
  ```

  Pin **v1.9.2**. `ops/systemd/autonomos-whisper.service` passes `-nt`, which a
  newer build may not accept — `whisper-server` then prints usage and exits 1,
  and the failure reads like a broken unit rather than a changed flag. If you do
  take a newer whisper.cpp, re-check the flags in that unit first.

**Gate:**

```bash
ls ~/.local/bin/{uv,ollama,tailscale,tailscaled,mkcert} \
   ~/.local/whisper.cpp/build/bin/whisper-server \
   ~/.local/whisper.cpp/models/ggml-small-q5_1.bin
node -v
```

---

## Phase 2 — SSH key, then the repo

The archive carries the SSH key this machine used for GitHub, so nothing needs
re-registering:

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
cp ~/autonomos-backup/ssh/id_ed25519* ~/.ssh/
chmod 600 ~/.ssh/id_ed25519 && chmod 644 ~/.ssh/id_ed25519.pub
ssh -T git@github.com          # expect: "Hi <user>! You've successfully authenticated"
```

If the key was left out of the backup, or you would rather not reuse it:
`ssh-keygen -t ed25519`, add the new public key at
<https://github.com/settings/keys>, and clone over HTTPS in the meantime.

```bash
git clone git@github.com:DavidAquiles/autonom-os.git ~/Proyectos/Autonom-OS
cd ~/Proyectos/Autonom-OS
```

**The path is load-bearing.** The units use `%h/Proyectos/Autonom-OS`; `%h` is
the new `$HOME`, so a different *username* is fine but a different *path* is not
— unless you also edit `WorkingDirectory`, `EnvironmentFile` and `ExecStart` in
`ops/systemd/autonomos-api.service`, and re-edit them after every `ops/setup.sh`,
which copies the units over.

If GitHub is unreachable, the archive has a full mirror of the repository:

```bash
git clone ~/autonomos-backup/repo.bundle ~/Proyectos/Autonom-OS
cd ~/Proyectos/Autonom-OS
git remote set-url origin git@github.com:DavidAquiles/autonom-os.git
```

**Gate:** `git log --oneline -1` matches `HEAD` in `MANIFEST.txt`.

---

## Phase 3 — Restore the data, the config and the CA

Do this **before** `ops/setup.sh`, which starts the API: a running API means
something is writing to the database you are replacing.

```bash
cd ~/Proyectos/Autonom-OS

# 1. the database. It is a VACUUM INTO copy: one self-contained file, no
#    -wal/-shm beside it. Do not create any.
mkdir -p data
cp ~/autonomos-backup/autonomos.db      data/autonomos.db
cp -a ~/autonomos-backup/snapshots      data/snapshots

# 2. the config. Same machine, so this installs as-is — the TLS paths are
#    already relative and LAN_BIND_ADDR already matches this NIC.
cp ~/autonomos-backup/autonomos.env     ops/autonomos.env

# 3. the mkcert CA — BEFORE any mkcert command runs on this host.
mkdir -p ~/.local/share
cp -a ~/autonomos-backup/mkcert-CA      ~/.local/share/mkcert
chmod 400 ~/.local/share/mkcert/rootCA-key.pem
```

Restoring the CA first is what lets `mkcert -install` reuse the existing root
instead of minting a new one. Skip it and the phone needs a second Android
certificate install — with the standing "network may be monitored" notice.

**Gate:**

```bash
# system python3, because backend/.venv does not exist until phase 4
python3 - data/autonomos.db <<'EOF'
import sqlite3, sys
c = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
print(c.execute("PRAGMA integrity_check").fetchone()[0])
for t, in c.execute("SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name NOT LIKE 'sqlite_%' ORDER BY name"):
    print(f"{c.execute(f'SELECT count(*) FROM \"{t}\"').fetchone()[0]:>8}  {t}")
EOF
ls data/autonomos.db-wal 2>/dev/null && echo "WRONG: there should be no -wal yet"
```

It must print `ok`, and the per-table counts must match the ones in
`MANIFEST.txt`.

---

## Phase 4 — Build the frontend, then run setup

`FRONTEND_DIST=frontend/dist` is gitignored and the API serves the SPA from it,
so an unbuilt frontend is a healthy API with no UI at all.

```bash
cd frontend && npm ci && npm run build && cd ..
ops/setup.sh --check      # ports and prerequisites; changes nothing
ops/setup.sh              # venv, four user units, lingering, start
```

`ops/setup.sh` leaves an existing `ops/autonomos.env` untouched, so the file
from Phase 3 survives. It also runs `loginctl enable-linger`, which is not
optional — user units do not start at boot without it.

**On port 8001:** keep it. The reason for it (an unrelated `trace_erp_api`
container holding 8000) may or may not come back with your reinstall, but every
config value, unit and document already says 8001.

**Gate:**

```bash
systemctl --user status autonomos-api autonomos-whisper ollama tailscaled
curl -s http://127.0.0.1:8001/api/health
```

The API answers. `origins.public` still shows the *old* tailnet URL from the
restored env — Phase 5 fixes that. `origins.lan` may be `null`; Phase 7.

---

## Phase 5 — Rejoin the tailnet (HALT: needs a browser and the admin console)

The node key lived on the wiped disk, so this host joins as a **new node**.

**First, delete the old node** `david-ideapad-5-14are05` at
<https://login.tailscale.com/admin/machines>. Do this *before* `tailscale up`:
the name is only free if the old node is gone, and otherwise the tailnet hands
you `david-ideapad-5-14are05-1`, which changes `PUBLIC_URL` and breaks the
phone's saved home-screen origin.

```bash
TS="$HOME/.local/bin/tailscale --socket=$HOME/.local/share/tailscale/tailscaled.sock"
$TS up                                        # opens a login URL — browser needed
# then: disable key expiry for this node in the admin console (R2)
$TS serve --bg https / http://127.0.0.1:8001  # Funnel stays OFF
$TS status                                    # read the name it actually got
```

Put that origin in `ops/autonomos.env` as `PUBLIC_URL` (verbatim, no trailing
slash) and `systemctl --user restart autonomos-api`.

**Gate:** `curl -s http://127.0.0.1:8001/api/health` echoes the new
`origins.public`, and it equals what `tailscale status` printed.

---

## Phase 6 — Pull the model

Models are re-downloaded, never restored from backup:

```bash
~/.local/bin/ollama pull qwen2.5:3b-instruct-q4_K_M    # the LLM_MODEL in use, ~1.9 GB
```

Only pull `qwen3:4b-instruct` (the R3 ladder rung) if you actually switch
`LLM_MODEL` to it — the headroom fits one ladder step, not both.

**Gate:**

```bash
cd backend
.venv/bin/python tools/live_check.py llm
.venv/bin/python tools/live_check.py stt
```

---

## Phase 7 — LAN fallback origin (optional)

At backup time `LAN_BIND_ADDR` was **unset** and `ops/certs/` was empty, so the
LAN fallback was not running. Set it up only if you want the "home internet is
down, both devices on the private network" path:

```bash
ops/mkcert-lan.sh <this-PC-LAN-IP>        # make the DHCP reservation first
# set LAN_BIND_ADDR=<that same IP> in ops/autonomos.env
systemctl --user restart autonomos-api
curl -s http://127.0.0.1:8001/api/health  # origins.lan must now be non-null
```

Keep `TLS_CERTFILE`/`TLS_KEYFILE` **relative** (`ops/certs/...`). Absolute
`/home/david/...` paths work until the username changes and then fail silently:
the listener never starts and `origins.lan` is `null` with no other symptom.

The LAN listener is unauthenticated by design, so the home LAN is its access
boundary. On any network you do not control, leave `LAN_BIND_ADDR` empty.

---

## Phase 8 — The phone (HALT: needs the phone in hand)

`PUBLIC_URL` changed if the tailnet handed you a different name, and browser
permissions are **per-origin**:

1. Remove the old home-screen entry if the origin changed.
2. Add the current tailnet origin, grant microphone permission.
3. If Phase 7 was done: add `https://<LAN-IP>:8443`, grant microphone
   permission, give it a distinct label.

The mkcert root from Phase 3 means no certificate reinstall on Android.

---

## Final verification

```bash
systemctl --user status autonomos-api autonomos-whisper ollama tailscaled
curl -s http://127.0.0.1:8001/api/health   # origins.public non-null
curl -s http://127.0.0.1:8001/api/status   # both sidecars available
cd backend && .venv/bin/python -m pytest -q
```

Then open the tailnet origin on the phone and record **one real voice expense
end to end**, and check that entries from before the format are still listed.
That single action exercises the secure context, whisper, the LLM, a SQLite
write and the restored data — the five things this restore can break.

Keep the backup archive until that has worked for a few days.
