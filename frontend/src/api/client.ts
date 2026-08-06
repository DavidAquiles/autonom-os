import type { ApiErrorBody, ErrorCode, FieldError } from './types'

/**
 * KD-2: every request uses a RELATIVE path. No origin, no host, no port is
 * written anywhere in this bundle — the app is served from the same origin as
 * the API, on Tailscale or on the LAN fallback, and must work unchanged on both.
 */
const BASE = '/api'

/** A non-2xx response carrying the contract's error envelope. */
export class ApiError extends Error {
  readonly code: ErrorCode
  readonly httpStatus: number
  readonly fields: FieldError[]
  readonly details: Record<string, unknown>

  constructor(httpStatus: number, body: ApiErrorBody['error']) {
    // The message is a developer string. It exists for the console, and KD-17
    // forbids ever putting it on screen.
    super(body.message)
    this.name = 'ApiError'
    this.httpStatus = httpStatus
    this.code = body.code
    this.fields = body.fields ?? []
    this.details = (body.details ?? {}) as Record<string, unknown>
  }

  fieldReason(field: string): string | undefined {
    return this.fields.find((f) => f.field === field)?.reason
  }
}

/** The server could not be reached at all — 13.2's condition, not an API error. */
export class UnreachableError extends Error {
  constructor(cause?: unknown) {
    super('unreachable')
    this.name = 'UnreachableError'
    this.cause = cause
  }
}

interface RequestOptions {
  method?: string
  body?: unknown
  signal?: AbortSignal
  /** multipart bodies are passed through untouched */
  form?: FormData
}

export async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, signal, form } = opts
  let res: Response
  try {
    res = await fetch(BASE + path, {
      method,
      signal,
      headers: form || body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: form ?? (body === undefined ? undefined : JSON.stringify(body)),
    })
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') throw e
    throw new UnreachableError(e)
  }

  if (res.status === 204) return undefined as T

  let payload: unknown
  try {
    payload = await res.json()
  } catch {
    payload = undefined
  }

  if (!res.ok) {
    const envelope = (payload as ApiErrorBody | undefined)?.error
    throw new ApiError(
      res.status,
      envelope ?? { code: 'internal', message: `HTTP ${res.status}` },
    )
  }
  return payload as T
}

export const api = {
  get: <T>(path: string, signal?: AbortSignal) => request<T>(path, { signal }),
  post: <T>(path: string, body?: unknown, signal?: AbortSignal) =>
    request<T>(path, { method: 'POST', body, signal }),
  postForm: <T>(path: string, form: FormData, signal?: AbortSignal) =>
    request<T>(path, { method: 'POST', form, signal }),
  patch: <T>(path: string, body: unknown) => request<T>(path, { method: 'PATCH', body }),
  del: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}

/** Query-string builder that omits undefined values. */
export function qs(params: Record<string, string | number | boolean | undefined>): string {
  const parts = Object.entries(params)
    .filter(([, v]) => v !== undefined)
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
  return parts.length ? `?${parts.join('&')}` : ''
}
