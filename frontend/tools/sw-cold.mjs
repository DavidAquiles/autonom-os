import { dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
const HERE = dirname(fileURLToPath(import.meta.url))
import { launch, newPage, waitForLoad, evaluate, sleep } from './cdp.mjs'
import { writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
const { browser, proc } = await launch({ port: 9252, profileDir: resolve(HERE, 'out/swprofile') })
const p = await newPage(browser)
await p.send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true })
const load = waitForLoad(browser, p.sessionId)
await p.send('Page.navigate', { url: 'http://127.0.0.1:8001/finanzas' })
await load.catch(() => console.log('(no load event)'))
await sleep(4500)
console.log('--- cold open, server stopped ---')
console.log(await evaluate(p.send, `document.body.innerText.slice(0,220)`))
const { data } = await p.send('Page.captureScreenshot', { format: 'png' })
await writeFile(resolve(HERE, 'shots/sin-servidor-arranque-en-frio.png'), Buffer.from(data, 'base64'))
browser.close(); proc.kill(); process.exit(0)
