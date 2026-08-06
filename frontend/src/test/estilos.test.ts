import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

/**
 * Constraints 1-4, 14 and 22 are properties of the stylesheet, so they are
 * checked by reading it. The screenshot audit checks what a browser paints;
 * this checks what the source is allowed to say, which is what stops a second
 * hue or a dark-mode rule arriving later.
 */
const SRC = resolve(__dirname, '..')

function walk(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name)
    if (statSync(p).isDirectory()) walk(p, out)
    else if (p.endsWith('.css')) out.push(p)
  }
  return out
}

const cssFiles = walk(SRC)
const read = (p: string) => readFileSync(p, 'utf8')

describe('constraint 22 — light mode only', () => {
  it('has no prefers-color-scheme rule anywhere', () => {
    const offenders = cssFiles.filter((p) => /@media[^{]*prefers-color-scheme/.test(read(p)))
    expect(offenders).toEqual([])
  })

  it('declares color-scheme: light', () => {
    expect(read(resolve(SRC, 'styles/tokens.css'))).toMatch(/color-scheme:\s*light/)
  })
})

describe('constraints 1, 2 and 4 — one brand hue, declared in one place', () => {
  it('has no literal colour outside tokens.css, apart from white on violet', () => {
    const offenders: string[] = []
    for (const p of cssFiles) {
      if (p.endsWith('tokens.css')) continue
      for (const m of read(p).matchAll(/#[0-9a-fA-F]{3,8}\b/g)) {
        if (m[0].toLowerCase() !== '#fff' && m[0].toLowerCase() !== '#ffffff')
          offenders.push(`${p}: ${m[0]}`)
      }
      for (const m of read(p).matchAll(/\b(rgb|hsl)a?\(/g)) {
        // rgba() is allowed only for the modal veil, which is ink at 34%.
        if (!p.endsWith('Sheet.module.css')) offenders.push(`${p}: ${m[0]}`)
      }
    }
    expect(offenders).toEqual([])
  })

  it('keeps the whole palette in tokens.css', () => {
    const tokens = read(resolve(SRC, 'styles/tokens.css'))
    expect(tokens).toMatch(/--violet:\s*#5a2fce/i)
    expect(tokens).toMatch(/--danger:\s*#c0182b/i)
    // The breakdown ramp is ten steps of the one hue (constraint 4).
    for (let i = 1; i <= 10; i++) expect(tokens).toMatch(new RegExp(`--t${i}:`))
  })
})

describe('constraint 3 — red is reserved', () => {
  it('uses --danger only for destructive paths, validation errors and a failed save', () => {
    const allowed = new Set([
      'Button.module.css', // .danger / .dangerGhost — destructive confirmation
      'Form.module.css', // validation error text and field borders
      'Panel.module.css', // .alarm — the failed-save banner
    ])
    const offenders = cssFiles.filter(
      (p) => /var\(--danger/.test(read(p)) && !allowed.has(p.split('/').pop()!),
    )
    expect(offenders).toEqual([])
  })
})

describe('constraint 14 — the typeface is self-hosted and openly licensed', () => {
  it('loads Lato from the repo and never from a remote host', () => {
    const base = read(resolve(SRC, 'styles/base.css'))
    expect(base).toMatch(/@font-face/)
    expect(base).toMatch(/assets\/fonts\/lato-\d00\.woff2/)
    expect(base).not.toMatch(/https?:\/\//)
  })
})

describe('KD-13 — the service worker caches the shell and nothing else', () => {
  const sw = readFileSync(resolve(SRC, 'sw/sw-template.js'), 'utf8')

  it('treats /api/* as NetworkOnly', () => {
    expect(sw).toMatch(/url\.pathname\.startsWith\('\/api\/'\)/)
    // The early return happens before any caches.match for that path.
    const apiGuard = sw.indexOf("startsWith('/api/')")
    const firstCacheMatch = sw.indexOf('caches.match')
    expect(apiGuard).toBeLessThan(firstCacheMatch)
  })

  it('has no write queue and no background sync', () => {
    // Comments describe the policy; the code is what is checked.
    const code = sw.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '')
    expect(code).not.toMatch(/addEventListener\(\s*'sync'|SyncManager|indexedDB|localStorage/)
    // A non-GET request is never touched at all, so no write can be queued.
    expect(code).toMatch(/request\.method !== 'GET'/)
  })
})
