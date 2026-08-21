import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { TeamMark } from '../components/Marks'
import { Hint, HintLabel } from '../components/Hint'
import { MatchupNews } from '../components/MatchupNews'
import { GameIntelligenceBrief } from '../components/GameIntelligenceBrief'
import { WeeklyDeskCard } from '../components/WeeklyDeskCard'
import { UpgradeCard } from '../components/Locked'
import {
  fetchIntelligenceGame,
  fetchWeeklyGame,
  type GameIntelligencePackage,
  type UpcomingGame,
  type WeeklyCard,
} from '../lib/api'
import { comparisonMetrics, fmtMetric } from '../lib/metrics'
import { useAuth } from '../lib/auth'
import { can } from '../lib/entitlements'
import { useSlate } from '../lib/slate'

type Tab = 'overview' | 'models' | 'market' | 'trends'

function gameFromWeekly(card: WeeklyCard): UpcomingGame {
  return {
    league: card.league,
    game_id: card.game_id,
    kickoff: null,
    game_date: null,
    week: card.week ?? 1,
    season: null,
    season_type: 'REG',
    away_team: card.away_team,
    home_team: card.home_team,
    away_name: card.away_name || card.away_team,
    home_name: card.home_name || card.home_team,
    away_espn_id: card.away_espn_id,
    home_espn_id: card.home_espn_id,
    neutral: false,
    matchup: card.matchup || `${card.away_team} @ ${card.home_team}`,
    home_spread: card.home_spread ?? null,
    spread_label: card.spread_label ?? null,
    total_line: card.total_line ?? null,
    book: null,
    round: 'REG',
    status: null,
  }
}

