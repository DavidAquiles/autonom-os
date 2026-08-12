#!/usr/bin/env bash
# Gather everything that exists ONLY on this host into one folder to carry to
# the new machine. See ops/README-migration.md for the full move.
#
#   ops/stage-migration.sh              # stage into ~/autonomos-migration
#   ops/stage-migration.sh /media/usb   # stage somewhere else
#   ops/stage-migration.sh --retire     # stage, then leave the API stopped
#
# Code comes from git and models re-download, so neither is staged here. Two
# things have no other copy:
#
#   * data/autonomos.db  — the actual expenses and journal entries
#   * the mkcert CA      — the root the PHONE already trusts; regenerating it on
#                          the new host means installing a new certificate on
#                          Android by hand, warning notice and all
#
# Run this LAST, when you are ready to move. A copy taken a week early is a week
# stale, and this script cannot tell the difference.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${REPO_ROOT}/backend/.venv/bin/python"
CAROOT="${HOME}/.local/share/mkcert"

say()  { printf '\n\033[1m==> %s\033[0m\n' "$1"; }
warn() { printf '\033[33m    ! %s\033[0m\n' "$1"; }
die()  { printf '\n\033[31m==> %s\033[0m\n' "$1" >&2; exit 1; }

RETIRE=0
DEST="${HOME}/autonomos-migration"
for arg in "$@"; do
  case "${arg}" in
    --retire) RETIRE=1 ;;
    -*) die "unknown option: ${arg}" ;;
    *)  DEST="${arg}" ;;
  esac
done

[ -x "${PY}" ] || die "no venv at ${PY} — run ops/setup.sh first"
DB="${REPO_ROOT}/data/autonomos.db"
[ -f "${DB}" ] || die "no database at ${DB}"

say "Staging into ${DEST}"
mkdir -p "${DEST}"
[ -e "${DEST}/autonomos.db" ] && die "${DEST}/autonomos.db already exists — move it aside first"

# Stop the API so nothing writes mid-copy, and remember whether it WAS running
# so a dry run on a live host puts it back exactly as it was found.
WAS_ACTIVE=0
if systemctl --user is-active --quiet autonomos-api; then
  WAS_ACTIVE=1
  say "Stopping autonomos-api"
  systemctl --user stop autonomos-api
  echo "    stopped"
else
  echo "    autonomos-api was already stopped"
fi

# Idempotent, because it runs both explicitly (before the summary, so the
# summary does not claim a restart that has not happened yet) and from the EXIT
# trap, which is what puts the service back when a step above fails.
RESTORED=0
restore_service() {
  [ "${RESTORED}" = "1" ] && return 0
  RESTORED=1
  if [ "${WAS_ACTIVE}" = "1" ] && [ "${RETIRE}" = "0" ]; then
    say "Restarting autonomos-api"
    systemctl --user start autonomos-api || warn "could not restart autonomos-api"
  fi
}
trap restore_service EXIT

say "Copying the database"
# NOT `cp`. The database runs in WAL mode, so recent writes live in a separate
# -wal file; copying the main file alone silently drops them. VACUUM INTO writes
# one self-contained file with no -wal/-shm beside it, which is exactly the
# shape the restore procedure in README-setup.md expects.
"${PY}" - "${DB}" "${DEST}/autonomos.db" <<'PYEOF'
import sqlite3, sys
src, dst = sys.argv[1], sys.argv[2]
con = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
con.execute("VACUUM INTO ?", (dst,))
con.close()
print(f"    wrote {dst}")
PYEOF

say "Verifying the copy"
# A copy that is merely present is not a copy that is correct. Compare every
# table's row count against the source, and integrity-check the result.
"${PY}" - "${DB}" "${DEST}/autonomos.db" <<'PYEOF'
import sqlite3, sys
src, dst = sys.argv[1], sys.argv[2]

def counts(path):
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    out = {t: con.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0] for t in tables}
    con.close()
    return out

a, b = counts(src), counts(dst)
ok = sqlite3.connect(dst).execute("PRAGMA integrity_check").fetchone()[0]
if ok != "ok":
    sys.exit(f"    integrity_check failed: {ok}")
if a != b:
    diff = {k: (a.get(k), b.get(k)) for k in set(a) | set(b) if a.get(k) != b.get(k)}
    sys.exit(f"    row counts differ (source, copy): {diff}")
print(f"    integrity ok; {len(a)} tables, {sum(a.values())} rows match the source")
PYEOF

say "Copying the mkcert root CA"
if [ -d "${CAROOT}" ]; then
  # -a preserves the 0400 on rootCA-key.pem. Losing that mode is not fatal but
  # it leaves a CA signing key world-readable on whatever you carry this on.
  cp -a "${CAROOT}" "${DEST}/mkcert-CA"
  echo "    ${DEST}/mkcert-CA  (restore to ~/.local/share/mkcert on the new host)"
else
  warn "no mkcert CA at ${CAROOT} — skipping (the LAN fallback origin was never set up?)"
fi

say "Copying snapshot history"
if [ -d "${REPO_ROOT}/data/snapshots" ]; then
  cp -a "${REPO_ROOT}/data/snapshots" "${DEST}/snapshots"
  echo "    $(find "${DEST}/snapshots" -name '*.sqlite' | wc -l) snapshots"
else
  warn "no data/snapshots directory"
fi

# Reference only — deliberately NOT named autonomos.env, because dropping this
# straight into the new host is the mistake it exists to prevent. PUBLIC_URL,
# LAN_BIND_ADDR and the TLS paths all name THIS machine.
cp "${REPO_ROOT}/ops/autonomos.env" "${DEST}/autonomos.env.oldhost" 2>/dev/null || true

restore_service

say "Staged"
du -sh "${DEST}"
ls -la "${DEST}"

cat <<NEXT

==> Carry ${DEST} to the new host, then:

 1. The CA, BEFORE running ops/mkcert-lan.sh there:
      cp -a ${DEST##*/}/mkcert-CA ~/.local/share/mkcert
    Do this first and the phone's installed root still validates the new LAN
    certificate — no second Android certificate install.

 2. The database, with the API stopped there:
      cd ~/Proyectos/Autonom-OS
      systemctl --user stop autonomos-api
      rm -f data/autonomos.db data/autonomos.db-wal data/autonomos.db-shm
      cp ${DEST##*/}/autonomos.db data/autonomos.db
      cp -a ${DEST##*/}/snapshots data/snapshots       # optional history
      systemctl --user start autonomos-api

 3. autonomos.env.oldhost is a REFERENCE, not a file to install. Its
    PUBLIC_URL, LAN_BIND_ADDR and TLS paths all name this machine.

NEXT

if [ "${RETIRE}" = "1" ]; then
  cat <<RETIRENEXT
==> --retire: autonomos-api was left stopped.

    Once the new host is verified, finish decommissioning this one:
      systemctl --user disable --now autonomos-api autonomos-whisper ollama
      tailscale serve --https=443 off
      systemctl --user disable --now tailscaled
    Keep this repo and data/ on disk until the new host has run for a few days.

RETIRENEXT
else
  echo "==> autonomos-api is running again. Re-run with --retire when you actually move."
  echo
fi
