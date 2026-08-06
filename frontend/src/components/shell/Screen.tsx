import { Link, NavLink, useNavigate } from 'react-router-dom'
import { CloseIcon, MicIcon, PlusIcon } from '../ui/Icon'
import { capture as captureCopy, nav as navCopy } from '../../copy/es'
import { useVoice } from '../../voice/VoiceContext'
import s from './Screen.module.css'

export type CaptureModule = 'finanzas' | 'diario' | null

/**
 * Every screen in the app is one of these. The bottom navigation is part of the
 * frame rather than of any route, which is how constraint 11 ("the three
 * destinations, from every screen, in one interaction") holds by construction.
 */
export function Screen({
  header,
  capture,
  active,
  children,
  scroll = true,
}: {
  header?: React.ReactNode
  capture: CaptureModule
  active: 'finanzas' | 'diario' | 'gimnasio'
  children: React.ReactNode
  scroll?: boolean
}) {
  return (
    <div className={s.app}>
      {header}
      {scroll ? <main className={s.scroll}>{children}</main> : children}
      {capture && <CaptureBar module={capture} />}
      <BottomNav active={active} />
    </div>
  )
}

export function AppBar({
  module,
  action,
}: {
  module: string
  action?: { label: string; to: string }
}) {
  return (
    <div className={s.appbar}>
      <span className={s.module}>{module}</span>
      {action ? (
        <Link className={s.act} to={action.to}>
          {action.label}
        </Link>
      ) : (
        <span />
      )}
    </div>
  )
}

export function FormBar({ title, back }: { title: string; back: string | number }) {
  const navigate = useNavigate()
  return (
    <div className={s.formbar}>
      <button
        type="button"
        className={s.close}
        aria-label="Cerrar"
        onClick={() => (typeof back === 'number' ? navigate(back) : navigate(back))}
      >
        <CloseIcon />
      </button>
      <span className={s.formTitle}>{title}</span>
    </div>
  )
}

export function Tabs({ items }: { items: { label: string; to: string; end?: boolean }[] }) {
  return (
    <nav className={s.tabs}>
      {items.map((t) => (
        <NavLink
          key={t.to}
          to={t.to}
          end={t.end}
          className={({ isActive }) => (isActive ? `${s.tab} ${s.tabOn}` : s.tab)}
        >
          {t.label}
        </NavLink>
      ))}
    </nav>
  )
}

/**
 * 1.4 / constraint 9: both capture actions for the current module, in the thumb
 * zone, without navigating away from the module. KD-16: never rendered on
 * /gimnasio — a capture control there would be the data-entry control 1.3
 * forbids in as many words.
 */
function CaptureBar({ module }: { module: 'finanzas' | 'diario' }) {
  const voice = useVoice()
  const to = module === 'finanzas' ? '/finanzas/gasto/nuevo' : '/diario/nueva'
  const label = module === 'finanzas' ? captureCopy.anotarGasto : captureCopy.escribir
  return (
    <div className={s.capture}>
      <Link className={s.manual} to={to}>
        <PlusIcon size={18} />
        {label}
      </Link>
      <button
        type="button"
        className={s.mic}
        aria-label={captureCopy.grabarVoz}
        onClick={() => voice.start(module === 'finanzas' ? 'expense' : 'journal')}
      >
        <MicIcon size={28} />
      </button>
    </div>
  )
}

function BottomNav({ active }: { active: 'finanzas' | 'diario' | 'gimnasio' }) {
  const items = [
    { key: 'finanzas', label: navCopy.finanzas, to: '/finanzas' },
    { key: 'diario', label: navCopy.diario, to: '/diario' },
    { key: 'gimnasio', label: navCopy.gimnasio, to: '/gimnasio' },
  ] as const
  return (
    <nav className={s.nav} aria-label="Secciones">
      {items.map((i) => (
        <Link
          key={i.key}
          to={i.to}
          className={i.key === active ? s.navOn : undefined}
          aria-current={i.key === active ? 'page' : undefined}
        >
          <span>{i.label}</span>
          {/* Constraint 20: Gym is present and visibly marked as not yet available. */}
          <span className={s.soon}>{i.key === 'gimnasio' ? navCopy.pronto : ''}</span>
        </Link>
      ))}
    </nav>
  )
}

export const screenStyles = s
