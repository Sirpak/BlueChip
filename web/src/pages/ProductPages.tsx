import { Link } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { UpgradeCard } from '../components/Locked'
import { Hint } from '../components/Hint'
import { can } from '../lib/entitlements'

export { Teams } from './TeamsPage'

export function MarketsPage() {
  const { user } = useAuth()
  if (!can(user, 'markets')) {
    return (
      <>
        <div className="page-h">
          <h1>Markets</h1>
        </div>
        <UpgradeCard title="Markets" plan="Pro">
          De-vig, break-even, and Stern conversion are a Pro feature.
        </UpgradeCard>
      </>
    )
  }
  return (
    <>
      <div className="page-h">
        <div>
          <h1>Markets</h1>
          <p className="muted">How BlueChip compares model chances to sportsbook prices — explained for fans.</p>
        </div>
      </div>
      <section className="card">
        <p>
          Stage 1 engine: <Hint t="american-odds">American odds</Hint> → <Hint t="break-even">break-even</Hint>,{' '}
          <Hint t="no-vig">de-vig</Hint>, and <Hint t="stern">Stern</Hint> cover chance with NFL σ ≈ 13.5. Interactive
          quote desk at <a href="/legacy/markets">/legacy/markets</a>. Full glossary:{' '}
          <Link to="/about">About</Link>.
        </p>
        <p className="muted">
          Negative home <Hint t="spread">spread</Hint> = home favored. <Hint t="edge">Edge</Hint> = model p − no-vig p —
          also report vs priced break-even at −110 (52.38%).
        </p>
        <a className="btn btn-primary" href="/legacy/markets">
          Open conversion engine
        </a>
      </section>
    </>
  )
}

export function Settings() {
  const { user } = useAuth()
  return (
    <>
      <div className="page-h">
        <h1>Settings</h1>
      </div>
      <section className="card" id="profile">
        <h2>Profile</h2>
        <p>
          {user?.username} · {user?.role}
        </p>
        <p className="muted">{user?.email}</p>
      </section>
      <section className="card" id="account">
        <h2>Account</h2>
        <p className="muted">Password reset and email verification ship with Cognito.</p>
      </section>
      <section className="card" id="usage">
        <h2>Usage</h2>
        <p className="muted">Ask BlueChip meter and exports ship with Product. Stripe is not wired yet.</p>
      </section>
    </>
  )
}

export function PricingPage({ embedded = false }: { embedded?: boolean }) {
  const { user } = useAuth()
  const plan = user?.plan ?? 'FREE'
  const cta = (id: 'FREE' | 'PRO' | 'RESEARCH') => {
    if (plan === id || (plan === 'INTERNAL' && id === 'RESEARCH')) return 'Current Plan'
    if (plan === 'RESEARCH' || plan === 'INTERNAL') return id === 'FREE' || id === 'PRO' ? 'Included' : 'Current Plan'
    if (plan === 'PRO' && id === 'FREE') return 'Included'
    if (id === 'PRO') return 'Upgrade to Pro'
    if (id === 'RESEARCH') return 'Upgrade to Research'
    return 'Select'
  }
  return (
    <div className={embedded ? 'pricing pricing-embedded' : 'pricing'}>
      {!embedded && (
        <>
          <h1 style={{ fontSize: 36, fontWeight: 700, letterSpacing: '-0.03em', marginBottom: 8 }}>
            Football intelligence, metered as research
          </h1>
          <p className="muted">Credits internally. Never GPT tokens. ChatGPT/MCP is a later client.</p>
        </>
      )}
      {embedded && (
        <div className="page-h" style={{ marginBottom: 0 }}>
          <div>
            <h1>Pricing</h1>
            <p className="muted">Plans for games, models, research, and Ask BlueChip.</p>
          </div>
        </div>
      )}
      <div className="price-grid">
        <article className="price-card">
          <h2>Free</h2>
          <div className="amt">$0</div>
          <ul>
            <li>Games and schedules</li>
            <li>Basic statistics</li>
            <li>Limited model results</li>
            <li>10 Ask BlueChip queries / month</li>
          </ul>
          <Link className="btn" to={cta('FREE') === 'Current Plan' ? '/usage' : '/pricing/coming-soon'}>
            {cta('FREE')}
          </Link>
        </article>
        <article className="price-card featured-plan">
          <h2>Pro</h2>
          <div className="amt">$14.99<span>/mo</span></div>
          <ul>
            <li>NFL + CFB</li>
            <li>Full model outputs</li>
            <li>Model comparison</li>
            <li>Markets</li>
            <li>Ask BlueChip</li>
            <li>Research library</li>
            <li>Historical search with citations</li>
          </ul>
          <Link className="btn btn-primary" to={cta('PRO') === 'Current Plan' ? '/subscription' : '/pricing/coming-soon'}>
            {cta('PRO')}
          </Link>
        </article>
        <article className="price-card">
          <h2>Research</h2>
          <div className="amt">$29.99<span>/mo</span></div>
          <ul>
            <li>Everything in Pro</li>
            <li>Advanced backtests</li>
            <li>Deeper model analysis</li>
            <li>Export</li>
            <li>Larger AI allowance</li>
            <li>API access</li>
          </ul>
          <Link className="btn" to={cta('RESEARCH') === 'Current Plan' ? '/subscription' : '/pricing/coming-soon'}>
            {cta('RESEARCH')}
          </Link>
        </article>
      </div>

      <section className="card dev-access">
        <h2>Developer access / API</h2>
        <p className="muted">
          OpenAPI docs at <a href="/docs">/docs</a>. Programmatic access is a Research-tier feature — not a primary nav
          item for ordinary users.
        </p>
        <ul className="detail-list">
          <li>
            <code>GET /api/dashboard</code> — slate summary
          </li>
          <li>
            <code>POST /api/markets/price</code> — Stern / de-vig calculator
          </li>
          <li>
            <code>GET /games/upcoming</code> — ESPN window games
          </li>
        </ul>
        <p className="muted">Versioned model μ on the API ships with BCW-RIDGE-v0.1 production gates.</p>
      </section>
    </div>
  )
}

// Legacy re-exports for any stale imports
export { MarketsPage as MarketsPageLegacy }
// Legacy export for landing imports
export function Pricing() {
  return <PricingPage />
}
