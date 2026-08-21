import { createContext, useContext, useState } from 'react'
import { BrowserRouter, Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { AdminDashboardPage, AdminJsonPage, AdminModelsPage, AdminPlaceholder, AdminShell, AdminUsersPage } from './pages/AdminPage'
import { AccountPage, ComingSoonPage, ProfilePage, SignupPage, SubscriptionPage, UsagePage } from './pages/AccountPages'
import { AuthProvider, useAuth } from './lib/auth'
import { DeskShell } from './layout/DeskShell'
import { MarketingNav } from './layout/MarketingNav'
import { LoginPage } from './components/UserMenu'
import { Landing } from './pages/Landing'
import { Desk } from './pages/Desk'
import { Games } from './pages/Games'
import { Ask } from './pages/Ask'
import { ModelDetailPage } from './pages/ModelDetailPage'
import { ModelsPage } from './pages/ModelsPage'
import { ResearchPage } from './pages/ResearchPage'
import { BacktestsPage } from './pages/BacktestsPage'
import { MatchupPage } from './pages/MatchupPage'
import { MarketsPage, PricingPage, Settings, Teams } from './pages/ProductPages'

type LeagueFilter = 'All' | 'NFL' | 'CFB'

const LeagueCtx = createContext<{
  league: LeagueFilter
  setLeague: (v: LeagueFilter) => void
}>({ league: 'All', setLeague: () => undefined })

export function useDeskLeague() {
  return useContext(LeagueCtx)
}

function MarketingLayout() {
  return (
    <>
      <MarketingNav />
      <Outlet />
    </>
  )
}

function RequireAuth({ admin = false }: { admin?: boolean }) {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) {
    return <div className="desk-main muted" style={{ padding: 48 }}>Loading…</div>
  }
  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }
  if (admin && user.role !== 'ADMIN') {
    return <Navigate to="/desk" replace />
  }
  return <Outlet />
}

function DeskLayout() {
  const [league, setLeague] = useState<LeagueFilter>('All')
  const location = useLocation()
  const hideAskCta = location.pathname.startsWith('/ask')
  return (
    <LeagueCtx.Provider value={{ league, setLeague }}>
      <DeskShell league={league} onLeague={setLeague} status="NFL data live · Ridge in development" hideAskCta={hideAskCta}>
        <Outlet />
      </DeskShell>
    </LeagueCtx.Provider>
  )
}

function DeskPage() {
  const { league, setLeague } = useDeskLeague()
  return <Desk league={league} onLeague={setLeague} />
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route element={<MarketingLayout />}>
            <Route path="/" element={<Landing />} />
          </Route>
          <Route element={<RequireAuth />}>
            <Route element={<DeskLayout />}>
              <Route path="/desk" element={<DeskPage />} />
              <Route path="/games" element={<Games />} />
              <Route path="/games/:gameId" element={<MatchupPage />} />
              <Route path="/ask" element={<Ask />} />
              <Route path="/models" element={<ModelsPage />} />
              <Route path="/models/:modelId" element={<ModelDetailPage />} />
              <Route path="/markets" element={<MarketsPage />} />
              <Route path="/teams" element={<Teams />} />
              <Route path="/backtests" element={<BacktestsPage />} />
              <Route path="/research" element={<ResearchPage />} />
              <Route path="/pricing" element={<PricingPage embedded />} />
              <Route path="/pricing/coming-soon" element={<ComingSoonPage />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/account" element={<AccountPage />} />
              <Route path="/subscription" element={<SubscriptionPage />} />
              <Route path="/usage" element={<UsagePage />} />
            </Route>
            <Route element={<RequireAuth admin />}>
              <Route element={<AdminShell />}>
                <Route path="/admin" element={<AdminDashboardPage />} />
                <Route path="/admin/health" element={<AdminJsonPage title="System health" path="health" />} />
                <Route path="/admin/pipeline" element={<AdminJsonPage title="Data pipeline" path="pipeline" />} />
                <Route path="/admin/models" element={<AdminModelsPage />} />
                <Route path="/admin/users" element={<AdminUsersPage />} />
                <Route path="/admin/logs" element={<AdminJsonPage title="Application logs" path="logs" />} />
                <Route path="/admin/experiments" element={<AdminJsonPage title="Experiments" path="experiments" />} />
                <Route path="/admin/predictions" element={<AdminJsonPage title="Predictions" path="predictions" />} />
                <Route path="/admin/subscriptions" element={<AdminPlaceholder title="Subscriptions" />} />
                <Route path="/admin/jobs" element={<AdminPlaceholder title="Jobs" />} />
                <Route path="/admin/costs" element={<AdminPlaceholder title="AWS costs" />} />
              </Route>
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
