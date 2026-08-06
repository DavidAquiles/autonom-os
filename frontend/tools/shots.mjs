/*
 * The screenshot matrix, rendered against the REAL built app served by the real
 * backend — not against the mockups, and not assumed to match them.
 *
 *   node tools/shots.mjs [baseURL]
 *
 * Writes PNGs to frontend/tools/shots/ and an audit report to
 * frontend/tools/shots/audit.json. Chromium on this host is sandboxed and
 * silently writes nothing under /tmp, so every path here is inside the project.
 *
 * States the app can produce live (today, month, journal, settings, the expense
 * form, voice recording with a fake device) go through the real server. States
 * that depend on the server being in a particular condition — an empty month, a
 * question mid-flight, a failed summary, a truncated answer, the LLM being down
 * — are produced by fulfilling that one request with a contract-shaped payload
 * through CDP, so the components under test are still the real ones.
 */
import { mkdir, writeFile } from 'node:fs/promises'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { launch, newPage, waitForLoad, evaluate, forcePseudo, sleep } from './cdp.mjs'
import { AUDIT_JS } from './audit.mjs'

const HERE = dirname(fileURLToPath(import.meta.url))
const OUT = resolve(HERE, 'shots')
const PROFILE = resolve(HERE, 'out/chrome-profile')
const BASE = process.argv[2] ?? 'http://127.0.0.1:8001'

/* ------------------------------------------------------------ stub payloads */

const facts = (over = {}) => ({
  period_label: 'julio de 2026',
  period_start: '2026-07-01',
  period_end: '2026-07-31',
  period_assumed: false,
  domain: 'both',
  total_cop: 2418000,
  expense_count: 84,
  by_category: [{ name: 'Mercado', amount_cop: 812000, percent: 34 }],
  journal_entries_considered: 112,
  journal_entries_used: 40,
  journal_truncated: true,
  ...over,
})

const job = (over = {}) => ({
  job_id: 'a1b2c3d4-0000-4000-8000-000000000000',
  status: 'running',
  question: '¿En qué gasté más en julio?',
  elapsed_ms: 68_000,
  answer: null,
  facts: null,
  error_code: null,
  created_at: '2026-08-05T19:46:03.000-05:00',
  finished_at: null,
  ...over,
})

const SUMMARY_READY = {
  status: 'ready',
  period_kind: 'month',
  period_key: '2026-07',
  period_label: 'julio',
  text:
    'En julio anotaste 84 gastos por $2.418.000. Mercado y Comida se llevaron poco más de la mitad del mes; el resto se reparte entre Transporte y Servicios.\n\nEn el diario escribiste 26 veces. La mudanza aparece en nueve de esas entradas, casi siempre de noche, y a partir del 18 deja de aparecer.',
  generated_at: '2026-08-01T03:12:00.000-05:00',
  model: 'qwen2.5:3b-instruct-q4_K_M',
  facts: facts({ journal_truncated: false }),
}

const EMPTY_MONTH = {
  month: '2026-02',
  total_cop: 0,
  expense_count: 0,
  is_empty: true,
  by_category: [],
  by_payment_method: [],
}

/* ------------------------------------------------------------------- shots */

