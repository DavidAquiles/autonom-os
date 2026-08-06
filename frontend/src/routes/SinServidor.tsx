import { Fragment, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Screen } from '../components/shell/Screen'
import { Button } from '../components/ui/Button'
import { common, servidor } from '../copy/es'
import { otherOrigins, type OriginKey } from '../state/origin'
import s from './SinServidor.module.css'

const LABEL: Record<OriginKey, string> = {
  lan: servidor.abrirCasa,
  primary: servidor.abrirSiempre,
}

/** Each alternative explains itself, so the sentence always matches the link. */
const AYUDA: Record<OriginKey, string> = {
  lan: servidor.casaAyuda,
  primary: servidor.siempreAyuda,
}

/**
 * 13.2 / constraint 18. This is the screen a COLD open produces when the PC is
 * suspended: the service worker has the shell cached (KD-13), so the phone
 * renders this instead of Chrome's own network error page.
 *
 * 13.8 has two clauses and they are built separately, because tying them
 * together is what breaks the first one:
 *
 *  - the plain-Spanish instruction is UNCONDITIONAL — it is copy, not data, and
 *    renders even when no origin has ever been stored;
 *  - the one-tap alternative is a plain navigation to the other origin, which is
 *    the only thing that can cross an origin boundary. It is offered only from
 *    what this origin itself stored on an earlier successful /api/health. No
 *    stored value, no link — an address is never guessed.
 */
export function SinServidor() {
  const qc = useQueryClient()
  // Read once at mount: nothing can arrive later, because the server is not
  // answering. There is no fetch here by design (KD-2 mechanism 1).
  const [alternativas] = useState(otherOrigins)

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
          {alternativas.map((alt) => (
            <a key={alt.key} className={s.homeLink} href={alt.origin}>
              {LABEL[alt.key]}
            </a>
          ))}
        </div>
        {/*
          13.8's first clause is copy, not data, so this paragraph is never
          empty: with nothing stored it still says where the home version is and
          what has to be true for it to work. With an origin armed, the same
          sentence carries its address.
        */}
        <p className={s.addr}>
          {alternativas.length === 0 && servidor.casaAyuda}
          {alternativas.map((alt) => (
            <Fragment key={alt.key}>
              {AYUDA[alt.key]}
              <b>{alt.origin}</b>
            </Fragment>
          ))}
        </p>
      </div>
    </Screen>
  )
}
