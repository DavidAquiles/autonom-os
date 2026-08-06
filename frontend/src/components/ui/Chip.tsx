import { PlusIcon } from './Icon'
import s from './Chip.module.css'

export interface ChipOption {
  id: number
  name: string
}

interface ChipRowProps {
  options: ChipOption[]
  selectedId: number | null
  onSelect: (id: number) => void
  /** label for the "create one" chip (3.2); omitted where creation is not offered */
  newLabel?: string
  onNew?: () => void
  /** draws the attention box 9.2 asks for around a field voice could not fill */
  missing?: boolean
  /** id of the "falta…" tag, so the marking reaches a screen reader too */
  describedBy?: string
  ariaLabel: string
  disabled?: boolean
}

export function ChipRow({
  options,
  selectedId,
  onSelect,
  newLabel,
  onNew,
  missing,
  describedBy,
  ariaLabel,
  disabled,
}: ChipRowProps) {
  return (
    <div
      className={missing ? `${s.chips} ${s.missing}` : s.chips}
      role="radiogroup"
      aria-label={ariaLabel}
      aria-describedby={describedBy}
    >
      {options.map((o) => {
        const on = o.id === selectedId
        return (
          <button
            key={o.id}
            type="button"
            role="radio"
            aria-checked={on}
            disabled={disabled}
            className={on ? `${s.chip} ${s.on}` : s.chip}
            onClick={() => onSelect(o.id)}
          >
            {o.name}
          </button>
        )
      })}
      {newLabel && onNew && (
        <button type="button" className={`${s.chip} ${s.new}`} onClick={onNew} disabled={disabled}>
          <PlusIcon size={18} />
          {newLabel}
        </button>
      )}
    </div>
  )
}

export function Tag({
  children,
  need,
  id,
}: {
  children: React.ReactNode
  need?: boolean
  id?: string
}) {
  return (
    <span id={id} className={need ? `${s.tag} ${s.tagNeed}` : s.tag}>
      {children}
    </span>
  )
}

export const chipStyles = s