const SHOTS = [
  /* --- Finanzas, live against the real backend --- */
  { name: 'finanzas-hoy', url: '/finanzas' },
  {
    name: 'finanzas-hoy--fila-hover',
    url: '/finanzas',
    force: [['ul li a', ['hover']]],
  },
  {
    name: 'finanzas-hoy--fila-foco',
    url: '/finanzas',
    force: [['ul li a', ['focus', 'focus-visible']]],
  },
  {
    name: 'finanzas-hoy--fila-pulsada',
    url: '/finanzas',
    force: [['ul li a', ['hover', 'active']]],
  },
  {
    name: 'finanzas-hoy--captura-hover',
    url: '/finanzas',
    force: [
      ['a[href="/finanzas/gasto/nuevo"]', ['hover']],
      ['button[aria-label="Grabar con la voz"]', ['hover']],
    ],
  },
  {
    name: 'finanzas-hoy--captura-foco',
    url: '/finanzas',
    force: [['button[aria-label="Grabar con la voz"]', ['focus', 'focus-visible']]],
  },
  {
    name: 'finanzas-hoy--nav-hover',
    url: '/finanzas',
    force: [['nav[aria-label="Secciones"] a[href="/diario"]', ['hover']]],
  },
  {
    name: 'finanzas-hoy-vacio',
    url: '/finanzas',
    stubs: {
      '/api/summary/day': { date: '2026-08-05', total_cop: 0, expense_count: 0, items: [] },
    },
  },
  { name: 'finanzas-mes', url: '/finanzas/mes' },
  { name: 'finanzas-mes--desplazado', url: '/finanzas/mes', scroll: 520 },
  {
    name: 'finanzas-mes--flecha-deshabilitada',
    url: '/finanzas/mes',
    force: [['button[aria-label="Mes siguiente"]', ['hover']]],
  },
  { name: 'finanzas-mes-vacio', url: '/finanzas/mes', stubs: { '/api/summary/month': EMPTY_MONTH } },

  /* --- the expense form: the four-interaction budget --- */
  { name: 'gasto-nuevo', url: '/finanzas/gasto/nuevo' },
  {
    name: 'gasto-nuevo--chip-hover',
    url: '/finanzas/gasto/nuevo',
    force: [['[role="radio"]', ['hover']]],
  },
  {
    name: 'gasto-nuevo--chip-foco',
    url: '/finanzas/gasto/nuevo',
    force: [['[role="radio"]', ['focus', 'focus-visible']]],
  },
  {
    name: 'gasto-nuevo--chip-pulsado',
    url: '/finanzas/gasto/nuevo',
    force: [['[role="radio"]', ['hover', 'active']]],
  },
  {
    name: 'gasto-nuevo--elegido',
    url: '/finanzas/gasto/nuevo',
    before: [
      { click: '[role="radio"][aria-checked="false"]:nth-of-type(2)' },
      { clickText: 'Tarjeta de crédito' },
    ],
  },
  {
    name: 'gasto-nuevo--boton-hover',
    url: '/finanzas/gasto/nuevo',
    force: [['button[type="submit"]', ['hover']]],
  },
  {
    name: 'gasto-nuevo--boton-pulsado',
    url: '/finanzas/gasto/nuevo',
    force: [['button[type="submit"]', ['hover', 'active']]],
  },
  {
    name: 'gasto-nuevo-error',
    url: '/finanzas/gasto/nuevo',
    before: [{ clickText: 'Guardar gasto' }],
  },
  {
    name: 'gasto-nuevo-nueva-categoria',
    url: '/finanzas/gasto/nuevo',
    before: [{ clickText: 'Nueva' }, { type: 'Cafetería' }],
  },
  {
    name: 'gasto-nuevo-fecha',
    url: '/finanzas/gasto/nuevo',
    before: [{ clickText: 'Cambiar' }],
    scroll: 700,
  },
  {
    name: 'gasto-guardando',
    url: '/finanzas/gasto/nuevo',
    slowPost: true,
    before: [
      { fill: ['input[aria-label="Monto"]', '14000'] },
      { clickText: 'Transporte' },
      { clickText: 'Tarjeta de crédito' },
      { clickText: 'Guardar gasto' },
      { wait: 250 },
    ],
    scroll: 900,
  },
  {
    name: 'gasto-guardar-fallo',
    url: '/finanzas/gasto/nuevo',
    failPost: true,
    before: [
      { fill: ['input[aria-label="Monto"]', '14000'] },
      { clickText: 'Transporte' },
      { clickText: 'Tarjeta de crédito' },
      { clickText: 'Guardar gasto' },
      { wait: 500 },
    ],
  },
  { name: 'gasto-editar', url: '/finanzas/gasto/1', scroll: 900 },
  {
    name: 'gasto-eliminar',
    url: '/finanzas/gasto/1',
    before: [{ wait: 400 }, { clickText: 'Eliminar gasto' }],
  },
  {
    name: 'gasto-eliminar--boton-pulsado',
    url: '/finanzas/gasto/1',
    before: [{ wait: 400 }, { clickText: 'Eliminar gasto' }],
    force: [['[role="dialog"] button', ['hover', 'active']]],
  },
  {
    name: 'gasto-eliminar--boton-hover',
    url: '/finanzas/gasto/1',
    before: [{ wait: 400 }, { clickText: 'Eliminar gasto' }],
    force: [['[role="dialog"] button', ['hover']]],
  },
  {
    name: 'gasto-nuevo--monto-foco',
    url: '/finanzas/gasto/nuevo',
    forceText: [['Monto', ['focus']]],
  },
  {
    name: 'gasto-nuevo--descripcion-hover',
    url: '/finanzas/gasto/nuevo',
    force: [['input[maxlength="1000"]', ['hover']]],
    scroll: 700,
  },

  /* --- Diario --- */
  { name: 'diario', url: '/diario' },
  { name: 'diario--desplazado', url: '/diario', scroll: 480 },
  {
    name: 'diario--entrada-hover',
    url: '/diario',
    force: [['main a[href^="/diario/"]', ['hover']]],
  },
  { name: 'diario-vacio', url: '/diario', stubs: { '/api/journal': { items: [], next_before: null } } },
  { name: 'diario-fecha', url: '/diario/fecha' },
  {
    name: 'diario-fecha-vacia',
    url: '/diario/fecha',
    stubs: { '/api/journal': { items: [], next_before: null } },
  },
  { name: 'diario-entrada', url: '/diario/1' },
  { name: 'diario-escribir', url: '/diario/nueva' },
  {
    name: 'diario-escribir-error',
    url: '/diario/nueva',
    before: [{ fill: ['textarea', '   '] }, { clickText: 'Guardar' }],
  },

  /* --- Análisis --- */
  { name: 'analisis', url: '/finanzas/analisis', stubs: { '/api/insights/summaries/latest': SUMMARY_READY } },
  {
    name: 'analisis-sin-resumen',
    url: '/finanzas/analisis',
    stubs: { '/api/insights/summaries/latest': { status: 'none' } },
  },
  {
    name: 'analisis-generando',
    url: '/finanzas/analisis',
    stubs: {
      '/api/insights/summaries/latest': {
        status: 'generating',
        period_key: '2026-07',
        period_label: 'julio',
        started_at: new Date(Date.now() - 96_000).toISOString().replace('Z', '-05:00'),
      },
    },
    before: [{ wait: 1500 }],
  },
  {
    name: 'analisis-periodo-vacio',
    url: '/finanzas/analisis',
    stubs: {
      '/api/insights/summaries/latest': { status: 'empty', period_key: '2026-07', period_label: 'julio' },
    },
  },
  {
    name: 'analisis-resumen-fallo',
    url: '/finanzas/analisis',
    stubs: {
      '/api/insights/summaries/latest': {
        status: 'failed',
        period_key: '2026-07',
        error_code: 'llm_timeout',
      },
    },
  },
  {
    name: 'analisis-esperando--12s',
    url: '/finanzas/analisis',
    stubs: {
      '/api/insights/summaries/latest': SUMMARY_READY,
      '/api/insights/questions/*': job({ elapsed_ms: 12_000 }),
    },
    session: { 'autonomos.jobId': 'a1b2c3d4-0000-4000-8000-000000000000' },
  },
  {
    name: 'analisis-esperando--68s',
    url: '/finanzas/analisis',
    stubs: {
      '/api/insights/summaries/latest': SUMMARY_READY,
      '/api/insights/questions/*': job({ elapsed_ms: 68_000 }),
    },
    session: { 'autonomos.jobId': 'a1b2c3d4-0000-4000-8000-000000000000' },
  },
  {
    name: 'analisis-esperando--cancelar-hover',
    url: '/finanzas/analisis',
    stubs: {
      '/api/insights/summaries/latest': SUMMARY_READY,
      '/api/insights/questions/*': job({ elapsed_ms: 41_000 }),
    },
    session: { 'autonomos.jobId': 'a1b2c3d4-0000-4000-8000-000000000000' },
    force: [['main button', ['hover']]],
  },
  {
    name: 'analisis-respuesta',
    url: '/finanzas/analisis',
    stubs: {
      '/api/insights/summaries/latest': SUMMARY_READY,
      '/api/insights/questions/*': job({
        status: 'done',
        question: '¿Qué me preocupaba en julio?',
        elapsed_ms: 72_000,
        answer:
          'En julio la mudanza aparece en nueve entradas, casi todas escritas de noche. También vuelve el sueño con las cajas sin marcar. A partir del 18 deja de aparecer y lo que escribes cambia hacia el trabajo.',
        facts: facts(),
        finished_at: '2026-08-05T19:47:15.000-05:00',
      }),
    },
    session: { 'autonomos.jobId': 'a1b2c3d4-0000-4000-8000-000000000000' },
  },
  {
    name: 'analisis-respuesta-periodo-asumido',
    url: '/finanzas/analisis',
    stubs: {
      '/api/insights/summaries/latest': SUMMARY_READY,
      '/api/insights/questions/*': job({
        status: 'done',
        question: '¿Cuánto llevo en comida?',
        elapsed_ms: 34_000,
        answer: 'Llevas $298.500 en Comida este mes, repartidos en 21 gastos.',
        facts: facts({
          period_label: 'agosto de 2026',
          period_assumed: true,
          journal_truncated: false,
          journal_entries_considered: null,
          journal_entries_used: null,
        }),
      }),
    },
    session: { 'autonomos.jobId': 'a1b2c3d4-0000-4000-8000-000000000000' },
  },
  {
    name: 'analisis-error-preempted',
    url: '/finanzas/analisis',
    stubs: {
      '/api/insights/summaries/latest': SUMMARY_READY,
      '/api/insights/questions/*': job({ status: 'failed', error_code: 'preempted', elapsed_ms: 22_000 }),
    },
    session: { 'autonomos.jobId': 'a1b2c3d4-0000-4000-8000-000000000000' },
  },
  {
    name: 'analisis-error-unverifiable',
    url: '/finanzas/analisis',
    stubs: {
      '/api/insights/summaries/latest': SUMMARY_READY,
      '/api/insights/questions/*': job({
        status: 'failed',
        question: '¿Cuánto me ahorré en julio?',
        error_code: 'unverifiable_figures',
        elapsed_ms: 51_000,
      }),
    },
    session: { 'autonomos.jobId': 'a1b2c3d4-0000-4000-8000-000000000000' },
  },
  {
    name: 'analisis-error-insuficiente',
    url: '/finanzas/analisis',
    stubs: {
      '/api/insights/summaries/latest': SUMMARY_READY,
      '/api/insights/questions/*': job({
        status: 'failed',
        question: '¿Cómo me fue con la comida en 2024?',
        error_code: 'insufficient_data',
        elapsed_ms: 3_000,
      }),
    },
    session: { 'autonomos.jobId': 'a1b2c3d4-0000-4000-8000-000000000000' },
  },
  {
    name: 'analisis-error-periodo',
    url: '/finanzas/analisis',
    stubs: {
      '/api/insights/summaries/latest': SUMMARY_READY,
      '/api/insights/questions/*': job({
        status: 'failed',
        question: '¿Cuánto gasté en la temporada pasada?',
        error_code: 'period_unrecognised',
        elapsed_ms: 2_000,
      }),
    },
    session: { 'autonomos.jobId': 'a1b2c3d4-0000-4000-8000-000000000000' },
  },
  {
    name: 'analisis-error-timeout',
    url: '/finanzas/analisis',
    stubs: {
      '/api/insights/summaries/latest': SUMMARY_READY,
      '/api/insights/questions/*': job({
        status: 'failed',
        question: '¿Qué cambió entre mayo y julio?',
        error_code: 'llm_timeout',
        elapsed_ms: 118_000,
      }),
    },
    session: { 'autonomos.jobId': 'a1b2c3d4-0000-4000-8000-000000000000' },
  },
  {
    name: 'analisis-ia-no-disponible',
    url: '/finanzas/analisis',
    stubs: {
      '/api/insights/summaries/latest': SUMMARY_READY,
      '/api/status': { transcription: 'ok', llm: 'unavailable', checked_at: '2026-08-05T19:47:00-05:00' },
    },
  },
  {
    name: 'analisis-ocupado',
    url: '/finanzas/analisis',
    stubs: {
      '/api/insights/summaries/latest': SUMMARY_READY,
      'POST /api/insights/questions': {
        status: 409,
        body: { error: { code: 'busy', message: 'a question is already running' } },
      },
    },
    before: [
      { fill: ['input[aria-label="Haz una pregunta"]', '¿Cuánto gasté en transporte?'] },
      { clickText: 'Preguntar' },
      { wait: 500 },
    ],
  },
  {
    name: 'analisis-preguntar',
    url: '/finanzas/analisis',
    stubs: { '/api/insights/summaries/latest': SUMMARY_READY },
    before: [{ fill: ['input[aria-label="Haz una pregunta"]', '¿En qué gasté más en julio?'] }],
  },
  {
    name: 'analisis--pregunta-foco',
    url: '/finanzas/analisis',
    stubs: { '/api/insights/summaries/latest': SUMMARY_READY },
    force: [['input[aria-label="Haz una pregunta"]', ['focus']]],
  },
  {
    name: 'analisis--mic-pulsado',
    url: '/finanzas/analisis',
    stubs: { '/api/insights/summaries/latest': SUMMARY_READY },
    force: [['button[aria-label="Preguntar con la voz"]', ['hover', 'active']]],
  },
  {
    name: 'finanzas-ajustes--exportar-hover',
    url: '/finanzas/ajustes',
    forceText: [['Exportar todo', ['hover']]],
    scroll: 900,
  },

  /* --- Ajustes --- */
  { name: 'finanzas-ajustes', url: '/finanzas/ajustes' },
  { name: 'finanzas-ajustes--desplazado', url: '/finanzas/ajustes', scroll: 600 },
  { name: 'finanzas-ajustes-editar', url: '/finanzas/ajustes/categories/1' },
  {
    name: 'finanzas-ajustes-quitar',
    url: '/finanzas/ajustes/categories/1',
    stubs: {
      'DELETE /api/categories/1': {
        status: 409,
        body: { error: { code: 'in_use', message: 'in use', details: { affected_expenses: 34 } } },
      },
    },
    before: [{ wait: 400 }, { clickText: 'Quitar de la lista' }, { wait: 400 }],
  },

  /* --- Sistema --- */
  { name: 'gimnasio', url: '/gimnasio' },
  { name: 'sin-servidor', url: '/sin-servidor' },
  { name: 'sin-servidor-frio', url: '/finanzas', killApi: true, before: [{ wait: 2500 }] },
  {
    name: 'sin-servidor-banner',
    url: '/finanzas',
    stubs: { '/api/health': { status: 502, body: { error: { code: 'internal', message: 'down' } } } },
    before: [{ wait: 2500 }],
  },

  /* --- other widths (constraints 7, 8) --- */
  { name: 'finanzas-hoy--360', url: '/finanzas', width: 360 },
  { name: 'finanzas-hoy--320', url: '/finanzas', width: 320 },
  { name: 'gasto-nuevo--320', url: '/finanzas/gasto/nuevo', width: 320 },
  { name: 'gasto-nuevo--360', url: '/finanzas/gasto/nuevo', width: 360 },
  { name: 'diario--320', url: '/diario', width: 320 },
  { name: 'finanzas-hoy--900', url: '/finanzas', width: 900, height: 900 },
  { name: 'diario--900', url: '/diario', width: 900, height: 900 },
]

