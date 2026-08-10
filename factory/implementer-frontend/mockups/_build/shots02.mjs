/*
 * The Run 02 mockup screenshot matrix.
 *
 * Interactive states are forced with CDP `CSS.forcePseudoState` on the REAL
 * element, not with a mirrored `.is-hover` helper class — a helper is a second
 * source of truth that can drift from the rule it is supposed to prove.
 *
 * Every forced shot is md5'd against its own default. Identical bytes mean the
 * state never applied and the capture would be a lie; that is reported as
 * ESTADO-PERDIDO and is a failure, not a warning.
 */
import { createHash } from 'node:crypto'
import { mkdirSync, writeFileSync, readFileSync, rmSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { launch, newPage, waitForLoad, evaluate, forcePseudo, sleep } from '../../../../frontend/tools/cdp.mjs'

const HERE = dirname(fileURLToPath(import.meta.url))
const MOCK = resolve(HERE, '..')
const SHOTS = join(MOCK, 'shots')
const PROFILE = join(HERE, '.chrome-profile')

const W = 390
const H = 844

/** name, file, [opts] */
const MATRIX = [
  // ---- Historial ----
  ['historial', 'historial.html'],
  ['historial--abajo', 'historial.html', { scroll: 900 }],
  ['historial--fila-hover', 'historial.html', { force: '.ledger li:nth-child(2) .row', pseudo: ['hover'] }],
  ['historial--fila-foco', 'historial.html', { force: '.ledger li:nth-child(2) .row', pseudo: ['focus', 'focus-visible'] }],
  ['historial--fila-pulsada', 'historial.html', { force: '.ledger li:nth-child(2) .row', pseudo: ['hover', 'active'] }],
  ['historial--ver-mas-hover', 'historial.html', { scroll: 900, force: '.vermas .btn', pseudo: ['hover'] }],
  ['historial--ver-mas-foco', 'historial.html', { scroll: 900, force: '.vermas .btn', pseudo: ['focus', 'focus-visible'] }],
  ['historial--ver-mas-pulsado', 'historial.html', { scroll: 900, force: '.vermas .btn', pseudo: ['hover', 'active'] }],
  ['historial--ver-mas-en-curso', 'historial-ver-mas-en-curso.html', { scroll: 900 }],
  // Disabled must NOT light up: a byte-identical result here is the pass.
  ['historial--ver-mas-en-curso-hover', 'historial-ver-mas-en-curso.html',
    { scroll: 900, force: '.vermas .btn', pseudo: ['hover'], expectNoChange: true }],
  ['historial--sin-control', 'historial-completo.html', { scroll: 900 }],
  ['historial--vacio', 'historial-vacio.html'],
  ['historial--cargando', 'historial-cargando.html'],
  ['historial--sin-servidor', 'historial-sin-servidor.html'],
  ['historial--pestana-hover', 'historial.html', { force: '.tabs a:nth-child(2)', pseudo: ['hover'] }],
  ['historial--pestana-foco', 'historial.html', { force: '.tabs a:nth-child(2)', pseudo: ['focus', 'focus-visible'] }],
  ['historial--pestana-pulsada', 'historial.html', { force: '.tabs a:nth-child(2)', pseudo: ['hover', 'active'] }],
  ['historial--320', 'historial.html', { w: 320 }],
  ['historial--vacio-320', 'historial-vacio.html', { w: 320 }],
  // The 320px tab-wrap finding and its measured remedy, side by side.
  ['historial--tira-estrecha-320', 'historial-tira-estrecha.html', { w: 320 }],
  ['historial--tira-estrecha-390', 'historial-tira-estrecha.html'],

  // ---- el detalle ----
  ['gasto-detalle', 'gasto-detalle.html'],
  ['gasto-detalle--editar-hover', 'gasto-detalle.html', { force: '.formfoot .btn', pseudo: ['hover'] }],
  ['gasto-detalle--editar-foco', 'gasto-detalle.html', { force: '.formfoot .btn', pseudo: ['focus', 'focus-visible'] }],
  ['gasto-detalle--editar-pulsado', 'gasto-detalle.html', { force: '.formfoot .btn', pseudo: ['hover', 'active'] }],
  ['gasto-detalle--cerrar-hover', 'gasto-detalle.html', { force: '.formbar .close', pseudo: ['hover'] }],
  ['gasto-detalle--cerrar-foco', 'gasto-detalle.html', { force: '.formbar .close', pseudo: ['focus', 'focus-visible'] }],
  ['gasto-detalle--sin-descripcion', 'gasto-detalle-sin-descripcion.html'],
  ['gasto-detalle--descripcion-larga', 'gasto-detalle-descripcion-larga.html'],
  ['gasto-detalle--descripcion-larga-abajo', 'gasto-detalle-descripcion-larga.html', { scroll: 420 }],
  ['gasto-detalle--editado', 'gasto-detalle-editado.html'],
  ['gasto-detalle--no-existe', 'gasto-detalle-no-existe.html'],
  ['gasto-detalle--cargando', 'gasto-detalle-cargando.html'],
  ['gasto-detalle--320', 'gasto-detalle.html', { w: 320 }],
  ['gasto-detalle--larga-320', 'gasto-detalle-descripcion-larga.html', { w: 320 }],

  // ---- el mes ----
  ['finanzas-mes', 'finanzas-mes.html'],
  ['finanzas-mes--frontera', 'finanzas-mes.html', { scroll: 430 }],
  ['finanzas-mes--categoria-hover', 'finanzas-mes.html', { force: '.brk--tap li:nth-child(2) .catrow', pseudo: ['hover'] }],
  ['finanzas-mes--categoria-foco', 'finanzas-mes.html', { force: '.brk--tap li:nth-child(2) .catrow', pseudo: ['focus', 'focus-visible'] }],
  ['finanzas-mes--categoria-pulsada', 'finanzas-mes.html', { force: '.brk--tap li:nth-child(2) .catrow', pseudo: ['hover', 'active'] }],
  ['finanzas-mes--mes-siguiente-inerte', 'finanzas-mes.html',
    { force: '.monthnav .arrow.is-disabled', pseudo: ['hover'], expectNoChange: true }],
  ['finanzas-mes--categoria', 'finanzas-mes-categoria.html'],
  ['finanzas-mes--categoria-abajo', 'finanzas-mes-categoria.html', { scroll: 480 }],
  ['finanzas-mes--cerrar-hover', 'finanzas-mes-categoria.html', { force: '.opened .cerrar', pseudo: ['hover'] }],
  ['finanzas-mes--cerrar-foco', 'finanzas-mes-categoria.html', { force: '.opened .cerrar', pseudo: ['focus', 'focus-visible'] }],
  ['finanzas-mes--cerrar-pulsado', 'finanzas-mes-categoria.html', { force: '.opened .cerrar', pseudo: ['hover', 'active'] }],
  ['finanzas-mes--categoria-vacia', 'finanzas-mes-categoria-vacia.html'],
  ['finanzas-mes--categoria-320', 'finanzas-mes-categoria.html', { w: 320 }],
  ['finanzas-mes--320', 'finanzas-mes.html', { w: 320 }],
]

const AUDIT = [
  'historial.html',
  'historial-completo.html',
  'historial-ver-mas-en-curso.html',
  'historial-vacio.html',
  'historial-sin-servidor.html',
  'gasto-detalle.html',
  'gasto-detalle-sin-descripcion.html',
  'gasto-detalle-descripcion-larga.html',
  'gasto-detalle-editado.html',
  'gasto-detalle-no-existe.html',
  'finanzas-mes.html',
  'finanzas-mes-categoria.html',
  'finanzas-mes-categoria-vacia.html',
]

const md5 = (b) => createHash('md5').update(b).digest('hex')

async function capture(browser, file, { w = W, scroll = 0, force, pseudo } = {}) {
  const url = 'file://' + join(MOCK, file) + (scroll ? `?scroll=${scroll}` : '')
  const { targetId, sessionId, send } = await newPage(browser, 'about:blank')
  await send('Emulation.setDeviceMetricsOverride', {
    width: w, height: H, deviceScaleFactor: 2, mobile: true,
  })
  const loaded = waitForLoad(browser, sessionId)
  await send('Page.navigate', { url })
  await loaded
  await sleep(140)
  let forced = null
  if (force) forced = await forcePseudo(send, force, pseudo)
  await sleep(120)
  const { data } = await send('Page.captureScreenshot', { format: 'png' })
  await browser.send('Target.closeTarget', { targetId })
  return { png: Buffer.from(data, 'base64'), forced }
}

async function auditOne(browser, file, w = W) {
  const url = 'file://' + join(MOCK, file) + '?audit=1'
  const { targetId, sessionId, send } = await newPage(browser, 'about:blank')
  await send('Emulation.setDeviceMetricsOverride', {
    width: w, height: H, deviceScaleFactor: 1, mobile: true,
  })
  const loaded = waitForLoad(browser, sessionId)
  await send('Page.navigate', { url })
  await loaded
  await sleep(160)
  const title = await evaluate(send, 'document.title')
  await browser.send('Target.closeTarget', { targetId })
  return title
}

/** Constraint 29, measured rather than eyeballed. */
async function measureTabs(browser, file, w = W) {
  const url = 'file://' + join(MOCK, file)
  const { targetId, sessionId, send } = await newPage(browser, 'about:blank')
  await send('Emulation.setDeviceMetricsOverride', {
    width: w, height: H, deviceScaleFactor: 1, mobile: true,
  })
  const loaded = waitForLoad(browser, sessionId)
  await send('Page.navigate', { url })
  await loaded
  await sleep(160)
  const out = await evaluate(send, `(() => {
    const strip = document.querySelector('.tabs')
    const tabs = [...strip.querySelectorAll('.tab')]
    const cs = getComputedStyle
    return {
      viewport: innerWidth,
      stripClient: strip.clientWidth,
      stripScroll: strip.scrollWidth,
      docScroll: document.documentElement.scrollWidth,
      overflowX: strip.scrollWidth > strip.clientWidth + 0.5,
      docOverflow: document.documentElement.scrollWidth > innerWidth + 0.5,
      lastRight: Math.round(tabs[tabs.length-1].getBoundingClientRect().right * 10) / 10,
      tabs: tabs.map(t => {
        const r = t.getBoundingClientRect()
        const st = cs(t)
        // The real wrap test: how many line boxes the label's own text occupies.
        // The element's height proves nothing here — .tab has min-height:46px.
        const range = document.createRange()
        range.selectNodeContents(t)
        const rects = [...range.getClientRects()]
        const textW = Math.max(...rects.map(x => x.width))
        return {
          label: t.textContent,
          w: Math.round(r.width * 10) / 10,
          h: Math.round(r.height * 10) / 10,
          textW: Math.round(textW * 10) / 10,
          fontSize: st.fontSize,
          fontWeight: st.fontWeight,
          lineBoxes: rects.length,
          clipped: t.scrollWidth > t.clientWidth + 0.5,
          ellipsis: st.textOverflow,
        }
      }),
    }
  })()`)
  await browser.send('Target.closeTarget', { targetId })
  return out
}

async function main() {
  rmSync(PROFILE, { recursive: true, force: true })
  mkdirSync(SHOTS, { recursive: true })
  const { proc, browser } = await launch({ profileDir: PROFILE })

  // ---- constraint 29, measured ----
  console.log('== constraint 29 — the four-tab strip, measured ==')
  for (const [file, w] of [
    ['historial.html', 390], ['finanzas-mes.html', 390],
    ['historial.html', 360], ['historial.html', 320],
    ['historial-tira-estrecha.html', 320], ['historial-tira-estrecha.html', 390],
  ]) {
    const m = await measureTabs(browser, file, w)
    const sum = m.tabs.reduce((a, t) => a + t.w, 0)
    console.log(`  ${file} @${w}px  strip content=${m.stripScroll}px client=${m.stripClient}px ` +
      `labels=${Math.round(sum * 10) / 10}px lastRight=${m.lastRight}px ` +
      `overflowX=${m.overflowX} docOverflow=${m.docOverflow}`)
    for (const t of m.tabs) {
      console.log(`    "${t.label}" box=${t.w}x${t.h} texto=${t.textW}px  ` +
        `${t.fontSize}/${t.fontWeight}  lineBoxes=${t.lineBoxes} ` +
        `clipped=${t.clipped} textOverflow=${t.ellipsis}`)
    }
  }

  // ---- the matrix ----
  console.log('\n== screenshot matrix ==')
  const defaults = new Map()
  const problems = []
  for (const [name, file, opts = {}] of MATRIX) {
    const { png, forced } = await capture(browser, file, opts)
    const path = join(SHOTS, `${name}.png`)
    writeFileSync(path, png)
    const h = md5(png)
    const key = `${file}|${opts.w ?? W}|${opts.scroll ?? 0}`
    if (!opts.force) {
      if (!defaults.has(key)) defaults.set(key, h)
    } else {
      if (forced === null) problems.push(`${name}: forcePseudoState did not bind`)
      const base = defaults.get(key)
      const same = Boolean(base) && base === h
      if (opts.expectNoChange) {
        // A disabled control that lights up on hover is the defect here, so
        // "identical to the default" is the assertion, not the failure.
        if (!same) problems.push(`${name}: se esperaba SIN CAMBIO y cambió`)
      } else if (same) {
        problems.push(`${name}: ESTADO-PERDIDO — byte-identical to its default`)
      }
    }
    console.log(`  ${png.length.toString().padStart(7)}B  ${name}.png`)
  }

  // ---- the audit harness: contrast, 44x44, horizontal overflow ----
  console.log('\n== audit (contrast / touch targets / overflow) ==')
  for (const f of AUDIT) {
    for (const w of [390, 320]) {
      const t = await auditOne(browser, f, w)
      const clean = /^AUDIT h=0 t=0 c=0$/.test(t)
      if (!clean) problems.push(`${f} @${w}: ${t}`)
      console.log(`  @${w} ${clean ? 'ok  ' : 'FAIL'} ${f}${clean ? '' : '  ' + t}`)
    }
  }

  console.log('\n== problems ==')
  console.log(problems.length ? problems.map((p) => '  ! ' + p).join('\n') : '  none')

  await browser.send('Browser.close').catch(() => {})
  await sleep(300)
  proc.kill()
  rmSync(PROFILE, { recursive: true, force: true })
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
