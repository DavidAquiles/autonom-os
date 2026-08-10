import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
  type QueryClient,
} from '@tanstack/react-query'
import { api, qs } from './client'
import { rememberOrigins } from '../state/origin'
import type {
  CategorySuggestion,
  DaySummary,
  Expense,
  ExpenseList,
  Health,
  InsightJob,
  JobAccepted,
  JournalEntry,
  JournalPage,
  LatestSummary,
  MonthSummary,
  NamedItem,
  Status,
} from './types'

export const keys = {
  health: ['health'] as const,
  status: ['status'] as const,
  categories: ['categories'] as const,
  paymentMethods: ['payment-methods'] as const,
  day: (date?: string) => ['summary', 'day', date ?? 'hoy'] as const,
  month: (month?: string) => ['summary', 'month', month ?? 'actual'] as const,
  expense: (id: number) => ['expense', id] as const,
  // KD-25: the prefix is `expense-list`, NOT `expenses`. TanStack matches keys
  // by prefix element-by-element, so `['expenses', …]` would differ from the
  // existing `['expense', id]` by one character and match nothing it does not
  // intend to — correct, and exactly why it is dangerous to read. A visibly
  // different prefix removes the near-miss; both entries live in
  // `invalidateExpenseViews` and neither implies the other.
  expenseList: (...scope: (string | number | null)[]) => ['expense-list', ...scope] as const,
  journal: (date?: string) => ['journal', date ?? 'todo'] as const,
  journalEntry: (id: number) => ['journal', 'entry', id] as const,
  summaryLatest: ['insights', 'summary', 'latest'] as const,
  job: (id: string) => ['insights', 'job', id] as const,
}

/**
 * Anything that changes an expense invalidates the day total, the month total
 * and the breakdown — 4.6 ("without a manual refresh") is exactly this.
 */
function invalidateExpenseViews(qc: QueryClient) {
  qc.invalidateQueries({ queryKey: ['summary'] })
  qc.invalidateQueries({ queryKey: ['expense'] })
  // KD-25: `['expense']` does NOT match `['expense-list', …]`. Without this line
  // a deleted expense lingers in Historial (16.11) and a category's list never
  // goes empty (18.10) until a manual refresh.
  qc.invalidateQueries({ queryKey: ['expense-list'] })
}

/* ------------------------------------------------------------ reachability */

export function useHealth() {
  return useQuery({
    queryKey: keys.health,
    // KD-2 mechanism 1: the other origin is learned WHILE the server answers,
    // and stored by whatever origin is being served. Unconditional, on every
    // success, so a changed LAN address self-heals on the next load.
    queryFn: async () => {
      const health = await api.get<Health>('/health')
      rememberOrigins(health.origins)
      return health
    },
    refetchInterval: 20_000,
    refetchOnWindowFocus: true,
    retry: 1,
    staleTime: 5_000,
  })
}

export function useServerStatus() {
  return useQuery({
    queryKey: keys.status,
    queryFn: () => api.get<Status>('/status'),
    refetchInterval: 60_000,
    retry: 1,
  })
}

/* ---------------------------------------------------- categories / methods */

export function useCategories() {
  return useQuery({
    queryKey: keys.categories,
    queryFn: () => api.get<{ items: NamedItem[] }>('/categories'),
    select: (d) => d.items,
    staleTime: 60_000,
  })
}

export function usePaymentMethods() {
  return useQuery({
    queryKey: keys.paymentMethods,
    queryFn: () => api.get<{ items: NamedItem[] }>('/payment-methods'),
    select: (d) => d.items,
    staleTime: 60_000,
  })
}

export type NamedKind = 'categories' | 'payment-methods'

export function useCreateNamed(kind: NamedKind) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => api.post<NamedItem>(`/${kind}`, { name }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [kind === 'categories' ? 'categories' : 'payment-methods'] })
    },
  })
}

export function useRenameNamed(kind: NamedKind) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) =>
      api.patch<NamedItem>(`/${kind}/${id}`, { name }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [kind === 'categories' ? 'categories' : 'payment-methods'] })
      // 3.3: existing expenses hold the id, so the new name has to reappear on
      // every view that renders one.
      invalidateExpenseViews(qc)
    },
  })
}

