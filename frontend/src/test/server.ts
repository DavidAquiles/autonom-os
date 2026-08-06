import { vi } from 'vitest'

/**
 * A stub of the real API, shaped exactly like the Interface Contract. It exists
 * so component tests exercise the same payloads the backend returns; anything
 * it cannot produce is something the UI must not depend on.
 */
export interface Call {
  method: string
  path: string
  body: unknown
}

export function installApi(overrides: Record<string, unknown> = {}) {
  const calls: Call[] = []

  const routes: Record<string, unknown> = {
    'GET /api/health': {
      status: 'ok',
      server_time: '2026-08-05T19:47:11.000-05:00',
      tz: 'America/Bogota',
      version: '1.0.0',
      origins: {
        primary: 'https://autonomos.tail1a2b3c.ts.net',
        lan: 'https://192.168.1.24:8443',
      },
    },
    'GET /api/status': { transcription: 'ok', llm: 'ok', checked_at: '2026-08-05T19:47:00-05:00' },
    'GET /api/categories': {
      items: [
        'Comida',
        'Transporte',
        'Mercado',
        'Servicios',
        'Salud',
        'Ocio',
        'Hogar',
        'Ropa',
        'Educación',
        'Otros',
      ].map((name, i) => ({ id: i + 1, name, sort_order: i, archived: false, in_use_count: 0 })),
    },
    'GET /api/payment-methods': {
      items: ['Efectivo', 'Tarjeta de crédito', 'Tarjeta débito', 'Transferencia', 'Nequi', 'Daviplata'].map(
        (name, i) => ({ id: i + 1, name, sort_order: i, archived: false, in_use_count: 0 }),
      ),
    },
    'GET /api/summary/day': {
      date: '2026-08-05',
      total_cop: 0,
      expense_count: 0,
      items: [],
    },
    'POST /api/expenses': {
      id: 1,
      amount_cop: 14000,
      category_id: 2,
      category_name: 'Transporte',
      payment_method_id: 2,
      payment_method_name: 'Tarjeta de crédito',
      spent_on: '2026-08-05',
      description: null,
      created_at: '2026-08-05T19:47:11.000-05:00',
      updated_at: '2026-08-05T19:47:11.000-05:00',
    },
    ...overrides,
  }

  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input)
    const path = url.startsWith('http') ? new URL(url).pathname + new URL(url).search : url
    const method = init?.method ?? 'GET'
    const bare = path.split('?')[0]
    calls.push({
      method,
      path,
      body: init?.body && typeof init.body === 'string' ? JSON.parse(init.body) : undefined,
    })
    const payload = routes[`${method} ${bare}`]
    if (payload === undefined) {
      return new Response(
        JSON.stringify({ error: { code: 'not_found', message: `no stub for ${method} ${bare}` } }),
        { status: 404, headers: { 'Content-Type': 'application/json' } },
      )
    }
    return new Response(JSON.stringify(payload), {
      status: method === 'POST' ? 201 : 200,
      headers: { 'Content-Type': 'application/json' },
    })
  })

  vi.stubGlobal('fetch', fetchMock)
  return { calls }
}
