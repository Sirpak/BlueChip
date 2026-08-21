import { NavLink } from 'react-router-dom'

import type { ReactNode } from 'react'

import { brand } from '../brand'
import { PRODUCT_STATUS } from '../data/catalog'
import { I, Icon } from '../components/Icons'
import { LockMark } from '../components/Locked'
import { UserMenu } from '../components/UserMenu'
import { useAuth } from '../lib/auth'
import { can } from '../lib/entitlements'

type NavItem = { to: string; label: string; d: string; end?: boolean; entitlement?: string; hide?: boolean }

const ITEMS: NavItem[] = [
  { to: '/desk', label: 'Overview', d: I.grid, end: true, entitlement: 'dashboard' },
  { to: '/games', label: 'Games', d: I.calendar, entitlement: 'games' },
  { to: '/ask', label: 'Ask BlueChip', d: I.chat, entitlement: 'ask_bluechip_limited' },
  { to: '/models', label: 'Models', d: I.layers, entitlement: 'models_basic' },
  { to: '/markets', label: 'Markets', d: I.trend, entitlement: 'markets' },
  { to: '/teams', label: 'Teams', d: I.users, entitlement: 'teams_basic' },
  { to: '/backtests', label: 'Backtests', d: I.flask, entitlement: 'backtests_preview' },
  { to: '/research', label: 'Research', d: I.book, entitlement: 'research_preview' },
  { to: '/pricing', label: 'Pricing', d: I.card },
  { to: '/settings', label: 'Settings', d: I.cog },
]

type Props = {
  league: 'All' | 'NFL' | 'CFB'
  onLeague: (v: 'All' | 'NFL' | 'CFB') => void
  status: string
  hideAskCta?: boolean
  children: ReactNode
}

export function DeskShell({ league, onLeague, status, hideAskCta, children }: Props) {
  const { user } = useAuth()
  const items = ITEMS.filter((it) => {
    if (it.hide) return false
    return true
  })

  return (
    <div className="desk">
      <aside className="side">
        <NavLink to="/desk" className="brand" aria-label="BlueChipWager home">
          <img className="brand-icon" src={brand.icon} alt="" width={28} height={28} />
          <strong>BlueChipWager</strong>
        </NavLink>
        <nav>
          {items.map((it) => {
            const locked = Boolean(it.entitlement && !can(user, it.entitlement))
            return (
              <NavLink key={it.to} to={it.to} className={({ isActive }) => (isActive ? 'is-on' : '')} end={it.end}>
                <Icon d={it.d} />
                {it.label}
                {locked ? <LockMark /> : null}
              </NavLink>
            )
          })}
        </nav>
        <footer className="side-foot">
          <strong>{PRODUCT_STATUS.label}</strong>
          <ul>
            {PRODUCT_STATUS.items.map((item) => (
              <li key={item.label} className={item.live ? 'is-live' : ''}>
                <i aria-hidden />
                {item.label}
              </li>
            ))}
          </ul>
        </footer>
      </aside>
      <div>
        <div className="topbar">
          <div className="seg">
            {(['All', 'NFL', 'CFB'] as const).map((v) => (
              <button key={v} className={league === v ? 'is-on' : ''} onClick={() => onLeague(v)} type="button">
                {v}
              </button>
            ))}
          </div>
          <div className="search-wrap" style={{ flex: 1, maxWidth: 320 }}>
            <Icon d={I.search} size={15} />
            <input className="ask-input" placeholder="Search teams, games, papers…" />
          </div>
          <div className="health-dot" title={status}>
            <i />
            v0.1 preview
          </div>
          {!hideAskCta && (
            <NavLink className="btn btn-primary" to="/ask">
              Ask BlueChip
            </NavLink>
          )}
          <UserMenu />
        </div>
        <div className="desk-main">{children}</div>
      </div>
    </div>
  )
}
