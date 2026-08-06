import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError, UnreachableError, api } from '../api/client'
import type { ExpenseDraft, Transcription } from '../api/types'
import { blobToWav } from './wav'

export type VoiceContextKind = 'expense' | 'journal' | 'question'

/** The hard cap on a recording (8.8, and MAX_AUDIO_S on the server is 32 s). */
export const MAX_RECORD_S = 30
/**
 * KD-5: the client owns the failure clock for 8.8 — a transcript or an explicit
 * failure inside 30 s of the capture ending. We abort at 28 s to leave room for
 * the failure itself to render.
 */
export const TRANSCRIBE_DEADLINE_S = 28

export type VoicePhase =
  | { kind: 'idle' }
  | { kind: 'listening'; seconds: number }
  | { kind: 'working'; step: 'preparing' | 'uploading' | 'transcribing'; seconds: number }
  | { kind: 'failed'; code: string }
  | { kind: 'denied' }
  | { kind: 'unsupported' }

interface VoiceState {
  phase: VoicePhase
  context: VoiceContextKind | null
  start: (context: VoiceContextKind) => void
  stop: () => void
  cancel: () => void
  /** abandon an in-flight transcription and go to the manual form (8.9) */
  abandon: () => void
  retry: () => void
}

const Ctx = createContext<VoiceState | null>(null)

export function useVoice(): VoiceState {
  const v = useContext(Ctx)
  if (!v) throw new Error('VoiceProvider missing')
  return v
}

/** Handed to the review screens through router state — never persisted. */
export interface ExpenseVoiceResult {
  transcript: string
  draft: ExpenseDraft | null
}

