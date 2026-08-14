#!/usr/bin/env bash
# Pack everything that would be LOST by formatting this PC into one compressed
# archive, together with the instructions to bring it back.
#
#   ops/stage-format-backup.sh                    # -> ~/autonomos-backup-YYYY-MM-DD.tar.gz
#   ops/stage-format-backup.sh /media/usb         # write the archive somewhere else
#   ops/stage-format-backup.sh --no-ssh           # leave the SSH private key out
#   ops/stage-format-backup.sh --no-bundle        # skip the git mirror (~40 MB)
#
# This is the SAME-MACHINE case: wipe and reinstall, restore here. For moving to
# a different host use ops/stage-migration.sh + ops/README-migration.md, which
# regenerate the things that name this machine instead of preserving them.
#
# What is NOT in here, deliberately:
#   * the code            — it is on GitHub, and --bundle mirrors it anyway
#   * ollama / whisper models — ~2.1 GB, re-downloaded by name in the runbook
#   * backend/.venv, frontend/dist, node_modules — rebuilt by ops/setup.sh
#   * the tailscale node key — this host rejoins the tailnet as a new node
#
# Run it LAST, right before you format. A copy taken a week early is a week
# stale and this script cannot tell the difference.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${REPO_ROOT}/backend/.venv/bin/python"
CAROOT="${HOME}/.local/share/mkcert"
STAMP="$(date +%F)"

say()  { printf '\n\033[1m==> %s\033[0m\n' "$1"; }
note() { printf '    %s\n' "$1"; }
warn() { printf '\033[33m    ! %s\033[0m\n' "$1"; }
die()  { printf '\n\033[31m==> %s\033[0m\n' "$1" >&2; exit 1; }

WITH_SSH=1
WITH_BUNDLE=1
OUTDIR="${HOME}"
for arg in "$@"; do
  case "${arg}" in
    --no-ssh)    WITH_SSH=0 ;;
    --no-bundle) WITH_BUNDLE=0 ;;
    -*)          die "unknown option: ${arg}" ;;
    *)           OUTDIR="${arg}" ;;
  esac
done

[ -d "${OUTDIR}" ] || die "not a directory: ${OUTDIR}"
[ -x "${PY}" ]     || die "no venv at ${PY} — this must run on the live host"
DB="${REPO_ROOT}/data/autonomos.db"
[ -f "${DB}" ]     || die "no database at ${DB}"

NAME="autonomos-backup-${STAMP}"
STAGE="$(mktemp -d)/${NAME}"
ARCHIVE="${OUTDIR}/${NAME}.tar.gz"
trap 'rm -rf "$(dirname "${STAGE}")"' EXIT
mkdir -p "${STAGE}"

[ -e "${ARCHIVE}" ] && die "${ARCHIVE} already exists — move it aside first"

# ---------------------------------------------------------------------------
say "Is the code safe on GitHub?"
# The archive carries data, not code. If the branch is ahead of origin and the
# bundle is skipped, formatting loses commits — say so now, not afterwards.
if git -C "${REPO_ROOT}" rev-parse --verify --quiet origin/main >/dev/null; then
  AHEAD="$(git -C "${REPO_ROOT}" rev-list --count origin/main..HEAD)"
  DIRTY="$(git -C "${REPO_ROOT}" status --porcelain | wc -l)"
  if [ "${AHEAD}" != "0" ]; then
    warn "${AHEAD} commit(s) not pushed — run: git push origin main"
  else
    note "in sync with origin/main"
  fi
  [ "${DIRTY}" != "0" ] && warn "${DIRTY} uncommitted change(s) in the working tree"
else
  warn "no origin/main — the git bundle is the only copy of the code"
fi

# ---------------------------------------------------------------------------
WAS_ACTIVE=0
if systemctl --user is-active --quiet autonomos-api; then
  WAS_ACTIVE=1
  say "Stopping autonomos-api so nothing writes mid-copy"
  systemctl --user stop autonomos-api
  note "stopped"
else
  say "autonomos-api is not running"
fi

RESTORED=0
restore_service() {
  [ "${RESTORED}" = "1" ] && return 0
  RESTORED=1
  if [ "${WAS_ACTIVE}" = "1" ]; then
    say "Restarting autonomos-api"
    systemctl --user start autonomos-api || warn "could not restart autonomos-api"
  fi
}
# Runs on any exit, so a failure below never leaves the API stopped.
trap 'restore_service; rm -rf "$(dirname "${STAGE}")"' EXIT

