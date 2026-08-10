import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { useExpense } from '../../api/queries'
import { ApiError } from '../../api/client'
import { Button } from '../../components/ui/Button'
import { Banner, EmptyState } from '../../components/ui/Panel'
import { PencilIcon } from '../../components/ui/Icon'
import { FormBar, Screen } from '../../components/shell/Screen'
import { common, gasto, gastoDetalle, servidor } from '../../copy/es'
import { formatCOP } from '../../format/money'
import { longDate, stamp } from '../../format/dates'
import type { Expense } from '../../api/types'
import finanzas from './Finanzas.module.css'
import s from './GastoDetalle.module.css'

/**
 * KD-23: this takes the EXISTING route `/finanzas/gasto/:id`, and the edit form
 * moves to `/finanzas/gasto/:id/editar` — mirroring `/diario/:id` and
 * `/diario/:id/editar` (A25). That single move IS B1: every list row in the
 * application already links to `/finanzas/gasto/${id}`, so "tapping an expense
 * opens the detail" holds by construction and cannot be missed in one of three
 * places.
 *
 * KD-27: `useExpense` is the same hook and the same query key the edit form
 * uses, so opening the form is cache-warm and a save shows stored values (17.7)
 * with no bookkeeping.
 */
export function GastoDetalle() {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const expense = useExpense(Number(id))

  // 17.9: threaded row → detail → form, and used for exactly one thing — where
  // to land after deleting, since by then this entry is dead.
  const desde = (location.state as { desde?: string } | null)?.desde

  // Closing is a POP, not a navigation to a fixed path: only the previous
  // location entry carries `?mes=` and `?categoria=`, and only that entry's
  // scroll offset was recorded (17.8, 18.9). The fallback covers a location
  // with nothing behind it — a hand-typed URL, which no affordance produces.
  const hayLista = location.key !== 'default'
  const back = hayLista ? -1 : '/finanzas'

  const missing =
    expense.error instanceof ApiError && expense.error.code === 'not_found'

  return (
    <Screen
      header={<FormBar title={gastoDetalle.titulo} back={back} />}
      capture={null}
      active="finanzas"
    >
      {expense.isPending && <p className={finanzas.skeleton}>{common.cargando}</p>}

      {/* 17.11: plain Spanish, inside the frame. Never a blank screen, a spinner
          that never ends, or a raw technical error. */}
      {missing && (
        <EmptyState title={gastoDetalle.noExisteTitulo} body={gastoDetalle.noExisteCuerpo} />
      )}

      {/* Any other failure is the server being out of reach, not the expense
          being gone — saying "ya no existe" there would be a lie. This is the
          app's one unreachable treatment, which the tabbed screens inherit from
          FinanzasTabs and this one, being outside it, has to carry itself. */}
      {expense.isError && !missing && (
        <Banner title={servidor.bannerTitulo} detail={servidor.bannerCuerpo} />
      )}

      {/* QA D1(b): `!missing` is load-bearing. TanStack keeps the last good
          `data` when a refetch fails, so a detail reopened after the expense was
          deleted rendered the complete record — amount, category, description,
          both dates — UNDERNEATH its own "Este gasto ya no existe.", with a live
          "Editar gasto" that opened the form pre-filled with a dead record. A
          not-found state REPLACES the record; it never sits on top of it, and it
          offers no way to edit what is not there.

          Any other failure still shows the cached record with the unreachable
          banner above it, which is deliberate and is what the approved mockup
          draws: out of date is worth reading, gone is not. */}
      {expense.data && !missing && (
        <Recibo
          e={expense.data}
          onEdit={() =>
            navigate(`/finanzas/gasto/${expense.data!.id}/editar`, {
              // 17.9 / QA D1(a): `hayLista` says an entry exists behind this
              // detail, so deleting can pop past BOTH this screen and the form
              // and leave the stack at `[lista]` — the design's push/pop table.
              state: { desde, hayLista },
            })
          }
        />
      )}
    </Screen>
  )
}

function Recibo({ e, onEdit }: { e: Expense; onEdit: () => void }) {
  // 17.5: `create` writes one timestamp into both columns and `update` rewrites
  // only `updated_at`, so an exact string difference is a sound edited-since
  // test. R3 is known and accepted: a save that changed nothing still marks the
  // expense edited — which is why this line carries WHEN. That is what lets a
  // surprising mark be reconciled against a save the user remembers making.
  const edited = e.updated_at !== e.created_at

  return (
    <>
      <div className={s.receipt}>
        <div className={s.amount}>{formatCOP(e.amount_cop)}</div>
        <div className={s.category}>{e.category_name}</div>
        {/* 17.3: omitted entirely when there is none — no dash, no placeholder,
            no word standing in for "nothing". */}
        {e.description && <p className={s.description}>{e.description}</p>}

        <ul className={s.facts}>
          <li>
            <span className={s.factName}>{gastoDetalle.metodo}</span>
            <span className={s.factValue}>{e.payment_method_name}</span>
          </li>
          <li>
            <span className={s.factName}>{gastoDetalle.fechaGasto}</span>
            <span className={s.factValue}>{longDate(e.spent_on)}</span>
          </li>
        </ul>
      </div>

      <div className={s.stamp}>
        <p>{gastoDetalle.anotado(stamp(e.created_at))}</p>
        {edited && <p>{gastoDetalle.editado(stamp(e.updated_at))}</p>}
      </div>

      {/* 17.6 / constraint 35: exactly one control that touches this expense.
          No input, no chip, no editable field, nothing drawn as a greyed-out
          form. The ✕ above is navigation, the same one EntradaLeer carries. */}
      <div className={s.foot}>
        <Button kind="ghost" onClick={onEdit}>
          <PencilIcon size={20} />
          {gasto.editar}
        </Button>
      </div>
    </>
  )
}
