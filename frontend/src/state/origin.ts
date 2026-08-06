/*
 * KD-2: the bundle hardcodes no origin and no port. The LAN fallback address is
 * therefore learned rather than written down — the app remembers the origin it
 * was served from whenever that origin is not the tailnet one, which happens at
 * least once during setup when the second home-screen icon is installed.
 *
 * Nothing here is user data; it is one string naming a machine on his own LAN.
 */

const KEY = 'autonomos.homeOrigin'

export function rememberOriginIfHome(): void {
  try {
    const isTailnet = /\.ts\.net$/i.test(window.location.hostname)
    if (!isTailnet && window.location.protocol === 'https:') {
      window.localStorage.setItem(KEY, window.location.origin)
    }
  } catch {
    /* storage disabled — the app works without it */
  }
}

export function rememberedHomeOrigin(): string | null {
  try {
    const stored = window.localStorage.getItem(KEY)
    if (!stored) return null
    // Never offer a link back to where we already are.
    return stored === window.location.origin ? null : stored
  } catch {
    return null
  }
}
