/*
 * Types transcribed from `factory/architect/design.md` § Interface Contract.
 * Nothing here is invented: if a field is absent from the contract it is absent
 * here, so no component can render it. Two fields are deliberately missing and
 * their absence is load-bearing:
 *   - `source` on expenses and journal entries (9.5, 10.4)
 *   - `partial_answer` on an insight job (KD-11)
 */

export type ErrorCode =
  | 'validation'
  | 'not_found'
  | 'conflict'
  | 'in_use'
  | 'audio_invalid'
  | 'audio_too_long'
  | 'transcription_failed'
  | 'transcription_timeout'
  | 'llm_unavailable'
  | 'llm_timeout'
  | 'insufficient_data'
  | 'unverifiable_figures'
  | 'period_unrecognised'
  | 'preempted'
  | 'busy'
  | 'internal'

export type FieldReason =
  | 'required'
  | 'must_be_positive'
  | 'not_an_integer'
  | 'too_long'
  | 'future_date'
  | 'blank'
  | 'unknown_id'
  | 'duplicate_name'

export interface FieldError {
  field: string
  reason: FieldReason
}

export interface ApiErrorBody {
  error: {
    code: ErrorCode
    /** developer string — KD-17: never displayed */
    message: string
    fields?: FieldError[]
    details?: { affected_expenses?: number } & Record<string, unknown>
  }
}

export interface Health {
  status: 'ok'
  server_time: string
  tz: string
  version: string
  /**
   * Absolute origins from server configuration, never derived from the request.
   * Either may be `null` — `lan` is null whenever the fallback listener is
   * disabled — and null means "no alternative exists", not an error (KD-2).
   */
  origins: { primary: string | null; lan: string | null }
}

export interface Status {
  transcription: 'ok' | 'unavailable'
  llm: 'ok' | 'unavailable'
  checked_at: string
}

export interface NamedItem {
  id: number
  name: string
  sort_order: number
  archived: boolean
  in_use_count: number
}

export interface Expense {
  id: number
  amount_cop: number
  category_id: number
  category_name: string
  payment_method_id: number
  payment_method_name: string
  spent_on: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface DaySummary {
  date: string
  total_cop: number
  expense_count: number
  items: Expense[]
}

export interface MonthSummary {
  month: string
  total_cop: number
  expense_count: number
  is_empty: boolean
  by_category: { category_id: number; name: string; amount_cop: number; percent: number }[]
  by_payment_method: { payment_method_id: number; name: string; amount_cop: number }[]
}

export interface JournalEntry {
  id: number
  text: string
  written_at: string
  created_at: string
  updated_at: string
}

export interface JournalPage {
  items: JournalEntry[]
  next_before: string | null
}

export type ResolvedBy = 'rules' | 'llm' | 'none'

export interface ExpenseDraft {
  amount_cop: number | null
  category_id: number | null
  category_name: string | null
  payment_method_id: number | null
  payment_method_name: string | null
  description: string
  description_truncated: boolean
  resolved_by: { amount: ResolvedBy; category: ResolvedBy; payment_method: ResolvedBy }
}

export interface Transcription {
  transcript: string
  audio_ms: number
  elapsed_ms: number
  draft: ExpenseDraft | null
}

export interface CategorySuggestion {
  category_id: number | null
  category_name: string | null
  source: ResolvedBy
}

export interface InsightFacts {
  period_label: string
  period_start: string
  period_end: string
  period_assumed: boolean
  domain: 'finances' | 'journal' | 'both'
  total_cop: number | null
  expense_count: number | null
  by_category: { name: string; amount_cop: number; percent: number }[] | null
  journal_entries_considered: number | null
  journal_entries_used: number | null
  journal_truncated: boolean
}

export type JobStatus = 'queued' | 'running' | 'done' | 'failed' | 'cancelled'

export interface InsightJob {
  job_id: string
  status: JobStatus
  question: string
  /** the ONLY progress signal on the wire; no completion fraction exists (KD-11) */
  elapsed_ms: number
  /** null until `status === 'done'` — NumericGuard has not run before that */
  answer: string | null
  facts: InsightFacts | null
  error_code: ErrorCode | null
  created_at: string
  finished_at: string | null
}

export interface JobAccepted {
  job_id: string
  status: 'queued'
  created_at: string
}

export type LatestSummary =
  | {
      status: 'ready'
      period_kind: 'month'
      period_key: string
      period_label: string
      text: string
      generated_at: string
      model: string
      facts: InsightFacts
    }
  | { status: 'generating'; period_key: string; period_label: string; started_at: string }
  | { status: 'empty'; period_key: string; period_label: string }
  | { status: 'none' }
  | { status: 'failed'; period_key: string; error_code: ErrorCode }
