import { forwardRef, useId } from 'react'
import { AlertIcon } from './Icon'
import s from './Form.module.css'

export function Field({
  label,
  optional,
  after,
  children,
  className,
}: {
  label?: React.ReactNode
  optional?: string
  after?: React.ReactNode
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={className ? `${s.field} ${className}` : s.field}>
      {label && (
        <span className={s.label}>
          {label}
          {optional && <span className={s.optional}> {optional}</span>}
          {after}
        </span>
      )}
      {children}
    </div>
  )
}

export function FieldError({ children }: { children: React.ReactNode }) {
  return (
    <p className={s.error} role="alert">
      <AlertIcon size={18} />
      <span>{children}</span>
    </p>
  )
}

export function Hint({ centred, children }: { centred?: boolean; children: React.ReactNode }) {
  return <p className={centred ? `${s.hint} ${s.hintCentred}` : s.hint}>{children}</p>
}

export function Note({ children }: { children: React.ReactNode }) {
  return <div className={s.note}>{children}</div>
}

export const TextInput = forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement> & { invalid?: boolean }
>(function TextInput({ invalid, className, ...rest }, ref) {
  return (
    <input
      ref={ref}
      className={[s.input, invalid ? s.inputError : '', className ?? ''].join(' ').trim()}
      aria-invalid={invalid || undefined}
      {...rest}
    />
  )
})

export const TextArea = forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement> & { invalid?: boolean }
>(function TextArea({ invalid, className, ...rest }, ref) {
  return (
    <textarea
      ref={ref}
      className={[s.textarea, invalid ? s.textareaError : '', className ?? ''].join(' ').trim()}
      aria-invalid={invalid || undefined}
      {...rest}
    />
  )
})

/** The amount input. One parser, one formatter, live thousands grouping (2.4). */
export const AmountInput = forwardRef<
  HTMLInputElement,
  {
    value: string
    onValueChange: (v: string) => void
    invalid?: boolean
    /** 9.2: the voice pass could not determine the amount — mark it as needing input */
    missing?: boolean
    /** id of the "falta…" tag, so the marking reaches a screen reader too */
    describedBy?: string
    label: string
    autoFocus?: boolean
  }
>(function AmountInput(
  { value, onValueChange, invalid, missing, describedBy, label, autoFocus },
  ref,
) {
  const id = useId()
  const box = (
    <div className={invalid ? `${s.amountBox} ${s.amountError}` : s.amountBox}>
      <span className={s.currency} aria-hidden="true">
        $
      </span>
      <input
        ref={ref}
        id={id}
        className={s.amountInput}
        value={value}
        onChange={(e) => onValueChange(e.target.value)}
        inputMode="numeric"
        autoComplete="off"
        enterKeyHint="done"
        // 9.2: an undetermined amount shows no "0" to be misread as a value the
        // system decided on. The format hint is only offered where nothing is
        // being claimed about the number.
        placeholder={missing ? '' : '0'}
        aria-label={label}
        aria-invalid={invalid || undefined}
        aria-describedby={describedBy}
        autoFocus={autoFocus}
      />
    </div>
  )
  if (!missing) return box
  return (
    <div className={invalid ? `${s.needsInput} ${s.needsInputError}` : s.needsInput}>{box}</div>
  )
})

export const formStyles = s
