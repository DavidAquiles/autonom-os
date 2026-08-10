import { afterEach, describe, expect, it, vi } from 'vitest'
import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, useNavigate } from 'react-router-dom'
import { App } from '../App'
import { installApi, type Route } from './server'

/**
 * B1 and B2 are the two places a regression hides, because both change
 * behaviour that works today. B1: a row used to open the editable form. B2: the
 * viewed month used to reset on leaving the screen.
 */

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

const cliente = () =>
  new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })

function mount(initial = '/finanzas', qc = cliente()) {
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[initial]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

/**
 * One browser Back tap, driven from inside the router the app is mounted in —
 * the gesture QA used to find D1, and the only one no test was making.
 */
function Atras() {
  const navigate = useNavigate()
  return (
    <button type="button" onClick={() => navigate(-1)}>
      atrás-de-prueba
    </button>
  )
}

function mountConAtras(initial = '/finanzas') {
  return render(
    <QueryClientProvider client={cliente()}>
      <MemoryRouter initialEntries={[initial]}>
        <App />
        <Atras />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const irAtras = (user: ReturnType<typeof userEvent.setup>) =>
  user.click(screen.getByRole('button', { name: 'atrás-de-prueba' }))

const expense = (over: Record<string, unknown> = {}) => ({
  id: 1,
  amount_cop: 23500,
  category_id: 1,
  category_name: 'Comida',
  payment_method_id: 1,
  payment_method_name: 'Efectivo',
  spent_on: '2026-08-05',
  description: 'Almuerzo con Ana en el italiano de la 85',
  created_at: '2026-08-05T13:05:00.000-05:00',
  updated_at: '2026-08-05T13:05:00.000-05:00',
  ...over,
})

const list = (items: unknown[], over: Record<string, unknown> = {}) => ({
  items,
  total_count: items.length,
  next_before_id: null,
  ...over,
})

const dayWithOne = {
  date: '2026-08-05',
  total_cop: 23500,
  expense_count: 1,
  items: [expense()],
}

const monthWithComida = {
  month: '2026-08',
  total_cop: 1284500,
  expense_count: 43,
  is_empty: false,
  by_category: [
    { category_id: 1, name: 'Comida', amount_cop: 298500, percent: 23 },
    { category_id: 2, name: 'Transporte', amount_cop: 187000, percent: 15 },
  ],
  by_payment_method: [{ payment_method_id: 1, name: 'Efectivo', amount_cop: 331500 }],
}

/** The detail is a reading surface: none of these may be on it (constraint 35). */
async function expectReadingSurface() {
  expect(await screen.findByText('$23.500')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /Editar gasto/ })).toBeInTheDocument()
  expect(screen.queryByLabelText('Monto')).toBeNull()
  expect(screen.queryByRole('radio')).toBeNull()
  expect(screen.queryByRole('button', { name: /Guardar/ })).toBeNull()
  expect(screen.queryByRole('button', { name: /Eliminar gasto/ })).toBeNull()
}

describe('B1 / 17.1 — tapping an expense opens the detail, not the form', () => {
  const api = (over: Record<string, Route> = {}) =>
    installApi({
      'GET /api/summary/day': dayWithOne,
      'GET /api/summary/month': monthWithComida,
      'GET /api/expenses': list([expense()]),
      'GET /api/expenses/1': expense(),
      ...over,
    })

  it('opens the read-only detail from Hoy — the surface that worked the other way', async () => {
    api()
    const user = userEvent.setup()
    mount('/finanzas')
    await user.click(await screen.findByText('Comida'))
    await expectReadingSurface()
  })

  it('opens the read-only detail from Historial (16.12)', async () => {
    api()
    const user = userEvent.setup()
    mount('/finanzas/historial')
    await user.click(await screen.findByText('Comida'))
    await expectReadingSurface()
  })

  it('opens the read-only detail from a filtered category list (18.8)', async () => {
    api()
    const user = userEvent.setup()
    mount('/finanzas/mes?categoria=1')
    await user.click(await screen.findByText('5 de agosto'))
    await expectReadingSurface()
  })
})

describe('criteria 17.2-17.6 — what the detail shows', () => {
  it('shows the amount, category, method, dated-for date and the description in full', async () => {
    installApi({ 'GET /api/expenses/1': expense() })
    mount('/finanzas/gasto/1')

    expect(await screen.findByText('$23.500')).toBeInTheDocument()
    expect(screen.getByText('Comida')).toBeInTheDocument()
    expect(screen.getByText('Efectivo')).toBeInTheDocument()
    expect(screen.getByText('miércoles 5 de agosto')).toBeInTheDocument()
    // 17.2: whole, with no truncation marker and no "seguir leyendo".
    expect(screen.getByText('Almuerzo con Ana en el italiano de la 85')).toBeInTheDocument()
    expect(screen.queryByText(/seguir leyendo/i)).toBeNull()
    // 17.4: the recorded moment, labelled, and never adjacent to the dated-for
    // date in a way that could read as a range (constraint 37).
    expect(screen.getByText('Anotado el 5 de agosto a las 13:05.')).toBeInTheDocument()
  })

  it('omits the description entirely when there is none (17.3)', async () => {
    installApi({ 'GET /api/expenses/1': expense({ description: null }) })
    mount('/finanzas/gasto/1')
    await screen.findByText('$23.500')
    expect(screen.queryByText('—')).toBeNull()
    expect(screen.queryByText('-')).toBeNull()
    expect(screen.queryByText(/sin descripción/i)).toBeNull()
  })

  it('says plainly when it has been edited since, and nothing when it has not (17.5)', async () => {
    installApi({ 'GET /api/expenses/1': expense() })
    const { unmount } = mount('/finanzas/gasto/1')
    await screen.findByText('$23.500')
    expect(screen.queryByText(/^Editado el/)).toBeNull()
    unmount()

    vi.unstubAllGlobals()
    installApi({
      'GET /api/expenses/1': expense({ updated_at: '2026-08-07T09:20:00.000-05:00' }),
    })
    mount('/finanzas/gasto/1')
    expect(await screen.findByText('Editado el 7 de agosto a las 09:20.')).toBeInTheDocument()
  })

  it('offers exactly one edit action, which opens the form pre-filled (17.6)', async () => {
    installApi({ 'GET /api/expenses/1': expense() })
    const user = userEvent.setup()
    mount('/finanzas/gasto/1')

    await user.click(await screen.findByRole('button', { name: /Editar gasto/ }))
    const amount = await screen.findByLabelText('Monto')
    expect((amount as HTMLInputElement).value).toBe('23.500')
    expect(screen.getByRole('button', { name: 'Guardar cambios' })).toBeInTheDocument()
  })

  it('says so in plain Spanish when the expense does not exist (17.11)', async () => {
    installApi({
      'GET /api/expenses/1': undefined, // the stub answers 404 with the envelope
    })
    mount('/finanzas/gasto/1')
    expect(await screen.findByText('Este gasto ya no existe.')).toBeInTheDocument()
    expect(screen.queryByText(/not_found/)).toBeNull()
  })
})

describe('criterion 17.7 — leaving the edit form returns to the detail', () => {
  it('pops back to the detail after saving, showing the stored values', async () => {
    installApi({
      'GET /api/summary/day': dayWithOne,
      'GET /api/expenses': list([expense()]),
      'GET /api/expenses/1': expense(),
      'PATCH /api/expenses/1': expense(),
    })
    const user = userEvent.setup()
    mount('/finanzas')

    await user.click(await screen.findByText('Comida'))
    await user.click(await screen.findByRole('button', { name: /Editar gasto/ }))
    await screen.findByLabelText('Monto')
    await user.click(screen.getByRole('button', { name: 'Guardar cambios' }))

    // Back on the detail — not on Hoy, and not on a second copy of the detail.
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /Editar gasto/ })).toBeInTheDocument(),
    )
    expect(screen.queryByLabelText('Monto')).toBeNull()
  })
})

