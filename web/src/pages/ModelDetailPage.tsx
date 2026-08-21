import { Link, useParams } from 'react-router-dom'
import { MODELS, STATUS_LABEL, getModel, metricsFor } from '../data/catalog'

export function ModelDetailPage() {
  const { modelId } = useParams()
  const model = getModel(modelId ?? '')

  if (!model) {
    return (
      <section className="card">
        <h1>Model not found</h1>
        <p className="muted">Unknown model id.</p>
        <Link className="btn" to="/models">
          Back to Model Lab
        </Link>
      </section>
    )
  }

  const m = metricsFor(model)
  const idx = MODELS.findIndex((x) => x.id === model.id)
  const prev = MODELS[idx - 1]
  const next = MODELS[idx + 1]

  return (
    <>
      <div className="page-h">
        <div>
          <Link className="muted" to="/models" style={{ fontSize: 13 }}>
            ← Model Lab
          </Link>
          <h1>{model.name}</h1>
          <p className="muted">{model.tagline}</p>
        </div>
        <span className={`pill ${model.status === 'development' ? 'pill-medium' : model.status === 'production' ? 'pill-high' : 'pill-low'}`}>
          {STATUS_LABEL[model.status]}
        </span>
      </div>

      <section className="card">
        <h2>Overview</h2>
        <p>{model.predicts}</p>
        <p className="muted">Users cannot train, retrain, promote, or change parameters. That is admin-only.</p>
      </section>

      <div className="detail-grid">
        <section className="card">
          <h2>Mathematics</h2>
          <pre className="formula">{model.formula}</pre>
          <h2>Inputs</h2>
          <ul className="detail-list">
            {model.features.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
        </section>

        <section className="card">
          <h2>Methodology</h2>
          <dl className="detail-dl">
            <div>
              <dt>Training years</dt>
              <dd>{model.training}</dd>
            </div>
            <div>
              <dt>Walk-forward</dt>
              <dd>Season folds inside 2009–2022. No random CV.</dd>
            </div>
            <div>
              <dt>Sacred holdout</dt>
              <dd>{model.holdout}</dd>
            </div>
            <div>
              <dt>Market information</dt>
              <dd>{model.marketFeatures}</dd>
            </div>
            <div>
              <dt>Leakage safeguards</dt>
              <dd>known_at_max &lt; kickoff; rolling stats exclude the current game; no vegas_wp in PURE.</dd>
            </div>
            <div>
              <dt>Validation</dt>
              <dd>{model.validation}</dd>
            </div>
            <div>
              <dt>Version</dt>
              <dd>{m.version}</dd>
            </div>
            <div>
              <dt>Last trained</dt>
              <dd>{m.lastTrained}</dd>
            </div>
          </dl>
        </section>
      </div>

      <section className="card">
        <h2>Performance</h2>
        <p className="muted">Brier / log loss / MAE / RMSE / ATS vs close / n / calibration — empty until walk-forward. No fake 56.2%.</p>
        <table className="board">
          <thead>
            <tr>
              <th>Brier ↓</th>
              <th>Log loss ↓</th>
              <th>MAE ↓</th>
              <th>RMSE ↓</th>
              <th>ATS vs close</th>
              <th>N</th>
              <th>Calibration</th>
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
              <td>{m.calibration}</td>
            </tr>
          </tbody>
        </table>
        <div className="cal-placeholder" aria-hidden>
          <span>Brier / calibration by season — after walk-forward</span>
        </div>
      </section>

      {model.performanceByYear && model.performanceByYear.length > 0 && (
        <section className="card">
          <h2>Performance by year</h2>
          <table className="board">
            <thead>
              <tr>
                <th>Season</th>
                <th>Note</th>
              </tr>
            </thead>
            <tbody>
              {model.performanceByYear.map((row) => (
                <tr key={row.season}>
                  <td>{row.season}</td>
                  <td>{row.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {model.coefficients && (
        <section className="card">
          <h2>Explainability</h2>
          <p>
            For Ridge: <code>coefficient × feature value = contribution</code>. Examples publish with freeze — why the
            model produced a number, not a black box.
          </p>
          <p className="muted">{model.coefficients}</p>
        </section>
      )}

      <div className="detail-grid">
        <section className="card">
          <h2>Limitations</h2>
          <ul className="detail-list">
            {model.limitations.map((x) => (
              <li key={x}>{x}</li>
            ))}
          </ul>
        </section>
        <section className="card">
          <h2>Research & papers</h2>
          <ul className="detail-list">
            {model.papers.map((p) => (
              <li key={p.title}>
                {p.url ? (
                  <a href={p.url} target="_blank" rel="noreferrer">
                    {p.title}
                  </a>
                ) : (
                  p.title
                )}
              </li>
            ))}
          </ul>
        </section>
      </div>

      <div className="detail-nav">
        {prev ? (
          <Link to={`/models/${prev.id}`} className="btn">
            ← {prev.name}
          </Link>
        ) : (
          <span />
        )}
        {next ? (
          <Link to={`/models/${next.id}`} className="btn">
            {next.name} →
          </Link>
        ) : null}
      </div>
    </>
  )
}
