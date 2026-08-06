import { forwardRef } from 'react'
import { Link } from 'react-router-dom'
import s from './Button.module.css'

export type ButtonKind = 'primary' | 'ghost' | 'danger' | 'dangerGhost' | 'text'

interface Common {
  kind?: ButtonKind
  /** shrink-to-fit instead of filling the width */
  auto?: boolean
  className?: string
  children: React.ReactNode
}

type ButtonProps = Common &
  Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'className' | 'children'>

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { kind = 'primary', auto, className, children, type = 'button', ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      className={[s.btn, s[kind], auto ? s.auto : '', className ?? ''].join(' ').trim()}
      {...rest}
    >
      {children}
    </button>
  )
})

type LinkButtonProps = Common & { to: string; state?: unknown; replace?: boolean }

export function LinkButton({ kind = 'ghost', auto, className, to, children, ...rest }: LinkButtonProps) {
  return (
    <Link
      to={to}
      className={[s.btn, s[kind], auto ? s.auto : '', className ?? ''].join(' ').trim()}
      {...rest}
    >
      {children}
    </Link>
  )
}

export const buttonRow = s.row