export function MatchupPage() {
  const { gameId } = useParams()
  const { games } = useSlate()
  const [tab, setTab] = useState<Tab>('overview')
  const decoded = decodeURIComponent(gameId ?? '')
  const slateGame = useMemo(() => games.find((x) => x.game_id === decoded), [games, decoded])
  const [weeklyCard, setWeeklyCard] = useState<WeeklyCard | null>(null)
  const [intel, setIntel] = useState<GameIntelligencePackage | null>(null)
  const [weeklyLoaded, setWeeklyLoaded] = useState(false)

  useEffect(() => {
    let live = true
    setWeeklyLoaded(false)
    Promise.all([fetchWeeklyGame(decoded), fetchIntelligenceGame(decoded)])
      .then(([weeklyPayload, intelPayload]) => {
        if (!live) return
        setWeeklyCard(weeklyPayload.available && weeklyPayload.card ? weeklyPayload.card : null)
        setIntel(intelPayload.available && intelPayload.package ? intelPayload.package : null)
      })
      .catch(() => {
        if (!live) return
        setWeeklyCard(null)
        setIntel(null)
      })
      .finally(() => {
        if (live) setWeeklyLoaded(true)
      })
    return () => {
      live = false
    }
  }, [decoded])

  const g = slateGame || (weeklyCard ? gameFromWeekly(weeklyCard) : null)

  if (!games.length && !weeklyLoaded) {
    return <p className="muted">Loading slate…</p>
  }
  if (!g) {
    return (
      <section className="card">
        <h1>Game not found</h1>
        <p className="muted">This id is not in the current ESPN window or weekly desk.</p>
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
    { id: 'trends', label: 'Research' },
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
              <TeamMark abbr={g.away_team} league={g.league} espnId={g.away_espn_id} />
              <span className="matchup-vs">{g.neutral ? 'vs' : '@'}</span>
              <TeamMark abbr={g.home_team} league={g.league} espnId={g.home_espn_id} />
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
        <span className="preview-flag">
          <Hint t="research-preview">Research Preview</Hint> ·{' '}
          <Hint t="public-probability">public probability</Hint> not published
        </span>
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
            <span>
              <HintLabel t="Market">Market</HintLabel>
            </span>
            <b>{g.spread_label ?? '—'}</b>
          </article>
          <article className="kpi">
            <span>
              <HintLabel t="BCW Research Preview">BCW Research Preview</HintLabel>
            </span>
            <b>Snapshot pending</b>
          </article>
          <article className="kpi">
            <span>Bet recommendation</span>
            <b>{weeklyCard ? weeklyCard.ai.recommendation_team : '—'}</b>
          </article>
          <article className="kpi">
            <span>Confidence</span>
            <b>
              {weeklyCard
                ? `${Number(weeklyCard.ai.confidence_pct ?? weeklyCard.projection.confidence_pct ?? 0).toFixed(1)}%`
                : '—'}
            </b>
          </article>
        </div>
      )}

      {tab === 'overview' && (
        <>
          <div className="grid-12">
            <section className="card">
              <h2>
                Projected margin (<Hint t="mu">μ</Hint>)
              </h2>
              {weeklyCard ? (
                <p className="muted">
                  <strong>Snapshot pending</strong> for BCW-RIDGE. Desk lean below: bet{' '}
                  <strong>{weeklyCard.ai.recommendation_team}</strong> at{' '}
                  <strong>
                    {Number(weeklyCard.ai.confidence_pct ?? weeklyCard.projection.confidence_pct ?? 0).toFixed(1)}%
                  </strong>{' '}
                  confidence.
                </p>
              ) : showMu ? (
                <p className="muted">
                  <Hint t="ridge">BCW-RIDGE-PURE</Hint> v0.1-candidate is trained on 2009–2022. This ESPN kickoff does
                  not yet have a leakage-safe <Hint t="snapshot">snapshot</Hint>, so no μ is shown. Plain-English guide:{' '}
                  <Link to="/about">About</Link>.
                </p>
              ) : (
                <UpgradeCard title="BCW Projection" plan="Pro">
                  Unlock full analysis on Pro. Cover probability stays unpublished for every plan until calibration gates
                  pass.
                </UpgradeCard>
              )}
            </section>
            <section className="card">
              <h2>Market snapshot</h2>
              <p className="muted" style={{ marginTop: 0 }}>
                The sportsbook <Hint t="spread">spread</Hint> and total right now — not our model.
              </p>
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

          <MatchupNews game={g} />
          {intel ? (
            <div style={{ marginTop: 12 }}>
              <GameIntelligenceBrief pkg={intel} />
            </div>
          ) : null}
          {weeklyCard ? (
            <div style={{ marginTop: 12 }}>
              <WeeklyDeskCard card={weeklyCard} />
            </div>
          ) : null}
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
            <Hint t="market-0">No-vig close</Hint> is the benchmark.{' '}
            <Hint t="edge">Edge</Hint> = model P(cover) − break-even at −110 (52.38%). Changing a spread only reprices{' '}
            <Hint t="stern">Stern</Hint> P(cover); it does not retrain.
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
          <h2>Research view (Level 3)</h2>
          <p className="muted">Same evidence as the Game Intelligence Brief, structured for desk users.</p>
          <div className="sit" style={{ gridTemplateColumns: '1fr 1fr' }}>
            <div>
              <strong>Models</strong>
              Desk μ + BCW-MATCHUP-LOGISTIC (Research Preview). Ridge snapshot pending / gated.
            </div>
            <div>
              <strong>Matchup Matrix</strong>
              {intel
                ? (intel.headline_cards || []).map((c) => c.fan_line).join(' · ') || '—'
                : 'Build intelligence packages to populate.'}
            </div>
            <div>
              <strong>Market</strong>
              {g.spread_label ?? '—'} · tot {g.total_line ?? '—'}
            </div>
            <div>
              <strong>News &amp; sources</strong>
              Events are derived facts + citations — not full article republication.
            </div>
            <div>
              <strong>Methodology</strong>
              AI explains cached evidence. Regenerates on source_set_hash change only.
            </div>
            <div>
              <strong>Historical comparables</strong>
              Wave 4+
            </div>
          </div>
          <MetricTable away={g.away_team} home={g.home_team} metrics={metrics} />
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
            <span>
              <Hint t={m.name}>{m.name}</Hint>
            </span>
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