/**
 * QA D1, in two halves that were fixed separately because they fail separately.
 * The whole path passed 70 tests and 132 screenshots while broken: every test
 * stopped at the moment the delete landed on the list, which is exactly where
 * criterion 17.9 stops too.
 */
describe('QA D1 — a deleted expense is gone, not one Back tap away', () => {
  const vacio = { date: '2026-08-05', total_cop: 0, expense_count: 0, items: [] }

  it('leaves the stack at [lista]: Back after deleting does not reach the dead detail (D1a)', async () => {
    let vive = true
    installApi({
      'GET /api/summary/day': () => (vive ? dayWithOne : vacio),
      'GET /api/expenses': () => list(vive ? [expense()] : []),
      // What the server answers for a deleted id — QA confirmed the 404 by curl.
      'GET /api/expenses/1': () => (vive ? expense() : undefined),
      'DELETE /api/expenses/1': null,
    })
    const user = userEvent.setup()
    mountConAtras('/finanzas')

    // [lista] → [lista, detalle] → [lista, detalle, editar]
    await user.click(await screen.findByText('Comida'))
    await user.click(await screen.findByRole('button', { name: /Editar gasto/ }))
    await screen.findByLabelText('Monto')
    await user.click(screen.getByRole('button', { name: /Eliminar gasto/ }))
    vive = false
    await user.click(await screen.findByRole('button', { name: 'Eliminar' }))

    // 17.9: on the list it was opened from.
    await waitFor(() =>
      expect(screen.getByText('Todavía no has anotado nada hoy.')).toBeInTheDocument(),
    )

    await irAtras(user)

    // The design's push/pop table: after deleting, the stack is [lista], so
    // there is nothing behind it to walk back into.
    expect(screen.queryByText('Este gasto ya no existe.')).toBeNull()
    expect(screen.queryByText('$23.500')).toBeNull()
    expect(screen.queryByRole('button', { name: /Editar gasto/ })).toBeNull()
    expect(screen.getByText('Todavía no has anotado nada hoy.')).toBeInTheDocument()
  })

  it('replaces the record with the not-found state instead of rendering it underneath (D1b)', async () => {
    let vive = true
    installApi({ 'GET /api/expenses/1': () => (vive ? expense() : undefined) })
    const qc = cliente()
    mount('/finanzas/gasto/1', qc)

    await screen.findByText('$23.500')

    // The expense goes while its detail is on screen and its data is cached —
    // TanStack keeps the last good `data` when the refetch fails, which is what
    // put the whole record under "Este gasto ya no existe."
    vive = false
    await act(async () => {
      await qc.invalidateQueries({ queryKey: ['expense'] })
    })

    expect(await screen.findByText('Este gasto ya no existe.')).toBeInTheDocument()
    expect(screen.queryByText('$23.500')).toBeNull()
    expect(screen.queryByText('Efectivo')).toBeNull()
    expect(screen.queryByText('Almuerzo con Ana en el italiano de la 85')).toBeNull()
    expect(screen.queryByText(/^Anotado el/)).toBeNull()
    // The affordance that made this reachable: it opened the form pre-filled
    // with a dead record, and saving blamed a server that was answering.
    expect(screen.queryByRole('button', { name: /Editar gasto/ })).toBeNull()
  })
})

