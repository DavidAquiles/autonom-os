import { useEffect, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  useAskQuestion,
  useCancelJob,
  useJob,
  useLatestSummary,
  useServerStatus,
} from '../../api/queries'
import { ApiError } from '../../api/client'
import type { InsightFacts, InsightJob, LatestSummary } from '../../api/types'
import { Button } from '../../components/ui/Button'
import { TextInput } from '../../components/ui/Form'
import { Banner, panelStyles as panel } from '../../components/ui/Panel'
import { MicIcon, SendIcon } from '../../components/ui/Icon'
import { Sheet } from '../../components/ui/Sheet'
import { Tally } from '../../components/ui/Tally'
import { useVoice } from '../../voice/VoiceContext'
import { analisis, common, erroresAccion, errorEnEspanol, servidor } from '../../copy/es'
import { elapsedLabel, monthName, stamp } from '../../format/dates'
import s from './Analisis.module.css'

const JOB_KEY = 'autonomos.jobId'

/**
 * `/finanzas/analisis` — a sub-route inside Finanzas, reached from the Finanzas
 * tabs and from a control in Diario. It is NOT a fourth destination (1.1).
 */
export function Analisis() {
  const location = useLocation()
  const navigate = useNavigate()
  const spoken = (location.state as { question?: string; source?: 'voice' } | null) ?? null

  const summary = useLatestSummary()
  const status = useServerStatus()
  const ask = useAskQuestion()
  const cancel = useCancelJob()
  const voice = useVoice()

  const [question, setQuestion] = useState('')
  const [jobId, setJobId] = useState<string | null>(() => sessionStorage.getItem(JOB_KEY))
  const [busy, setBusy] = useState(false)
  const [askError, setAskError] = useState<string | null>(null)
  const pendingSource = useRef<'text' | 'voice'>('text')

  const job = useJob(jobId)
  const llmDown = status.data?.llm === 'unavailable'
  const working = job.data?.status === 'queued' || job.data?.status === 'running'

  /* A spoken question arrives as router state, is put in the field, and is sent
     — 11.10 accepts typed or spoken and the transcript is what was heard. */
  useEffect(() => {
    if (!spoken?.question) return
    setQuestion(spoken.question)
    pendingSource.current = 'voice'
    navigate(location.pathname, { replace: true, state: null })
    submit(spoken.question, 'voice')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [spoken?.question])

  useEffect(() => {
    if (jobId) sessionStorage.setItem(JOB_KEY, jobId)
    else sessionStorage.removeItem(JOB_KEY)
  }, [jobId])

  // A finished job stops being the screen's business once it has been read; the
  // id is dropped so a reload does not resurrect an answered question.
  useEffect(() => {
    if (job.error instanceof ApiError && job.error.code === 'not_found') setJobId(null)
  }, [job.error])

  function submit(text: string, source: 'text' | 'voice') {
    const trimmed = text.trim()
    if (trimmed === '') return
    setAskError(null)
    ask.mutate(
      { question: trimmed, source },
      {
        onSuccess: (accepted) => {
          setJobId(accepted.job_id)
          setQuestion('')
        },
        onError: (e) => {
          // 409 is the only condition that emits `busy`: one question at a time.
          if (e instanceof ApiError && e.code === 'busy') setBusy(true)
          else if (e instanceof ApiError) setAskError(errorEnEspanol(e.code))
          else setAskError(servidor.bannerTitulo)
        },
      },
    )
  }

  return (
    <>
      {/* 11.4: the failure is visible and explained, and everything else keeps
          working — only the ask box goes quiet. */}
      {llmDown && (
        <Banner
          tone="flat"
          title={analisis.iaNoDisponibleTitulo}
          detail={analisis.iaNoDisponibleCuerpo}
          action={
            <Link className={panel.action} to="/finanzas/ajustes">
              {analisis.verEstadoServidor}
            </Link>
          }
        />
      )}

      {jobId && job.data && <JobCard job={job.data} onCancel={cancelJob} onClear={() => setJobId(null)} />}

      {!working && summary.data && <SummaryCard summary={summary.data} />}

      <div className={s.ask}>
        <div className={s.askLabel}>{analisis.hazUnaPregunta}</div>
        <div className={s.askRow}>
          <TextInput
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={llmDown ? analisis.preguntaNoDisponible : analisis.preguntaPlaceholder}
            disabled={llmDown || working}
            enterKeyHint="send"
            aria-label={analisis.hazUnaPregunta}
            maxLength={500}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                submit(question, 'text')
              }
            }}
          />
          <button
            type="button"
            className={s.askMic}
            aria-label={analisis.preguntarConVoz}
            disabled={llmDown || working}
            onClick={() => voice.start('question')}
          >
            <MicIcon />
          </button>
        </div>
        {question.trim() !== '' && !working && (
          <Button
            kind="primary"
            className={s.askSubmit}
            disabled={llmDown || ask.isPending}
            onClick={() => submit(question, 'text')}
          >
            <SendIcon size={20} />
            {analisis.preguntar}
          </Button>
        )}
        {askError && <div className={s.note}>{askError}</div>}
        <p className={s.local}>{analisis.preguntaAyuda}</p>
      </div>
      <div className={s.tail} />

      {busy && (
        <Sheet
          title={analisis.ocupadoTitulo}
          body={
            job.data?.question
              ? analisis.ocupadoCuerpo(job.data.question)
              : analisis.ocupadoCuerpoSinTexto
          }
          onDismiss={() => setBusy(false)}
          actions={
            <>
              <Button
                kind="primary"
                onClick={() => {
                  setBusy(false)
                  if (jobId) {
                    cancel.mutate(jobId, {
                      onSuccess: () => {
                        setJobId(null)
                        submit(question, pendingSource.current)
                      },
                    })
                  }
                }}
              >
                {analisis.cancelarEsa}
              </Button>
              <Button kind="text" onClick={() => setBusy(false)}>
                {analisis.esperar}
              </Button>
            </>
          }
        />
      )}
    </>
  )

  function cancelJob() {
    if (!jobId) return
    // 11.13: cancelling stops generation and touches no saved data.
    cancel.mutate(jobId, { onSettled: () => setJobId(null) })
  }
}

