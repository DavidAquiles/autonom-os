import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { App } from './App'
import './styles/tokens.css'
import './styles/base.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // One user, one device, a server on his own PC: a short retry keeps a
      // suspended-PC blip from becoming an error screen, and a long one would
      // just delay the honest "cannot reach your server" state (13.2).
      retry: 1,
      refetchOnWindowFocus: true,
      staleTime: 2_000,
    },
    mutations: { retry: 0 },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)

// KD-13: a shell-only service worker, so 13.2's most common real case — tapping
// the home-screen icon while the PC is suspended — renders this app's own
// Spanish error state instead of the browser's network error page.
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    void navigator.serviceWorker.register('/sw.js')
  })
}
