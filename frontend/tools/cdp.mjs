/*
 * A very small Chrome DevTools Protocol client. It exists so the screenshot
 * matrix can force :hover, :focus-visible and :active on the REAL components —
 * the states no static render shows, and where the previous pilot's only escaped
 * constraint violation lived.
 *
 * Node's global WebSocket is used; there is no dependency to install.
 */
import { spawn } from 'node:child_process'
import { setTimeout as sleep } from 'node:timers/promises'

const CHROMIUM = '/usr/bin/chromium-browser'

export async function launch({ port = 9222, profileDir, fakeMedia = false } = {}) {
  const args = [
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${profileDir}`,
    '--no-first-run',
    '--no-default-browser-check',
  ]
  if (fakeMedia) {
    args.push('--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream')
  }
  const proc = spawn(CHROMIUM, args, { stdio: 'ignore' })

  let version
  for (let i = 0; i < 100; i++) {
    try {
      version = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json()
      break
    } catch {
      await sleep(150)
    }
  }
  if (!version) throw new Error('chromium did not expose a debugging port')

  const browser = await connect(version.webSocketDebuggerUrl)
  return { proc, browser, port }
}

function connect(url) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(url)
    const pending = new Map()
    const listeners = new Map()
    let nextId = 1

    ws.onopen = () =>
      resolve({
        send(method, params = {}, sessionId) {
          const id = nextId++
          const msg = JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) })
          return new Promise((res, rej) => {
            pending.set(id, { res, rej })
            ws.send(msg)
          })
        },
        on(event, fn) {
          const list = listeners.get(event) ?? []
          list.push(fn)
          listeners.set(event, list)
        },
        off(event, fn) {
          listeners.set(event, (listeners.get(event) ?? []).filter((f) => f !== fn))
        },
        close: () => ws.close(),
      })

    ws.onerror = reject
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data)
      if (msg.id && pending.has(msg.id)) {
        const { res, rej } = pending.get(msg.id)
        pending.delete(msg.id)
        if (msg.error) rej(new Error(`${msg.error.message} (${JSON.stringify(msg.error.data ?? '')})`))
        else res(msg.result)
      } else if (msg.method) {
        for (const fn of listeners.get(msg.method) ?? []) fn(msg.params, msg.sessionId)
      }
    }
  })
}

export async function newPage(browser, url = 'about:blank') {
  const { targetId } = await browser.send('Target.createTarget', { url })
  const { sessionId } = await browser.send('Target.attachToTarget', { targetId, flatten: true })
  const send = (method, params) => browser.send(method, params, sessionId)
  await send('Page.enable')
  await send('Runtime.enable')
  await send('DOM.enable')
  await send('CSS.enable')
  await send('Network.enable')
  return { targetId, sessionId, send }
}

export async function waitForLoad(browser, sessionId, timeout = 15000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      browser.off('Page.loadEventFired', handler)
      reject(new Error('load timed out'))
    }, timeout)
    const handler = (_p, sid) => {
      if (sid !== sessionId) return
      clearTimeout(timer)
      browser.off('Page.loadEventFired', handler)
      resolve()
    }
    browser.on('Page.loadEventFired', handler)
  })
}

export async function evaluate(send, expression, awaitPromise = false) {
  const { result, exceptionDetails } = await send('Runtime.evaluate', {
    expression,
    returnByValue: true,
    awaitPromise,
  })
  if (exceptionDetails) throw new Error(exceptionDetails.exception?.description ?? 'eval failed')
  return result.value
}

/** Force a real pseudo-class on a real element — no mirrored helper classes. */
export async function forcePseudo(send, selector, pseudos) {
  const { root } = await send('DOM.getDocument', { depth: -1, pierce: true })
  const { nodeId } = await send('DOM.querySelector', { nodeId: root.nodeId, selector })
  if (!nodeId) throw new Error(`no element for ${selector}`)
  await send('CSS.forcePseudoState', { nodeId, forcedPseudoClasses: pseudos })
  return nodeId
}

export { sleep }
