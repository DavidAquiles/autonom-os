import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
  useCategories,
  useCreateNamed,
  usePaymentMethods,
  useRemoveNamed,
  useRenameNamed,
  useServerStatus,
  type NamedKind,
} from '../../api/queries'
import { ApiError } from '../../api/client'
import type { NamedItem } from '../../api/types'
import { Button } from '../../components/ui/Button'
import { chipStyles } from '../../components/ui/Chip'
import { Field, FieldError, Hint, TextInput, formStyles } from '../../components/ui/Form'
import { SectionLabel } from '../../components/ui/Panel'
import { DownloadIcon, PlusIcon, TrashIcon } from '../../components/ui/Icon'
import { Sheet } from '../../components/ui/Sheet'
import { FormBar, Screen } from '../../components/shell/Screen'
import { ajustes, common, razonEnEspanol } from '../../copy/es'
import fin from './Finanzas.module.css'
import s from './Ajustes.module.css'

/**
 * The maintenance that is not capture: rename (3.3), remove with the in-use
 * warning (3.4) and export (14.2). A sub-route inside Finanzas — the bottom
 * navigation still carries exactly three destinations (1.1).
 */
export function Ajustes() {
  const categories = useCategories()
  const methods = usePaymentMethods()
  const status = useServerStatus()
  const [creating, setCreating] = useState<NamedKind | null>(null)

  return (
    <Screen header={<FormBar title={ajustes.titulo} back="/finanzas" />} capture={null} active="finanzas">
      <SectionLabel>{ajustes.categorias}</SectionLabel>
      <NamedList kind="categories" items={categories.data ?? []} />
      <div className={s.newRow}>
        {creating === 'categories' ? (
          <CreateInline kind="categories" onDone={() => setCreating(null)} />
        ) : (
          <button
            type="button"
            className={`${chipStyles.chip} ${chipStyles.new}`}
            onClick={() => setCreating('categories')}
          >
            <PlusIcon size={18} />
            {ajustes.nuevaCategoria}
          </button>
        )}
      </div>

      <SectionLabel>{ajustes.metodosPago}</SectionLabel>
      <NamedList kind="payment-methods" items={methods.data ?? []} />
      <div className={s.newRow}>
        {creating === 'payment-methods' ? (
          <CreateInline kind="payment-methods" onDone={() => setCreating(null)} />
        ) : (
          <button
            type="button"
            className={`${chipStyles.chip} ${chipStyles.new}`}
            onClick={() => setCreating('payment-methods')}
          >
            <PlusIcon size={18} />
            {ajustes.nuevoMetodo}
          </button>
        )}
      </div>

      {/* 11.4: the AI layers report themselves here, so an unavailable model is
          explained rather than discovered. */}
      <SectionLabel>{ajustes.tuServidor}</SectionLabel>
      <ul className={fin.pm}>
        <li>
          <span className={fin.name}>{ajustes.transcripcion}</span>
          <span className={s.statusValue}>
            {status.data?.transcription === 'ok' ? ajustes.disponible : ajustes.noDisponible}
          </span>
        </li>
        <li>
          <span className={fin.name}>{ajustes.modeloTexto}</span>
          <span className={s.statusValue}>
            {status.data?.llm === 'ok' ? ajustes.disponible : ajustes.noDisponible}
          </span>
        </li>
      </ul>

      {/* 14.2: the whole record, in a file that reads without this app. */}
      <SectionLabel>{ajustes.copiaSeguridad}</SectionLabel>
      <div className={s.exportBlock}>
        <a className={s.exportLink} href="/api/export" download>
          <DownloadIcon size={20} />
          {ajustes.exportarTodo}
        </a>
        <Hint>{ajustes.exportarAyuda}</Hint>
      </div>
    </Screen>
  )
}

function NamedList({ kind, items }: { kind: NamedKind; items: NamedItem[] }) {
  return (
    <ul className={fin.ledger}>
      {items.map((i) => (
        <li key={i.id}>
          <Link className={fin.row} to={`/finanzas/ajustes/${kind}/${i.id}`}>
            <span className={fin.what}>
              <span className={fin.cat}>{i.name}</span>
              <span className={fin.meta}>
                {i.in_use_count > 0 ? ajustes.enNGastos(i.in_use_count) : ajustes.sinUsar}
              </span>
            </span>
            <span className={fin.editHint}>{common.editar}</span>
          </Link>
        </li>
      ))}
    </ul>
  )
}

