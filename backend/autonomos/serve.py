"""Process entry point serving **two origins from one process** (KD-2).

| Origin | Bind | Purpose |
| --- | --- | --- |
| `https://<host>.<tailnet>.ts.net` | `tailscale serve` -> `127.0.0.1:8001` | primary |
| `https://<LAN-IP>:8443` | uvicorn TLS on `${LAN_BIND_ADDR}` | LAN fallback for 15.5 |

The loopback port is 8001 rather than the conventional 8000 because 8000 is
permanently occupied on this host by an unrelated project's container; it is
`AUTONOMOS_API_PORT` and may be changed.

Two uvicorn *processes* would mean two InferenceArbiters and two schedulers,
which KD-3 rules out ("two arbiters is the same as none"), so both listeners are
`uvicorn.Server` instances inside one event loop over one app. The LAN listener
runs continuously, because 15.5 can occur at any moment and a listener that must
be started by hand during an outage is not a mechanism.

    python -m autonomos.serve
"""

from __future__ import annotations

import asyncio
import logging

import uvicorn

from .config import get_settings, lan_fallback_status
from .main import configure_logging, create_app

log = logging.getLogger("autonomos.serve")


async def _run() -> None:
    configure_logging()
    settings = get_settings()
    app = create_app()

    servers = [
        uvicorn.Server(
            uvicorn.Config(
                app,
                host=settings.api_host,
                port=settings.api_port,
                workers=1,
                access_log=False,
                lifespan="on",
            )
        )
    ]
    # One predicate, shared with GET /api/health: the origin advertised to
    # the client and the listener that must answer it cannot disagree.
    enabled, reason = lan_fallback_status(settings)
    if enabled:
        servers.append(
            uvicorn.Server(
                uvicorn.Config(
                    app,
                    host=settings.lan_bind_addr,
                    port=settings.lan_port,
                    workers=1,
                    access_log=False,
                    lifespan="off",  # the primary listener owns startup
                    ssl_certfile=settings.tls_certfile,
                    ssl_keyfile=settings.tls_keyfile,
                )
            )
        )
        log.info(
            "LAN fallback origin on https://%s:%s",
            settings.lan_bind_addr,
            settings.lan_port,
        )
    else:
        log.warning("LAN fallback origin not started: %s", reason)

    await asyncio.gather(*(server.serve() for server in servers))


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