export function VoiceProvider({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()
  const [phase, setPhase] = useState<VoicePhase>({ kind: 'idle' })
  const [context, setContext] = useState<VoiceContextKind | null>(null)

  const streamRef = useRef<MediaStream | null>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const abortRef = useRef<AbortController | null>(null)
  const timerRef = useRef<number | null>(null)
  const cancelledRef = useRef(false)

  const clearTimer = () => {
    if (timerRef.current !== null) {
      window.clearInterval(timerRef.current)
      timerRef.current = null
    }
  }

  const releaseMic = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    recorderRef.current = null
  }, [])

  const reset = useCallback(() => {
    clearTimer()
    abortRef.current?.abort()
    abortRef.current = null
    releaseMic()
    chunksRef.current = []
    setPhase({ kind: 'idle' })
    setContext(null)
  }, [releaseMic])

  useEffect(() => () => clearTimer(), [])

  const transcribe = useCallback(
    async (audio: Blob, kind: VoiceContextKind) => {
      cancelledRef.current = false
      const started = Date.now()
      clearTimer()
      timerRef.current = window.setInterval(() => {
        setPhase((p) =>
          p.kind === 'working'
            ? { ...p, seconds: Math.floor((Date.now() - started) / 1000) }
            : p,
        )
      }, 1000)

      const controller = new AbortController()
      abortRef.current = controller
      const deadline = window.setTimeout(
        () => controller.abort(),
        TRANSCRIBE_DEADLINE_S * 1000,
      )

      try {
        setPhase({ kind: 'working', step: 'preparing', seconds: 0 })
        const wav = await blobToWav(audio)
        if (cancelledRef.current) return

        setPhase({ kind: 'working', step: 'uploading', seconds: elapsed(started) })
        const form = new FormData()
        form.append('audio', wav, 'captura.wav')
        form.append('context', kind)

        // Flip to "transcribing" as soon as the bytes are on their way: it is one
        // blocking round trip with no server-side progress channel, so the phase
        // label plus the elapsed count is the whole progress signal (constraint 25).
        window.setTimeout(
          () =>
            setPhase((p) =>
              p.kind === 'working' ? { ...p, step: 'transcribing' } : p,
            ),
          300,
        )

        const result = await api.postForm<Transcription>(
          '/voice/transcribe',
          form,
          controller.signal,
        )
        if (cancelledRef.current) return

        clearTimer()
        window.clearTimeout(deadline)
        releaseMic()
        setPhase({ kind: 'idle' })
        setContext(null)

        // 8.2 / 8.6: what was heard is shown for confirmation; nothing is written
        // until the user submits the form.
        if (kind === 'expense') {
          navigate('/finanzas/gasto/nuevo', {
            state: { voice: { transcript: result.transcript, draft: result.draft } },
          })
        } else if (kind === 'journal') {
          navigate('/diario/nueva', { state: { voice: { transcript: result.transcript } } })
        } else {
          navigate('/finanzas/analisis', {
            state: { question: result.transcript, source: 'voice' },
          })
        }
      } catch (e) {
        clearTimer()
        window.clearTimeout(deadline)
        releaseMic()
        if (cancelledRef.current) return
        if (e instanceof DOMException && e.name === 'AbortError') {
          setPhase({ kind: 'failed', code: 'transcription_timeout' })
        } else if (e instanceof ApiError) {
          setPhase({ kind: 'failed', code: e.code })
        } else if (e instanceof UnreachableError) {
          setPhase({ kind: 'failed', code: 'unreachable' })
        } else {
          setPhase({ kind: 'failed', code: 'audio_invalid' })
        }
      }
    },
    [navigate, releaseMic],
  )

  const finish = useCallback(
    (kind: VoiceContextKind) => {
      const rec = recorderRef.current
      if (!rec) return
      rec.onstop = () => {
        const audio = new Blob(chunksRef.current, { type: chunksRef.current[0]?.type })
        chunksRef.current = []
        if (cancelledRef.current) {
          releaseMic()
          return
        }
        void transcribe(audio, kind)
      }
      if (rec.state !== 'inactive') rec.stop()
    },
    [releaseMic, transcribe],
  )

  const start = useCallback(
    async (kind: VoiceContextKind) => {
      cancelledRef.current = false
      setContext(kind)

      if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
        setPhase({ kind: 'unsupported' })
        return
      }

      let stream: MediaStream
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      } catch {
        // 8.5: permission denied is explained, and the manual path keeps working.
        setPhase({ kind: 'denied' })
        return
      }
      if (cancelledRef.current) {
        stream.getTracks().forEach((t) => t.stop())
        return
      }

      streamRef.current = stream
      chunksRef.current = []
      const rec = new MediaRecorder(stream)
      recorderRef.current = rec
      rec.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }
      rec.start()

      const startedAt = Date.now()
      setPhase({ kind: 'listening', seconds: 0 })
      clearTimer()
      timerRef.current = window.setInterval(() => {
        const secs = elapsed(startedAt)
        if (secs >= MAX_RECORD_S) {
          clearTimer()
          setPhase({ kind: 'working', step: 'preparing', seconds: 0 })
          finish(kind)
          return
        }
        setPhase({ kind: 'listening', seconds: secs })
      }, 250)
    },
    [finish],
  )

  const stop = useCallback(() => {
    if (!context) return
    clearTimer()
    setPhase({ kind: 'working', step: 'preparing', seconds: 0 })
    finish(context)
  }, [context, finish])

  /** 8.3: cancelling discards everything locally and issues no request. */
  const cancel = useCallback(() => {
    cancelledRef.current = true
    const rec = recorderRef.current
    if (rec && rec.state !== 'inactive') {
      rec.onstop = null
      rec.stop()
    }
    reset()
  }, [reset])

  /** 8.9: abandon an in-flight transcription for the manual form. */
  const abandon = useCallback(() => {
    const kind = context
    cancelledRef.current = true
    reset()
    if (kind === 'journal') navigate('/diario/nueva')
    else if (kind === 'expense') navigate('/finanzas/gasto/nuevo')
  }, [context, navigate, reset])

  const retry = useCallback(() => {
    const kind = context ?? 'expense'
    reset()
    void start(kind)
  }, [context, reset, start])

  const value = useMemo<VoiceState>(
    () => ({ phase, context, start: (k) => void start(k), stop, cancel, abandon, retry }),
    [phase, context, start, stop, cancel, abandon, retry],
  )

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

function elapsed(since: number): number {
  return Math.floor((Date.now() - since) / 1000)
}
