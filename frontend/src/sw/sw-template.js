/*
 * Autonom-OS shell service worker (KD-13). Generated at build time by the
 * `autonomos-shell-sw` plugin in vite.config.ts — the precache list and the
 * cache name come from the real build output, so they cannot drift.
 *
 * Its scope is deliberately narrow, and these three lines are the whole policy:
 *   1. Precache the built shell ONLY: index.html, hashed JS/CSS, the self-hosted
 *      font, the manifest and the icons.
 *   2. `/api/*` is NetworkOnly. No API response is cached, served stale, or
 *      replayed — a stale total is worse than no total in a ledger.
 *   3. No background sync, no write queue, no offline mutation. A capture
 *      attempted while unreachable fails and keeps the text on screen (13.5).
 */

const VERSION = __VERSION__
const PRECACHE = __PRECACHE__

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(VERSION)
      .then((cache) => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting()),
  )
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((names) => Promise.all(names.filter((n) => n !== VERSION).map((n) => caches.delete(n))))
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (event) => {
  const request = event.request
  if (request.method !== 'GET') return

  const url = new URL(request.url)
  if (url.origin !== self.location.origin) return

  // NetworkOnly, and not even a cache lookup on the way past.
  if (url.pathname.startsWith('/api/')) return

  // A navigation is answered from the cached shell when the network is gone, so
  // the app can render its own "no puedo alcanzar tu servidor" state instead of
  // the browser's network error page. This is 13.2's primary case.
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(() =>
        caches.match('/index.html', { cacheName: VERSION }).then(
          (hit) =>
            hit ??
            new Response('', { status: 504, statusText: 'sin servidor' }),
        ),
      ),
    )
    return
  }

  event.respondWith(
    caches.match(request, { cacheName: VERSION }).then((hit) => hit ?? fetch(request)),
  )
})
