import { useEffect, useId, useRef } from 'react'
import s from './Sheet.module.css'

interface SheetProps {
  title: string
  body?: React.ReactNode
  subject?: React.ReactNode
  actions: React.ReactNode
  onDismiss: () => void
}

/**
 * The confirmation surface (constraint 19). It traps nothing the user cannot
 * escape: Escape and a tap on the veil both cancel, and the primary action is
 * never the destructive one by position alone — it is labelled with the verb it
 * performs.
 */
export function Sheet({ title, body, subject, actions, onDismiss }: SheetProps) {
  const titleId = useId()
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onDismiss()
    }
    document.addEventListener('keydown', onKey)
    // Move focus into the sheet so a keyboard user is not left behind it.
    ref.current?.querySelector<HTMLElement>('button, a')?.focus()
    return () => document.removeEventListener('keydown', onKey)
  }, [onDismiss])

  return (
    <div className={s.veil} onClick={onDismiss}>
      <div
        ref={ref}
        className={s.sheet}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(e) => e.stopPropagation()}
      >
        <div className={s.grab} />
        <h2 id={titleId}>{title}</h2>
        {body && <p>{body}</p>}
        {subject && <div className={s.subject}>{subject}</div>}
        <div className={s.acts}>{actions}</div>
      </div>
    </div>
  )
}

export const sheetStyles = s
