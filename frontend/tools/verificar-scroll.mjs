/*
 * Ad-hoc verification of R1 / criterion 17.8 — "the same position in the list".
 * Not part of the matrix; run by hand:
 *     node tools/verificar-scroll.mjs [baseURL]
 *
 * R1 says this is the single most likely criterion to be quietly failed,
 * because all three lists look correct in any manual test that does not scroll
 * first. So: scroll, leave, come back, and read the offset off the real
 * container (<main>, not the document — that is the whole point).
 */
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { rm } from 'node:fs/promises'

process.on('unhandledRejection', () => {})
import { launch, newPage, waitForLoad, evaluate, sleep } from './cdp.mjs'

const HERE = dirname(fileURLToPath(import.meta.url))
const BASE = process.argv[2] ?? 'http://127.0.0.1:8011'
let profileSeq = 0
const profileDir = () => resolve(HERE, 'out', `chrome-profile-scroll-${profileSeq++}`)

const top = (send) =>
  evaluate(send, `document.querySelector('main').scrollTop`)

async function check(browser, { name, url }) {
  const { sessionId, send } = await newPage(browser)
  await send('Emulation.setDeviceMetricsOverride', {
    width: 390,
    height: 844,
    deviceScaleFactor: 1,
    mobile: true,
  })
  const load = waitForLoad(browser, sessionId)
  await send('Page.navigate', { url: BASE + url })
  await load
  for (let i = 0; i < 40 && !(await evaluate(send, `!!document.querySelector('main')`)); i++) await sleep(100)
  await sleep(1400)

  // Scroll as far as this list actually allows, so a short list is reported as
  // "cannot scroll" rather than passing vacuously at offset 0.
  const room = await evaluate(
    send,
    `(() => { const m = document.querySelector('main'); return m.scrollHeight - m.clientHeight })()`,
  )
  const goal = Math.min(420, room)
  await evaluate(send, `document.querySelector('main').scrollTop = ${goal}`)
  await sleep(350)
  const before = await top(send)

  // A list with nothing in it cannot answer the question. Say so, rather than
  // failing in a way that looks like the app is broken: Hoy is empty on a day
  // with no expenses, and the filtered list is empty for an untouched category.
  const rows = await evaluate(
    send,
    `[...document.querySelectorAll('a')].filter((x) => /^\\/finanzas\\/gasto\\/\\d+$/.test(x.getAttribute('href') || '')).length`,
  )
  if (rows === 0 || room === 0) {
    console.log(
      `SKIP ${name.padEnd(18)} nothing to test here — ${rows} filas, ${room}px de recorrido`,
    )
    return true
  }

  const opened = await evaluate(
    send,
    `(() => {
      const a = [...document.querySelectorAll('a')]
        .find((x) => /^\\/finanzas\\/gasto\\/\\d+$/.test(x.getAttribute('href') || ''))
      if (!a) return false
      a.click()
      return true
    })()`,
  )
  await sleep(900)
  const onDetail = await evaluate(
    send,
    `!!document.body.textContent.includes('Editar gasto')`,
  )

  await evaluate(send, `history.back()`)
  await sleep(1400)
  const after = await top(send)

  const ok = opened && onDetail && before > 0 && Math.abs(after - before) <= 2
  const verdict = before === 0 ? 'SKIP' : ok ? 'OK  ' : 'FAIL'
  console.log(
    `${verdict} ${name.padEnd(18)} room=${room} left at ${before} · detail=${onDetail} · returned at ${after}`,
  )
  return verdict !== 'FAIL'
}

let allOk = true
let port = 9333
for (const c of [
  { name: 'Historial', url: '/finanzas/historial' },
  { name: 'Hoy', url: '/finanzas' },
  { name: 'mes + categoría', url: '/finanzas/mes?categoria=2' },
]) {
  // One browser per case. Sharing one and closing targets between cases made
  // the shared CDP socket reject a pending command, which killed the run and
  // said nothing about the app.
  // A REUSED profile serves a cached index.html pointing at the previous
  // hashed bundle, which once made an already-fixed build look broken. Each
  // case gets its own fresh profile directory.
  const dir = profileDir()
  const { proc, browser } = await launch({ port: port++, profileDir: dir })
  try {
    allOk = (await check(browser, c)) && allOk
  } catch (e) {
    console.log(`ERR  ${c.name.padEnd(18)} ${e.message}`)
    allOk = false
  } finally {
    // SIGTERM rather than Browser.close: closing the browser rejects every
    // still-pending CDP command, and one of those rejections is not awaited
    // anywhere, which killed this run with an error about the browser rather
    // than about the app. Nothing here depends on a clean shutdown.
    proc.kill()
    await sleep(400)
    await rm(dir, { recursive: true, force: true }).catch(() => {})
  }
}
process.exit(allOk ? 0 : 1)