/* --- voice shots need a fake microphone, so they run in a second browser --- */
const VOICE_SHOTS = [
  {
    name: 'voz-escuchando',
    url: '/finanzas',
    before: [{ clickSelector: 'button[aria-label="Grabar con la voz"]' }, { wait: 7300 }],
  },
  {
    name: 'voz-escuchando--listo-hover',
    url: '/finanzas',
    before: [{ clickSelector: 'button[aria-label="Grabar con la voz"]' }, { wait: 3200 }],
    forceText: [['Listo', ['hover']]],
  },
  {
    name: 'voz-escuchando--cancelar-foco',
    url: '/finanzas',
    before: [{ clickSelector: 'button[aria-label="Grabar con la voz"]' }, { wait: 3200 }],
    forceText: [['Cancelar', ['focus', 'focus-visible']]],
  },
  {
    name: 'voz-transcribiendo',
    url: '/finanzas',
    slowTranscribe: true,
    before: [
      { clickSelector: 'button[aria-label="Grabar con la voz"]' },
      { wait: 3200 },
      { clickText: 'Listo' },
      { wait: 9000 },
    ],
  },
  {
    name: 'voz-fallo',
    url: '/finanzas',
    stubs: {
      'POST /api/voice/transcribe': {
        status: 422,
        body: { error: { code: 'transcription_failed', message: 'nothing usable' } },
      },
    },
    before: [
      { clickSelector: 'button[aria-label="Grabar con la voz"]' },
      { wait: 2200 },
      { clickText: 'Listo' },
      { wait: 2500 },
    ],
  },
  {
    name: 'gasto-voz-revision',
    url: '/finanzas',
    stubs: {
      'POST /api/voice/transcribe': {
        transcript: 'Gasté catorce mil pesos en un Uber a la casa desde el trabajo',
        audio_ms: 4100,
        elapsed_ms: 6900,
        draft: {
          amount_cop: 14000,
          category_id: 2,
          category_name: 'Transporte',
          payment_method_id: null,
          payment_method_name: null,
          description: 'Uber a la casa desde el trabajo',
          description_truncated: false,
          resolved_by: { amount: 'rules', category: 'rules', payment_method: 'none' },
        },
      },
    },
    before: [
      { clickSelector: 'button[aria-label="Grabar con la voz"]' },
      { wait: 2200 },
      { clickText: 'Listo' },
      { wait: 2500 },
    ],
  },
  {
    name: 'diario-voz-revision',
    url: '/diario',
    stubs: {
      'POST /api/voice/transcribe': {
        transcript:
          'Hoy fue un día raro. Empecé con la sensación de que no iba a rendir nada y terminé sacando adelante todo lo que tenía pendiente. ¿Por qué me cuesta tanto confiar en las mañanas?',
        audio_ms: 9200,
        elapsed_ms: 8100,
        draft: null,
      },
    },
    before: [
      { clickSelector: 'button[aria-label="Grabar con la voz"]' },
      { wait: 2200 },
      { clickText: 'Listo' },
      { wait: 2500 },
    ],
  },
]

