/*
 * The accessibility audit, carried over from the Phase 1 mockup pass and now run
 * against the built app. It caught two real classes of defect there and those
 * are exactly the ones that regress when hand-written CSS becomes components:
 *
 *   - a contrast failure that existed ONLY in :active (4.23:1 secondary text on
 *     the pressed tint), invisible in every static render;
 *   - three touch targets under 44x44.
 *
 * It walks every text-bearing element, resolves the background actually painted
 * behind it, computes the WCAG 2.1 ratio, and compares against 4.5 (or 3.0 for
 * large text). It also measures every interactive box and reports horizontal
 * overflow. Run under forced pseudo-states, it audits states no screenshot shows.
 */
export const AUDIT_JS = `(() => {
  const lum = (c) => {
    const m = c.match(/[\\d.]+/g)
    if (!m) return null
    const a = m.length > 3 ? parseFloat(m[3]) : 1
    if (a === 0) return null
    const f = [m[0], m[1], m[2]].map((v) => {
      v = v / 255
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4)
    })
    return { L: 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2], a }
  }
  const bgOf = (el) => {
    let e = el
    while (e && e !== document.documentElement) {
      const o = lum(getComputedStyle(e).backgroundColor)
      if (o && o.a >= 0.95) return o
      e = e.parentElement
    }
    return { L: 1, a: 1 }
  }

  const contrast = []
  const targets = []
  const all = document.querySelectorAll('*')

  for (const el of all) {
    const cs = getComputedStyle(el)
    if (cs.display === 'none' || cs.visibility === 'hidden') continue
    const box = el.getBoundingClientRect()

    let hasText = false
    for (const n of el.childNodes) {
      if (n.nodeType === 3 && n.textContent.trim().length > 0) { hasText = true; break }
    }
    if (hasText && box.width > 0 && box.height > 0) {
      const fg = lum(cs.color)
      if (fg && fg.a > 0.1) {
        const bg = bgOf(el)
        const r = (Math.max(fg.L, bg.L) + 0.05) / (Math.min(fg.L, bg.L) + 0.05)
        const size = parseFloat(cs.fontSize)
        const w = parseInt(cs.fontWeight, 10) || 400
        const large = size >= 24 || (size >= 18.66 && w >= 700)
        const need = large ? 3 : 4.5
        if (r < need - 0.005) {
          contrast.push({
            tag: el.tagName,
            cls: String(el.className || ''),
            ratio: Number(r.toFixed(2)),
            need,
            text: el.textContent.trim().slice(0, 32),
          })
        }
      }
    }

    if (el.matches('a[href],button,input,textarea,select,[role="button"],[role="radio"],[role="progressbar"]')) {
      if (el.getAttribute('role') === 'progressbar') continue
      if (box.width > 0 && box.height > 0 && (box.width < 44 || box.height < 44)) {
        targets.push({
          tag: el.tagName,
          cls: String(el.className || ''),
          w: Math.round(box.width),
          h: Math.round(box.height),
          text: (el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 32),
        })
      }
    }
  }

  const overflow = document.documentElement.scrollWidth > window.innerWidth + 0.5

  // Constraint 22 tripwire: a dark-mode rule must not exist anywhere.
  let darkRules = 0
  for (const sheet of document.styleSheets) {
    let rules
    try { rules = sheet.cssRules } catch { continue }
    for (const rule of rules || []) {
      if (rule.conditionText && /prefers-color-scheme/.test(rule.conditionText)) darkRules++
    }
  }

  return { contrast, targets, overflow, darkRules, scrollWidth: document.documentElement.scrollWidth, innerWidth: window.innerWidth }
})()`
