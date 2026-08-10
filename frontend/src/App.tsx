import { Link, Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { useHealth } from './api/queries'
import { AppBar, Screen, Tabs } from './components/shell/Screen'
import { Banner, panelStyles as panel } from './components/ui/Panel'
import { VoiceProvider, useVoice } from './voice/VoiceContext'
import { VoiceScreen } from './voice/VoiceScreen'
import { Hoy } from './routes/finanzas/Hoy'
import { Mes } from './routes/finanzas/Mes'
import { Historial } from './routes/finanzas/Historial'
import { GastoDetalle } from './routes/finanzas/GastoDetalle'
import { Analisis } from './routes/finanzas/Analisis'
import { Ajustes, EditarNombre } from './routes/finanzas/Ajustes'
import { EditarGasto, NuevoGasto } from './routes/finanzas/GastoForm'
import { DiarioPorFecha, DiarioTodo } from './routes/diario/Diario'
import { EntradaEscribir, EntradaLeer } from './routes/diario/Entrada'
import { Gimnasio } from './routes/Gimnasio'
import { SinServidor } from './routes/SinServidor'
import { ajustes, nav, servidor, tabs } from './copy/es'

export function App() {
  return (
    <VoiceProvider>
      <Shell />
    </VoiceProvider>
  )
}

function Shell() {
  const voice = useVoice()
  const health = useHealth()

  // 13.2: reaching nothing at all, on a cold open, is a designed screen — the
  // service worker cached the shell so this can render without the server.
  const neverReached = health.isError && health.data === undefined
  if (neverReached) return <SinServidor />

  // Voice takes over the content area of whatever module the user is in. The
  // bottom navigation stays put (constraint 11), because VoiceScreen is a Screen.
  if (voice.phase.kind !== 'idle') return <VoiceScreen />

  return (
    <Routes>
      <Route path="/" element={<Navigate to="/finanzas" replace />} />

      <Route element={<FinanzasTabs />}>
        <Route path="/finanzas" element={<Hoy />} />
        <Route path="/finanzas/mes" element={<Mes />} />
        <Route path="/finanzas/historial" element={<Historial />} />
        <Route path="/finanzas/analisis" element={<Analisis />} />
      </Route>

      <Route path="/finanzas/ajustes" element={<Ajustes />} />
      <Route path="/finanzas/ajustes/:kind/:id" element={<EditarNombre />} />
      <Route path="/finanzas/gasto/nuevo" element={<NuevoGasto />} />
      {/* KD-23 / B1: the detail takes the existing route and the form moves
          under it, mirroring /diario/:id and /diario/:id/editar (A25). Every
          list already links to /finanzas/gasto/:id, so no row changes. */}
      <Route path="/finanzas/gasto/:id" element={<GastoDetalle />} />
      <Route path="/finanzas/gasto/:id/editar" element={<EditarGasto />} />

      <Route element={<DiarioTabs />}>
        <Route path="/diario" element={<DiarioTodo />} />
        <Route path="/diario/fecha" element={<DiarioPorFecha />} />
      </Route>

      <Route path="/diario/nueva" element={<EntradaEscribir mode="nueva" />} />
      <Route path="/diario/:id" element={<EntradaLeer />} />
      <Route path="/diario/:id/editar" element={<EntradaEscribir mode="editar" />} />

      <Route path="/gimnasio" element={<Gimnasio />} />
      <Route path="/sin-servidor" element={<SinServidor />} />

      <Route path="*" element={<Navigate to="/finanzas" replace />} />
    </Routes>
  )
}

/**
 * Análisis is the third tab inside Finanzas, not a fourth destination — 1.1
 * requires exactly three, and constraint 11 requires those three from every
 * screen, so the insights area cannot be one.
 */
function FinanzasTabs() {
  return (
    <Screen
      header={
        <>
          <AppBar module={nav.finanzas} action={{ label: ajustes.titulo, to: '/finanzas/ajustes' }} />
          <Tabs
            items={[
              // A23 / 16.1: the three views of the record sit together and
              // Análisis, which is derived rather than recorded, stays last.
              // Constraint 29: all four legible at 390 px, measured not
              // eyeballed — 278.7 px of labels with 70.3 px of slack.
              { label: tabs.hoy, to: '/finanzas', end: true },
              { label: tabs.mes, to: '/finanzas/mes' },
              { label: tabs.historial, to: '/finanzas/historial' },
              { label: tabs.analisis, to: '/finanzas/analisis' },
            ]}
          />
        </>
      }
      capture="finanzas"
      active="finanzas"
    >
      <ReachabilityBanner />
      <Outlet />
    </Screen>
  )
}

/** 11.9 makes journal questions first-class, so Diario reaches the same route. */
function DiarioTabs() {
  return (
    <Screen
      header={
        <>
          <AppBar module={nav.diario} action={{ label: tabs.analisis, to: '/finanzas/analisis' }} />
          <Tabs
            items={[
              { label: tabs.todo, to: '/diario', end: true },
              { label: tabs.porFecha, to: '/diario/fecha' },
            ]}
          />
        </>
      }
      capture="diario"
      active="diario"
    >
      <ReachabilityBanner />
      <Outlet />
    </Screen>
  )
}

/**
 * 13.2 with the app already open, and 13.3: it recovers on its own — the health
 * query keeps polling and the banner disappears when the server answers again.
 */
function ReachabilityBanner() {
  const health = useHealth()
  if (!health.isError) return null
  return (
    <Banner
      title={servidor.bannerTitulo}
      detail={servidor.bannerCuerpo}
      action={
        <Link className={panel.action} to="/sin-servidor">
          {servidor.verQueHacer}
        </Link>
      }
    />
  )
}
