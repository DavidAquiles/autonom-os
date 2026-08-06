import { AlertIcon } from './Icon'
import s from './Panel.module.css'

export function Banner({
  tone = 'violet',
  title,
  detail,
  action,
}: {
  tone?: 'violet' | 'flat' | 'alarm'
  title: React.ReactNode
  detail?: React.ReactNode
  action?: React.ReactNode
}) {
  const cls = [s.banner, tone === 'flat' ? s.flat : '', tone === 'alarm' ? s.alarm : '']
    .join(' ')
    .trim()
  return (
    <div className={cls} role="status">
      <AlertIcon />
      <div>
        <div className={s.title}>{title}</div>
        {detail && <div className={s.detail}>{detail}</div>}
        {action}
      </div>
    </div>
  )
}

export function EmptyState({ title, body }: { title: string; body?: React.ReactNode }) {
  return (
    <div className={s.empty}>
      <div className={s.mark} />
      <h2>{title}</h2>
      {body && <p>{body}</p>}
    </div>
  )
}

export function SectionLabel({ children }: { children: React.ReactNode }) {
  return <div className={s.sectionLabel}>{children}</div>
}

export const panelStyles = s
