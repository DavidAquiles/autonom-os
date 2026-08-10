import { afterEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
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

function mount(initial = '/finanzas') {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[initial]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

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
