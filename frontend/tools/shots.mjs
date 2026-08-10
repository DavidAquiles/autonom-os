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

/* --- Run 02: Historial, the expense detail, the opened category --- */

const expense = (over = {}) => ({
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

/*
 * Constraint 32 requires the show-more control's two states to be
 * "distinguishable on sight", so both must be photographed — and whichever the
 * live data CANNOT produce is the one to stub. Checked rather than assumed:
 * tools/seed.mjs writes 12 expenses (4 for today, 8 for the month) against a
 * page size of 30, so a live Historial is one short page with
 * `next_before_id: null` and NO control. The live matrix therefore carries the
 * ABSENT half, and the PRESENT half is stubbed here.
 *
 * If the seeder ever grows past a page the live shot flips to the other state
 * and the absent half is the one that needs stubbing instead.
 */
const HISTORIAL_HAY_MAS = {
  items: [
    ['Transporte', 18000, '2026-08-05', 'Tarjeta de crédito'],
    ['Mercado', 150000, '2026-08-02', 'Tarjeta débito'],
    ['Comida', 23500, '2026-08-05', 'Efectivo'],
    ['Comida', 9000, '2026-08-04', 'Nequi'],
    ['Servicios', 62000, '2026-08-01', 'Transferencia'],
    ['Transporte', 12000, '2026-08-05', 'Efectivo'],
    ['Hogar', 340000, '2026-07-28', 'Tarjeta de crédito'],
    ['Comida', 7500, '2026-08-03', 'Efectivo'],
    ['Salud', 86000, '2026-07-30', 'Tarjeta débito'],
    ['Ocio', 21000, '2026-08-02', 'Nequi'],
    ['Mercado', 15400, '2026-08-03', 'Efectivo'],
    ['Comida', 4800, '2026-08-01', 'Efectivo'],
    ['Ropa', 54000, '2026-07-26', 'Tarjeta de crédito'],
  ].map(([category_name, amount_cop, spent_on, payment_method_name], i) =>
    expense({
      id: 400 - i,
      amount_cop,
      category_name,
      spent_on,
      payment_method_name,
      description: null,
    }),
  ),
  total_count: 431,
  next_before_id: 387,
}

const HISTORIAL_VACIO = { items: [], total_count: 0, next_before_id: null }

const LARGA =
  'Mercado grande del mes en la plaza de Paloquemao, con Ana. Fuimos temprano porque después se ' +
  'llena y los precios de la fruta suben. Llevamos la papa criolla, la yuca, el plátano, tres kilos ' +
  'de naranja para el jugo de la semana, el tomate de árbol, cilantro, cebolla larga y una libra de ' +
  'queso campesino del puesto del fondo, que es el que sirve. También pagamos el domicilio hasta la ' +
  'casa porque no cabía en el carro y salía más caro pedir un taxi. Anoto todo junto en un solo ' +
  'gasto porque fue un solo pago con la tarjeta; si lo separo después no me acuerdo de qué era cada cosa.'

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

  /* --- Run 02: the month opened by category (18.1-18.5, constraints 39-42) --- */
  {
    // Constraint 39: the boundary between a tappable category row and an inert
    // payment-method row, in one frame.
    name: 'finanzas-mes--frontera',
    url: '/finanzas/mes',
    scroll: 320,
  },
  {
    name: 'finanzas-mes--categoria-hover',
    url: '/finanzas/mes',
    force: [['ul li button', ['hover']]],
  },
  {
    name: 'finanzas-mes--categoria-foco',
    url: '/finanzas/mes',
    force: [['ul li button', ['focus', 'focus-visible']]],
  },
  {
    name: 'finanzas-mes--categoria-pulsada',
    url: '/finanzas/mes',
    force: [['ul li button', ['hover', 'active']]],
  },
  {
    // Constraint 40 (both totals distinguishable) and 41 (the way to close it
    // visible without scrolling).
    name: 'finanzas-mes--categoria',
    url: '/finanzas/mes?categoria=2',
  },
  {
    name: 'finanzas-mes--cerrar-hover',
    url: '/finanzas/mes?categoria=2',
    forceText: [['Cerrar', ['hover']]],
  },
  {
    name: 'finanzas-mes--cerrar-foco',
    url: '/finanzas/mes?categoria=2',
    forceText: [['Cerrar', ['focus', 'focus-visible']]],
  },
  {
    // 18.10 / constraint 42. OQ3: no total and no count in the band — a zero
    // row is exactly what 18.10 forbids.
    name: 'finanzas-mes--categoria-vacia',
    url: '/finanzas/mes?categoria=8',
    stubs: { '/api/expenses': { items: [], total_count: 0, next_before_id: null } },
  },

  /* --- Run 02: Historial (16.x, constraints 29-34, 42) --- */
  {
    // Carries constraint 29 (four tabs, no truncation), 30 (row treatment,
    // against finanzas-hoy), 31 (the ordering statement above the first row),
    // 33 (flat), 34 (nothing else operable) — and constraint 32's ABSENT half,
    // because 12 seeded expenses fit in one page of 30.
    name: 'finanzas-historial',
    url: '/finanzas/historial',
  },
  {
    // Where a date heading or a day separator would show up if one crept in.
    name: 'finanzas-historial--desplazado',
    url: '/finanzas/historial',
    scroll: 520,
  },
  {
    name: 'finanzas-historial--fila-hover',
    url: '/finanzas/historial',
    force: [['ul li a', ['hover']]],
  },
  {
    name: 'finanzas-historial--fila-foco',
    url: '/finanzas/historial',
    force: [['ul li a', ['focus', 'focus-visible']]],
  },
  {
    name: 'finanzas-historial--pestana-foco',
    url: '/finanzas/historial',
    force: [['a[href="/finanzas/historial"]', ['focus', 'focus-visible']]],
  },
  {
    // Constraint 32, PRESENT half. Stubbed because the live seed cannot make it.
    name: 'finanzas-historial--ver-mas',
    url: '/finanzas/historial',
    stubs: { '/api/expenses': HISTORIAL_HAY_MAS },
    scroll: 2000,
  },
  {
    name: 'finanzas-historial--ver-mas-hover',
    url: '/finanzas/historial',
    stubs: { '/api/expenses': HISTORIAL_HAY_MAS },
    scroll: 2000,
    forceText: [['Ver gastos más antiguos', ['hover']]],
  },
  {
    name: 'finanzas-historial--ver-mas-foco',
    url: '/finanzas/historial',
    stubs: { '/api/expenses': HISTORIAL_HAY_MAS },
    scroll: 2000,
    forceText: [['Ver gastos más antiguos', ['focus', 'focus-visible']]],
  },
  {
    name: 'finanzas-historial--ver-mas-pulsado',
    url: '/finanzas/historial',
    stubs: { '/api/expenses': HISTORIAL_HAY_MAS },
    scroll: 2000,
    forceText: [['Ver gastos más antiguos', ['hover', 'active']]],
  },
  {
    /*
     * Constraint 32's in-flight case, and the ONLY shot that exercises the
     * Button.module.css `.text:disabled` fix. Against a stub the fetch resolves
     * in microseconds, so the state is set on the real control instead — the
     * same two things the component itself sets while `isFetchingNextPage`.
     * The control stays in place and greys; it must NOT wash violet under the
     * pointer, which is precisely what it did before the fix.
     */
    name: 'finanzas-historial--ver-mas-en-curso',
    url: '/finanzas/historial',
    stubs: { '/api/expenses': HISTORIAL_HAY_MAS },
    scroll: 2000,
    before: [
      {
        eval: `(() => {
          const b = [...document.querySelectorAll('button')]
            .find((x) => x.textContent.trim() === 'Ver gastos más antiguos')
          if (!b) return false
          b.disabled = true
          b.textContent = 'Cargando…'
          return true
        })()`,
      },
    ],
    forceText: [['Cargando…', ['hover']]],
  },
  {
    name: 'finanzas-historial--pestana-hover',
    url: '/finanzas/historial',
    force: [['a[href="/finanzas/historial"]', ['hover']]],
  },
  {
    name: 'finanzas-historial--pestana-pulsada',
    url: '/finanzas/historial',
    force: [['a[href="/finanzas/mes"]', ['hover', 'active']]],
  },
  {
    // 16.10 / constraint 42: distinct from the shot above — no rows at all,
    // versus rows with nothing after them.
    name: 'finanzas-historial-vacio',
    url: '/finanzas/historial',
    stubs: { '/api/expenses': HISTORIAL_VACIO },
  },

  /* --- Run 02: the expense detail (17.x, constraints 35-38, 43) --- */
  {
    // Constraints 35 (no form), 36 (the journal read frame), 37 (two labelled
    // dates), 43 (nothing reveals how it was captured).
    name: 'gasto-detalle',
    url: '/finanzas/gasto/1',
  },
  {
    name: 'gasto-detalle--editar-hover',
    url: '/finanzas/gasto/1',
    forceText: [['Editar gasto', ['hover']]],
  },
  {
    name: 'gasto-detalle--editar-foco',
    url: '/finanzas/gasto/1',
    forceText: [['Editar gasto', ['focus', 'focus-visible']]],
  },
  {
    name: 'gasto-detalle--editar-pulsado',
    url: '/finanzas/gasto/1',
    forceText: [['Editar gasto', ['hover', 'active']]],
  },
  {
    name: 'gasto-detalle--cerrar-foco',
    url: '/finanzas/gasto/1',
    force: [['button[aria-label="Cerrar"]', ['focus', 'focus-visible']]],
  },
  {
    // 17.3: omitted entirely, not a dash and not a placeholder.
    name: 'gasto-detalle--sin-descripcion',
    url: '/finanzas/gasto/1',
    stubs: { '/api/expenses/1': expense({ description: null }) },
  },
  {
    // 17.5 / constraint 38: the same ink, the same size, the same block as
    // "Anotado el…". No red, no icon, no badge.
    name: 'gasto-detalle--editado',
    url: '/finanzas/gasto/1',
    stubs: { '/api/expenses/1': expense({ updated_at: '2026-08-07T09:20:00.000-05:00' }) },
  },
  {
    // Without this NOTHING in the matrix can fail constraint 37's "shown in
    // full, unclamped": the live shot runs against seed.mjs's "Café y pan" and
    // the --sin-descripcion stub has none at all, so a line-clamp or a
    // "seguir leyendo" would be invisible in every capture.
    name: 'gasto-detalle--descripcion-larga',
    url: '/finanzas/gasto/1',
    stubs: {
      '/api/expenses/1': expense({
        amount_cop: 150000,
        category_name: 'Mercado',
        payment_method_name: 'Tarjeta débito',
        spent_on: '2026-08-02',
        description: LARGA,
      }),
    },
  },
  {
    name: 'gasto-detalle--no-existe',
    url: '/finanzas/gasto/999',
    // main.tsx sets `retry: 1`, so a 404 settles about a second after load and
    // shows "Cargando…" until it does. Same wait the unreachable shots use.
    before: [{ wait: 2500 }],
    stubs: {
      '/api/expenses/999': {
        status: 404,
        body: { error: { code: 'not_found', message: 'expense 999' } },
      },
    },
  },

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
  /*
   * KD-23 moved the form: /finanzas/gasto/1 now renders the READ-ONLY detail,
   * which by constraint 35 and A31 has no delete control. Left unrepointed,
   * gasto-editar.png would silently become a picture of the detail while still
   * being reviewed as the form — B1 regressing in the very artefact meant to
   * prove it did not — and the three delete recipes would throw. One failure
   * loud, one silent; the silent one is the problem.
   */
  { name: 'gasto-editar', url: '/finanzas/gasto/1/editar', scroll: 900 },
  {
    name: 'gasto-eliminar',
    url: '/finanzas/gasto/1/editar',
    before: [{ wait: 400 }, { clickText: 'Eliminar gasto' }],
  },
  {
    name: 'gasto-eliminar--boton-pulsado',
    url: '/finanzas/gasto/1/editar',
    before: [{ wait: 400 }, { clickText: 'Eliminar gasto' }],
    force: [['[role="dialog"] button', ['hover', 'active']]],
  },
  {
    name: 'gasto-eliminar--boton-hover',
    url: '/finanzas/gasto/1/editar',
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
  /*
   * KD-2 mechanism 1 / criterion 13.8. The alternative origin is only ever what
   * THIS origin stored on an earlier successful /api/health, so these shots seed
   * `localStorage` — the exact thing the health response writes — and then kill
   * the API, which is the real condition of the screen. Both halves are
   * captured: with an armed origin and with nothing stored at all.
   */
  {
    name: 'sin-servidor',
    url: '/sin-servidor',
    killApi: true,
    local: { 'autonomos.origins': { primary: BASE, lan: 'https://192.168.1.24:8443' } },
  },
  {
    name: 'sin-servidor--sin-origen',
    url: '/sin-servidor',
    killApi: true,
  },
  {
    // Served from the LAN origin and away from home: the alternative offered is
    // the everyday one, not the local one.
    name: 'sin-servidor--desde-casa',
    url: '/sin-servidor',
    killApi: true,
    local: {
      'autonomos.origins': { primary: 'https://autonomos.tail1a2b3c.ts.net', lan: BASE },
    },
  },
  {
    // A third origin (localhost during setup) is the only state where both
    // alternatives exist at once; captured rather than assumed.
    name: 'sin-servidor--ambos',
    url: '/sin-servidor',
    killApi: true,
    local: {
      'autonomos.origins': {
        primary: 'https://autonomos.tail1a2b3c.ts.net',
        lan: 'https://192.168.1.24:8443',
      },
    },
  },
  {
    name: 'sin-servidor--enlace-hover',
    url: '/sin-servidor',
    killApi: true,
    local: { 'autonomos.origins': { primary: BASE, lan: 'https://192.168.1.24:8443' } },
    // The unreachable state re-mounts when the health query settles; forcing
    // before that would bind the pseudo-class to a node React then replaces.
    before: [{ wait: 2500 }],
    forceText: [['Abrir la versión de casa', ['hover']]],
  },
  {
    name: 'sin-servidor--enlace-foco',
    url: '/sin-servidor',
    killApi: true,
    local: { 'autonomos.origins': { primary: BASE, lan: 'https://192.168.1.24:8443' } },
    // The unreachable state re-mounts when the health query settles; forcing
    // before that would bind the pseudo-class to a node React then replaces.
    before: [{ wait: 2500 }],
    forceText: [['Abrir la versión de casa', ['focus', 'focus-visible']]],
  },
  {
    name: 'sin-servidor--enlace-pulsado',
    url: '/sin-servidor',
    killApi: true,
    local: { 'autonomos.origins': { primary: BASE, lan: 'https://192.168.1.24:8443' } },
    // The unreachable state re-mounts when the health query settles; forcing
    // before that would bind the pseudo-class to a node React then replaces.
    before: [{ wait: 2500 }],
    forceText: [['Abrir la versión de casa', ['hover', 'active']]],
  },
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
  // The four-tab strip is this run's most likely overflow; the audit's OVERFLOW
  // flag is what catches it (constraint 29).
  { name: 'finanzas-historial--320', url: '/finanzas/historial', width: 320 },
  { name: 'finanzas-historial--360', url: '/finanzas/historial', width: 360 },
  { name: 'finanzas-mes--categoria-320', url: '/finanzas/mes?categoria=2', width: 320 },
  { name: 'gasto-detalle--320', url: '/finanzas/gasto/1', width: 320 },
  {
    // The armed address is the longest unbreakable string on any screen.
    name: 'sin-servidor--320',
    url: '/sin-servidor',
    width: 320,
    killApi: true,
    local: { 'autonomos.origins': { primary: BASE, lan: 'https://192.168.1.24:8443' } },
  },
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
  /*
   * 9.2 (defect D1): the three shapes of "the voice pass could not determine
   * this". Each one is a real transcribe response with `resolved_by` saying
   * "none" for a different field — the same signal the UI reads — so the mark
   * is verified where it is painted, not where it is coded.
   */
  ...(() => {
    const draft = (over) => ({
      transcript: over.transcript,
      audio_ms: 3100,
      elapsed_ms: 5400,
      draft: {
        amount_cop: null,
        category_id: null,
        category_name: null,
        payment_method_id: null,
        payment_method_name: null,
        description: over.transcript,
        description_truncated: false,
        ...over.draft,
      },
    })
    // Nothing suggested, so the empty category stays empty and stays marked.
    const noAssist = { category_id: null, category_name: null, source: 'none' }
    const record = [
      { clickSelector: 'button[aria-label="Grabar con la voz"]' },
      { wait: 2200 },
      { clickText: 'Listo' },
      { wait: 2500 },
    ]

    // QA's own repro, whole: "compré algo" resolves nothing (verified against
    // POST /api/expenses/parse), then the assist offers "Otros". The suggested
    // category must read as a suggestion while the amount reads as a hole.
    const sinMonto = {
      'POST /api/expenses/suggest-category': {
        category_id: 10,
        category_name: 'Otros',
        source: 'llm',
      },
      'POST /api/voice/transcribe': draft({
        transcript: 'compré algo',
        draft: { resolved_by: { amount: 'none', category: 'none', payment_method: 'none' } },
      }),
    }
    const sinCategoria = {
      'POST /api/expenses/suggest-category': noAssist,
      'POST /api/voice/transcribe': draft({
        transcript: 'gasté cinco mil, no sé en qué',
        draft: {
          amount_cop: 5000,
          payment_method_id: 1,
          payment_method_name: 'Efectivo',
          resolved_by: { amount: 'rules', category: 'none', payment_method: 'rules' },
        },
      }),
    }
    const sinNada = {
      'POST /api/expenses/suggest-category': noAssist,
      'POST /api/voice/transcribe': draft({
        transcript: 'no sé qué pasó',
        draft: { resolved_by: { amount: 'none', category: 'none', payment_method: 'none' } },
      }),
    }

    return [
      { name: 'gasto-voz-revision--sin-monto', url: '/finanzas', stubs: sinMonto, before: record },
      {
        name: 'gasto-voz-revision--sin-monto-foco',
        url: '/finanzas',
        stubs: sinMonto,
        before: record,
        forceText: [['Monto', ['focus', 'focus-visible']]],
      },
      {
        // Rejected while still unfilled: red must win over the violet region.
        name: 'gasto-voz-revision--sin-monto-error',
        url: '/finanzas',
        stubs: sinMonto,
        before: [...record, { clickText: 'Guardar gasto' }, { wait: 500 }],
        forceText: [['Monto', ['focus', 'focus-visible']]],
      },
      {
        name: 'gasto-voz-revision--sin-categoria',
        url: '/finanzas',
        stubs: sinCategoria,
        before: record,
      },
      {
        name: 'gasto-voz-revision--sin-categoria-hover',
        url: '/finanzas',
        stubs: sinCategoria,
        before: record,
        forceText: [['Mercado', ['hover']]],
      },
      {
        // The first chip sits against the region's 10px padding: the worst case
        // for a focus ring being clipped by the region's own border.
        name: 'gasto-voz-revision--sin-categoria-foco',
        url: '/finanzas',
        stubs: sinCategoria,
        before: record,
        forceText: [['Comida', ['focus', 'focus-visible']]],
      },
      {
        name: 'gasto-voz-revision--sin-categoria-activo',
        url: '/finanzas',
        stubs: sinCategoria,
        before: record,
        forceText: [['Mercado', ['active']]],
      },
      { name: 'gasto-voz-revision--sin-nada', url: '/finanzas', stubs: sinNada, before: record },
      {
        name: 'gasto-voz-revision--sin-nada--320',
        url: '/finanzas',
        width: 320,
        height: 720,
        stubs: sinNada,
        before: record,
      },
    ]
  })(),
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
  // Sets a state on a real element that the live server resolves too fast to
  // photograph — the same idea as CSS.forcePseudoState, for a state carried by
  // an attribute rather than a pseudo-class. The element, its classes and its
  // stylesheet are the real ones.
  if (action.eval) {
    const ok = await evaluate(send, action.eval)
    if (!ok) throw new Error('eval action returned falsy')
    return sleep(160)
  }
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

  // localStorage survives between shots in this shared profile, so the armed
  // origins are cleared first and seeded only where a shot asks for them. A
  // shot that inherited another's storage would prove nothing about KD-2.
  const preamble = [
    `try { localStorage.removeItem('autonomos.origins') } catch (e) {}`,
    ...Object.entries(shot.local ?? {}).map(
      ([k, v]) => `localStorage.setItem(${JSON.stringify(k)}, ${JSON.stringify(JSON.stringify(v))});`,
    ),
    ...Object.entries(shot.session ?? {}).map(
      ([k, v]) => `sessionStorage.setItem(${JSON.stringify(k)}, ${JSON.stringify(v)});`,
    ),
  ].join('\n')
  await send('Page.addScriptToEvaluateOnNewDocument', { source: preamble })

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

  // A forced pseudo-state is bound to a node id, so a re-render that replaces
  // the node drops it — and the capture then looks exactly like the default
  // state while claiming to be hover, focus or active. That silent no-op is the
  // failure mode this whole matrix exists to prevent, so it is detected: if the
  // stamped element is gone by capture time the shot is a finding, not a pass.
  let forceLost = false
  if (shot.forceText?.length) {
    const alive = await evaluate(send, `!!document.querySelector('[data-force-target]')`)
    if (!alive) {
      forceLost = true
      console.warn(`  ! ${shot.name}: forced state was lost before capture (element re-rendered)`)
    }
  }

  const audit = await evaluate(send, AUDIT_JS)
  const { data } = await send('Page.captureScreenshot', { format: 'png' })
  await writeFile(resolve(OUT, `${shot.name}.png`), Buffer.from(data, 'base64'))

  detach()
  await browser.send('Target.closeTarget', { targetId })
  return { name: shot.name, width, forceLost, ...audit }
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
        r.forceLost ? 'ESTADO-PERDIDO' : '',
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
        r.forceLost ? 'ESTADO-PERDIDO' : '',
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
    (r) =>
      r.error || r.overflow || r.contrast?.length || r.targets?.length || r.darkRules || r.forceLost,
  )
  console.log(`\n${results.length} capturas · ${bad.length} con hallazgos`)
  for (const r of bad) {
    console.log(`\n${r.name}${r.error ? ` — ${r.error}` : ''}`)
    for (const c of r.contrast ?? []) console.log(`   contraste ${c.ratio} < ${c.need}  ${c.tag}.${c.cls}  "${c.text}"`)
    for (const t of r.targets ?? []) console.log(`   toque ${t.w}x${t.h}  ${t.tag}.${t.cls}  "${t.text}"`)
    if (r.overflow) console.log(`   desbordamiento horizontal ${r.scrollWidth} > ${r.innerWidth}`)
    if (r.darkRules) console.log(`   ${r.darkRules} reglas prefers-color-scheme (constraint 22)`)
    if (r.forceLost) console.log(`   el estado forzado se perdió antes de la captura`)
  }
  process.exit(bad.length ? 1 : 0)
}

main()
