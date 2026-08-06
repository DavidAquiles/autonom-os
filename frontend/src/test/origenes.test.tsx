import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { App } from '../App'
import { servidor } from '../copy/es'
import { installApi } from './server'

/**
 * KD-2 mechanism 1 and criterion 13.8. The first implementation stored the
 * fallback address only when the app was served from a non-tailnet host, which
 * — `localStorage` being per-origin — put it where the origin that renders the
 * failure can never read it, so the link could never appear. These tests pin
 * the mechanism in the direction it has to run: written on success by whatever
 * origin is serving, read on failure from that same origin's storage.
 */

const KEY = 'autonomos.origins'
const LAN = 'https://192.168.1.24:8443'
const PRIMARY = 'https://autonomos.tail1a2b3c.ts.net'

beforeEach(() => window.localStorage.clear())
afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
  window.localStorage.clear()
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

/** The server is not answering at all — 13.2's condition, not an API error. */
function unreachable() {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => {
      throw new TypeError('Failed to fetch')
    }),
  )
}

describe('arming the alternative origin (KD-2 mechanism 1)', () => {
  it('persists both origins on a successful /api/health, whatever origin is serving', async () => {
    installApi()
    mount()

    await waitFor(() =>
      expect(JSON.parse(window.localStorage.getItem(KEY) ?? 'null')).toEqual({
        primary: PRIMARY,
        lan: LAN,
      }),
    )
  })

  it('overwrites on every success, so a changed LAN address self-heals', async () => {
    window.localStorage.setItem(KEY, JSON.stringify({ primary: null, lan: 'https://10.0.0.9:8443' }))
    installApi()
    mount()

    await waitFor(() =>
      expect(JSON.parse(window.localStorage.getItem(KEY) ?? 'null').lan).toBe(LAN),
    )
  })
})

describe('offering the alternative origin (criterion 13.8)', () => {
  it('links every stored origin that is not the one we are already on', async () => {
    window.localStorage.setItem(KEY, JSON.stringify({ primary: PRIMARY, lan: LAN }))
    unreachable()
    mount()

    const casa = await screen.findByRole('link', { name: servidor.abrirCasa }, { timeout: 4000 })
    expect(casa).toHaveAttribute('href', LAN)
    expect(screen.getByRole('link', { name: servidor.abrirSiempre })).toHaveAttribute(
      'href',
      PRIMARY,
    )
    // The address is printed, not only linked, so it can be typed by hand, and
    // each alternative carries the sentence that explains it.
    expect(screen.getByText(LAN)).toBeInTheDocument()
    expect(screen.getByText(PRIMARY)).toBeInTheDocument()
    expect(screen.getByText(servidor.casaAyuda, { exact: false })).toBeInTheDocument()
    expect(screen.getByText(servidor.siempreAyuda, { exact: false })).toBeInTheDocument()
  })

  it('never offers a link back to the origin already being served', async () => {
    window.localStorage.setItem(
      KEY,
      JSON.stringify({ primary: window.location.origin, lan: null }),
    )
    unreachable()
    mount()

    await screen.findByText(servidor.titulo, {}, { timeout: 4000 })
    expect(screen.queryByRole('link', { name: servidor.abrirSiempre })).toBeNull()
    expect(screen.queryByRole('link', { name: servidor.abrirCasa })).toBeNull()
  })

  it('still says in Spanish what to do when nothing has ever been stored', async () => {
    unreachable()
    mount()

    // 13.8's first clause is copy, not data: it must hold on first run too.
    await screen.findByText(servidor.titulo, {}, { timeout: 4000 })
    expect(screen.getByText(servidor.casaAyuda)).toBeInTheDocument()
    expect(screen.getByText(servidor.cuerpo1)).toBeInTheDocument()
    // 13.2: explicit, named, and not a dead end.
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeInTheDocument()
    // No address is guessed to fill the gap.
    expect(screen.queryByRole('link', { name: servidor.abrirCasa })).toBeNull()
  })

  it('ignores a stored value that is not a usable absolute origin', async () => {
    window.localStorage.setItem(KEY, JSON.stringify({ primary: null, lan: 'casa' }))
    unreachable()
    mount()

    await screen.findByText(servidor.titulo, {}, { timeout: 4000 })
    expect(screen.queryByRole('link', { name: servidor.abrirCasa })).toBeNull()
  })
})