/* --------------------------------------------------------------- the driver */

const b64 = (s) => Buffer.from(s, 'utf8').toString('base64')

async function applyStubs(browser, sessionId, send, shot) {
  const patterns = [{ urlPattern: '*/api/*', requestStage: 'Request' }]
  await send('Fetch.enable', { patterns })

  const handler = async (params, sid) => {
    if (sid !== sessionId) return
    const { requestId, request } = params
    const path = new URL(request.url).pathname
    const key = `${request.method} ${path}`

    if (shot.killApi) {
      await send('Fetch.failRequest', { requestId, errorReason: 'ConnectionRefused' }).catch(() => {})
      return
    }

    let stub = shot.stubs?.[key] ?? shot.stubs?.[path]
    if (!stub && shot.stubs) {
      for (const [k, v] of Object.entries(shot.stubs)) {
        const bare = k.includes(' ') ? k.split(' ')[1] : k
        if (bare.endsWith('/*') && path.startsWith(bare.slice(0, -1))) {
          if (!k.includes(' ') || k.startsWith(request.method)) stub = v
        }
      }
    }

    if (shot.failPost && request.method === 'POST') {
      await send('Fetch.failRequest', { requestId, errorReason: 'ConnectionRefused' }).catch(() => {})
      return
    }
    if (shot.slowPost && request.method === 'POST') {
      await new Promise((r) => setTimeout(r, 30_000))
      return
    }
    if (shot.slowTranscribe && path === '/api/voice/transcribe') {
      await new Promise((r) => setTimeout(r, 30_000))
      return
    }

    if (stub) {
      // Several contract payloads carry their own `status` field ("ready",
      // "running", "none"), so an HTTP status is only recognised when it is a
      // number AND paired with an explicit body.
      const envelope = typeof stub.status === 'number' && stub.body !== undefined
      const status = envelope ? stub.status : 200
      const body = envelope ? stub.body : stub
      await send('Fetch.fulfillRequest', {
        requestId,
        responseCode: status,
        responseHeaders: [{ name: 'Content-Type', value: 'application/json' }],
        body: b64(JSON.stringify(body)),
      }).catch(() => {})
      return
    }

    await send('Fetch.continueRequest', { requestId }).catch(() => {})
  }

  browser.on('Fetch.requestPaused', handler)
  return () => browser.off('Fetch.requestPaused', handler)
}

