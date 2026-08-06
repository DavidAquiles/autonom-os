import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useHealth, useJournal } from '../../api/queries'
import type { JournalEntry } from '../../api/types'
import { EmptyState } from '../../components/ui/Panel'
import { Button } from '../../components/ui/Button'
import { LeftIcon, RightIcon } from '../../components/ui/Icon'
import { clockTime, dateOf, longDate, shiftDay } from '../../format/dates'
import { common, diario } from '../../copy/es'
import s from './Diario.module.css'

/** 7.1: newest first, grouped and labelled by date. */
export function DiarioTodo() {
  const page = useJournal()

  if (page.isPending) return <p className={s.skeleton}>{common.cargando}</p>
  const items = page.data?.items ?? []

  // 7.3: an empty journal is an invitation, not a blank screen.
  if (items.length === 0) {
    return (
      <div className={s.empty}>
        <EmptyState title={diario.vacioTitulo} body={diario.vacioCuerpo} />
      </div>
    )
  }

  const days = groupByDay(items)

  return (
    <>
      {days.map(([day, entries], i) => (
        <div key={day}>
          {i > 0 && <div className={s.daySep} />}
          <div className={s.dayLabel}>{longDate(day)}</div>
          {entries.map((e) => (
            <EntryPreview key={e.id} entry={e} />
          ))}
        </div>
      ))}
      <div className={s.tail} />
    </>
  )
}

/** 7.2: a chosen date shows its entries, or says nothing was written. */
export function DiarioPorFecha() {
  const health = useHealth()
  const today = health.data?.server_time.slice(0, 10)
  const [date, setDate] = useState<string | null>(null)
  const day = date ?? today
  const page = useJournal(day)

  if (!day) return <p className={s.skeleton}>{common.cargando}</p>
  const items = page.data?.items ?? []

  return (
    <>
      <div className={s.dateNav}>
        <span className={s.dateName}>{longDate(day)}</span>
        <button
          type="button"
          className={s.arrow}
          aria-label={diario.diaAnterior}
          onClick={() => setDate(shiftDay(day, -1))}
        >
          <LeftIcon />
        </button>
        <button
          type="button"
          className={s.arrow}
          aria-label={diario.diaSiguiente}
          disabled={Boolean(today) && day >= today!}
          onClick={() => setDate(shiftDay(day, 1))}
        >
          <RightIcon />
        </button>
      </div>

      {items.length === 0 ? (
        <div className={s.empty}>
          <EmptyState
            title={diario.fechaVaciaTitulo(longDate(day))}
            body={diario.fechaVaciaCuerpo}
          />
        </div>
      ) : (
        <>
          {items.map((e) => (
            <EntryPreview key={e.id} entry={e} />
          ))}
          <div className={s.tail} />
        </>
      )}
    </>
  )
}

/**
 * Nothing here says whether the entry was spoken or typed — 10.4 requires the
 * two to be indistinguishable, and the API returns no field that could tell.
 */
function EntryPreview({ entry }: { entry: JournalEntry }) {
  const long = entry.text.length > 420 || entry.text.split('\n').length > 7
  return (
    <Link className={s.entry} to={`/diario/${entry.id}`}>
      <div className={s.time}>{clockTime(entry.written_at)}</div>
      <div className={long ? `${s.body} ${s.clamp}` : s.body}>{entry.text}</div>
      {long && <span className={s.more}>{diario.seguirLeyendo}</span>}
    </Link>
  )
}

function groupByDay(items: JournalEntry[]): [string, JournalEntry[]][] {
  const map = new Map<string, JournalEntry[]>()
  for (const e of items) {
    const day = dateOf(e.written_at)
    const list = map.get(day)
    if (list) list.push(e)
    else map.set(day, [e])
  }
  return [...map.entries()]
}

export { Button }
