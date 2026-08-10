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

/**
 * A route is a payload, or a function of the request when one path has to
 * answer differently per query string — `GET /api/expenses` is keyed on the
 * bare path, so keyset paging (16.7, 16.8) needs the `before_id` cursor to
 * change the answer. Still contract-shaped; still not a hand-rolled mock.
 */
export type Route = unknown | ((req: { path: string; method: string; body: unknown }) => unknown)

export function installApi(overrides: Record<string, Route> = {}) {
  const calls: Call[] = []

  const routes: Record<string, Route> = {
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
    // One entry covers every parameter combination: the stub keys off the bare
    // path (`:79`), so `?order=registered`, `?month=&category_id=` and a
    // `?before_id=` page all resolve here. `next_before_id` is null, which is
    // the contract's "everything is shown" (16.9).
    'GET /api/expenses': { items: [], total_count: 0, next_before_id: null },
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
    const body = init?.body && typeof init.body === 'string' ? JSON.parse(init.body) : undefined
    calls.push({ method, path, body })
    const route = routes[`${method} ${bare}`]
    const payload = typeof route === 'function' ? route({ path, method, body }) : route
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
