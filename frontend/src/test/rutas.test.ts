import { readFileSync, readdirSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

/**
 * B1's second pinning. The behavioural tests check that a row opens the detail;
 * this checks that the behaviour cannot be undone in a place they do not look.
 *
 * A list added in a later run that re-points at the form is precisely how B1
 * would regress — invisibly, with every other test still green — because the
 * new list would have no test of its own. A source read is the only thing that
 * covers code nobody has written yet.
 */
const FINANZAS = resolve(__dirname, '..', 'routes', 'finanzas')
const read = (f: string) => readFileSync(join(FINANZAS, f), 'utf8')
const files = readdirSync(FINANZAS).filter((f) => f.endsWith('.tsx'))

describe('B1 / 17.1 — no list anywhere links to the edit form', () => {
  it('reaches /finanzas/gasto/:id/editar from the detail screen and nowhere else', () => {
    const offenders = files.filter(
      (f) => f !== 'GastoDetalle.tsx' && /\/finanzas\/gasto\/[^'"`]*editar/.test(read(f)),
    )
    expect(offenders).toEqual([])
  })

  it('has the detail screen actually make that navigation, so the rule is not vacuous', () => {
    expect(read('GastoDetalle.tsx')).toMatch(/\/finanzas\/gasto\/\$\{[^}]+\}\/editar/)
  })

  it('routes /finanzas/gasto/:id to the detail and .../editar to the form', () => {
    const app = readFileSync(resolve(__dirname, '..', 'App.tsx'), 'utf8')
    expect(app).toMatch(/path="\/finanzas\/gasto\/:id"\s+element=\{<GastoDetalle \/>\}/)
    expect(app).toMatch(/path="\/finanzas\/gasto\/:id\/editar"\s+element=\{<EditarGasto \/>\}/)
  })
})

describe('KD-25 — the list key prefix is invalidated, and is visibly its own prefix', () => {
  it('invalidates expense-list alongside expense on every expense mutation', () => {
    const queries = readFileSync(resolve(__dirname, '..', 'api', 'queries.ts'), 'utf8')
    const fn = queries.match(/function invalidateExpenseViews[\s\S]*?\n}/)![0]
    // Neither prefix implies the other: TanStack matches element by element.
    expect(fn).toContain("queryKey: ['expense']")
    expect(fn).toContain("queryKey: ['expense-list']")
    // The near-miss KD-25 exists to remove — checked against the code, with
    // comments stripped, since naming the wrong prefix to warn about it is
    // exactly what a comment here has to do.
    const code = queries.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '')
    expect(code).not.toMatch(/\['expenses'/)
  })
})
