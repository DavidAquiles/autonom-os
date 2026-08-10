import { useHealth } from '../../api/queries'
import { Banner, panelStyles as panel } from '../../components/ui/Panel'
import { common, servidor } from '../../copy/es'

/**
 * QA D2 and D3, which are the same defect on two screens: a list request that
 * FAILED was being reported as a list that came back EMPTY (the month's
 * category band) or as nothing at all (Historial). An error state must not make
 * a factual claim about the data, and it must not be a blank screen — that is
 * what constraint 42 and criteria 16.10 / 18.10 exist to prevent, and the user
 * cannot tell the two situations apart from the outside.
 *
 * One component for both, for constraint 30's reason: two copies of an error
 * state drift, and this one has a condition attached that is easy to forget.
 *
 * The condition: when the app cannot reach the server at all, this renders
 * NOTHING. `ReachabilityBanner` (App.tsx:140) is already on screen a few pixels
 * above, saying exactly that with the "Ver qué hacer" route attached. Two
 * banners about one condition, in two wordings, is the self-contradicting
 * screen D2 is about. Health, not the error's own class, is the right signal:
 * QA's repro blocks `/api/expenses` at the network layer while `/api/health`
 * keeps answering, which raises `UnreachableError` for a server that is in fact
 * reachable.
 *
 * The retry carries its own in-flight state rather than growing a spinner —
 * the same discipline as "Ver gastos más antiguos" (constraint 32).
 */
export function ListFailure({ onRetry, pending }: { onRetry: () => void; pending: boolean }) {
  const health = useHealth()
  if (health.isError) return null

  return (
    <Banner
      title={servidor.listaFalloTitulo}
      detail={servidor.listaFalloCuerpo}
      action={
        <button className={panel.action} type="button" onClick={onRetry} disabled={pending}>
          {pending ? common.cargando : common.reintentar}
        </button>
      }
    />
  )
}