/** One question: waiting, answered, or explicitly failed. */
function JobCard({
  job,
  onCancel,
  onClear,
}: {
  job: InsightJob
  onCancel: () => void
  onClear: () => void
}) {
  const working = job.status === 'queued' || job.status === 'running'

  return (
    <div className={s.card}>
      <div className={s.qhead}>“{job.question}”</div>

      {working && (
        <div className={s.wait}>
          <div className={s.phase}>{analisis.pensando}</div>
          {/*
            `elapsed_ms` is the only progress signal on the wire, and no generated
            text exists before the job is `done` (KD-11) — so elapsed time is all
            there is to draw, and a determinate bar would be a promise nobody can
            keep (constraint 28).
          */}
          <Tally seconds={job.elapsed_ms / 1000} />
          <p className={s.local}>{analisis.esperaCuerpo}</p>
          <div className={s.acts}>
            <Button kind="ghost" onClick={onCancel}>
              {analisis.cancelarPregunta}
            </Button>
          </div>
        </div>
      )}

      {job.status === 'done' && job.answer && (
        <>
          <div className={s.prose}>
            {job.answer.split(/\n{2,}/).map((p, i) => (
              <p key={i}>{p}</p>
            ))}
          </div>
          {job.facts && <FactsBlock facts={job.facts} elapsedMs={job.elapsed_ms} />}
        </>
      )}

      {job.status === 'failed' && job.error_code && (
        <>
          <div className={s.prose}>
            <p>{errorEnEspanol(job.error_code)}</p>
          </div>
          {erroresAccion[job.error_code] && (
            <Button kind="ghost" className={s.retry} onClick={onClear}>
              {erroresAccion[job.error_code]}
            </Button>
          )}
        </>
      )}

      {job.status === 'cancelled' && <div className={`${s.prose} ${s.pending}`}>{analisis.sinResponder}</div>}
    </div>
  )
}

