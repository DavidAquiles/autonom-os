import { useSearchParams } from 'react-router-dom'
import { useCategories, useCategoryExpenses, useHealth, useMonthSummary } from '../../api/queries'
import { EmptyState, SectionLabel } from '../../components/ui/Panel'
import { CloseIcon, LeftIcon, RightIcon } from '../../components/ui/Icon'
import { formatCOP } from '../../format/money'
import { monthLabel, monthName, shiftMonth } from '../../format/dates'
import { common, mes } from '../../copy/es'
import { ExpenseLedger } from './ExpenseLedger'
import { ListFailure } from './ListFailure'
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
 *
 * KD-24 / B2: the viewed month and the selected category are `?mes=` and
 * `?categoria=` in the URL, not `useState`. They are therefore part of the
 * location, so a history entry carries them and returning from an expense's
 * detail restores both (18.9) with no bookkeeping — and they survive a reload.
 */
export function Mes() {
  // The server decides what the current month is (4.8) — /health carries its
  // clock, and the response's own `month` is what we render and page from.
  const health = useHealth()
  const currentMonth = health.data ? health.data.server_time.slice(0, 7) : undefined

  const [params, setParams] = useSearchParams()
  const monthParam = params.get('mes') ?? undefined
  const raw = params.get('categoria')
  const categoryId = raw !== null && /^\d+$/.test(raw) ? Number(raw) : null

  const summary = useMonthSummary(monthParam)
  const month = summary.data?.month
  const filtered = useCategoryExpenses(month, categoryId)
  // 18.3 fallback: a category with nothing left in the viewed month is absent
  // from `by_category`, so the band's name has to come from somewhere else.
  const categories = useCategories()

  /*
   * Deferred 4 — switching category REPLACES the current entry rather than
   * pushing one, and so does changing month. Two reasons: it is what the
   * `useState` this displaces did (no entry per month), so the back button
   * still means "leave Finanzas" rather than "walk back through months I
   * paged"; and 18.5 requires an on-screen way to close a category, so history
   * is not carrying that job. 18.9 holds either way, because the restored
   * ENTRY carries the search string.
   */
  function go(next: { mes?: string; categoria?: number | null }) {
    const out = new URLSearchParams()
    const m = 'mes' in next ? next.mes : monthParam
    // 18.7 / A34: `?categoria` is dropped whenever `?mes` changes, so no
    // month's heading can ever sit over another month's expenses.
    const c = 'mes' in next ? null : 'categoria' in next ? next.categoria : categoryId
    if (m) out.set('mes', m)
    if (c !== null && c !== undefined) out.set('categoria', String(c))
    setParams(out, { replace: true })
  }

  if (summary.isPending) return <p className={s.skeleton}>{common.cargando}</p>
  if (!summary.data) return null

  const data = summary.data
  const atCurrent = currentMonth ? data.month >= currentMonth : true
  const chosen = data.by_category.find((c) => c.category_id === categoryId) ?? null
  const categoryName =
    chosen?.name ?? categories.data?.find((c) => c.id === categoryId)?.name ?? null

  return (
    <>
      <div className={`${s.hero} ${s.heroMonth}`}>
        <div className={s.monthnav}>
          <span className={s.mname}>{monthLabel(data.month)}</span>
          <button
            type="button"
            className={s.arrow}
            aria-label={mes.mesAnterior}
            onClick={() => go({ mes: shiftMonth(data.month, -1) })}
          >
            <LeftIcon />
          </button>
          <button
            type="button"
            className={s.arrow}
            aria-label={mes.mesSiguiente}
            disabled={atCurrent}
            onClick={() => go({ mes: shiftMonth(data.month, 1) })}
          >
            <RightIcon />
          </button>
        </div>
        {/* A33 / 18.4: selecting a category never swaps this number out from
            under the user. The month's own total stays exactly where it was. */}
        {!data.is_empty && (
          <>
            <div className={s.sum}>{formatCOP(data.total_cop)}</div>
            <div className={s.sub}>{mes.gastosContados(data.expense_count)}</div>
          </>
        )}
      </div>

      {/* 4.5: an empty month is a plain empty state — never a zeroed breakdown.
          18.11: and no category selection is offered at all. */}
      {data.is_empty ? (
        <EmptyState title={mes.vacioTitulo(monthName(data.month))} body={mes.vacioCuerpo} />
      ) : categoryId !== null ? (
        <>
          {/* 18.3-18.5 / constraints 40, 41. OQ3, ruled at the gate: on an
              empty category the band keeps the name and the way out and shows
              NO total and NO count. "$0 · sin gastos" is the zero row 18.10
              forbids. */}
          <div className={s.opened}>
            <div className={s.openedHead}>
              {categoryName && <span className={s.openedName}>{categoryName}</span>}
              <button type="button" className={s.cerrar} onClick={() => go({ categoria: null })}>
                <CloseIcon size={18} strokeWidth={2.1} />
                {common.cerrar}
              </button>
            </div>
            {chosen && filtered.data && filtered.data.total_count > 0 && (
              <div className={s.figures}>
                <span className={s.categoryTotal}>{formatCOP(chosen.amount_cop)}</span>
                {/* KD-22: the count is `total_count`, which ignores `limit`, so
                    the figure is right even where the list is capped (R4). */}
                <span className={s.categoryCount}>
                  {mes.gastosContados(filtered.data.total_count)}
                </span>
              </div>
            )}
          </div>

          {filtered.isPending && <p className={s.skeleton}>{common.cargando}</p>}

          {/* QA D2: this request failing used to fall through to 18.10's copy,
              so the screen told the user the category was empty while the
              breakdown above still showed its total — and the false half was
              the reassuring one. `?categoria=0`, which the server 400s, is only
              the cheapest trigger; the same branch caught EVERY failure of this
              request. The list failing and the category being empty are now
              different things on screen. */}
          {filtered.isError && (
            <ListFailure onRetry={() => filtered.refetch()} pending={filtered.isFetching} />
          )}

          {filtered.data && filtered.data.items.length > 0 && (
            <>
              {/* 18.2, 18.12, 18.13 — this category, this month, newest dated
                  first. Deliberately a different order from Historial (A37). */}
              <ExpenseLedger items={filtered.data.items} variant="categoria" />
              <div className={s.tail} />
            </>
          )}

          {/* 18.10 / constraint 42: said in Spanish, never a blank area — and
              only ever about a list the server actually returned. `isSuccess`
              is the whole fix: it is the difference between "there is nothing
              here" and "I do not know what is here". */}
          {filtered.isSuccess && filtered.data.items.length === 0 && (
            <EmptyState
              title={mes.categoriaVaciaTitulo(monthName(data.month), categoryName)}
              body={mes.categoriaVaciaCuerpo}
            />
          )}
        </>
      ) : (
        <>
          <SectionLabel>{mes.enQueSeFue}</SectionLabel>
          {/* 18.1 / constraint 39: every category row opens in ONE interaction
              and is visibly tappable — full-bleed like the ledger rows, with
              the app's existing chevron. The payment-method rows below stay
              inset and inert, so the boundary is visible without touching
              either (A35). */}
          <ul className={s.brkTap}>
            {data.by_category.map((c, i) => (
              <li key={c.category_id}>
                <button
                  type="button"
                  className={s.catrow}
                  onClick={() => go({ categoria: c.category_id })}
                >
                  <span className={s.line}>
                    <span className={s.name}>{c.name}</span>
                    <span className={s.val}>{formatCOP(c.amount_cop)}</span>
                    <span className={s.pct}>{c.percent} %</span>
                    <span className={s.chev}>
                      <RightIcon size={18} strokeWidth={2.1} />
                    </span>
                  </span>
                  <span className={s.track}>
                    <span
                      className={s.fill}
                      style={{
                        width: `${c.percent}%`,
                        background: TINTS[Math.min(i, TINTS.length - 1)],
                      }}
                    />
                  </span>
                </button>
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