describe('B2 / 18.9 — the month and the category live in the location', () => {
  it('renders the month named in the URL, not the current one', async () => {
    const { calls } = installApi({
      'GET /api/summary/month': { ...monthWithComida, month: '2026-07' },
    })
    mount('/finanzas/mes?mes=2026-07')

    expect(await screen.findByText('julio 2026')).toBeInTheDocument()
    // Read from the location, not from state: the month reached the request.
    expect(calls.some((c) => c.path === '/api/summary/month?month=2026-07')).toBe(true)
  })

  it('comes back to the same month and the same category after a detail round trip', async () => {
    installApi({
      'GET /api/summary/month': monthWithComida,
      'GET /api/expenses': list([expense()]),
      'GET /api/expenses/1': expense(),
    })
    const user = userEvent.setup()
    mount('/finanzas/mes?categoria=1')

    // The opened band: name, the category's own total, its count (18.3), with
    // the month's own total still on screen (18.4).
    expect(await screen.findByText('Comida')).toBeInTheDocument()
    expect(await screen.findByText('$298.500')).toBeInTheDocument()
    expect(screen.getByText('1 gasto')).toBeInTheDocument()
    expect(screen.getByText('$1.284.500')).toBeInTheDocument()

    await user.click(await screen.findByText('5 de agosto'))
    await screen.findByRole('button', { name: /Editar gasto/ })

    await user.click(screen.getByRole('button', { name: 'Cerrar' }))

    // Same month, same category still open — not a reset view of the current
    // month with the full breakdown back.
    await waitFor(() => expect(screen.getByText('agosto 2026')).toBeInTheDocument())
    expect(screen.getByText('$298.500')).toBeInTheDocument()
    expect(screen.queryByText('En qué se fue')).toBeNull()
  })

  it('drops the selection when the month changes (18.7)', async () => {
    installApi({
      'GET /api/summary/month': ({ path }: { path: string }) =>
        path.includes('month=2026-07')
          ? { ...monthWithComida, month: '2026-07' }
          : monthWithComida,
      'GET /api/expenses': list([expense()]),
    })
    const user = userEvent.setup()
    mount('/finanzas/mes?categoria=1')

    await screen.findByText('$298.500')
    await user.click(screen.getByRole('button', { name: 'Mes anterior' }))

    // The new month's full breakdown, so no month's heading can sit over
    // another month's expenses.
    await waitFor(() => expect(screen.getByText('julio 2026')).toBeInTheDocument())
    expect(screen.getByText('En qué se fue')).toBeInTheDocument()
  })
})