async function runAction(send, action) {
  if (action.wait) return sleep(action.wait)
  if (action.clickText) {
    const ok = await evaluate(
      send,
      `(() => {
        const t = ${JSON.stringify(action.clickText)}
        const els = [...document.querySelectorAll('button, a, [role="radio"]')]
        const el = els.find((e) => e.textContent.trim() === t) || els.find((e) => e.textContent.includes(t))
        if (!el) return false
        el.click()
        return true
      })()`,
    )
    if (!ok) throw new Error(`no control labelled "${action.clickText}"`)
    return sleep(220)
  }
  if (action.clickSelector) {
    await evaluate(send, `document.querySelector(${JSON.stringify(action.clickSelector)}).click()`)
    return sleep(220)
  }
  if (action.click) {
    await evaluate(send, `document.querySelector(${JSON.stringify(action.click)}).click()`)
    return sleep(220)
  }
  if (action.fill) {
    const [selector, value] = action.fill
    await evaluate(
      send,
      `(() => {
        const el = document.querySelector(${JSON.stringify(selector)})
        const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement : HTMLInputElement
        const setter = Object.getOwnPropertyDescriptor(proto.prototype, 'value').set
        setter.call(el, ${JSON.stringify(value)})
        el.dispatchEvent(new Event('input', { bubbles: true }))
        return true
      })()`,
    )
    return sleep(220)
  }
  if (action.type) {
    await evaluate(
      send,
      `(() => {
        const el = document.activeElement
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set
        setter.call(el, ${JSON.stringify(action.type)})
        el.dispatchEvent(new Event('input', { bubbles: true }))
        return true
      })()`,
    )
    return sleep(220)
  }
}

