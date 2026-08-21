import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { TeamMark } from '../components/Marks'
import { UpgradeCard } from '../components/Locked'
import { comparisonMetrics, fmtMetric } from '../lib/metrics'
import { useAuth } from '../lib/auth'
import { can } from '../lib/entitlements'
import { useSlate } from '../lib/slate'

type Tab = 'overview' | 'models' | 'market' | 'trends'

export function MatchupPage() {
  const { gameId } = useParams()
  const { games } = useSlate()
  const [tab, setTab] = useState<Tab>('overview')
  const decoded = decodeURIComponent(gameId ?? '')
  const g = useMemo(() => games.find((x) => x.game_id === decoded), [games, decoded])

  if (!games.length) {
    return <p className="muted">Loading slate…</p>
  }
  if (!g) {
    return (
      <section className="card">
        <h1>Game not found</h1>
        <p className="muted">This id is not in the current ESPN window.</p>
        <Link className="btn" to="/games">
          Back to Games
        </Link>
      </section>
    )
  }

  const { user } = useAuth()
  const showMu = can(user, 'models_full')
  const metrics = comparisonMetrics(g.game_id)
  const askQ = `Ask BlueChip about ${g.matchup}`

  const tabs: { id: Tab; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'models', label: 'Models' },
    { id: 'market', label: 'Market' },
    { id: 'trends', label: 'Trends' },
  ]

  return (
    <>
      <div className="page-h">
        <div>
          <Link className="muted" to="/games" style={{ fontSize: 13 }}>
            ← Games
          </Link>
          <div className="matchup-head">
            <div className="matchup-logos">
              <TeamMark abbr={g.away_team} league={g.league} />
              <span className="matchup-vs">{g.neutral ? 'vs' : '@'}</span>
              <TeamMark abbr={g.home_team} league={g.league} />
            </div>
            <div>
              <h1 style={{ margin: 0 }}>
                {g.away_team} {g.neutral ? 'vs' : '@'} {g.home_team}
              </h1>
              <p className="muted" style={{ margin: '4px 0 0' }}>
                {g.league} · Week {g.week ?? '—'} · {g.round ?? g.season_type} · {g.away_name} {g.neutral ? 'vs' : '@'} {g.home_name}
              </p>
            </div>
          </div>
        </div>
        <span className="preview-flag">Research Preview · public probability not published</span>
      </div>

      <div className="matchup-tabs" role="tablist">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            className={`matchup-tab ${tab === t.id ? 'is-on' : ''}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {(tab === 'overview' || tab === 'market') && (
        <div className="kpis">
          <article className="kpi">
            <span>Market</span>
            <b>{g.spread_label ?? '—'}</b>
          </article>
          <article className="kpi">
            <span>BCW Research Preview</span>
            <b>{showMu ? 'Snapshot pending' : 'Available with Pro'}</b>
          </article>
          <article className="kpi">
            <span>Public probability</span>
            <b>Not yet published</b>
          </article>
        </div>
      )}

      {tab === 'overview' && (
        <>
          <div className="grid-12">
            <section className="card">
              <h2>Projected margin</h2>
              {showMu ? (
                <p className="muted">
                  BCW-RIDGE-PURE v0.1-candidate is trained on 2009–2022. This ESPN kickoff does not yet have a leakage-safe snapshot, so no μ is shown.
                </p>
              ) : (
                <UpgradeCard title="BCW Projection" plan="Pro">
                  Unlock full analysis on Pro. Cover probability stays unpublished for every plan until calibration gates pass.
                </UpgradeCard>
              )}
            </section>
            <section className="card">
              <h2>Market snapshot</h2>
              <div className="sit" style={{ gridTemplateColumns: '1fr 1fr' }}>
                <div>
                  <strong>Spread</strong>
                  {g.spread_label ?? '—'}
                </div>
                <div>
                  <strong>Total</strong>
                  {g.total_line ?? '—'}
                </div>
                <div>
                  <strong>Book</strong>
                  {g.book ?? 'espn'}
                </div>
                <div>
                  <strong>Kickoff</strong>
                  {g.kickoff ?? '—'}
                </div>
              </div>
            </section>
          </div>

          <section className="card" style={{ marginTop: 12 }}>
            <h2>Head-to-head (snapshot placeholders)</h2>
            <p className="muted">Real EPA/Elo/SRS diffs bind after team pages read BCW-SNAP-v0.1.</p>
            <MetricTable away={g.away_team} home={g.home_team} metrics={metrics} />
          </section>
        </>
      )}

      {tab === 'models' && (
        <section className="card">
          <h2>Model outputs</h2>
          <p className="muted">
            BCW-RIDGE-v0.1 is in development. Elo, SRS, and HFA live on snapshots but are not yet bound to the live slate.
          </p>
          <div className="detail-dl" style={{ marginTop: 16 }}>
            <div>
              <dt>BCW-RIDGE-PURE</dt>
              <dd className="muted">Research Preview candidate · public probability not published</dd>
            </div>
            <div>
              <dt>Cover / win %</dt>
              <dd className="muted">Not yet published</dd>
            </div>
            <div>
              <dt>BCW-ELO / BCW-SRS</dt>
              <dd className="muted">On snapshots · desk binding next</dd>
            </div>
          </div>
          <Link className="btn" to="/models" style={{ marginTop: 16 }}>
            Open Model Lab
          </Link>
        </section>
      )}

      {tab === 'market' && (
        <section className="card">
          <h2>Market vs model</h2>
          <p className="muted">
            No-vig close is the benchmark. Edge = model P(cover) − break-even at −110 (52.38%). Changing a spread only reprices Stern P(cover); it does not retrain.
          </p>
          <div className="sit" style={{ marginTop: 16 }}>
            <div>
              <strong>Spread</strong>
              {g.spread_label ?? '—'}
            </div>
            <div>
              <strong>Total</strong>
              {g.total_line ?? '—'}
            </div>
            <div>
              <strong>Source</strong>
              {g.book ?? 'espn'}
            </div>
            <div>
              <strong>Model cover %</strong>
              Not yet published
            </div>
            <div>
              <strong>Edge</strong>
              —
            </div>
            <div>
              <strong>Why BlueChip?</strong>
              {showMu ? 'Candidate μ after snapshot bind' : '🔒 Pro'}
            </div>
          </div>
          <Link className="btn" to="/markets" style={{ marginTop: 16 }}>
            Markets desk
          </Link>
        </section>
      )}

      {tab === 'trends' && (
        <section className="card">
          <h2>Team trends</h2>
          <p className="muted">
            Season-to-date, last-3, and last-5 rolling stats live in extras_json on BCW-SNAP-v0.1. Weather, injuries, and QB context are out of the v0.1 freeze.
          </p>
          <MetricTable away={g.away_team} home={g.home_team} metrics={metrics} />
          <div className="sit" style={{ marginTop: 16 }}>
            <div>
              <strong>Rest</strong>
              Trailing snapshot later
            </div>
            <div>
              <strong>Weather</strong>
              Out of v0.1 freeze
            </div>
            <div>
              <strong>QB / injuries</strong>
              known_at required
            </div>
            <div>
              <strong>Travel</strong>
              —
            </div>
          </div>
        </section>
      )}

      <div className="ask-sticky">
        <Link className="btn btn-primary" to={`/ask?q=${encodeURIComponent(askQ)}`}>
          Ask BlueChip about this game
        </Link>
      </div>
    </>
  )
}

function MetricTable({
  away,
  home,
  metrics,
}: {
  away: string
  home: string
  metrics: ReturnType<typeof comparisonMetrics>
}) {
  return (
    <div className="metric-list">
      <div className="metric" style={{ fontWeight: 650, color: 'var(--muted)' }}>
        <span>Metric</span>
        <span />
        <span />
        <span style={{ textAlign: 'center' }}>{away}</span>
        <span style={{ textAlign: 'center' }}>{home}</span>
      </div>
      {metrics.map((m) => {
        const homeWins = m.home > m.away
        return (
          <div className="metric" key={m.name}>
            <span>{m.name}</span>
            <span />
            <span />
            <span className={`val ${homeWins ? 'down' : 'up'}`}>{fmtMetric(m, 'away')}</span>
            <span className={`val ${homeWins ? 'up' : 'down'}`}>{fmtMetric(m, 'home')}</span>
          </div>
        )
      })}
    </div>
  )
}
