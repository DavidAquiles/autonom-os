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

function mount(initial: string | object = '/finanzas') {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[initial as string]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('criterion 2.8 — a complete expense in four interactions', () => {
  it('saves in exactly four taps beyond typing the amount', async () => {
    const { calls } = installApi()
    const user = userEvent.setup()
    mount()

    await screen.findByText('Anotar gasto')
    let taps = 0

    // 1 — open the manual form
    await user.click(screen.getByText('Anotar gasto'))
    taps++

    // typing the amount is explicitly not counted by 2.8
    const amount = await screen.findByLabelText('Monto')
    await user.type(amount, '14000')
    expect((amount as HTMLInputElement).value).toBe('14.000')

    // 2 — the category, a single tap on a chip already on screen
    await user.click(await screen.findByRole('radio', { name: 'Transporte' }))
    taps++

    // 3 — the payment method, likewise
    await user.click(screen.getByRole('radio', { name: 'Tarjeta de crédito' }))
    taps++

    // 4 — save
    await user.click(screen.getByRole('button', { name: 'Guardar gasto' }))
    taps++

    expect(taps).toBe(4)

    await waitFor(() => {
      const post = calls.find((c) => c.method === 'POST' && c.path === '/api/expenses')
      expect(post).toBeDefined()
      expect(post!.body).toMatchObject({
        amount_cop: 14000,
        category_id: 2,
        payment_method_id: 2,
      })
    })
  })

  it('offers every category and every payment method as a one-tap chip', async () => {
    installApi()
    mount('/finanzas/gasto/nuevo')
    const chips = await screen.findAllByRole('radio')
    // Ten categories and six payment methods, no <select> and no picker: a
    // native select or a bottom sheet is two interactions and blows the budget.
    expect(chips).toHaveLength(16)
    expect(document.querySelectorAll('select')).toHaveLength(0)
  })
})

describe('criteria 2.2 and 2.3 — validation names the offending field', () => {
  it('rejects an empty amount and both missing choices, all at once', async () => {
    const { calls } = installApi()
    const user = userEvent.setup()
    mount('/finanzas/gasto/nuevo')

    await user.click(await screen.findByRole('button', { name: 'Guardar gasto' }))

    expect(await screen.findByText('Escribe un monto mayor que cero.')).toBeInTheDocument()
    expect(screen.getByText('Elige una categoría.')).toBeInTheDocument()
    expect(screen.getByText('Elige un método de pago.')).toBeInTheDocument()
    // Nothing was sent: the rejection is client-side pre-flight.
    expect(calls.some((c) => c.method === 'POST')).toBe(false)
  })
})

describe('criterion 9.2 — an undetermined field is empty AND marked', () => {
  /**
   * The review screen is reached by navigation state, exactly as VoiceContext
   * hands it over. `resolved_by` is the only signal read: a field is marked
   * because the contract says "none", never because it looks empty.
   */
  const review = (draft: Record<string, unknown>, transcript: string) => ({
    pathname: '/finanzas/gasto/nuevo',
    state: {
      voice: {
        transcript,
        draft: {
          amount_cop: null,
          category_id: null,
          category_name: null,
          payment_method_id: null,
          payment_method_name: null,
          description: transcript,
          description_truncated: false,
          resolved_by: { amount: 'rules', category: 'rules', payment_method: 'rules' },
          ...draft,
        },
      },
    },
  })

  it('marks the amount, leaving it empty — "compré algo"', async () => {
    installApi({
      'POST /api/expenses/suggest-category': { category_id: null, category_name: null, source: 'none' },
    })
    mount(
      review(
        {
          category_id: 10,
          category_name: 'Otros',
          payment_method_id: 1,
          payment_method_name: 'Efectivo',
          resolved_by: { amount: 'none', category: 'llm', payment_method: 'rules' },
        },
        'compré algo',
      ),
    )

    const monto = (await screen.findByLabelText('Monto')) as HTMLInputElement
    expect(monto.value).toBe('')
    expect(screen.getByText('Falta escribirlo')).toBeInTheDocument()
    // The mark is the field's description, not a loose label beside it.
    expect(monto.getAttribute('aria-describedby')).toBe(
      screen.getByText('Falta escribirlo').getAttribute('id'),
    )
    // No "0" that could be read as an amount the system decided on.
    expect(monto.getAttribute('placeholder')).toBe('')
    // A field the assist filled is a suggestion, not a hole.
    expect(screen.getByText('sugerido')).toBeInTheDocument()
    expect(screen.queryByText('Falta elegirla')).not.toBeInTheDocument()
  })

  it('marks the category, leaving it empty — "gasté cinco mil, no sé en qué"', async () => {
    installApi({
      'POST /api/expenses/suggest-category': { category_id: null, category_name: null, source: 'none' },
    })
    mount(
      review(
        {
          amount_cop: 5000,
          payment_method_id: 1,
          payment_method_name: 'Efectivo',
          resolved_by: { amount: 'rules', category: 'none', payment_method: 'rules' },
        },
        'gasté cinco mil, no sé en qué',
      ),
    )

    await screen.findByRole('radio', { name: 'Comida' }) // the chips have loaded
    const grupo = screen.getByRole('radiogroup', { name: 'Categoría' })
    expect(grupo.querySelectorAll('[aria-checked="true"]')).toHaveLength(0)
    const tag = await screen.findByText('Falta elegirla')
    expect(grupo.getAttribute('aria-describedby')).toBe(tag.getAttribute('id'))
    expect(screen.queryByText('sugerido')).not.toBeInTheDocument()
  })

  it('marks the payment method, and clears the mark once it is chosen', async () => {
    installApi()
    const user = userEvent.setup()
    mount(
      review(
        {
          amount_cop: 14000,
          category_id: 2,
          category_name: 'Transporte',
          resolved_by: { amount: 'rules', category: 'rules', payment_method: 'none' },
        },
        'gasté catorce mil en un Uber',
      ),
    )

    const tag = await screen.findByText('Falta elegirlo')
    const grupo = screen.getByRole('radiogroup', { name: 'Método de pago' })
    expect(grupo.getAttribute('aria-describedby')).toBe(tag.getAttribute('id'))

    await user.click(await screen.findByRole('radio', { name: 'Efectivo' }))
    await waitFor(() => expect(screen.queryByText('Falta elegirlo')).not.toBeInTheDocument())
  })

  it('marks all three when nothing at all could be determined', async () => {
    installApi({
      'POST /api/expenses/suggest-category': { category_id: null, category_name: null, source: 'none' },
    })
    mount(
      review(
        { resolved_by: { amount: 'none', category: 'none', payment_method: 'none' } },
        'no sé qué pasó',
      ),
    )

    expect(await screen.findByText('Falta escribirlo')).toBeInTheDocument()
    expect(screen.getByText('Falta elegirla')).toBeInTheDocument()
    expect(screen.getByText('Falta elegirlo')).toBeInTheDocument()
  })

  it('marks nothing on a manually opened form', async () => {
    installApi()
    mount('/finanzas/gasto/nuevo')
    await screen.findByLabelText('Monto')
    expect(screen.queryByText('Falta escribirlo')).not.toBeInTheDocument()
    expect(screen.queryByText('Falta elegirla')).not.toBeInTheDocument()
    expect(screen.queryByText('Falta elegirlo')).not.toBeInTheDocument()
  })
})

describe('criterion 1.3 and KD-16 — Gimnasio is inert', () => {
  it('has no capture control and makes no request of its own', async () => {
    const { calls } = installApi()
    mount('/gimnasio')

    await screen.findByText('Todavía no está disponible.')
    expect(screen.queryByText('Anotar gasto')).not.toBeInTheDocument()
    expect(screen.queryByText('Escribir')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Grabar con la voz')).not.toBeInTheDocument()
    expect(calls.some((c) => c.path.includes('gym') || c.path.includes('gimnasio'))).toBe(false)

    // Constraint 11: the three destinations are still there.
    const bottom = screen.getByRole('navigation', { name: 'Secciones' })
    expect(bottom.textContent).toContain('Finanzas')
    expect(bottom.textContent).toContain('Diario')
    expect(bottom.textContent).toContain('Gimnasio')
  })
})

describe('criterion 1.1 — exactly three top-level destinations', () => {
  it('never shows a fourth, and Análisis is a tab inside Finanzas', async () => {
    installApi()
    mount('/finanzas')
    const bottom = await screen.findByRole('navigation', { name: 'Secciones' })
    expect(bottom.querySelectorAll('a')).toHaveLength(3)
    expect(bottom.textContent).not.toMatch(/Análisis/)
  })
})

describe('criterion 13.2 — a cold open with no server', () => {
  it('renders the Spanish "cannot reach your server" screen, not a blank', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new TypeError('Failed to fetch')
      }),
    )
    mount()
    expect(
      await screen.findByText('No puedo alcanzar tu servidor.', {}, { timeout: 5000 }),
    ).toBeInTheDocument()
    // Constraint 11 holds even here.
    expect(screen.getByRole('navigation', { name: 'Secciones' })).toBeInTheDocument()
  })
})
