import { useEffect, useLayoutEffect, useRef, type RefObject } from 'react'
import { useLocation } from 'react-router-dom'

/**
 * 17.8 — "the same position in the list" — for Hoy, Historial AND the filtered
 * month list (design § "Every list returns in the state it was left in", R1).
 *
 * Nothing restores this for us. The app scrolls inside `<main className={scroll}>`
 * (Screen.tsx), not the document, so neither the browser's history scroll
 * restoration nor React Router touches the offset. R1 calls this the single most
 * likely criterion to be quietly failed, because all three screens look correct
 * in any manual test that does not scroll first.
 *
 * One mechanism, applied once at the Screen scroll container, rather than three
 * screen-local copies (Deferred 3 leaves the mechanism free; that it covers all
 * three lists is not free).
 *
 * Keyed on `location.key`, which React Router assigns per history entry: a POP
 * back to a list returns the key it left with, so the offset is found; a fresh
 * PUSH has no entry and starts at the top, which is what a new location should
 * do. Module scope rather than component state, because the container unmounts
 * on the way to a screen outside `<FinanzasTabs>` and remounts on the way back.
 */
const offsets = new Map<string, number>()

/** Bounded retry budget: the restored rows may render a frame or two late. */
const MAX_FRAMES = 40

export function useScrollMemory(ref: RefObject<HTMLElement | null>) {
  const { key } = useLocation()
  // While the restore loop is writing scrollTop the container fires `scroll`
  // events. Recording those would overwrite the target with the clamped value
  // the not-yet-tall-enough list allows — the offset would decay to near zero
  // and the bug would look like "restoration does not work on long lists".
  const restoring = useRef(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const remember = () => {
      if (!restoring.current) offsets.set(key, el.scrollTop)
    }
    el.addEventListener('scroll', remember, { passive: true })
    // Deliberately does NOT take a final reading on the way out. React runs this
    // passive cleanup AFTER the container has been detached from the document,
    // and a detached element reports `scrollTop === 0` — so a read here does not
    // capture the position, it DESTROYS the one the listener already captured,
    // and every list silently returns to the top. That is R1's exact failure
    // mode, and it survived a code read: it was found by driving a real browser
    // through list → detail → back and reading the offset off <main>.
    return () => el.removeEventListener('scroll', remember)
  }, [key, ref])

  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    const target = offsets.get(key) ?? 0
    if (target === 0) {
      el.scrollTop = 0
      return
    }
    restoring.current = true
    let frames = 0
    let raf = 0
    const settle = () => {
      el.scrollTop = target
      if (Math.abs(el.scrollTop - target) < 1 || ++frames > MAX_FRAMES) {
        restoring.current = false
        return
      }
      raf = requestAnimationFrame(settle)
    }
    settle()
    return () => {
      cancelAnimationFrame(raf)
      restoring.current = false
    }
  }, [key, ref])
}