async function shoot(browser, shot) {
  const { sessionId, send, targetId } = await newPage(browser)
  const width = shot.width ?? 390
  const height = shot.height ?? 844

  await send('Emulation.setDeviceMetricsOverride', {
    width,
    height,
    deviceScaleFactor: 2,
    mobile: true,
  })

  const detach = await applyStubs(browser, sessionId, send, shot)

  if (shot.session) {
    await send('Page.addScriptToEvaluateOnNewDocument', {
      source: Object.entries(shot.session)
        .map(([k, v]) => `sessionStorage.setItem(${JSON.stringify(k)}, ${JSON.stringify(v)});`)
        .join('\n'),
    })
  }

  const load = waitForLoad(browser, sessionId)
  await send('Page.navigate', { url: BASE + shot.url })
  await load
  await sleep(900)

  for (const action of shot.before ?? []) await runAction(send, action)

  if (shot.scroll) {
    await evaluate(send, `(document.querySelector('main')||document.documentElement).scrollTop = ${shot.scroll}`)
    await sleep(200)
  }

  // Force by visible label where a CSS selector cannot name the control: a
  // temporary attribute is stamped on it, then the real pseudo-class is forced
  // through CDP. No helper class exists in the app's CSS to drift from.
  for (const [label, pseudos] of shot.forceText ?? []) {
    const ok = await evaluate(
      send,
      `(() => {
        document.querySelectorAll('[data-force-target]').forEach(e => e.removeAttribute('data-force-target'))
        const t = ${JSON.stringify(label)}
        const el = [...document.querySelectorAll('button, a, input, textarea, [role="radio"]')]
          .find((e) => (e.textContent || e.getAttribute('aria-label') || '').trim() === t)
        if (!el) return false
        el.setAttribute('data-force-target', '1')
        return true
      })()`,
    )
    if (!ok) {
      console.warn(`  ! ${shot.name}: no control labelled "${label}" to force ${pseudos}`)
      continue
    }
    await forcePseudo(send, '[data-force-target]', pseudos)
  }

  for (const [selector, pseudos] of shot.force ?? []) {
    try {
      await forcePseudo(send, selector, pseudos)
    } catch (e) {
      console.warn(`  ! ${shot.name}: could not force ${pseudos} on ${selector} — ${e.message}`)
    }
  }
  if (shot.force || shot.forceText) await sleep(150)

  const audit = await evaluate(send, AUDIT_JS)
  const { data } = await send('Page.captureScreenshot', { format: 'png' })
  await writeFile(resolve(OUT, `${shot.name}.png`), Buffer.from(data, 'base64'))

  detach()
  await browser.send('Target.closeTarget', { targetId })
  return { name: shot.name, width, ...audit }
}

