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
  ariaLabel,
  disabled,
}: ChipRowProps) {
  return (
    <div
      className={missing ? `${s.chips} ${s.missing}` : s.chips}
      role="radiogroup"
      aria-label={ariaLabel}
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

export function Tag({ children, need }: { children: React.ReactNode; need?: boolean }) {
  return <span className={need ? `${s.tag} ${s.tagNeed}` : s.tag}>{children}</span>
}

export const chipStyles = s
