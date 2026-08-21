import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { Reliability, Sparkline } from '../components/Charts'
import { Hint, HintLabel } from '../components/Hint'
import { TeamMark } from '../components/Marks'
import { UpgradeCard } from '../components/Locked'
import { kickoffLocal } from '../lib/preview'
import { useAuth } from '../lib/auth'
import { can } from '../lib/entitlements'
import { useSlate } from '../lib/slate'

type LeagueFilter = 'All' | 'NFL' | 'CFB'

const BASELINE_MODELS = ['HFA', 'Elo', 'SRS', 'Opp-adj EPA']

export function Desk({ league, onLeague }: { league: LeagueFilter; onLeague: (v: LeagueFilter) => void }) {
  const { games, count } = useSlate()
  const { user } = useAuth()
  const showMu = can(user, 'models_full')
  const rows = useMemo(() => games.filter((g) => (league === 'All' ? true : g.league === league)).slice(0, 18), [games, league])
  const selected = rows[0]

  return (
    <>
      <div className="page-h">
        <div>
          <h1>Football Research Desk</h1>
          <p className="muted">
            {count.nfl} NFL + {count.cfb} FBS games in the current ESPN window. New here? Read{' '}
            <Link to="/about">About in plain English</Link> — hover any dotted term for a tip.
          </p>
        </div>
        <span className="preview-flag">
          <Hint t="research-preview">Research Preview</Hint> ·{' '}
          <Hint t="public-probability">public cover %</Hint> not published
        </span>
      </div>

      <div className="kpis">
        <article className="kpi">
          <span>Games in window</span>
          <b>{count.nfl + count.cfb}</b>
        </article>
        <article className="kpi">
          <span>Baselines on snapshots</span>
          <b>{BASELINE_MODELS.length}</b>
        </article>
        <article className="kpi">
          <span>
            <HintLabel t="holdout">Holdout</HintLabel>
          </span>
          <b>2023–2025 sealed</b>
        </article>
        <article className="kpi">
          <span>Plan</span>
          <b>{user?.plan_label ?? '—'}</b>
        </article>
      </div>

      <section className="card">
        <h2>This week’s board</h2>
        <div className="filters">
          {(['All', 'NFL', 'CFB'] as const).map((v) => (
            <button key={v} className={`chip ${league === v ? 'is-on' : ''}`} type="button" onClick={() => onLeague(v)}>
              {v}
            </button>
          ))}
        </div>
        <table className="board desk-only">
          <thead>
            <tr>
              <th>Game</th>
              <th>Kickoff</th>
              <th>
                <HintLabel t="Market">Market</HintLabel>
              </th>
              <th>
                <HintLabel t="BCW Research Preview">BCW Research Preview</HintLabel>
              </th>
              <th>
                <HintLabel t="Public probability">Public probability</HintLabel>
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((g) => (
              <tr key={g.game_id}>
                <td>
                  <Link to={`/games/${encodeURIComponent(g.game_id)}`} className="game-cell">
                    <div className="logos">
                      <TeamMark abbr={g.away_team} league={g.league} espnId={g.away_espn_id} />
                      <TeamMark abbr={g.home_team} league={g.league} espnId={g.home_espn_id} />
                    </div>
                    <div>
                      <strong>
                        {g.away_team} {g.neutral ? 'vs' : '@'} {g.home_team}
                      </strong>
                      <div className="muted" style={{ fontSize: 11 }}>
                        {g.league} · {g.round ?? g.away_name}
                      </div>
                    </div>
                  </Link>
                </td>
                <td>{kickoffLocal(g.kickoff)}</td>
                <td>{g.spread_label ?? '—'}</td>
                <td>{showMu ? 'No snapshot for this kickoff yet' : 'Available with Pro'}</td>
                <td className="muted">Not yet published</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {!showMu && (
        <UpgradeCard title="BCW projected margin" plan="Pro">
          Free sees kickoff, records, and the market line. Candidate Ridge μ is a Pro Research Preview — still not a public cover percentage.
        </UpgradeCard>
      )}

      <div className="grid-3">
        <section className="card">
          <h2>Model status</h2>
          <p className="muted" style={{ marginTop: 0, fontSize: 12 }}>
            {selected ? selected.matchup : 'No slate yet'} · <Link to="/models">Model Lab →</Link>
          </p>
          <ul className="detail-list" style={{ fontSize: 13, margin: 0 }}>
            <li>
              <strong>BCW-RIDGE-PURE</strong> — v0.1-candidate · Research Preview
            </li>
            {BASELINE_MODELS.map((m) => (
              <li key={m}>
                <strong>
                  <Hint t={m}>{m}</Hint>
                </strong>{' '}
                — Baseline on snapshots
              </li>
            ))}
          </ul>
        </section>
        <section className="card">
          <h2>
            Projected margin (<Hint t="mu">μ</Hint>)
          </h2>
          <p className="muted">
            Candidate <Hint t="mu">μ</Hint> is fit on 2009–2022 only. Upcoming ESPN games need a leakage-safe{' '}
            <Hint t="snapshot">snapshot</Hint> before a number appears.{' '}
            <Hint t="public-probability">Public cover %</Hint> stays unpublished.
          </p>
        </section>
        <section className="card">
          <h2>Model health</h2>
          <p className="muted" style={{ marginTop: 0, fontSize: 12 }}>
            <Hint t="walk-forward">Walk-forward</Hint> lives in 2009–2022.{' '}
            <Hint t="holdout">Holdout</Hint> closed. No ROI.
          </p>
          <div className="health-grid">
            <div>
              <strong>
                <Hint t="calibration">Reliability</Hint>
              </strong>
              <Reliability />
            </div>
            <div>
              <strong>
                <HintLabel t="brier">Brier</HintLabel> vs <Hint t="market-0">Market 0</Hint>
              </strong>
              <Sparkline seed={42} up />
              <div className="muted" style={{ fontSize: 11 }}>
                Market still leads — not a ship claim
              </div>
            </div>
            <div>
              <strong>
                Margin <HintLabel t="mae">MAE</HintLabel>
              </strong>
              <Sparkline seed={91} up={false} />
              <div className="muted" style={{ fontSize: 11 }}>
                vs <Hint t="hfa">HFA</Hint> / <Hint t="srs">SRS</Hint> on the development window
              </div>
            </div>
          </div>
        </section>
      </div>
    </>
  )
}
