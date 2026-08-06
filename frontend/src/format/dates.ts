/*
 * Date presentation only. The SERVER is authoritative for what "today" and
 * "this month" are (design.md § Time, 4.8) — nothing here derives a day or a
 * month boundary from the device clock. Every function takes a date the server
 * has already decided and only renders it.
 */

const DIAS = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado']
const MESES = [
  'enero',
  'febrero',
  'marzo',
  'abril',
  'mayo',
  'junio',
  'julio',
  'agosto',
  'septiembre',
  'octubre',
  'noviembre',
  'diciembre',
]

/** Reads `YYYY-MM-DD` as calendar parts. No timezone maths: these ARE the parts. */
function parts(isoDate: string): { y: number; m: number; d: number } {
  const [y, m, d] = isoDate.slice(0, 10).split('-').map(Number)
  return { y, m, d }
}

/** Weekday for a calendar date, computed without touching local time. */
function weekday(isoDate: string): number {
  const { y, m, d } = parts(isoDate)
  return new Date(Date.UTC(y, m - 1, d)).getUTCDay()
}

/** `2026-08-05` → `miércoles 5 de agosto` */
export function longDate(isoDate: string): string {
  const { m, d } = parts(isoDate)
  return `${DIAS[weekday(isoDate)]} ${d} de ${MESES[m - 1]}`
}

/** `2026-08-05` → `5 de agosto` */
export function shortDate(isoDate: string): string {
  const { m, d } = parts(isoDate)
  return `${d} de ${MESES[m - 1]}`
}

/** `2026-08` → `agosto 2026` */
export function monthLabel(monthKey: string): string {
  const [y, m] = monthKey.slice(0, 7).split('-').map(Number)
  return `${MESES[m - 1]} ${y}`
}

/** `2026-08` → `agosto` */
export function monthName(monthKey: string): string {
  const m = Number(monthKey.slice(5, 7))
  return MESES[m - 1]
}

/** ISO-8601 with offset → `21:14`, using the offset the server sent. */
export function clockTime(iso: string): string {
  const match = iso.match(/T(\d{2}):(\d{2})/)
  return match ? `${match[1]}:${match[2]}` : ''
}

/** ISO-8601 with offset → the local calendar date it names, `YYYY-MM-DD`. */
export function dateOf(iso: string): string {
  return iso.slice(0, 10)
}

/** ISO-8601 with offset → `1 de agosto a las 03:12` */
export function stamp(iso: string): string {
  return `${shortDate(dateOf(iso))} a las ${clockTime(iso)}`
}

/** Calendar arithmetic on `YYYY-MM` keys, no Date involved. */
export function shiftMonth(monthKey: string, delta: number): string {
  const [y, m] = monthKey.slice(0, 7).split('-').map(Number)
  const total = y * 12 + (m - 1) + delta
  const ny = Math.floor(total / 12)
  const nm = (total % 12) + 1
  return `${ny}-${String(nm).padStart(2, '0')}`
}

/** Calendar arithmetic on `YYYY-MM-DD`, done in UTC so no DST can shift it. */
export function shiftDay(isoDate: string, delta: number): string {
  const { y, m, d } = parts(isoDate)
  const t = new Date(Date.UTC(y, m - 1, d + delta))
  return t.toISOString().slice(0, 10)
}

/** Elapsed milliseconds → `1 min 12 s` / `47 s`. */
export function elapsedLabel(ms: number): string {
  const total = Math.max(0, Math.round(ms / 1000))
  if (total < 60) return `${total} s`
  const min = Math.floor(total / 60)
  const sec = total % 60
  return sec === 0 ? `${min} min` : `${min} min ${sec} s`
}

/** Seconds → `0:07`, for the recording clock. */
export function mmss(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}
