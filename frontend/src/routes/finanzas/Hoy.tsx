import { Link } from 'react-router-dom'
import { useDaySummary } from '../../api/queries'
import { EmptyState } from '../../components/ui/Panel'
import { formatCOP } from '../../format/money'
import { clockTime, longDate } from '../../format/dates'
import { common, hoy } from '../../copy/es'
import type { Expense } from '../../api/types'
import s from './Finanzas.module.css'

/**
 * The default landing screen (1.2). 4.1: today's total and today's expenses,
 * newest first, each showing amount, category and payment method.
 */
export function Hoy() {
  const day = useDaySummary()

  if (day.isPending) return <p className={s.skeleton}>{common.cargando}</p>
  if (!day.data) return null

  const { date, total_cop, expense_count, items } = day.data

  return (
    <>
      <div className={s.hero}>
        <div className={s.when}>{longDate(date)}</div>
        <div className={s.sum}>{formatCOP(total_cop)}</div>
        {expense_count > 0 && <div className={s.sub}>{hoy.gastosContados(expense_count)}</div>}
      </div>

      {/* Constraint 15: a day with nothing on it is a designed state. */}
      {items.length === 0 ? (
        <EmptyState title={hoy.vacioTitulo} body={hoy.vacioCuerpo} />
      ) : (
        <>
          <ExpenseLedger items={items} />
          <div className={s.tail} />
        </>
      )}
    </>
  )
}

/**
 * One row per expense. Nothing here distinguishes a spoken expense from a typed
 * one — the API deliberately returns no `source` field, and 9.5 requires the two
 * to be identical everywhere.
 */
export function ExpenseLedger({ items }: { items: Expense[] }) {
  return (
    <ul className={s.ledger}>
      {items.map((e) => (
        <li key={e.id}>
          <Link className={s.row} to={`/finanzas/gasto/${e.id}`}>
            <span className={s.what}>
              <span className={s.cat}>{e.category_name}</span>
              <span className={s.meta}>
                {[clockTime(e.created_at), e.payment_method_name, e.description]
                  .filter(Boolean)
                  .join(' · ')}
              </span>
            </span>
            <span className={s.amt}>{formatCOP(e.amount_cop)}</span>
          </Link>
        </li>
      ))}
    </ul>
  )
}
