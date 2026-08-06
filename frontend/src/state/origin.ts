/*
 * KD-2 mechanism 1. The bundle hardcodes no origin and no port, so the two
 * origins are learned as data: the server advertises both on `GET /api/health`,
 * and the client keeps them.
 *
 * The rule, in the direction it must run: the write happens on EVERY successful
 * health response, into the storage of whatever origin is currently being
 * served, unconditionally. `localStorage` is partitioned by origin, so gating
 * the write on which origin is serving puts the address where the origin that
 * renders the failure can never read it. Overwriting each time is also what
 * lets a changed LAN address self-heal on the next successful load.
 *
 * The read happens when the server is unreachable. There is no fetch at that
 * moment — by definition nothing would answer.
 *
 * Nothing here is user data; it is two strings naming machines on his own
 * network.
 */

const KEY = 'autonomos.origins'

export type OriginKey = 'primary' | 'lan'

export interface Origins {
  primary: string | null
  lan: string | null
}

export interface Alternative {
  key: OriginKey
  origin: string
}

/** An origin is usable only if it parses and is exactly scheme + host + port. */
function usable(value: unknown): string | null {
  if (typeof value !== 'string' || !value) return null
  try {
    const url = new URL(value)
    return url.origin === value.replace(/\/$/, '') ? url.origin : null
  } catch {
    return null
  }
}

/**
 * Obligation 1 — called on every successful `GET /api/health`, never gated on
 * which origin is serving. A response without the field leaves the previous
 * value alone rather than erasing a good address.
 */
export function rememberOrigins(origins: Origins | undefined | null): void {
  if (!origins || typeof origins !== 'object') return
  try {
    window.localStorage.setItem(
      KEY,
      JSON.stringify({ primary: usable(origins.primary), lan: usable(origins.lan) }),
    )
  } catch {
    /* storage disabled — the app works without it, just without the link */
  }
}

/**
 * Obligation 2 — every stored origin that exists and is not the one we are
 * already on. Empty when nothing has been stored yet, which is the named
 * residual in KD-2: an origin that has never once reached the server cannot
 * offer the alternative, and no address is ever guessed to cover that.
 */
export function otherOrigins(): Alternative[] {
  let stored: Partial<Origins>
  try {
    const raw = window.localStorage.getItem(KEY)
    if (!raw) return []
    stored = JSON.parse(raw) as Partial<Origins>
  } catch {
    return []
  }
  if (!stored || typeof stored !== 'object') return []

  const here = window.location.origin
  const out: Alternative[] = []
  for (const key of ['lan', 'primary'] as const) {
    const origin = usable(stored[key])
    if (!origin || origin === here) continue
    if (out.some((a) => a.origin === origin)) continue
    out.push({ key, origin })
  }
  return out
}
