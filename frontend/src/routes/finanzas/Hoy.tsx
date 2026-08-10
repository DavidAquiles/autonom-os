import { useDaySummary } from '../../api/queries'
import { EmptyState } from '../../components/ui/Panel'
import { formatCOP } from '../../format/money'
import { longDate } from '../../format/dates'
import { common, hoy } from '../../copy/es'
import { ExpenseLedger } from './ExpenseLedger'
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
          {/* KD-26: the row moved to ExpenseLedger.tsx unchanged. B1 — tapping
              it now opens the read-only detail, which is a route change, not a
              row change: it already linked to /finanzas/gasto/:id. */}
          <ExpenseLedger items={items} variant="hoy" />
          <div className={s.tail} />
        </>
      )}
    </>
  )
}
