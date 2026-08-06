/* An end-to-end pass through the real UI against the real backend. Development
   tooling: it writes and then removes one expense. */
import { launch, newPage, waitForLoad, evaluate, sleep } from './cdp.mjs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
const HERE = dirname(fileURLToPath(import.meta.url))
const BASE = process.argv[2] ?? 'http://127.0.0.1:8001'

const { browser, proc } = await launch({ port: 9260, profileDir: resolve(HERE, 'out/e2e') })
const p = await newPage(browser)
await p.send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true })

const click = async (label) => {
  const ok = await evaluate(p.send, `(() => {
    const els = [...document.querySelectorAll('button, a, [role="radio"]')]
    const el = els.find(e => e.textContent.trim() === ${JSON.stringify(label)})
    if (!el) return false; el.click(); return true })()`)
  if (!ok) throw new Error(`no control "${label}"`)
  await sleep(400)
}

let load = waitForLoad(browser, p.sessionId)
await p.send('Page.navigate', { url: BASE + '/finanzas' })
await load
await sleep(1200)

const before = await evaluate(p.send, `document.querySelector('main').innerText.split('\\n')[1]`)
console.log('total antes:', before)

await click('Anotar gasto')
await sleep(600)
await evaluate(p.send, `(() => {
  const el = document.querySelector('input[aria-label="Monto"]')
  const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set
  set.call(el, '9 900'); el.dispatchEvent(new Event('input', { bubbles: true })) })()`)
console.log('monto escrito como "9 900" → campo muestra:',
  await evaluate(p.send, `document.querySelector('input[aria-label="Monto"]').value`))
await click('Ocio')
await click('Nequi')
await click('Guardar gasto')
await sleep(1800)

const after = await evaluate(p.send, `document.querySelector('main').innerText.split('\\n').slice(0,4).join(' | ')`)
console.log('tras guardar (sin recargar):', after)

// 3.3 — rename a category and see it on the expense that already used it
load = waitForLoad(browser, p.sessionId)
await p.send('Page.navigate', { url: BASE + '/finanzas/ajustes/categories/6' })
await load
await sleep(1200)
await evaluate(p.send, `(() => {
  const el = document.querySelector('input')
  const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set
  set.call(el, 'Ocio y salidas'); el.dispatchEvent(new Event('input', { bubbles: true })) })()`)
await click('Guardar nombre')
await sleep(1200)
load = waitForLoad(browser, p.sessionId)
await p.send('Page.navigate', { url: BASE + '/finanzas' })
await load
await sleep(1200)
console.log('tras renombrar:', await evaluate(p.send,
  `document.querySelector('main').innerText.split('\\n').slice(0,5).join(' | ')`))

browser.close(); proc.kill(); process.exit(0)
