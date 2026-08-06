import { defineConfig } from 'vitest/config'
import type { Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import { readFileSync, writeFileSync, readdirSync } from 'node:fs'
import { resolve } from 'node:path'

/**
 * KD-13: a shell-only service worker. The precache list is generated from the
 * real build output so it can never drift from the hashed filenames, and the
 * cache name is keyed to a hash of that list so a new build takes effect on the
 * next open. `/api/*` is NetworkOnly — no API response is cached, ever.
 */
function shellServiceWorker(): Plugin {
  return {
    name: 'autonomos-shell-sw',
    apply: 'build',
    closeBundle() {
      const dist = resolve(__dirname, 'dist')
      const assetDir = resolve(dist, 'assets')
      const assets = readdirSync(assetDir).map((f) => `/assets/${f}`)
      const shell = [
        '/',
        '/index.html',
        '/manifest.webmanifest',
        '/icon-192.png',
        '/icon-512.png',
        ...assets,
      ]
      // Cheap, deterministic build key: length + a rolling hash of the list.
      let h = 0
      for (const s of shell.join('|')) h = (h * 31 + s.charCodeAt(0)) | 0
      const version = `autonomos-shell-${(h >>> 0).toString(36)}`
      const template = readFileSync(resolve(__dirname, 'src/sw/sw-template.js'), 'utf8')
      const sw = template
        .replace('__PRECACHE__', JSON.stringify(shell, null, 2))
        .replace('__VERSION__', JSON.stringify(version))
      writeFileSync(resolve(dist, 'sw.js'), sw, 'utf8')
    },
  }
}

export default defineConfig({
  plugins: [react(), shellServiceWorker()],
  // KD-2: the bundle contains no origin and no port. Every request is relative.
  base: '/',
  build: {
    manifest: true,
    assetsInlineLimit: 0,
  },
  server: {
    port: 5173,
    proxy: {
      // Dev only. Port 8001 because 8000 is permanently held by an unrelated
      // container on this host. Nothing about this reaches the built bundle.
      '/api': { target: 'http://127.0.0.1:8001', changeOrigin: false },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: false,
  },
})
