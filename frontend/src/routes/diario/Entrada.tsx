import { useEffect, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import {
  useCreateJournalEntry,
  useDeleteJournalEntry,
  useJournalEntry,
  useUpdateJournalEntry,
} from '../../api/queries'
import { ApiError, UnreachableError } from '../../api/client'
import { Button } from '../../components/ui/Button'
import { FieldError, Hint, TextArea, formStyles } from '../../components/ui/Form'
import { Banner } from '../../components/ui/Panel'
import { MicIcon, PencilIcon, TrashIcon } from '../../components/ui/Icon'
import { Sheet } from '../../components/ui/Sheet'
import { FormBar, Screen } from '../../components/shell/Screen'
import { useVoice } from '../../voice/VoiceContext'
import { common, diario, gasto, razonEnEspanol, servidor } from '../../copy/es'
import { clockTime, dateOf, longDate } from '../../format/dates'
import s from './Diario.module.css'

/** 6.5: the entry view never clamps — a 5.000-character entry is shown whole. */
export function EntradaLeer() {
  const { id } = useParams()
  const navigate = useNavigate()
  const entry = useJournalEntry(Number(id))
  const remove = useDeleteJournalEntry()
  const [confirm, setConfirm] = useState(false)

  const title = entry.data
    ? `${longDate(dateOf(entry.data.written_at))}, ${clockTime(entry.data.written_at)}`
    : ''

  return (
    <Screen header={<FormBar title={title} back="/diario" />} capture={null} active="diario">
      {entry.data && (
        <>
          <div className={s.reader}>
            <div className={s.body}>{entry.data.text}</div>
          </div>
          <div className={s.foot}>
            <Button kind="ghost" onClick={() => navigate(`/diario/${entry.data!.id}/editar`)}>
              <PencilIcon size={20} />
              {common.editar}
            </Button>
            <div className={s.gap} />
            {/* 5.2 / constraint 19: this opens a confirmation, nothing more. */}
            <Button kind="dangerGhost" onClick={() => setConfirm(true)}>
              <TrashIcon size={20} />
              {diario.eliminarEntrada}
            </Button>
          </div>
        </>
      )}

      {confirm && entry.data && (
        <Sheet
          title={diario.confirmarTitulo}
          body={diario.confirmarCuerpo}
          onDismiss={() => setConfirm(false)}
          actions={
            <>
              <Button
                kind="danger"
                disabled={remove.isPending}
                onClick={() =>
                  remove.mutate(entry.data!.id, {
                    onSuccess: () => navigate('/diario', { replace: true }),
                  })
                }
              >
                {gasto.eliminar}
              </Button>
              <Button kind="text" onClick={() => setConfirm(false)}>
                {common.cancelar}
              </Button>
            </>
          }
        />
      )}
    </Screen>
  )
}

/** 6.1 / 6.6 (write), 5.3 (edit), 10.1-10.3 (review a spoken entry). */
export function EntradaEscribir({ mode }: { mode: 'nueva' | 'editar' }) {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const voice = useVoice()
  const spoken = (location.state as { voice?: { transcript: string } } | null)?.voice ?? null

  const existing = useJournalEntry(mode === 'editar' ? Number(id) : null)
  const create = useCreateJournalEntry()
  const update = useUpdateJournalEntry()

  const [text, setText] = useState(spoken?.transcript ?? '')
  const [error, setError] = useState<string | null>(null)
  const [failed, setFailed] = useState(false)
  const [seeded, setSeeded] = useState(mode === 'nueva')

  useEffect(() => {
    if (seeded || !existing.data) return
    setText(existing.data.text)
    setSeeded(true)
  }, [existing.data, seeded])

  const saving = create.isPending || update.isPending

  function save() {
    setFailed(false)
    // 6.2: blank or whitespace-only is rejected inline, before the request.
    if (text.trim() === '') {
      setError(razonEnEspanol('text', 'blank'))
      return
    }
    const onError = (e: unknown) => {
      // 13.5: what was typed or transcribed stays on screen for the retry.
      if (e instanceof UnreachableError) setFailed(true)
      else if (e instanceof ApiError && e.code === 'validation')
        setError(razonEnEspanol('text', e.fieldReason('text') ?? 'blank'))
      else setFailed(true)
    }
    if (mode === 'nueva') {
      create.mutate(
        { text, source: spoken ? 'voice' : 'manual' },
        { onSuccess: () => navigate('/diario', { replace: true }), onError },
      )
    } else {
      update.mutate(
        { id: Number(id), text },
        { onSuccess: () => navigate(`/diario/${id}`, { replace: true }), onError },
      )
    }
  }

  const title = spoken ? diario.revisarEntrada : mode === 'editar' ? common.editar : diario.escribir

  return (
    <Screen header={<FormBar title={title} back="/diario" />} capture={null} active="diario">
      {failed && (
        <Banner
          tone="alarm"
          title={servidor.guardarFalloTitulo}
          detail={servidor.guardarFalloCuerpo}
        />
      )}

      {/* 10.2: the transcript is the user's own words, unedited by anything. */}
      {spoken && (
        <div className={s.transcriptHead}>
          <div className={s.transcriptLabel}>{gasto.escuche}</div>
          <Hint>{diario.sonTusPalabras}</Hint>
        </div>
      )}

      <div className={s.field}>
        <TextArea
          className={spoken ? s.medium : s.tall}
          value={text}
          onChange={(e) => {
            setText(e.target.value)
            setError(null)
          }}
          placeholder={diario.placeholder}
          invalid={Boolean(error)}
          autoFocus={!spoken}
        />
        {error && <FieldError>{error}</FieldError>}
        {!spoken && !error && <Hint>{diario.ayuda}</Hint>}
      </div>

      <div className={s.foot}>
        <Button kind="primary" onClick={save} disabled={saving}>
          {saving ? gasto.guardando : common.guardar}
        </Button>
        {saving && <Hint centred>{gasto.seGuardaAqui}</Hint>}
        {spoken && (
          <>
            <div className={s.gap} />
            <Button kind="text" onClick={() => voice.start('journal')}>
              <MicIcon />
              {gasto.grabarOtraVez}
            </Button>
          </>
        )}
      </div>
    </Screen>
  )
}

export const formModule = formStyles
