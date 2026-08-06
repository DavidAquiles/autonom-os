import { useState } from 'react'
import { useHealth, useMonthSummary } from '../../api/queries'
import { EmptyState, SectionLabel } from '../../components/ui/Panel'
import { LeftIcon, RightIcon } from '../../components/ui/Icon'
import { formatCOP } from '../../format/money'
import { monthLabel, monthName, shiftMonth } from '../../format/dates'
import { common, mes } from '../../copy/es'
import s from './Finanzas.module.css'

const TINTS = [
  'var(--t1)',
  'var(--t2)',
  'var(--t3)',
  'var(--t4)',
  'var(--t5)',
  'var(--t6)',
  'var(--t7)',
  'var(--t8)',
  'var(--t9)',
  'var(--t10)',
]

/**
 * 4.2-4.4, 4.7. The breakdown is a ranked list with proportional bars, not a
 * chart: it answers "where did it go" in reading order, and every segment
 * carries its own label and number (constraint 6).
 */
export function Mes() {
  // The server decides what the current month is (4.8) — /health carries its
  // clock, and the response's own `month` is what we render and page from.
  const health = useHealth()
  const currentMonth = health.data ? health.data.server_time.slice(0, 7) : undefined
  const [month, setMonth] = useState<string | undefined>(undefined)
  const summary = useMonthSummary(month)

  if (summary.isPending) return <p className={s.skeleton}>{common.cargando}</p>
  if (!summary.data) return null

  const data = summary.data
  const atCurrent = currentMonth ? data.month >= currentMonth : true

  return (
    <>
      <div className={`${s.hero} ${s.heroMonth}`}>
        <div className={s.monthnav}>
          <span className={s.mname}>{monthLabel(data.month)}</span>
          <button
            type="button"
            className={s.arrow}
            aria-label={mes.mesAnterior}
            onClick={() => setMonth(shiftMonth(data.month, -1))}
          >
            <LeftIcon />
          </button>
          <button
            type="button"
            className={s.arrow}
            aria-label={mes.mesSiguiente}
            disabled={atCurrent}
            onClick={() => setMonth(shiftMonth(data.month, 1))}
          >
            <RightIcon />
          </button>
        </div>
        {!data.is_empty && (
          <>
            <div className={s.sum}>{formatCOP(data.total_cop)}</div>
            <div className={s.sub}>{mes.gastosContados(data.expense_count)}</div>
          </>
        )}
      </div>

      {/* 4.5: an empty month is a plain empty state — never a zeroed breakdown. */}
      {data.is_empty ? (
        <EmptyState title={mes.vacioTitulo(monthName(data.month))} body={mes.vacioCuerpo} />
      ) : (
        <>
          <SectionLabel>{mes.enQueSeFue}</SectionLabel>
          <ul className={s.brk}>
            {data.by_category.map((c, i) => (
              <li key={c.category_id}>
                <div className={s.line}>
                  <span className={s.name}>{c.name}</span>
                  <span className={s.val}>{formatCOP(c.amount_cop)}</span>
                  <span className={s.pct}>{c.percent} %</span>
                </div>
                <div className={s.track}>
                  <div
                    className={s.fill}
                    style={{
                      width: `${c.percent}%`,
                      background: TINTS[Math.min(i, TINTS.length - 1)],
                    }}
                  />
                </div>
              </li>
            ))}
          </ul>

          <SectionLabel>{mes.comoSePago}</SectionLabel>
          <ul className={s.pm}>
            {data.by_payment_method.map((p) => (
              <li key={p.payment_method_id}>
                <span className={s.name}>{p.name}</span>
                <span className={s.val}>{formatCOP(p.amount_cop)}</span>
              </li>
            ))}
          </ul>
          <div className={s.tail} />
        </>
      )}
    </>
  )
}