# ---------------------------------------------------------------------------
say "Copying the database"
# NOT `cp`. WAL mode keeps recent writes in a separate -wal file, so copying the
# main file alone drops them silently. VACUUM INTO writes one self-contained
# file with no -wal/-shm — the exact shape the restore expects.
"${PY}" - "${DB}" "${STAGE}/autonomos.db" <<'PYEOF'
import sqlite3, sys
src, dst = sys.argv[1], sys.argv[2]
con = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
con.execute("VACUUM INTO ?", (dst,))
con.close()
print(f"    wrote {dst}")
PYEOF

say "Verifying the copy against the source"
# A copy that is merely present is not a copy that is correct.
"${PY}" - "${DB}" "${STAGE}/autonomos.db" "${STAGE}/rowcounts.txt" <<'PYEOF'
import sqlite3, sys
src, dst, out = sys.argv[1], sys.argv[2], sys.argv[3]

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
with open(out, "w") as fh:
    for t, n in sorted(a.items()):
        fh.write(f"{n:>8}  {t}\n")
print(f"    integrity ok; {len(a)} tables, {sum(a.values())} rows match the source")
PYEOF

# ---------------------------------------------------------------------------
say "Copying snapshot history"
if [ -d "${REPO_ROOT}/data/snapshots" ]; then
  cp -a "${REPO_ROOT}/data/snapshots" "${STAGE}/snapshots"
  note "$(find "${STAGE}/snapshots" -name '*.sqlite' | wc -l) snapshots"
else
  warn "no data/snapshots directory"
fi

say "Copying the gitignored config"
# Named plainly, unlike stage-migration.sh's .oldhost suffix: this is the same
# machine, so the file installs as-is. Only PUBLIC_URL is re-checked, after the
# tailnet hands this host a node name.
cp "${REPO_ROOT}/ops/autonomos.env" "${STAGE}/autonomos.env"
note "autonomos.env"

if [ -d "${REPO_ROOT}/ops/certs" ] && [ -n "$(ls -A "${REPO_ROOT}/ops/certs" 2>/dev/null)" ]; then
  cp -a "${REPO_ROOT}/ops/certs" "${STAGE}/certs"
  note "ops/certs (LAN certificate — reusable, the IP does not change)"
fi

say "Copying the mkcert root CA"
# The root the PHONE already trusts. Losing it means a second Android
# certificate install, warning notice and all.
if [ -d "${CAROOT}" ]; then
  cp -a "${CAROOT}" "${STAGE}/mkcert-CA"     # -a keeps 0400 on rootCA-key.pem
  note "mkcert-CA/  -> restore to ~/.local/share/mkcert BEFORE any mkcert command"
else
  warn "no mkcert CA at ${CAROOT}"
fi

say "Copying the SSH key"
if [ "${WITH_SSH}" = "1" ] && [ -f "${HOME}/.ssh/id_ed25519" ]; then
  mkdir -p "${STAGE}/ssh"
  cp -a "${HOME}/.ssh/id_ed25519" "${HOME}/.ssh/id_ed25519.pub" "${STAGE}/ssh/"
  note "ssh/id_ed25519 — this is what clones the repo back from GitHub"
elif [ "${WITH_SSH}" = "0" ]; then
  note "skipped (--no-ssh): generate a new key and register it at github.com/settings/keys"
else
  warn "no ~/.ssh/id_ed25519"
fi

say "Mirroring the repository"
if [ "${WITH_BUNDLE}" = "1" ]; then
  git -C "${REPO_ROOT}" bundle create "${STAGE}/repo.bundle" --all >/dev/null 2>&1
  note "repo.bundle ($(du -h "${STAGE}/repo.bundle" | cut -f1)) — a clonable mirror if GitHub is unreachable"
else
  note "skipped (--no-bundle): the code comes back from GitHub only"
fi

say "Writing the runbook and manifest"
cp "${REPO_ROOT}/ops/RESTORE-AFTER-FORMAT.md" "${STAGE}/RESTORE.md"