function CreateInline({ kind, onDone }: { kind: NamedKind; onDone: () => void }) {
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const create = useCreateNamed(kind)
  return (
    <div className={s.createInline}>
      <TextInput
        value={name}
        onChange={(e) => {
          setName(e.target.value)
          setError(null)
        }}
        maxLength={40}
        autoFocus
        invalid={Boolean(error)}
        placeholder={kind === 'categories' ? ajustes.nuevaCategoria : ajustes.nuevoMetodo}
      />
      {error && <FieldError>{error}</FieldError>}
      <div className={s.createActions}>
        <Button
          kind="primary"
          className={s.smallButton}
          disabled={create.isPending}
          onClick={() => {
            if (name.trim() === '') return setError(razonEnEspanol('name', 'blank'))
            create.mutate(name.trim(), {
              onSuccess: onDone,
              onError: (e) =>
                setError(
                  e instanceof ApiError && e.code === 'conflict'
                    ? razonEnEspanol('name', 'duplicate_name')
                    : razonEnEspanol('name', 'blank'),
                ),
            })
          }}
        >
          {common.guardar}
        </Button>
        <Button kind="text" auto onClick={onDone}>
          {common.cancelar}
        </Button>
      </div>
    </div>
  )
}

/** Rename (3.3) and remove (3.4) for one category or payment method. */
export function EditarNombre() {
  const { kind, id } = useParams()
  const navigate = useNavigate()
  const named = kind === 'payment-methods' ? 'payment-methods' : 'categories'
  const categories = useCategories()
  const methods = usePaymentMethods()
  const items = named === 'categories' ? categories.data : methods.data
  const item = items?.find((i) => i.id === Number(id))

  const rename = useRenameNamed(named as NamedKind)
  const remove = useRemoveNamed(named as NamedKind)

  const [name, setName] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [confirm, setConfirm] = useState<{ affected: number } | null>(null)

  const value = name ?? item?.name ?? ''

  function save() {
    if (!item) return
    if (value.trim() === '') return setError(razonEnEspanol('name', 'blank'))
    rename.mutate(
      { id: item.id, name: value.trim() },
      {
        onSuccess: () => navigate('/finanzas/ajustes'),
        onError: (e) =>
          setError(
            e instanceof ApiError && e.code === 'conflict'
              ? razonEnEspanol('name', 'duplicate_name')
              : razonEnEspanol('name', e instanceof ApiError ? (e.fieldReason('name') ?? 'blank') : 'blank'),
          ),
      },
    )
  }

  /**
   * The warning 3.4 requires is composed from `error.details.affected_expenses`
   * — we probe with `confirm=false` first precisely to get that count from the
   * server rather than guessing it, and only then ask.
   */
  function askToRemove() {
    if (!item) return
    if (item.in_use_count === 0) {
      setConfirm({ affected: 0 })
      return
    }
    remove.mutate(
      { id: item.id, confirm: false },
      {
        onSuccess: () => navigate('/finanzas/ajustes'),
        onError: (e) => {
          if (e instanceof ApiError && e.code === 'in_use') {
            setConfirm({ affected: Number(e.details.affected_expenses ?? item.in_use_count) })
          }
        },
      },
    )
  }

  if (!item) return null

  return (
    <Screen
      header={<FormBar title={ajustes.titulo} back="/finanzas/ajustes" />}
      capture={null}
      active="finanzas"
    >
      <Field label={ajustes.nombre}>
        <TextInput
          value={value}
          maxLength={40}
          invalid={Boolean(error)}
          onChange={(e) => {
            setName(e.target.value)
            setError(null)
          }}
        />
        {error && <FieldError>{error}</FieldError>}
      </Field>

      <div className={formStyles.foot}>
        <Button kind="primary" onClick={save} disabled={rename.isPending}>
          {ajustes.guardarNombre}
        </Button>
        <div className={s.gap} />
        <Button kind="dangerGhost" onClick={askToRemove} disabled={remove.isPending}>
          <TrashIcon size={20} />
          {ajustes.quitarDeLaLista}
        </Button>
      </div>

      {confirm && (
        <Sheet
          title={
            confirm.affected > 0
              ? ajustes.quitarTitulo(item.name, confirm.affected)
              : ajustes.quitarSinUsoTitulo(item.name)
          }
          body={
            confirm.affected > 0
              ? ajustes.quitarCuerpo(item.name, confirm.affected)
              : ajustes.quitarSinUsoCuerpo
          }
          onDismiss={() => setConfirm(null)}
          actions={
            <>
              <Button
                kind="danger"
                disabled={remove.isPending}
                onClick={() =>
                  remove.mutate(
                    { id: item.id, confirm: true },
                    { onSuccess: () => navigate('/finanzas/ajustes') },
                  )
                }
              >
                {ajustes.quitarDeLaLista}
              </Button>
              <Button kind="text" onClick={() => setConfirm(null)}>
                {common.cancelar}
              </Button>
            </>
          }
        />
      )}
    </Screen>
  )
}