function FactsBlock({ facts, elapsedMs }: { facts: InsightFacts; elapsedMs: number }) {
  const used = facts.journal_entries_used
  const considered = facts.journal_entries_considered
  return (
    <>
      {/* Client-side contract: when `journal_truncated` is true the client MUST
          say so, using the two counts. This is an obligation, not an option. */}
      {facts.journal_truncated && used !== null && considered !== null && (
        <div className={s.note}>
          <b>{analisis.truncado(used, considered)}</b>
        </div>
      )}
      {/* `period_assumed` says the question named no period, so the answer says
          which one it was about rather than letting the user assume. */}
      {facts.period_assumed && <div className={s.note}>{analisis.periodoAsumido(facts.period_label)}</div>}
      <ul className={s.facts}>
        <li>
          <span className={s.factName}>{analisis.periodo}</span>
          <span className={s.factValue}>{facts.period_label}</span>
        </li>
        {used !== null && considered !== null && (
          <li>
            <span className={s.factName}>{analisis.entradasLeidas}</span>
            <span className={s.factValue}>{analisis.deN(used, considered)}</span>
          </li>
        )}
        <li>
          <span className={s.factName}>{analisis.tardo}</span>
          <span className={s.factValue}>{elapsedLabel(elapsedMs)}</span>
        </li>
      </ul>
    </>
  )
}

/**
 * Constraint 27: ready, never produced, and being produced are three surfaces
 * you can tell apart on sight, plus a failure. None of the four is an empty area.
 */
function SummaryCard({ summary }: { summary: LatestSummary }) {
  if (summary.status === 'ready') {
    return (
      <div className={s.card}>
        {/* 11.18: which period, and when it was produced. */}
        <h2>{analisis.resumenDe(summary.period_label)}</h2>
        <div className={s.stamp}>{analisis.escritoEl(stamp(summary.generated_at))}</div>
        <div className={s.prose}>
          {summary.text.split(/\n{2,}/).map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </div>
      </div>
    )
  }

  if (summary.status === 'generating') {
    return (
      <div className={s.card}>
        <h2>{analisis.escribiendoResumen(summary.period_label)}</h2>
        <div className={s.stamp}>{analisis.empezoALas(stamp(summary.started_at))}</div>
        <div className={s.wait}>
          <SummaryTally since={summary.started_at} />
          <p className={s.local}>{analisis.escribiendoCuerpo}</p>
        </div>
      </div>
    )
  }

  if (summary.status === 'empty') {
    return (
      <div className={s.card}>
        <h2>{analisis.periodoVacioTitulo(summary.period_label)}</h2>
        <div className={s.prose}>
          <p>{analisis.periodoVacioCuerpo}</p>
        </div>
      </div>
    )
  }

  if (summary.status === 'failed') {
    return (
      <div className={s.card}>
        <h2>{analisis.resumenFalloTitulo(monthName(summary.period_key))}</h2>
        <div className={s.prose}>
          <p>{analisis.resumenFalloCuerpo}</p>
        </div>
        {/* There is no endpoint to re-run a summary and KD-12 already gives it
            three automatic attempts, so this promises nothing it cannot do. */}
        <div className={s.note}>{analisis.resumenFalloNota}</div>
      </div>
    )
  }

  return (
    <div className={s.card}>
      <h2>{analisis.sinResumenTitulo}</h2>
      <div className={s.prose}>
        <p>{analisis.sinResumenCuerpo}</p>
      </div>
    </div>
  )
}

/**
 * The background summary has no `elapsed_ms` on the wire — only `started_at` —
 * so the tally counts from that timestamp. Same shape, same honesty: elapsed
 * time and nothing implying an end.
 */
function SummaryTally({ since }: { since: string }) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const t = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(t)
  }, [])
  const seconds = Math.max(0, (now - new Date(since).getTime()) / 1000)
  return <Tally seconds={seconds} />
}

export const analisisStyles = s
export { common }
