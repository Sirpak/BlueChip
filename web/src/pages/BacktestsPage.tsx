import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { MODELS } from '../data/catalog'

const FILTERS = ['NFL', 'CFB', 'Model', 'Season', 'Spread range', 'Favorite / underdog', 'Home / away'] as const

type LeaderboardPayload = {
  available: boolean
  message?: string
  models?: Record<string, Record<string, unknown>>
  window?: { season_start: number; season_end: number }
  n_games?: number
}

function fmt(v: unknown, digits = 3): string {
  if (typeof v === 'number' && Number.isFinite(v)) return v.toFixed(digits)
  return '—'
}

function ridgeRow(payload: LeaderboardPayload | null) {
  const ridge = payload?.models?.['BCW-RIDGE-v0.1'] as
    | { adj_epa?: Record<string, number>; recommended_variant?: string }
    | undefined
  const adj = ridge?.adj_epa
  if (!adj) return null
  return {
    brier: fmt(adj.brier),
    logLoss: fmt(adj.log_loss),
    mae: fmt(adj.mae, 2),
    rmse: fmt(adj.rmse, 2),
    ats: fmt(adj.ats_pct, 3),
    n: String(adj.n ?? '—'),
    note: ridge?.recommended_variant ? `OOS · ${ridge.recommended_variant} EPA wins MAE` : 'OOS',
  }
}

function logisticRow(payload: LeaderboardPayload | null) {
  const log = payload?.models?.['BCW-LOGISTIC-v0.1'] as Record<string, number> | undefined
  if (!log) return null
  return {
    brier: fmt(log.brier),
    logLoss: fmt(log.log_loss),
    mae: '—',
    rmse: '—',
    ats: '—',
    n: String(log.n ?? '—'),
    note: 'OOS win prob',
  }
}

function baselineRow(payload: LeaderboardPayload | null, key: string) {
  const row = payload?.models?.[key] as Record<string, number> | undefined
  if (!row) return null
  return {
    brier: fmt(row.brier),
    logLoss: fmt(row.log_loss),
    mae: fmt(row.mae, 2),
    rmse: fmt(row.rmse, 2),
    ats: fmt(row.ats_pct, 3),
    n: String(row.n ?? '—'),
    note: 'Snapshot baseline',
  }
}

export function BacktestsPage() {
  const [lb, setLb] = useState<LeaderboardPayload | null>(null)

  useEffect(() => {
    fetch('/api/models/leaderboard', { credentials: 'include' })
      .then((r) => {
        if (r.status === 403) return { available: false, message: 'Upgrade for the walk-forward matrix.' }
        return r.ok ? r.json() : { available: false }
      })
      .then(setLb)
      .catch(() => setLb({ available: false }))
  }, [])

  const ridge = ridgeRow(lb)
  const logistic = logisticRow(lb)
  const hfa = baselineRow(lb, 'BCW-HFA')
  const srs = baselineRow(lb, 'BCW-SRS')

  function metricsForModel(id: string) {
    if (id === 'bcw-ridge-v0-1') return ridge
    if (id === 'bcw-logistic') return logistic
    if (id === 'bcw-hfa') return hfa
    if (id === 'bcw-srs') return srs
    return null
  }

  return (
    <>
      <div className="page-h">
        <div>
          <h1>Backtests</h1>
          <p className="muted">
            Walk-forward research on 2009–2022. Sacred holdout 2023–2025 opens once after freeze. Research methodology
            — not a units brag page.
          </p>
        </div>
      </div>

      <section className="card">
        <h2>Methodology</h2>
        <p>
          Season walk-forward inside <strong>2009–2022</strong>. No random CV. Compare every model to Market 0 (nflverse
          close). Metrics: Brier, log loss, MAE, RMSE, ATS vs close, n, calibration buckets.{' '}
          <strong>No ROI, units, or bankroll</strong> at v0.1 launch.
        </p>
        {lb?.available && (
          <p className="muted">
            Latest run: {lb.n_games} REG games ({lb.window?.season_start}–{lb.window?.season_end}).
          </p>
        )}
      </section>

      <section className="card">
        <h2>Filters</h2>
        <div className="filters">
          {FILTERS.map((f) => (
            <span key={f} className="filter-sel">
              {f}
            </span>
          ))}
        </div>
        <p className="muted">Season and spread filters ship next; matrix below is walk-forward OOS where available.</p>
      </section>

      <section className="card">
        <h2>Results matrix</h2>
        {!lb?.available && (
          <p className="muted">{lb?.message ?? 'Leaderboard loads after walk-forward run.'}</p>
        )}
        <table className="board">
          <thead>
            <tr>
              <th>Model</th>
              <th>Period</th>
              <th>Walk-forward</th>
              <th>Brier</th>
              <th>Log loss</th>
              <th>MAE</th>
              <th>RMSE</th>
              <th>ATS</th>
              <th>N</th>
              <th>Calibration</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Market 0</td>
              <td>2009–2022</td>
              <td>Close as prior</td>
              <td>{logistic ? fmt((lb?.models?.['BCW-LOGISTIC-v0.1'] as { market0_brier?: number })?.market0_brier) : '—'}</td>
              <td>{logistic ? fmt((lb?.models?.['BCW-LOGISTIC-v0.1'] as { market0_log_loss?: number })?.market0_log_loss) : '—'}</td>
              <td colSpan={3} className="muted">
                Benchmark — not a trained model
              </td>
              <td>—</td>
              <td>—</td>
            </tr>
            {MODELS.filter((m) => m.status !== 'future').map((m) => {
              const met = metricsForModel(m.id)
              return (
                <tr key={m.id}>
                  <td>
                    <Link to={`/models/${m.id}`}>{m.name}</Link>
                  </td>
                  <td>{m.training}</td>
                  <td>{met?.note ?? 'Season folds'}</td>
                  <td>{met?.brier ?? '—'}</td>
                  <td>{met?.logLoss ?? '—'}</td>
                  <td>{met?.mae ?? '—'}</td>
                  <td>{met?.rmse ?? '—'}</td>
                  <td>{met?.ats ?? '—'}</td>
                  <td>{met?.n ?? '—'}</td>
                  <td>{met ? 'ECE in artifact' : '—'}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </section>

      <section className="card">
        <h2>Calibration</h2>
        <p className="muted">
          Logistic ECE ≈ {(lb?.models?.['BCW-LOGISTIC-v0.1'] as { ece?: number })?.ece?.toFixed(3) ?? '—'} on OOS
          2009–2022. Full bucket tables live in the walk-forward artifact.
        </p>
        <div className="cal-placeholder" aria-hidden>
          <span>Reliability diagram — next desk iteration</span>
        </div>
      </section>
    </>
  )
}
