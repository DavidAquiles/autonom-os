import { dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
const HERE = dirname(fileURLToPath(import.meta.url))
import { launch, newPage, waitForLoad, evaluate, sleep } from './cdp.mjs'
import { resolve } from 'node:path'
const { browser, proc } = await launch({ port: 9251, profileDir: resolve(HERE, 'out/swprofile') })
const p = await newPage(browser)
await p.send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true })
const load = waitForLoad(browser, p.sessionId)
await p.send('Page.navigate', { url: 'http://127.0.0.1:8001/finanzas' })
await load
await sleep(3500)
console.log('sw controlling:', await evaluate(p.send, `!!navigator.serviceWorker.controller`))
console.log('cached entries:', await evaluate(p.send, `caches.keys().then(k=>caches.open(k[0])).then(c=>c.keys()).then(r=>r.length)`, true))
console.log('cache name:', await evaluate(p.send, `caches.keys().then(k=>k.join(','))`, true))
browser.close(); proc.kill(); process.exit(0)