describe('requirement 18 — one category at a time', () => {
  it('selects any category in one interaction and replaces the previous one (18.1, 18.6)', async () => {
    const { calls } = installApi({
      'GET /api/summary/month': monthWithComida,
      'GET /api/expenses': list([expense()]),
    })
    const user = userEvent.setup()
    mount('/finanzas/mes')

    await user.click(await screen.findByRole('button', { name: /Comida/ }))
    await screen.findByRole('button', { name: 'Cerrar' })

    await user.click(screen.getByRole('button', { name: 'Cerrar' }))
    await user.click(await screen.findByRole('button', { name: /Transporte/ }))

    await waitFor(() => {
      const asked = calls.filter((c) => c.path.startsWith('/api/expenses?'))
      expect(asked.some((c) => c.path.includes('category_id=2'))).toBe(true)
    })
    // One selection at a time: never two category filters in one request.
    for (const c of calls.filter((c) => c.path.startsWith('/api/expenses?')))
      expect(c.path.match(/category_id=/g)!.length).toBe(1)
  })

  it('clears the selection from the on-screen control (18.5)', async () => {
    installApi({
      'GET /api/summary/month': monthWithComida,
      'GET /api/expenses': list([expense()]),
    })
    const user = userEvent.setup()
    mount('/finanzas/mes?categoria=1')

    await user.click(await screen.findByRole('button', { name: 'Cerrar' }))
    expect(await screen.findByText('En qué se fue')).toBeInTheDocument()
    expect(screen.getByText('Cómo se pagó')).toBeInTheDocument()
  })

  it('says there is nothing left rather than showing a zero row (18.10)', async () => {
    installApi({
      'GET /api/summary/month': monthWithComida,
      'GET /api/expenses': list([]),
    })
    mount('/finanzas/mes?categoria=1')

    expect(await screen.findByText('En agosto ya no queda nada en Comida.')).toBeInTheDocument()
    // OQ3, ruled at the gate: no total and no count in the band, because a
    // zero row is what 18.10 names as the thing to avoid.
    expect(screen.queryByText('$0')).toBeNull()
    expect(screen.queryByText('0 gastos')).toBeNull()
  })

  /**
   * QA D2. The empty-category branch caught every failure of this request, so a
   * screen that could not load the list told the user the category had been
   * emptied — while the month's own total, from a request that DID succeed,
   * still sat above it. The test above ("says there is nothing left…") is the
   * other half: the true claim must survive this fix.
   */
  it('says the list did not load rather than claiming the category is empty (D2)', async () => {
    installApi({
      'GET /api/summary/month': monthWithComida,
      // The 400 the server really answers for a malformed `category_id` — the
      // cheapest trigger, and the same branch as a 500 or a dropped request.
      'GET /api/expenses': () =>
        new Response(
          JSON.stringify({ error: { code: 'validation', message: 'category_id' } }),
          { status: 400, headers: { 'Content-Type': 'application/json' } },
        ),
    })
    mount('/finanzas/mes?categoria=1')

    expect(await screen.findByText('No pude cargar esta lista.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeInTheDocument()
    expect(screen.queryByText('En agosto ya no queda nada en Comida.')).toBeNull()
    expect(screen.queryByText(/Puede que lo hayas borrado/)).toBeNull()
    // The figure the false claim used to contradict is still on screen.
    expect(screen.getByText('$1.284.500')).toBeInTheDocument()
  })

  it('offers no selection at all in an empty month (18.11)', async () => {
    installApi({
      'GET /api/summary/month': {
        month: '2026-02',
        total_cop: 0,
        expense_count: 0,
        is_empty: true,
        by_category: [],
        by_payment_method: [],
      },
    })
    mount('/finanzas/mes?mes=2026-02')

    await screen.findByText('En febrero no hay gastos anotados.')
    expect(screen.queryByText('En qué se fue')).toBeNull()
    expect(screen.queryByRole('button', { name: 'Cerrar' })).toBeNull()
  })
})
