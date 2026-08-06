#!/usr/bin/env bash
# Certificate for the LAN fallback origin (KD-2).
#
#   ops/mkcert-lan.sh 192.168.1.50
#
# The certificate names a FIXED LAN IP, not `.local`: mDNS resolution of
# `.local` from Android Chrome is unreliable, so the IP goes in the SAN and the
# hostname is a convenience only. The address is stable because you make a DHCP
# reservation for it on the router — do that first.
set -euo pipefail

LAN_IP="${1:-}"
if [ -z "${LAN_IP}" ]; then
  echo "usage: ops/mkcert-lan.sh <LAN-IP>   (e.g. 192.168.1.50)" >&2
  exit 2
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CERT_DIR="${REPO_ROOT}/ops/certs"
MKCERT="${HOME}/.local/bin/mkcert"
mkdir -p "${CERT_DIR}"

"${MKCERT}" -install
"${MKCERT}" \
  -cert-file "${CERT_DIR}/lan-cert.pem" \
  -key-file  "${CERT_DIR}/lan-key.pem" \
  "${LAN_IP}" autonomos.local localhost 127.0.0.1

cat <<NEXT

Certificate written to ops/certs/.

Next:
  1. Set LAN_BIND_ADDR=${LAN_IP} in ops/autonomos.env  (never 0.0.0.0)
  2. systemctl --user restart autonomos-api
  3. Install the mkcert root CA on the phone, once:
       $("${MKCERT}" -CAROOT)/rootCA.pem
     Copy it to the phone and add it under
       Settings -> Security -> Encryption & credentials -> Install a certificate
     Android will show a standing "network may be monitored" notice; that is
     expected for a user-installed CA and is why this is the fallback, not the
     primary origin.
  4. Open https://${LAN_IP}:8443 on the phone, add it to the home screen with a
     distinct label, and grant microphone permission there too.
NEXT
