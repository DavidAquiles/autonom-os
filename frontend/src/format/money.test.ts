import { describe, expect, it } from 'vitest'
import { formatAmountInput, formatCOP, parseAmount } from './money'

describe('parseAmount — criterion 2.4', () => {
  it('reads all three forms as fourteen thousand', () => {
    expect(parseAmount('14.000')).toBe(14000)
    expect(parseAmount('14000')).toBe(14000)
    expect(parseAmount('14 000')).toBe(14000)
  })

  it('tolerates the non-breaking spaces an Android keyboard can emit', () => {
    expect(parseAmount('14 000')).toBe(14000)
    expect(parseAmount('14 000')).toBe(14000)
  })

  it('returns null for nothing, so empty is distinguishable from zero', () => {
    expect(parseAmount('')).toBeNull()
    expect(parseAmount('   ')).toBeNull()
    expect(parseAmount('abc')).toBeNull()
    expect(parseAmount('-14000')).toBeNull()
    expect(parseAmount('0')).toBe(0)
  })
})

describe('formatCOP — criterion 2.5, constraint 21', () => {
  it('uses the dot as thousands separator and no cents', () => {
    expect(formatCOP(14000)).toBe('$14.000')
    expect(formatCOP(1284500)).toBe('$1.284.500')
    expect(formatCOP(6200)).toBe('$6.200')
    expect(formatCOP(0)).toBe('$0')
    expect(formatCOP(500)).toBe('$500')
  })
})

describe('formatAmountInput', () => {
  it('regroups while typing', () => {
    expect(formatAmountInput('14000')).toBe('14.000')
    expect(formatAmountInput('1')).toBe('1')
    expect(formatAmountInput('1234567')).toBe('1.234.567')
    expect(formatAmountInput('')).toBe('')
    expect(formatAmountInput('007')).toBe('7')
  })
})
