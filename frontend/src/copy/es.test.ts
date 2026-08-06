import { describe, expect, it } from 'vitest'
import * as copy from './es'

/**
 * 1.5 and constraint 23: every string the interface can show is Spanish, and
 * the backend's closed error-code set is fully mapped. A code the frontend
 * cannot translate would surface as a developer string, which KD-17 forbids.
 */
const CONTRACT_CODES = [
  'validation',
  'not_found',
  'conflict',
  'in_use',
  'audio_invalid',
  'audio_too_long',
  'transcription_failed',
  'transcription_timeout',
  'llm_unavailable',
  'llm_timeout',
  'insufficient_data',
  'unverifiable_figures',
  'period_unrecognised',
  'preempted',
  'busy',
  'internal',
]

describe('the error-code map', () => {
  it('covers every code in the Interface Contract', () => {
    for (const code of CONTRACT_CODES) {
      expect(copy.errores[code], `missing Spanish copy for ${code}`).toBeTruthy()
    }
  })

  it('has nothing outside the closed set', () => {
    expect(Object.keys(copy.errores).sort()).toEqual([...CONTRACT_CODES].sort())
  })

  it('never falls through to an untranslated code', () => {
    expect(copy.errorEnEspanol('something_new')).toBe(copy.errores.internal)
  })
})

describe('every field reason has Spanish', () => {
  it('names the offending field for 2.2 and 2.3', () => {
    expect(copy.razonEnEspanol('amount_cop', 'must_be_positive')).toMatch(/monto/i)
    expect(copy.razonEnEspanol('category_id', 'required')).toMatch(/categoría/i)
    expect(copy.razonEnEspanol('payment_method_id', 'required')).toMatch(/método de pago/i)
    expect(copy.razonEnEspanol('spent_on', 'future_date')).toMatch(/futura/i)
    expect(copy.razonEnEspanol('text', 'blank')).toMatch(/escribe/i)
  })
})

describe('no English leaks into the interface', () => {
  const collect = (o: unknown, out: string[] = []): string[] => {
    if (typeof o === 'string') out.push(o)
    else if (o && typeof o === 'object')
      for (const v of Object.values(o)) collect(v, out)
    return out
  }

  it('has no obviously English words in any static string', () => {
    const strings = collect(
      Object.fromEntries(
        Object.entries(copy).filter(([, v]) => typeof v === 'object' && v !== null),
      ),
    )
    const english = /\b(save|cancel|delete|loading|error|settings|today|month|search|submit)\b/i
    const offenders = strings.filter((s) => english.test(s))
    expect(offenders).toEqual([])
  })

  it('keeps accents, ñ and the opening marks intact', () => {
    expect(copy.analisis.preguntaPlaceholder.startsWith('¿')).toBe(true)
    expect(copy.gasto.categoria).toBe('Categoría')
    expect(copy.diario.ayuda).toContain('línea')
  })
})