async function main() {
  await mkdir(OUT, { recursive: true })
  await mkdir(PROFILE, { recursive: true })

  const results = []

  const plain = await launch({ port: 9222, profileDir: resolve(PROFILE, 'plain') })
  for (const shot of SHOTS) {
    try {
      const r = await shoot(plain.browser, shot)
      results.push(r)
      const flags = [
        r.overflow ? 'OVERFLOW' : '',
        r.contrast.length ? `contraste:${r.contrast.length}` : '',
        r.targets.length ? `toque:${r.targets.length}` : '',
        r.darkRules ? `dark:${r.darkRules}` : '',
      ]
        .filter(Boolean)
        .join(' ')
      console.log(`  ${flags ? '✗' : '✓'} ${shot.name}${flags ? '  ' + flags : ''}`)
    } catch (e) {
      console.log(`  ! ${shot.name}: ${e.message}`)
      results.push({ name: shot.name, error: e.message })
    }
  }
  plain.browser.close()
  plain.proc.kill()

  const mic = await launch({ port: 9223, profileDir: resolve(PROFILE, 'mic'), fakeMedia: true })
  for (const shot of VOICE_SHOTS) {
    try {
      const r = await shoot(mic.browser, shot)
      results.push(r)
      const flags = [
        r.overflow ? 'OVERFLOW' : '',
        r.contrast.length ? `contraste:${r.contrast.length}` : '',
        r.targets.length ? `toque:${r.targets.length}` : '',
      ]
        .filter(Boolean)
        .join(' ')
      console.log(`  ${flags ? '✗' : '✓'} ${shot.name}${flags ? '  ' + flags : ''}`)
    } catch (e) {
      console.log(`  ! ${shot.name}: ${e.message}`)
      results.push({ name: shot.name, error: e.message })
    }
  }
  mic.browser.close()
  mic.proc.kill()

  await writeFile(resolve(OUT, 'audit.json'), JSON.stringify(results, null, 2))

  const bad = results.filter(
    (r) => r.error || r.overflow || r.contrast?.length || r.targets?.length || r.darkRules,
  )
  console.log(`\n${results.length} capturas · ${bad.length} con hallazgos`)
  for (const r of bad) {
    console.log(`\n${r.name}${r.error ? ` — ${r.error}` : ''}`)
    for (const c of r.contrast ?? []) console.log(`   contraste ${c.ratio} < ${c.need}  ${c.tag}.${c.cls}  "${c.text}"`)
    for (const t of r.targets ?? []) console.log(`   toque ${t.w}x${t.h}  ${t.tag}.${t.cls}  "${t.text}"`)
    if (r.overflow) console.log(`   desbordamiento horizontal ${r.scrollWidth} > ${r.innerWidth}`)
    if (r.darkRules) console.log(`   ${r.darkRules} reglas prefers-color-scheme (constraint 22)`)
  }
  process.exit(bad.length ? 1 : 0)
}

main()
