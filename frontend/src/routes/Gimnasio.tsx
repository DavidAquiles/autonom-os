import { AppBar, Screen } from '../components/shell/Screen'
import { gimnasio, nav } from '../copy/es'
import s from './Gimnasio.module.css'

/**
 * KD-16: Gym is a route and nothing else. No data-entry control, no empty list,
 * no error, and — this is the part that is easy to get wrong — no capture bar
 * (1.3, constraint 20). It makes no API call of any kind.
 */
export function Gimnasio() {
  return (
    <Screen
      header={<AppBar module={nav.gimnasio} />}
      capture={null}
      active="gimnasio"
      scroll={false}
    >
      <div className={s.gym}>
        <div className={s.mark} />
        <h1>{gimnasio.titulo}</h1>
        <p>{gimnasio.cuerpo}</p>
      </div>
    </Screen>
  )
}
