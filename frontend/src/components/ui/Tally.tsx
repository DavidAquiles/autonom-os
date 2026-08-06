import { voz } from '../../copy/es'
import s from './Tally.module.css'

/**
 * Draws `seconds` elapsed as tally marks plus the numeral. It is given elapsed
 * time and nothing else — there is deliberately no `total` prop, because a
 * completion fraction does not exist on the wire for any wait this is used for
 * (KD-11), and a component that could accept one would eventually be given one.
 */
export function Tally({ seconds }: { seconds: number }) {
  const n = Math.max(0, Math.floor(seconds))
  const groups: number[] = []
  for (let done = 0; done < n; done += 5) groups.push(Math.min(5, n - done))

  return (
    <div className={s.wrap}>
      <div className={s.tally} aria-hidden="true">
        {groups.map((inGroup, g) => (
          <span key={g} className={inGroup < 5 ? `${s.group} ${s.partial}` : s.group}>
            {Array.from({ length: Math.min(inGroup, 4) }, (_, m) => {
              const idx = g * 5 + m
              return (
                <i
                  key={m}
                  className={s.tick}
                  style={{ opacity: fade(idx + 1, n) }}
                />
              )
            })}
            {inGroup === 5 && (
              <i className={s.tickFive} style={{ opacity: fade(g * 5 + 5, n) }} />
            )}
          </span>
        ))}
      </div>
      <div className={s.secs}>
        <span className={s.n}>{n}</span>
        <span className={s.u}>{voz.segundos}</span>
      </div>
    </div>
  )
}

function fade(index: number, total: number): number {
  if (total <= 0) return 1
  return Math.round(Math.max(0.3, Math.min(1, 0.3 + (0.7 * index) / total)) * 100) / 100
}
