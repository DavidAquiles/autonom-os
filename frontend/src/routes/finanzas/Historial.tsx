import { useHistorial } from '../../api/queries'
import { Button } from '../../components/ui/Button'
import { EmptyState } from '../../components/ui/Panel'
import { common, historial } from '../../copy/es'
import { ExpenseLedger } from './ExpenseLedger'
import s from './Finanzas.module.css'

/**
 * The fourth Finanzas tab (16.1). Everything ever recorded, newest-recorded
 * first (16.2), a screenful at a time (16.13).
 *
 * Deliberately absent, and all four are requirements rather than omissions:
 * no title (the tab strip says "Historial" two centimetres above — the app does
 * not explain itself twice), no count readout (constraint 34 and the brief's
 * Avoid list), no date headings or day separators (constraint 33, A27), and no
 * search, filter or sort (constraint 34, A36). The screen has one job.
 */
export function Historial() {
  const list = useHistorial()

  if (list.isPending) return <p className={s.skeleton}>{common.cargando}</p>
  if (!list.data) return null

  const items = list.data.pages.flatMap((p) => p.items)

  // 16.10 / constraint 42: never a blank screen or an empty list frame. The
  // ordering statement goes with it — there is no order to explain yet.
  if (items.length === 0)
    return <EmptyState title={historial.vacioTitulo} body={historial.vacioCuerpo} />

  return (
    <>
      {/* 16.6 / constraint 31: read before the first row, so a screen of dates
          that are not descending cannot be mistaken for a fault (R6). */}
      <div className={s.orden}>
        <p>{historial.orden}</p>
      </div>

      <ExpenseLedger items={items} variant="historial" />

      {/* Constraint 32: present exactly while `next_before_id !== null`, and
          when it is null nothing at all follows the last rule — no label, no
          spinner, no trailing affordance. An in-flight fetch keeps the control
          in place and disables it rather than growing the endless bottom
          spinner the brief names as a thing to avoid. */}
      {list.hasNextPage && (
        <div className={s.verMas}>
          <Button
            kind="text"
            auto
            disabled={list.isFetchingNextPage}
            onClick={() => list.fetchNextPage()}
          >
            {list.isFetchingNextPage ? common.cargando : historial.verMas}
          </Button>
        </div>
      )}
      <div className={s.tail} />
    </>
  )
}
