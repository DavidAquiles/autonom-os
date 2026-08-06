import { describe, expect, it } from 'vitest'
import { clockTime, dateOf, longDate, monthLabel, shiftDay, shiftMonth, elapsedLabel } from './dates'

describe('date rendering — Spanish, and never derived from the device clock', () => {
  it('renders a calendar date as the parts it already is', () => {
    expect(longDate('2026-08-05')).toBe('miércoles 5 de agosto')
    expect(monthLabel('2026-08')).toBe('agosto 2026')
  })

  it('reads the time from the offset the server sent, not the device timezone', () => {
    // 4.8: an 11pm expense belongs to that day. The server sends -05:00; the
    // machine running this test may be anywhere.
    expect(clockTime('2026-08-05T23:14:07.975-05:00')).toBe('23:14')
    expect(dateOf('2026-08-05T23:14:07.975-05:00')).toBe('2026-08-05')
  })

  it('walks months and days on the calendar, with no DST to shift it', () => {
    expect(shiftMonth('2026-01', -1)).toBe('2025-12')
    expect(shiftMonth('2026-12', 1)).toBe('2027-01')
    expect(shiftDay('2026-03-01', -1)).toBe('2026-02-28')
    expect(shiftDay('2024-02-28', 1)).toBe('2024-02-29')
  })

  it('says how long something took in Spanish units', () => {
    expect(elapsedLabel(47_000)).toBe('47 s')
    expect(elapsedLabel(72_000)).toBe('1 min 12 s')
    expect(elapsedLabel(120_000)).toBe('2 min')
  })
})
