#!/usr/bin/env bash
# Autonom-OS one-time host setup. Installs four systemd USER units, nothing as
# root, and enables lingering so they survive a reboot with no login session.
#
#   ops/setup.sh            # install and start everything
#   ops/setup.sh --units    # (re)install unit files only
#   ops/setup.sh --check    # preflight only: ports and prerequisites, no changes
#
# What this does NOT do, because it needs a human at a keyboard:
#   * `tailscale up` (interactive login)
#   * `tailscale serve` (run it once after login — printed at the end)
#   * granting microphone permission on the phone for both origins
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OPS="${REPO_ROOT}/ops"
UNIT_DIR="${HOME}/.config/systemd/user"
UNITS=(autonomos-api.service autonomos-whisper.service ollama.service tailscaled.service)

MODE="${1:-}"

say() { printf '\n\033[1m==> %s\033[0m\n' "$1"; }
warn() { printf '\033[33m    ! %s\033[0m\n' "$1"; }
die() { printf '\n\033[31m==> %s\033[0m\n' "$1" >&2; exit 1; }

env_value() {
  # Read NAME from ops/autonomos.env, falling back to the example, then $2.
  local name="$1" default="$2" file
  for file in "${OPS}/autonomos.env" "${OPS}/autonomos.env.example"; do
    if [ -f "${file}" ]; then
      local found
      found="$(sed -n "s/^[[:space:]]*${name}=//p" "${file}" | tail -n1)"
      [ -n "${found}" ] && { printf '%s' "${found}"; return; }
    fi
  done
  printf '%s' "${default}"
}

port_is_listening() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -ltn 2>/dev/null | awk '{print $4}' | grep -qE "[:.]${port}\$"
  else
    (exec 3<>"/dev/tcp/127.0.0.1/${port}") >/dev/null 2>&1
  fi
}

say "Preflight: ports"
# This collision is not hypothetical. Port 8000 on this host belongs to an
# unrelated project's Docker container (trace_erp_api, published on all
# interfaces); a unit pointed at an occupied port crash-loops on start and the
# failure reads like a bug in this app. Fail here instead, with the port named.
API_PORT="$(env_value AUTONOMOS_API_PORT 8001)"
LAN_PORT="$(env_value LAN_PORT 8443)"
LAN_ADDR="$(env_value LAN_BIND_ADDR '')"

if port_is_listening "${API_PORT}"; then
  cat >&2 <<EOF

    Port ${API_PORT} is already in use by something else on this machine.

    Do NOT stop whatever holds it — it may belong to another project (port 8000
    here is an unrelated ERP container). Pick a free port instead:

      1. set AUTONOMOS_API_PORT=<free port> in ops/autonomos.env
      2. re-run ops/setup.sh
      3. point Tailscale at the new port:
           tailscale serve --bg https / http://127.0.0.1:<free port>
EOF
  die "refusing to install a unit that would crash-loop on port ${API_PORT}"
fi
echo "    API port ${API_PORT} is free"

if [ -n "${LAN_ADDR}" ] && port_is_listening "${LAN_PORT}"; then
  warn "LAN fallback port ${LAN_PORT} is already in use; change LAN_PORT"
else
  echo "    LAN fallback port ${LAN_PORT} is free"
fi
for sidecar in 8081 11434; do
  if port_is_listening "${sidecar}"; then
    echo "    ${sidecar} already listening (sidecar already running — fine)"
  fi
done

require() {
  if [ ! -e "$1" ]; then
    warn "missing: $1${2:+  ($2)}"
    MISSING=1
  else
    printf '    ok: %s\n' "$1"
  fi
}

say "Checking what this host already has"
MISSING=0
require "${HOME}/.local/bin/uv" "curl -LsSf https://astral.sh/uv/install.sh | sh"
require "${HOME}/.local/bin/ollama" "https://ollama.com/download"
require "${HOME}/.local/whisper.cpp/build/bin/whisper-server" "build whisper.cpp"
require "${HOME}/.local/whisper.cpp/models/ggml-small-q5_1.bin" "download-ggml-model.sh small"
require "${HOME}/.local/bin/tailscale" "https://tailscale.com/download"
require "${HOME}/.local/bin/mkcert" "needed only for the LAN fallback origin"
[ "${MISSING}" = "1" ] && warn "install the items above before starting the units"

if [ "${MODE}" = "--check" ]; then
  say "Preflight only (--check): nothing was installed or changed"
  exit 0
fi

say "Configuration"
if [ ! -f "${OPS}/autonomos.env" ]; then
  cp "${OPS}/autonomos.env.example" "${OPS}/autonomos.env"
  echo "    created ops/autonomos.env from the example"
  warn "set LAN_BIND_ADDR to this PC's DHCP-reserved LAN address (or leave it"
  warn "unset to run without the LAN fallback origin)"
else
  echo "    ops/autonomos.env already exists — left untouched"
fi
mkdir -p "${REPO_ROOT}/data/snapshots" "${OPS}/certs"

if [ "${MODE}" != "--units" ]; then
  say "Python environment (CPython 3.12 is pinned; the system 3.14 is not used)"
  cd "${REPO_ROOT}/backend"
  "${HOME}/.local/bin/uv" venv --python "${HOME}/.local/bin/python3.12" .venv
  "${HOME}/.local/bin/uv" pip install -e .
  cd "${REPO_ROOT}"
fi

say "Installing systemd user units"
mkdir -p "${UNIT_DIR}"
for unit in "${UNITS[@]}"; do
  cp "${OPS}/systemd/${unit}" "${UNIT_DIR}/${unit}"
  echo "    ${UNIT_DIR}/${unit}"
done
systemctl --user daemon-reload

say "Enabling lingering so the units start at boot without a login session"
# User units do not run before first login unless lingering is on. 14.1 and 13.7
# both require the thing to just be there after a restart.
if loginctl enable-linger "${USER}"; then
  echo "    linger enabled for ${USER}"
else
  warn "loginctl enable-linger failed; the units will only run while logged in"
fi

say "Starting units"
for unit in "${UNITS[@]}"; do
  systemctl --user enable --now "${unit}" || warn "could not start ${unit}"
done
sleep 3
systemctl --user --no-pager --lines=0 status "${UNITS[@]}" || true

say "Health"
curl -fsS --max-time 5 "http://127.0.0.1:${API_PORT}/api/health" && echo || warn "API not answering yet"
curl -fsS --max-time 5 "http://127.0.0.1:${API_PORT}/api/status" && echo || true

cat <<NEXT

==> Remaining steps, which need you at the keyboard

 1. Join the tailnet (interactive, one time):
      ~/.local/bin/tailscale --socket=\$HOME/.local/share/tailscale/tailscaled.sock up
    Then disable key expiry for this node in the Tailscale admin console (R2).

 2. Publish the app over HTTPS on the tailnet — this is what makes voice
    capture possible at all, because getUserMedia needs a secure context.
    Note the port: ${API_PORT}, not 8000, which belongs to another project here.
      ~/.local/bin/tailscale --socket=\$HOME/.local/share/tailscale/tailscaled.sock \\
          serve --bg https / http://127.0.0.1:${API_PORT}
    Funnel (the public option) must stay OFF (13.6).

 3. LAN fallback origin for 15.5 (home internet down):
      ops/mkcert-lan.sh <this-PC-LAN-IP>
    then set LAN_BIND_ADDR in ops/autonomos.env and:
      systemctl --user restart autonomos-api

 4. On the phone: add BOTH origins to the home screen, and grant microphone
    permission on BOTH, at setup time — browser permission is per-origin, and
    15.5's scenario must not begin with a permission prompt.
NEXT