{
  echo "Autonom-OS backup — taken before formatting this PC"
  echo "date          : ${STAMP}"
  echo "host          : $(hostname)  ($(. /etc/os-release 2>/dev/null && echo "${PRETTY_NAME}"))"
  echo "user / home   : ${USER} / ${HOME}"
  # -P, not the logical path: /home/david/Proyectos/autonom-os is a symlink to
  # the real Autonom-OS, and the units hardcode the real one. Restoring to the
  # symlink's spelling gives four units pointing at a directory that is not there.
  echo "repo path     : $(cd "${REPO_ROOT}" && pwd -P)"
  echo "git HEAD      : $(git -C "${REPO_ROOT}" log --oneline -1)"
  echo "git remote    : $(git -C "${REPO_ROOT}" remote get-url origin 2>/dev/null || echo none)"
  echo
  echo "Versions this host was running (see RESTORE.md phase 1):"
  echo "  uv          : $("${HOME}/.local/bin/uv" --version 2>/dev/null || echo '-')"
  echo "  python      : $("${PY}" -V 2>/dev/null || echo '-')"
  echo "  node / npm  : $(node -v 2>/dev/null || echo '-') / $(npm -v 2>/dev/null || echo '-')"
  echo "  ollama      : $("${HOME}/.local/bin/ollama" --version 2>/dev/null | head -1 || echo '-')"
  echo "  tailscale   : $("${HOME}/.local/bin/tailscale" version 2>/dev/null | head -1 || echo '-')"
  echo "  mkcert      : $("${HOME}/.local/bin/mkcert" -version 2>/dev/null || echo '-')"
  echo "  whisper.cpp : $(git -C "${HOME}/.local/whisper.cpp" describe --tags 2>/dev/null || echo '-')"
  echo
  echo "Models to re-pull (NOT in this archive):"
  "${HOME}/.local/bin/ollama" list 2>/dev/null | sed 's/^/  /' || echo "  (ollama not running)"
  echo "  whisper     : ggml-small-q5_1.bin via models/download-ggml-model.sh small-q5_1"
  echo
  echo "Database contents at backup time (row count, table):"
  cat "${STAGE}/rowcounts.txt"
} > "${STAGE}/MANIFEST.txt"
rm -f "${STAGE}/rowcounts.txt"

( cd "${STAGE}" && find . -type f ! -name SHA256SUMS -print0 \
    | sort -z | xargs -0 sha256sum > SHA256SUMS )
note "SHA256SUMS over $(wc -l < "${STAGE}/SHA256SUMS") files"

# ---------------------------------------------------------------------------
say "Compressing"
tar czf "${ARCHIVE}" -C "$(dirname "${STAGE}")" "${NAME}"
chmod 600 "${ARCHIVE}"      # it holds an SSH private key and a CA signing key

say "Verifying the archive"
# Unpack it somewhere else and check the database that actually came out of the
# tarball — not the one that went in.
VERIFY="$(mktemp -d)"
tar xzf "${ARCHIVE}" -C "${VERIFY}"
( cd "${VERIFY}/${NAME}" && sha256sum -c SHA256SUMS >/dev/null ) \
  || die "checksum mismatch inside the archive"
"${PY}" - "${VERIFY}/${NAME}/autonomos.db" <<'PYEOF'
import sqlite3, sys
con = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
ok = con.execute("PRAGMA integrity_check").fetchone()[0]
if ok != "ok":
    sys.exit(f"    unpacked database failed integrity_check: {ok}")
tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' "
                                    "AND name NOT LIKE 'sqlite_%'")]
n = sum(con.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0] for t in tables)
print(f"    unpacked database: integrity ok, {len(tables)} tables, {n} rows")
PYEOF
rm -rf "${VERIFY}"

restore_service

say "Done"
ls -lh "${ARCHIVE}"
tar tzf "${ARCHIVE}" | sed 's/^/    /'

cat <<NEXT

==> This archive is the only copy of your data. It is on the disk you are about
    to erase. Copy it OFF this machine before you format — a USB stick, another
    computer, a phone, cloud storage. Two places is better than one.

      sha256sum ${ARCHIVE}

    Check that hash again after copying: a truncated tarball looks fine in a
    file manager and fails at the moment you need it.

==> It contains an SSH PRIVATE KEY and a CA signing key. Keep it private; if it
    goes to cloud storage, put it in an encrypted container, or re-run with
    --no-ssh and register a fresh key on GitHub afterwards.

==> To restore: extract it and follow RESTORE.md inside — it is the full
    reinstall runbook, from prerequisites to the phone.

NEXT
