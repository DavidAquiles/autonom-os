import { useQueryClient } from '@tanstack/react-query'
import { Screen } from '../components/shell/Screen'
import { Button } from '../components/ui/Button'
import { common, servidor } from '../copy/es'
import { rememberedHomeOrigin } from '../state/origin'
import s from './SinServidor.module.css'

/**
 * 13.2 / constraint 18. This is the screen a COLD open produces when the PC is
 * suspended: the service worker has the shell cached (KD-13), so the phone
 * renders this instead of Chrome's own network error page.
 *
 * 13.8: the working alternative is one deliberate action away — a navigation to
 * the LAN origin, which is the only thing that can cross an origin boundary.
 */
export function SinServidor() {
  const qc = useQueryClient()
  const home = rememberedHomeOrigin()

  return (
    <Screen capture={null} active="finanzas" scroll={false}>
      <div className={s.offline}>
        <div className={s.mark} />
        <h1>{servidor.titulo}</h1>
        <p>{servidor.cuerpo1}</p>
        <p>{servidor.cuerpo2}</p>
        <div className={s.acts}>
          <Button kind="primary" onClick={() => qc.invalidateQueries()}>
            {common.reintentar}
          </Button>
          {/*
            KD-2 forbids an origin constant in this bundle, so the fallback
            address is not written here: it is REMEMBERED from the visit setup
            makes to the LAN origin when it installs the second home-screen icon.
            Before that has happened there is no address to offer, and inventing
            one would be worse than saying where the icon is.
          */}
          {home && (
            <a className={s.homeLink} href={home}>
              {servidor.abrirCasa}
            </a>
          )}
        </div>
        <p className={s.addr}>
          {servidor.casaAyuda}
          {home && <b>{home}</b>}
        </p>
      </div>
    </Screen>
  )
}