export function useRemoveNamed(kind: NamedKind) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, confirm }: { id: number; confirm: boolean }) =>
      api.del<{ archived: true; affected_expenses: number }>(`/${kind}/${id}${qs({ confirm })}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [kind === 'categories' ? 'categories' : 'payment-methods'] })
      invalidateExpenseViews(qc)
    },
  })
}

/* ------------------------------------------------------------- expenses */

export function useDaySummary(date?: string) {
  return useQuery({
    queryKey: keys.day(date),
    queryFn: () => api.get<DaySummary>(`/summary/day${qs({ date })}`),
  })
}

export function useMonthSummary(month?: string) {
  return useQuery({
    queryKey: keys.month(month),
    queryFn: () => api.get<MonthSummary>(`/summary/month${qs({ month })}`),
  })
}

export function useExpense(id: number | null) {
  return useQuery({
    queryKey: keys.expense(id ?? -1),
    queryFn: () => api.get<Expense>(`/expenses/${id}`),
    enabled: id !== null,
  })
}

/** Deferred 1: 30 rows is roughly three screenfuls at 390×844 (16.13). */
export const HISTORIAL_PAGE = 30

/**
 * Historial (16.2, 16.7-16.9). KD-20: keyset paging on `before_id`, never
 * offset — an expense captured or deleted mid-scroll would make offset paging
 * repeat or skip a row. KD-25: the pages live in the query cache, so returning
 * from an expense's detail re-renders the list at full length instead of
 * collapsing to page one (17.8).
 */
export function useHistorial() {
  return useInfiniteQuery({
    queryKey: keys.expenseList('registrados'),
    queryFn: ({ pageParam }) =>
      api.get<ExpenseList>(
        `/expenses${qs({
          order: 'registered',
          limit: HISTORIAL_PAGE,
          before_id: pageParam ?? undefined,
        })}`,
      ),
    initialPageParam: null as number | null,
    // `next_before_id === null` is the contract's "everything is shown", so
    // `hasNextPage` is exactly 16.9's condition with no extra state.
    getNextPageParam: (last) => last.next_before_id,
  })
}

/**
 * One category inside one month (18.2, 18.13). Ordered by the date each expense
 * is dated for — deliberately not Historial's order (A37, R6). KD-21: not
 * paged; `total_count` is what 18.3 counts, and it ignores `limit` (R4).
 */
export function useCategoryExpenses(month: string | undefined, categoryId: number | null) {
  return useQuery({
    queryKey: keys.expenseList('mes', month ?? 'actual', categoryId),
    queryFn: () =>
      api.get<ExpenseList>(`/expenses${qs({ month, category_id: categoryId ?? undefined })}`),
    enabled: month !== undefined && categoryId !== null,
  })
}

export interface ExpenseInput {
  amount_cop: number
  category_id: number
  payment_method_id: number
  spent_on?: string
  description?: string | null
  source?: 'manual' | 'voice'
}

export function useCreateExpense() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (input: ExpenseInput) => api.post<Expense>('/expenses', input),
    onSuccess: () => invalidateExpenseViews(qc),
  })
}

export function useUpdateExpense() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: Partial<ExpenseInput> }) =>
      api.patch<Expense>(`/expenses/${id}`, patch),
    onSuccess: () => invalidateExpenseViews(qc),
  })
}

export function useDeleteExpense() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.del<void>(`/expenses/${id}`),
    onSuccess: () => invalidateExpenseViews(qc),
  })
}

/* -------------------------------------------------------------- journal */

export function useJournal(date?: string) {
  return useQuery({
    queryKey: keys.journal(date),
    queryFn: () => api.get<JournalPage>(`/journal${qs({ date, limit: 50 })}`),
  })
}

export function useJournalEntry(id: number | null) {
  return useQuery({
    queryKey: keys.journalEntry(id ?? -1),
    queryFn: () => api.get<JournalEntry>(`/journal/${id}`),
    enabled: id !== null,
  })
}

export function useCreateJournalEntry() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (input: { text: string; source?: 'manual' | 'voice' }) =>
      api.post<JournalEntry>('/journal', input),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['journal'] }),
  })
}

export function useUpdateJournalEntry() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, text }: { id: number; text: string }) =>
      api.patch<JournalEntry>(`/journal/${id}`, { text }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['journal'] }),
  })
}

export function useDeleteJournalEntry() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.del<void>(`/journal/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['journal'] }),
  })
}

/* ------------------------------------------------------------- insights */

export function useLatestSummary() {
  return useQuery({
    queryKey: keys.summaryLatest,
    queryFn: () => api.get<LatestSummary>('/insights/summaries/latest'),
    // 11.15: this reads a stored row and never triggers generation, so it can be
    // refetched cheaply to notice a background summary finishing.
    refetchInterval: (q) =>
      (q.state.data as LatestSummary | undefined)?.status === 'generating' ? 10_000 : false,
  })
}

export function useAskQuestion() {
  return useMutation({
    mutationFn: (input: { question: string; source: 'text' | 'voice' }) =>
      api.post<JobAccepted>('/insights/questions', input),
  })
}

export function useJob(jobId: string | null) {
  return useQuery({
    queryKey: keys.job(jobId ?? ''),
    queryFn: () => api.get<InsightJob>(`/insights/questions/${jobId}`),
    enabled: jobId !== null,
    // KD-11: poll at ~1 s. `elapsed_ms` is the only progress signal there is.
    refetchInterval: (q) => {
      const s = (q.state.data as InsightJob | undefined)?.status
      return s === 'queued' || s === 'running' ? 1000 : false
    },
  })
}

export function useCancelJob() {
  return useMutation({
    mutationFn: (jobId: string) => api.del<void>(`/insights/questions/${jobId}`),
  })
}

export function useSuggestCategory() {
  return useMutation({
    mutationFn: (text: string) =>
      api.post<CategorySuggestion>('/expenses/suggest-category', { text }),
  })
}
