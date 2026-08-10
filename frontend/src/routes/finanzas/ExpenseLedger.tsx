import { Link, useLocation } from 'react-router-dom'
import { formatCOP } from '../../format/money'
import { clockTime, shortDate } from '../../format/dates'
import type { Expense } from '../../api/types'
import s from './Finanzas.module.css'

/**
 * KD-26: ONE expense row, three content variants. Constraint 30 requires
 * Historial's rows to be structurally identical to Hoy's — "the two screenshots
 * differ in content, not in structure" — and that only survives review if there
 * is one implementation. Three copies drift on the first CSS tweak.
 *
 * Nothing here distinguishes a spoken expense from a typed one: the API returns
 * no `source` field at all (9.5, 17.10, constraint 43).
 *
 * B1 / 17.1: every row anywhere links to the read-only detail. No list links to
 * `…/editar` — that is what makes "a mis-tap is harmless" true by construction
 * rather than in three places that can each be forgotten.
 */
export type LedgerVariant = 'hoy' | 'historial' | 'categoria'

export function ExpenseLedger({
  items,
  variant = 'hoy',
}: {
  items: Expense[]
  variant?: LedgerVariant
}) {
  const location = useLocation()
  // 17.9: where to land after deleting from the edit form, since by then the
  // detail entry behind it is dead. Pathname AND search — dropping the search
  // half would reset the month and the selection on the delete path, which is
  // exactly the reset B2 exists to remove.
  const desde = location.pathname + location.search

  return (
    <ul className={s.ledger}>
      {items.map((e) => (
        <li key={e.id}>
          <Link className={s.row} to={`/finanzas/gasto/${e.id}`} state={{ desde }}>
            <span className={s.what}>
              <span className={s.cat}>{primary(e, variant)}</span>
              <span className={s.meta}>{secondary(e, variant)}</span>
            </span>
            <span className={s.amt}>{formatCOP(e.amount_cop)}</span>
          </Link>
        </li>
      ))}
    </ul>
  )
}

/**
 * The filtered category list is every row of one category, so repeating the
 * name would say nothing; the date leads instead, because that list is ordered
 * by date (18.13) and the date is what makes the order legible.
 */
function primary(e: Expense, variant: LedgerVariant): string {
  return variant === 'categoria' ? shortDate(e.spent_on) : e.category_name
}

/**
 * 16.5 — Historial shows amount, category, payment method and the date the
 * expense is DATED FOR. The date leads the secondary line because it is the
 * fact that makes a non-descending list legible (16.6), so it must never be the
 * thing the ellipsis eats.
 * 18.12 — the filtered list shows amount, payment method, date and description
 * where there is one.
 */
function secondary(e: Expense, variant: LedgerVariant): string {
  const facts =
    variant === 'historial'
      ? [shortDate(e.spent_on), e.payment_method_name]
      : variant === 'categoria'
        ? [e.payment_method_name, e.description]
        : [clockTime(e.created_at), e.payment_method_name, e.description]
  return facts.filter(Boolean).join(' · ')
}
