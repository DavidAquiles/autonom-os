import { useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import {
  useCategories,
  useCreateExpense,
  useCreateNamed,
  useDeleteExpense,
  useExpense,
  useHealth,
  usePaymentMethods,
  useSuggestCategory,
  useUpdateExpense,
  type NamedKind,
} from '../../api/queries'
import { ApiError, UnreachableError } from '../../api/client'
import type { ExpenseDraft } from '../../api/types'
import { Button } from '../../components/ui/Button'
import { ChipRow, Tag, chipStyles } from '../../components/ui/Chip'
import {
  AmountInput,
  Field,
  FieldError,
  Hint,
  Note,
  TextInput,
  formStyles,
} from '../../components/ui/Form'
import { Banner } from '../../components/ui/Panel'
import { CalendarIcon, PlusIcon, TrashIcon } from '../../components/ui/Icon'
import { Sheet } from '../../components/ui/Sheet'
import { FormBar, Screen } from '../../components/shell/Screen'
import { common, gasto, razonEnEspanol, servidor } from '../../copy/es'
import { formatAmountInput, formatCOP, parseAmount } from '../../format/money'
import { longDate } from '../../format/dates'
import s from './GastoForm.module.css'

interface VoiceState {
  transcript: string
  draft: ExpenseDraft | null
}

type Errors = Partial<Record<'amount_cop' | 'category_id' | 'payment_method_id' | 'spent_on', string>>

// 9.2: the "falta…" tag is the field's description, not decoration, so the
// control points at it and the marking survives being read aloud. One form is
// on screen at a time, so these are constants rather than generated ids.
const NEED_AMOUNT = 'falta-monto'
const NEED_CATEGORY = 'falta-categoria'
const NEED_METHOD = 'falta-metodo'

export function NuevoGasto() {
  return <GastoForm mode="nuevo" />
}

export function EditarGasto() {
  const { id } = useParams()
  return <GastoForm mode="editar" expenseId={Number(id)} />
}

function GastoForm({ mode, expenseId }: { mode: 'nuevo' | 'editar'; expenseId?: number }) {
  const navigate = useNavigate()
  const location = useLocation()
  const voice = (location.state as { voice?: VoiceState } | null)?.voice ?? null
  // 17.9: the list this expense was opened from — pathname AND search, so the
  // delete path does not drop the month and the selection that B2 exists to
  // preserve. A hint with a fallback, never a data source.
  const desde = (location.state as { desde?: string } | null)?.desde ?? '/finanzas'

  /*
   * 17.7: BOTH ways of leaving the edit form are the same POP back to the
   * detail — this is where the journal's pattern must not be copied literally.
   * `Entrada.tsx:131` REPLACES on save, which the journal survives because its
   * read screen closes to a fixed path; this detail cannot, because only the
   * previous location entry carries `?mes=`, `?categoria=` and the recorded
   * scroll offset (17.8). Replacing here would leave a duplicate detail entry,
   * so the next close would land on the detail already on screen.
   *
   * `location.key === 'default'` is the session's first entry — i.e. a
   * hand-typed `…/editar` URL, which no affordance in the app produces. There
   * is nothing to pop, so the detail is reached directly instead.
   */
  const canPop = location.key !== 'default'
  const backToDetalle = () => {
    if (canPop) navigate(-1)
    else navigate(`/finanzas/gasto/${expenseId}`, { replace: true })
  }

  const health = useHealth()
  const today = health.data?.server_time.slice(0, 10)
  const categories = useCategories()
  const methods = usePaymentMethods()
  const existing = useExpense(mode === 'editar' ? (expenseId ?? null) : null)

  const create = useCreateExpense()
  const update = useUpdateExpense()
  const remove = useDeleteExpense()
  const suggest = useSuggestCategory()

  const [amount, setAmount] = useState('')
  const [categoryId, setCategoryId] = useState<number | null>(null)
  const [methodId, setMethodId] = useState<number | null>(null)
  const [spentOn, setSpentOn] = useState<string | null>(null)
  const [description, setDescription] = useState('')
  const [errors, setErrors] = useState<Errors>({})
  const [showDate, setShowDate] = useState(false)
  const [creating, setCreating] = useState<NamedKind | null>(null)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [saveFailed, setSaveFailed] = useState<'unreachable' | 'server' | null>(null)
  const [categorySuggested, setCategorySuggested] = useState(false)

  // 9.4 / 10.3: a field the user touched is never overwritten by a late
  // suggestion arriving from the server.
  const categoryTouched = useRef(false)
  const seeded = useRef(false)
  const suggestAsked = useRef(false)

  /* ---- seed from the voice draft (9.1, 9.2) ---- */
  useEffect(() => {
    if (seeded.current || !voice) return
    seeded.current = true
    const d = voice.draft
    if (!d) {
      setDescription(voice.transcript.slice(0, 1000))
      return
    }
    if (d.amount_cop !== null) setAmount(formatAmountInput(String(d.amount_cop)))
    if (d.category_id !== null) {
      setCategoryId(d.category_id)
      setCategorySuggested(true)
    }
    if (d.payment_method_id !== null) setMethodId(d.payment_method_id)
    setDescription(d.description)
  }, [voice])

  /* ---- the category assist, only when the draft could not resolve one ---- */
  useEffect(() => {
    if (suggestAsked.current) return
    const d = voice?.draft
    if (!d || d.resolved_by.category !== 'none') return
    suggestAsked.current = true
    suggest.mutate(voice.transcript, {
      onSuccess: (r) => {
        // Applied only if the field is still untouched, and labelled *sugerido*.
        if (r.category_id !== null && !categoryTouched.current) {
          setCategoryId(r.category_id)
          setCategorySuggested(true)
        }
      },
    })
    // `suggest` is a stable mutation object; re-running on it would loop.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [voice])

  /* ---- seed from the existing expense when editing (5.1) ---- */
  useEffect(() => {
    if (mode !== 'editar' || !existing.data || seeded.current) return
    seeded.current = true
    const e = existing.data
    setAmount(formatAmountInput(String(e.amount_cop)))
    setCategoryId(e.category_id)
    setMethodId(e.payment_method_id)
    setSpentOn(e.spent_on)
    setDescription(e.description ?? '')
  }, [mode, existing.data])

  const saving = create.isPending || update.isPending
  const effectiveDate = spentOn ?? today ?? null

  function validate(): Errors {
    const next: Errors = {}
    const value = parseAmount(amount)
    if (value === null || value <= 0) next.amount_cop = razonEnEspanol('amount_cop', 'must_be_positive')
    if (categoryId === null) next.category_id = razonEnEspanol('category_id', 'required')
    if (methodId === null) next.payment_method_id = razonEnEspanol('payment_method_id', 'required')
    if (effectiveDate && today && effectiveDate > today)
      next.spent_on = razonEnEspanol('spent_on', 'future_date')
    return next
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaveFailed(null)
    // 2.2, 2.3: rejected before the request, with every offending field named.
    const found = validate()
    setErrors(found)
    if (Object.keys(found).length > 0) return

    const payload = {
      amount_cop: parseAmount(amount) as number,
      category_id: categoryId as number,
      payment_method_id: methodId as number,
      spent_on: effectiveDate ?? undefined,
      description: description.trim() === '' ? null : description.trim(),
    }

    const onError = (err: unknown) => {
      // 13.5: a failed save keeps everything the user typed on screen.
      if (err instanceof UnreachableError) setSaveFailed('unreachable')
      else if (err instanceof ApiError && err.code === 'validation') {
        const mapped: Errors = {}
        for (const f of err.fields) {
          const key = f.field as keyof Errors
          mapped[key] = razonEnEspanol(f.field, f.reason)
        }
        setErrors(mapped)
      } else setSaveFailed('server')
    }

    if (mode === 'nuevo') {
      create.mutate(
        { ...payload, source: voice ? 'voice' : 'manual' },
        { onSuccess: () => navigate('/finanzas', { replace: true }), onError },
      )
    } else if (expenseId) {
      // 17.7: back to this expense's detail, showing the values now stored —
      // `useUpdateExpense` invalidates the shared `keys.expense(id)` (KD-27).
      update.mutate({ id: expenseId, patch: payload }, { onSuccess: backToDetalle, onError })
    }
  }

  const title = mode === 'editar' ? gasto.editar : voice ? gasto.revisar : gasto.nuevo
  const draft = voice?.draft ?? null

  /*
   * 9.2: `resolved_by.<field> === 'none'` is the contract's own statement that
   * the field could not be determined, and the only signal used here — an
   * empty value is not evidence of anything, and a field the assist *suggested*
   * is a different state that keeps its "sugerido" tag instead. The mark clears
   * the moment the field is filled, so it always describes the form as it is.
   */
  const amountMissing = draft?.resolved_by.amount === 'none' && amount.trim() === ''
  const categoryMissing = draft?.resolved_by.category === 'none' && categoryId === null
  const methodMissing = draft?.resolved_by.payment_method === 'none' && methodId === null

  return (
    <Screen
      header={
        <FormBar
          title={title}
          // `nuevo` is untouched. `editar` pops to the detail it was opened
          // from — see backToDetalle above (17.7).
          back={mode === 'editar' ? (canPop ? -1 : `/finanzas/gasto/${expenseId}`) : '/finanzas'}
        />
      }
      capture={null}
      active="finanzas"
    >
      <form onSubmit={onSubmit} noValidate>
        {saveFailed && (
          <Banner
            tone="alarm"
            title={servidor.guardarFalloTitulo}
            detail={servidor.guardarFalloCuerpo}
          />
        )}

        {/* 8.2: what was heard, shown before anything is written. */}
        {voice && (
          <div className={s.transcript}>
            <div className={s.transcriptLabel}>{gasto.escuche}</div>
            <p className={s.transcriptText}>“{voice.transcript}”</p>
            <Button
              kind="text"
              auto
              className={s.transcriptRetry}
              onClick={() => navigate('/finanzas/gasto/nuevo', { replace: true, state: null })}
            >
              {gasto.grabarOtraVez}
            </Button>
            <div className={s.transcriptRule} />
          </div>
        )}

        <Field
          label={gasto.monto}
          after={
            amountMissing ? (
              <>
                {' '}
                <Tag need id={NEED_AMOUNT}>
                  {gasto.faltaEscribirlo}
                </Tag>
              </>
            ) : null
          }
        >
          <AmountInput
            value={amount}
            onValueChange={(v) => setAmount(formatAmountInput(v))}
            invalid={Boolean(errors.amount_cop)}
            missing={amountMissing}
            describedBy={amountMissing ? NEED_AMOUNT : undefined}
            label={gasto.monto}
            autoFocus={mode === 'nuevo' && !voice}
          />
          {errors.amount_cop && <FieldError>{errors.amount_cop}</FieldError>}
        </Field>

        <Field
          label={gasto.categoria}
          after={
            categorySuggested && categoryId !== null ? (
              <>
                {' '}
                <Tag>{gasto.sugerido}</Tag>
              </>
            ) : categoryMissing ? (
              <>
                {' '}
                <Tag need id={NEED_CATEGORY}>
                  {gasto.faltaElegirla}
                </Tag>
              </>
            ) : null
          }
        >
          <ChipRow
            ariaLabel={gasto.categoria}
            options={categories.data ?? []}
            selectedId={categoryId}
            missing={categoryMissing}
            describedBy={categoryMissing ? NEED_CATEGORY : undefined}
            onSelect={(id) => {
              categoryTouched.current = true
              setCategorySuggested(false)
              setCategoryId(id)
            }}
            newLabel={gasto.nueva}
            onNew={() => setCreating('categories')}
          />
          {creating === 'categories' && (
            <InlineCreate
              kind="categories"
              placeholder={gasto.nuevaCategoria}
              onDone={(id) => {
                categoryTouched.current = true
                setCategorySuggested(false)
                setCategoryId(id)
                setCreating(null)
              }}
              onCancel={() => setCreating(null)}
            />
          )}
          {errors.category_id && <FieldError>{errors.category_id}</FieldError>}
        </Field>

        <Field
          label={gasto.metodoPago}
          after={
            methodMissing ? (
              <>
                {' '}
                <Tag need id={NEED_METHOD}>
                  {gasto.faltaElegirlo}
                </Tag>
              </>
            ) : null
          }
        >
          <ChipRow
            ariaLabel={gasto.metodoPago}
            options={methods.data ?? []}
            selectedId={methodId}
            onSelect={setMethodId}
            newLabel={gasto.nuevo_}
            onNew={() => setCreating('payment-methods')}
            missing={methodMissing}
            describedBy={methodMissing ? NEED_METHOD : undefined}
          />
          {creating === 'payment-methods' && (
            <InlineCreate
              kind="payment-methods"
              placeholder={gasto.nuevoMetodo}
              onDone={(id) => {
                setMethodId(id)
                setCreating(null)
              }}
              onCancel={() => setCreating(null)}
            />
          )}
          {errors.payment_method_id && <FieldError>{errors.payment_method_id}</FieldError>}
        </Field>

        <Field label={gasto.fecha}>
          {showDate ? (
            <input
              type="date"
              className={formStyles.dateInput}
              value={effectiveDate ?? ''}
              max={today}
              aria-label={gasto.fecha}
              onChange={(e) => setSpentOn(e.target.value)}
            />
          ) : (
            <div className={formStyles.dateRow}>
              <span className={formStyles.dateValue}>
                {effectiveDate
                  ? effectiveDate === today
                    ? gasto.hoyEs(longDate(effectiveDate))
                    : longDate(effectiveDate)
                  : ''}
              </span>
              <Button kind="text" auto onClick={() => setShowDate(true)}>
                <CalendarIcon size={20} />
                {gasto.cambiarFecha}
              </Button>
            </div>
          )}
          {errors.spent_on && <FieldError>{errors.spent_on}</FieldError>}
        </Field>

        <Field label={gasto.descripcion} optional={gasto.opcional}>
          <TextInput
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder={gasto.descripcionPlaceholder}
            maxLength={1000}
          />
          {draft?.description_truncated && <Note>{gasto.descripcionRecortada}</Note>}
        </Field>

        <div className={formStyles.foot}>
          <Button type="submit" kind="primary" disabled={saving}>
            {saving ? gasto.guardando : mode === 'editar' ? gasto.guardarCambios : gasto.guardarGasto}
          </Button>
          {saving && <Hint centred>{gasto.seGuardaAqui}</Hint>}
          {voice && !saving && <Hint centred>{gasto.nadaSeGuarda}</Hint>}
          {mode === 'editar' && (
            <>
              <div className={s.gap} />
              {/* Constraint 19 / 5.2: this opens a confirmation, it does not delete. */}
              <Button kind="dangerGhost" onClick={() => setConfirmDelete(true)}>
                <TrashIcon size={20} />
                {gasto.eliminarGasto}
              </Button>
            </>
          )}
        </div>
      </form>

      {confirmDelete && existing.data && (
        <Sheet
          title={gasto.confirmarTitulo}
          body={gasto.confirmarCuerpo}
          subject={
            <>
              {formatCOP(existing.data.amount_cop)} · {existing.data.category_name} ·{' '}
              {existing.data.payment_method_name}
              <br />
              <span className={s.subjectMeta}>
                {[longDate(existing.data.spent_on), existing.data.description]
                  .filter(Boolean)
                  .join(' · ')}
              </span>
            </>
          }
          onDismiss={() => setConfirmDelete(false)}
          actions={
            <>
              <Button
                kind="danger"
                disabled={remove.isPending}
                onClick={() =>
                  remove.mutate(existing.data!.id, {
                    // 17.9: never leave the user on the detail of a record that
                    // no longer exists — replace straight to the list this
                    // expense was opened from, with its month and selection.
                    onSuccess: () => navigate(desde, { replace: true }),
                  })
                }
              >
                {gasto.eliminar}
              </Button>
              <Button kind="text" onClick={() => setConfirmDelete(false)}>
                {common.cancelar}
              </Button>
            </>
          }
        />
      )}
    </Screen>
  )
}

/**
 * 3.2: creating a category or payment method from inside the form. It opens an
 * inline field rather than a screen, so the draft is never abandoned — nothing
 * already typed is disturbed, which is the half of 3.2 the endpoint cannot do.
 */
function InlineCreate({
  kind,
  placeholder,
  onDone,
  onCancel,
}: {
  kind: NamedKind
  placeholder: string
  onDone: (id: number) => void
  onCancel: () => void
}) {
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const createNamed = useCreateNamed(kind)

  function submit() {
    if (name.trim() === '') {
      setError(razonEnEspanol('name', 'blank'))
      return
    }
    createNamed.mutate(name.trim(), {
      onSuccess: (item) => onDone(item.id),
      onError: (e) => {
        if (e instanceof ApiError && e.code === 'conflict')
          setError(razonEnEspanol('name', 'duplicate_name'))
        else if (e instanceof ApiError && e.code === 'validation')
          setError(razonEnEspanol('name', e.fieldReason('name') ?? 'blank'))
        else setError(razonEnEspanol('name', 'blank'))
      },
    })
  }

  return (
    <div className={s.inlineCreate}>
      <TextInput
        value={name}
        onChange={(e) => {
          setName(e.target.value)
          setError(null)
        }}
        placeholder={placeholder}
        maxLength={40}
        invalid={Boolean(error)}
        autoFocus
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault()
            submit()
          }
        }}
      />
      {error && <FieldError>{error}</FieldError>}
      <div className={s.inlineActions}>
        <Button kind="primary" className={s.inlineButton} onClick={submit} disabled={createNamed.isPending}>
          <PlusIcon size={18} />
          {gasto.crearYElegir}
        </Button>
        <Button kind="text" auto onClick={onCancel}>
          {common.cancelar}
        </Button>
      </div>
      <Hint>{gasto.seQuedaComoEsta}</Hint>
    </div>
  )
}

export const chipModule = chipStyles
