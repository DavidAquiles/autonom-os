import { afterEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { App } from '../App'
import { installApi } from './server'

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

function mount(initial = '/finanzas/historial') {
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

/**
 * Registration order, so the dated-for dates deliberately do NOT descend — that
 * is the whole reason 16.6 exists. id 9 is dated 28 July and sits above id 8,
 * dated 3 August.
 */
const ROWS = [
  { id: 11, amount_cop: 18000, cat: 'Transporte', pm: 'Tarjeta de crédito', on: '2026-08-05' },
  { id: 10, amount_cop: 150000, cat: 'Mercado', pm: 'Tarjeta débito', on: '2026-08-02' },
  { id: 9, amount_cop: 340000, cat: 'Hogar', pm: 'Tarjeta de crédito', on: '2026-07-28' },
  { id: 8, amount_cop: 7500, cat: 'Comida', pm: 'Efectivo', on: '2026-08-03' },
]

const row = (r: (typeof ROWS)[number]) => ({
  id: r.id,
  amount_cop: r.amount_cop,
  category_id: 1,
  category_name: r.cat,
  payment_method_id: 1,
  payment_method_name: r.pm,
  spent_on: r.on,
  description: null,
  created_at: '2026-08-05T19:41:00.000-05:00',
  updated_at: '2026-08-05T19:41:00.000-05:00',
})

describe('criteria 16.1, 16.2, 16.5, 16.6 — Historial is reachable and says what order it is in', () => {
  it('is a fourth Finanzas tab, reachable from another tab in one interaction', async () => {
    installApi({ 'GET /api/expenses': { items: [], total_count: 0, next_before_id: null } })
    const user = userEvent.setup()
    mount('/finanzas')

    await user.click(await screen.findByRole('link', { name: 'Historial' }))
    expect(await screen.findByText('Todavía no has anotado ningún gasto.')).toBeInTheDocument()
  })

  it('states its order on screen, above the first row', async () => {
    installApi({
      'GET /api/expenses': { items: ROWS.map(row), total_count: 4, next_before_id: null },
    })
    mount()

    const orden = await screen.findByText('En el orden en que los anotaste, no por su fecha.')
    const first = screen.getByText('Transporte')
    // Read before the first row: DOCUMENT_POSITION_FOLLOWING.
    expect(orden.compareDocumentPosition(first) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  })

  it('asks the server for registration order, and shows amount, category, method and dated-for date', async () => {
    const { calls } = installApi({
      'GET /api/expenses': { items: ROWS.map(row), total_count: 4, next_before_id: null },
    })
    mount()

    await screen.findByText('Transporte')
    expect(calls.some((c) => c.path.includes('order=registered'))).toBe(true)
    // 16.5, on one row: all four facts.
    expect(screen.getByText('$18.000')).toBeInTheDocument()
    expect(screen.getByText('5 de agosto · Tarjeta de crédito')).toBeInTheDocument()
    // 16.2 / R6: the dates are not descending, and that is correct.
    expect(screen.getByText('28 de julio · Tarjeta de crédito')).toBeInTheDocument()
  })

  it('is flat: no date heading, day separator or month band (constraint 33)', async () => {
    installApi({
      'GET /api/expenses': { items: ROWS.map(row), total_count: 4, next_before_id: null },
    })
    mount()

    await screen.findByText('Transporte')
    // A27: each row carries its own date; nothing groups them.
    expect(screen.queryByRole('heading')).toBeNull()
    expect(screen.queryByText('agosto 2026')).toBeNull()
    expect(screen.queryByText('julio 2026')).toBeNull()
  })

  it('carries no search, filter or sort control (constraint 34, A36)', async () => {
    installApi({
      'GET /api/expenses': { items: ROWS.map(row), total_count: 4, next_before_id: null },
    })
    mount()

    await screen.findByText('Transporte')
    expect(screen.queryByRole('textbox')).toBeNull()
    expect(screen.queryByRole('combobox')).toBeNull()
    expect(screen.queryByRole('radio')).toBeNull()
  })
})

describe('criteria 16.7, 16.8, 16.9, 16.13 — showing more without losing what is on screen', () => {
  it('offers no control at all when everything is already shown (16.9)', async () => {
    installApi({
      'GET /api/expenses': { items: ROWS.map(row), total_count: 4, next_before_id: null },
    })
    mount()

    await screen.findByText('Transporte')
    expect(screen.queryByRole('button', { name: /más antiguos/ })).toBeNull()
    expect(screen.queryByText(/Cargando/)).toBeNull()
  })

  it('appends older records with the keyset cursor, keeping what is on screen (16.7, 16.8)', async () => {
    const older = {
      id: 3,
      amount_cop: 54000,
      category_id: 1,
      category_name: 'Ropa',
      payment_method_id: 1,
      payment_method_name: 'Tarjeta de crédito',
      spent_on: '2026-07-26',
      description: null,
      created_at: '2026-07-26T10:00:00.000-05:00',
      updated_at: '2026-07-26T10:00:00.000-05:00',
    }
    const { calls } = installApi({
      // KD-20: the answer depends on the cursor, which is exactly what makes
      // paging terminate at the first expense ever recorded (16.8).
      'GET /api/expenses': ({ path }: { path: string }) =>
        path.includes('before_id=8')
          ? { items: [older], total_count: 5, next_before_id: null }
          : { items: ROWS.map(row), total_count: 5, next_before_id: 8 },
    })
    const user = userEvent.setup()
    mount()

    await screen.findByText('Transporte')
    // 16.13: the first screenful only — the page size, not every expense.
    expect(calls.some((c) => c.path.includes('limit=30'))).toBe(true)

    await user.click(screen.getByRole('button', { name: 'Ver gastos más antiguos' }))

    // Appended, with the earlier rows still on screen and still in order.
    expect(await screen.findByText('Ropa')).toBeInTheDocument()
    expect(screen.getByText('Transporte')).toBeInTheDocument()
    const rows = screen
      .getAllByRole('link')
      .filter((a) => /^\/finanzas\/gasto\/\d+$/.test(a.getAttribute('href') ?? ''))
      .map((a) => a.textContent)
    expect(rows[0]).toContain('Transporte')
    expect(rows[rows.length - 1]).toContain('Ropa')

    // The cursor came from `next_before_id`, not from an offset.
    expect(calls.some((c) => c.path.includes('before_id=8'))).toBe(true)
    expect(calls.every((c) => !c.path.includes('offset='))).toBe(true)

    // 16.9 again, now that the last page has arrived.
    await waitFor(() =>
      expect(screen.queryByRole('button', { name: /más antiguos/ })).toBeNull(),
    )
  })

})

describe('criteria 16.11, 17.9 — a deleted expense leaves Historial entirely', () => {
  it('removes it with no gap or placeholder, and does not land on its dead detail', async () => {
    // KD-25's consequence, made visible: without `['expense-list']` in
    // `invalidateExpenseViews` the deleted row would sit here until a manual
    // refresh, and every other test would still be green.
    let alive = ROWS.map(row)
    installApi({
      'GET /api/expenses': () => ({
        items: alive,
        total_count: alive.length,
        next_before_id: null,
      }),
      'GET /api/expenses/11': row(ROWS[0]),
      'DELETE /api/expenses/11': null,
    })
    const user = userEvent.setup()
    mount()

    await user.click(await screen.findByText('Transporte'))
    await user.click(await screen.findByRole('button', { name: /Editar gasto/ }))
    await screen.findByLabelText('Monto')
    await user.click(screen.getByRole('button', { name: /Eliminar gasto/ }))

    alive = alive.filter((e) => e.id !== 11)
    await user.click(await screen.findByRole('button', { name: 'Eliminar' }))

    // 17.9: back on the list it was opened from, never on the detail of a
    // record that no longer exists.
    await waitFor(() =>
      expect(screen.getByText('En el orden en que los anotaste, no por su fecha.')).toBeInTheDocument(),
    )
    // 16.11 / A29: gone, with no tombstone left behind.
    await waitFor(() => expect(screen.queryByText('Transporte')).toBeNull())
    expect(screen.getByText('Mercado')).toBeInTheDocument()
    expect(screen.queryByText(/eliminado/i)).toBeNull()
  })
})

describe('criterion 16.10 — nothing has ever been recorded', () => {
  it('shows a designed state, not a blank screen or an empty frame', async () => {
    installApi({ 'GET /api/expenses': { items: [], total_count: 0, next_before_id: null } })
    mount()

    expect(await screen.findByText('Todavía no has anotado ningún gasto.')).toBeInTheDocument()
    expect(
      screen.getByText('Cuando anotes el primero, aquí van quedando todos, del último al primero.'),
    ).toBeInTheDocument()
    // No order statement: there is no order to explain yet.
    expect(screen.queryByText(/En el orden en que los anotaste/)).toBeNull()
  })
})
