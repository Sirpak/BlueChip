import { Link } from 'react-router-dom'
import { HintLabel } from '../components/Hint'
import {
  MODELS,
  PRODUCTION_MODEL_ID,
  STATUS_LABEL,
  metricsFor,
  type ModelEntry,
  type ModelStatus,
} from '../data/catalog'

function StatusPill({ status }: { status: ModelStatus }) {
  const cls =
    status === 'production'
      ? 'pill pill-high'
      : status === 'development'
        ? 'pill pill-medium'
        : status === 'baseline'
          ? 'pill pill-low'
          : 'pill pill-low'
  return <span className={cls}>{STATUS_LABEL[status]}</span>
}

function ModelCard({ model, featured }: { model: ModelEntry; featured?: boolean }) {
  const m = metricsFor(model)
  return (
    <article className={`model-card${featured ? ' model-card-featured' : ''}`}>
      <div className="model-card-head">
        <div>
          <h3>{model.name}</h3>
          <p className="muted">{model.tagline}</p>
        </div>
        <StatusPill status={model.status} />
      </div>
      <dl className="model-meta">
        <div>
          <dt>Training</dt>
          <dd>{model.training}</dd>
        </div>
        <div>
          <dt>Holdout</dt>
          <dd>{model.holdout}</dd>
        </div>
        <div>
          <dt>Market features</dt>
          <dd>{model.marketFeatures}</dd>
        </div>
      </dl>
      <table className="board model-metrics">
        <thead>
          <tr>
            <th>
              <HintLabel t="Brier">Brier</HintLabel>
            </th>
            <th>
              <HintLabel t="Log loss">Log loss</HintLabel>
            </th>
            <th>
              <HintLabel t="MAE">MAE</HintLabel>
            </th>
            <th>
              <HintLabel t="RMSE">RMSE</HintLabel>
            </th>
            <th>
              <HintLabel t="ATS vs close">ATS vs close</HintLabel>
            </th>
            <th>
              <HintLabel t="N">N</HintLabel>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>{m.brier}</td>
            <td>{m.logLoss}</td>
            <td>{m.mae}</td>
            <td>{m.rmse}</td>
            <td>{m.ats}</td>
            <td>{m.n}</td>
          </tr>
        </tbody>
      </table>
      <Link className="btn" to={`/models/${model.id}`}>
        Model detail
      </Link>
    </article>
  )
}

export function ModelsPage() {
  const production = MODELS.find((m) => m.id === PRODUCTION_MODEL_ID)!
  const others = MODELS.filter((m) => m.id !== PRODUCTION_MODEL_ID)

  return (
    <>
      <div className="page-h">
        <div>
          <h1>BlueChip Model Lab</h1>
          <p className="muted">
            What each model is trying to do — in status language, not fake probabilities. New to the terms? Open{' '}
            <Link to="/about">About (plain English)</Link> or hover dotted labels.
          </p>
        </div>
      </div>

      <section className="card model-hero">
        <div className="model-hero-top">
          <div>
            <span className="eyebrow">Published number (target)</span>
            <h2>{production.name}</h2>
            <p>{production.predicts}</p>
          </div>
          <StatusPill status={production.status} />
        </div>
        <dl className="model-meta model-meta-inline">
          <div>
            <dt>Status</dt>
            <dd>{STATUS_LABEL[production.status]}</dd>
          </div>
          <div>
            <dt>Purpose</dt>
            <dd>Pregame expected scoring margin</dd>
          </div>
          <div>
            <dt>Version</dt>
            <dd>{metricsFor(production).version}</dd>
          </div>
          <div>
            <dt>Last trained</dt>
            <dd>{metricsFor(production).lastTrained}</dd>
          </div>
          <div>
            <dt>Training</dt>
            <dd>{production.training}</dd>
          </div>
          <div>
            <dt>Holdout</dt>
            <dd>{production.holdout}</dd>
          </div>
          <div>
            <dt>Features</dt>
            <dd>{production.features.length}</dd>
          </div>
          <div>
            <dt>Market features</dt>
            <dd>NO</dd>
          </div>
        </dl>
        <ul className="detail-list" style={{ margin: '12px 0' }}>
          <li>Outputs (after freeze): projected spread, win probability, cover probability, uncertainty interval</li>
        </ul>
        <p className="muted model-note">
          Snapshots exist (BCW-SNAP-v0.1, 7,276 games). Ridge training and ship gates are next. Desk cover % is still
          Stern + preview overlay until this passes gates.
        </p>
        <Link className="btn btn-primary" to={`/models/${production.id}`}>
          Why we will trust this number
        </Link>
      </section>

      <h2 className="section-h">Reference & research models</h2>
      <div className="model-grid">
        {others.map((m) => (
          <ModelCard key={m.id} model={m} />
        ))}
      </div>

      <section className="card" style={{ marginTop: 18 }}>
        <h2>Leaderboard (v0.1)</h2>
        <p className="muted">Brier, log loss, MAE/RMSE, ATS vs close, n, calibration. No ROI, units, or bankroll.</p>
        <table className="board">
          <thead>
            <tr>
              <th>Model</th>
              <th>Status</th>
              <th>
                <HintLabel t="Brier">Brier ↓</HintLabel>
              </th>
              <th>
                <HintLabel t="Log loss">Log loss ↓</HintLabel>
              </th>
              <th>
                <HintLabel t="MAE">MAE ↓</HintLabel>
              </th>
              <th>
                <HintLabel t="RMSE">RMSE ↓</HintLabel>
              </th>
              <th>
                <HintLabel t="ATS vs close">ATS</HintLabel>
              </th>
              <th>
                <HintLabel t="N">N</HintLabel>
              </th>
              <th>Calibration</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Market 0 (close)</td>
              <td>Benchmark</td>
              <td colSpan={7} className="muted">
                nflverse_pfr historical_close — prior, not a PURE feature
              </td>
            </tr>
            {MODELS.filter((m) => m.status !== 'future').map((m) => {
              const met = metricsFor(m)
              return (
                <tr key={m.id}>
                  <td>
                    <Link to={`/models/${m.id}`}>{m.name}</Link>
                  </td>
                  <td>{STATUS_LABEL[m.status]}</td>
                  <td>{met.brier}</td>
                  <td>{met.logLoss}</td>
                  <td>{met.mae}</td>
                  <td>{met.rmse}</td>
                  <td>{met.ats}</td>
                  <td>{met.n}</td>
                  <td>{met.calibration}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </section>
    </>
  )
}
