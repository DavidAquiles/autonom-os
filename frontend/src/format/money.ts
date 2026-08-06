/*
 * One formatter and one parser for the whole app (client-side contract:
 * "Amount input and display"; criteria 2.4, 2.5; constraint 21).
 */

/** `14000` → `$14.000`. Colombian convention: `.` thousands, no cents. */
export function formatCOP(amount: number): string {
  return `$${groupThousands(Math.trunc(Math.abs(amount)))}`
}

/** `14000` → `14.000` — the same grouping without the sign, for input fields. */
export function groupThousands(n: number): string {
  const digits = String(Math.trunc(Math.abs(n)))
  let out = ''
  for (let i = 0; i < digits.length; i++) {
    if (i > 0 && (digits.length - i) % 3 === 0) out += '.'
    out += digits[i]
  }
  return out
}

/**
 * `14.000` / `14000` / `14 000` → `14000` (2.4). Also tolerates the non-breaking
 * and thin spaces some Android keyboards emit. Returns null when nothing
 * numeric is left, so the caller can distinguish "empty" from "zero".
 */
export function parseAmount(input: string): number | null {
  const digits = input.replace(/[.\s  ']/g, '')
  if (digits === '' || !/^\d+$/.test(digits)) return null
  const n = Number(digits)
  return Number.isSafeInteger(n) ? n : null
}

/** Live formatting while typing: keeps the digits, regroups the dots. */
export function formatAmountInput(raw: string): string {
  const digits = raw.replace(/\D/g, '').replace(/^0+(?=\d)/, '')
  if (digits === '') return ''
  return groupThousands(Number(digits))
}
