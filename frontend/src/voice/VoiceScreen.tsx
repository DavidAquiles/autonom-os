import { useLocation } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { MicIcon, StopIcon } from '../components/ui/Icon'
import { Tally } from '../components/ui/Tally'
import { FormBar, Screen } from '../components/shell/Screen'
import { common, gasto, servidor, voz } from '../copy/es'
import { mmss } from '../format/dates'
import { MAX_RECORD_S, useVoice, type VoiceContextKind } from './VoiceContext'
import s from './VoiceScreen.module.css'

const TITLES: Record<VoiceContextKind, string> = {
  expense: voz.gastoPorVoz,
  journal: voz.entradaPorVoz,
  question: voz.preguntaPorVoz,
}

export function VoiceScreen() {
  const voice = useVoice()
  const { pathname } = useLocation()
  const kind = voice.context ?? 'expense'
  const active = pathname.startsWith('/diario') ? 'diario' : 'finanzas'

  return (
    <Screen
      header={<FormBar title={TITLES[kind]} back={-1} />}
      capture={null}
      active={active}
      scroll={voice.phase.kind !== 'listening'}
    >
      {render()}
    </Screen>
  )

  function render() {
    const p = voice.phase
    switch (p.kind) {
      case 'listening':
        return <Listening seconds={p.seconds} onStop={voice.stop} onCancel={voice.cancel} />
      case 'working':
        return <Working step={p.step} seconds={p.seconds} kind={kind} />
      case 'denied':
        return <Denied kind={kind} />
      case 'unsupported':
        return <Unsupported kind={kind} />
      case 'failed':
        return <Failed code={p.code} kind={kind} />
      default:
        return null
    }
  }
}

/**
 * A bounded wait: the recording stops itself at 30 s, so the meter has a real
 * endpoint and is not a promise about work nobody can time.
 */
function Listening({
  seconds,
  onStop,
  onCancel,
}: {
  seconds: number
  onStop: () => void
  onCancel: () => void
}) {
  const pct = Math.min(100, (seconds / MAX_RECORD_S) * 100)
  return (
    <div className={s.listen}>
      <div className={s.pulse}>
        <MicIcon size={46} strokeWidth={1.5} />
      </div>
      <h2>{voz.escuchando}</h2>
      <div className={s.clock}>{mmss(seconds)}</div>
      <div className={s.cap}>
        <div
          className={s.capTrack}
          role="progressbar"
          aria-label={voz.maximo}
          aria-valuemin={0}
          aria-valuemax={MAX_RECORD_S}
          aria-valuenow={Math.min(seconds, MAX_RECORD_S)}
        >
          <div className={s.capFill} style={{ width: `${pct}%` }} />
        </div>
        <div className={s.capLabel}>{voz.maximo}</div>
      </div>
      <div className={s.acts}>
        <Button kind="primary" onClick={onStop}>
          <StopIcon size={26} />
          {voz.listo}
        </Button>
        <Button kind="text" onClick={onCancel}>
          {common.cancelar}
        </Button>
      </div>
    </div>
  )
}

/**
 * An unbounded wait: a phase label, a tally that gains a stroke a second, and a
 * cancel from t=0 rather than from t=10 (constraint 26 — this is the wait the
 * user meets several times a day; a control that appears late is one he learns
 * not to look for).
 */
function Working({
  step,
  seconds,
  kind,
}: {
  step: 'preparing' | 'uploading' | 'transcribing'
  seconds: number
  kind: VoiceContextKind
}) {
  const voice = useVoice()
  const label =
    step === 'preparing' ? voz.preparando : step === 'uploading' ? voz.enviando : voz.transcribiendo
  return (
    <div className={s.wait}>
      <h2>{voz.pasandoATexto}</h2>
      <div className={s.phase}>{label}</div>
      <Tally seconds={seconds} />
      <p className={s.local}>{voz.local}</p>
      <div className={s.acts}>
        {kind !== 'question' && (
          <Button kind="ghost" onClick={voice.abandon}>
            {voz.escribirAMano}
          </Button>
        )}
        <Button kind="text" onClick={voice.cancel}>
          {common.cancelar}
        </Button>
      </div>
    </div>
  )
}

function Failed({ code, kind }: { code: string; kind: VoiceContextKind }) {
  const voice = useVoice()
  const unreachable = code === 'unreachable'
  return (
    <div className={s.wait}>
      <h2>{unreachable ? servidor.guardarFalloTitulo : voz.falloTitulo}</h2>
      <p className={s.local} style={{ marginTop: 12 }}>
        {unreachable ? servidor.guardarFalloCuerpo : bodyFor(code)}
      </p>
      <div className={s.acts}>
        <Button kind="primary" onClick={voice.retry}>
          <MicIcon />
          {gasto.grabarOtraVez}
        </Button>
        {kind !== 'question' && (
          <Button kind="ghost" onClick={voice.abandon}>
            {voz.escribirAMano}
          </Button>
        )}
      </div>
      {!unreachable && <div className={s.note}>{voz.falloNota}</div>}
    </div>
  )
}

function Denied({ kind }: { kind: VoiceContextKind }) {
  const voice = useVoice()
  return (
    <div className={s.wait}>
      <h2>{voz.sinPermisoTitulo}</h2>
      <p className={s.local} style={{ marginTop: 12 }}>
        {voz.sinPermisoCuerpo}
      </p>
      <p className={s.local}>{voz.sinPermisoManual}</p>
      <div className={s.acts}>
        <Button kind="primary" onClick={kind === 'question' ? voice.cancel : voice.abandon}>
          {kind === 'question' ? common.volver : voz.escribirGastoAMano}
        </Button>
      </div>
    </div>
  )
}

function Unsupported({ kind }: { kind: VoiceContextKind }) {
  const voice = useVoice()
  return (
    <div className={s.wait}>
      <h2>{voz.sinMicrofonoTitulo}</h2>
      <p className={s.local} style={{ marginTop: 12 }}>
        {voz.sinMicrofonoCuerpo}
      </p>
      <div className={s.acts}>
        <Button kind="primary" onClick={kind === 'question' ? voice.cancel : voice.abandon}>
          {kind === 'question' ? common.volver : voz.escribirGastoAMano}
        </Button>
      </div>
    </div>
  )
}

function bodyFor(code: string): string {
  // 8.4: a failure says what happened in plain language and saves nothing. The
  // backend's own `message` is never shown (KD-17).
  if (code === 'transcription_timeout') return voz.falloTimeout
  if (code === 'audio_too_long') return voz.falloLargo
  if (code === 'audio_invalid') return voz.falloAudio
  return voz.falloCuerpo
}
