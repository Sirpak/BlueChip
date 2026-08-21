import type { WeeklyCard } from '../lib/api'

function pct(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return '—'
  return `${(v * 100).toFixed(1)}%`
}

export function WeeklyDeskCard({ card }: { card: WeeklyCard }) {
  const p = card.projection
  const ai = card.ai
  const conf = ai.confidence_pct ?? p.confidence_pct
  return (
    <section className="card weekly-card">
      <div className="weekly-card-head">
        <div>
          <h2 style={{ margin: 0 }}>Bet recommendation</h2>
          <p className="muted" style={{ margin: '4px 0 0' }}>
            {p.model_id} · Ridge snapshot pending · Research Preview
          </p>
        </div>
        <span className="preview-flag">{card.featured ? 'AI enriched' : 'Desk model'}</span>
      </div>

      <div className="bet-hero">
        <div>
          <span className="muted">Who to bet</span>
          <b className="bet-team">{ai.recommendation_team}</b>
          <span className="muted">
            {ai.recommendation_side === 'HOME' ? 'Home' : 'Away'} vs the spread · {card.spread_label ?? 'pick'}
          </span>
        </div>
        <div className="bet-conf">
          <span className="muted">Confidence</span>
          <b>{conf != null ? `${Number(conf).toFixed(1)}%` : ai.confidence}</b>
        </div>
      </div>

      <div className="kpis" style={{ marginTop: 12 }}>
        <article className="kpi">
          <span>Projected home margin (μ)</span>
          <b>
            {p.mu_home >= 0 ? '+' : ''}
            {p.mu_home.toFixed(1)}
          </b>
        </article>
        <article className="kpi">
          <span>Model P(home win)</span>
          <b>{pct(p.p_home_win)}</b>
        </article>
        <article className="kpi">
          <span>Model P(home cover)</span>
          <b>{pct(p.p_home_cover)}</b>
        </article>
        <article className="kpi">
          <span>BCW-RIDGE snapshot</span>
          <b>Pending</b>
        </article>
      </div>

      <p className="muted" style={{ fontSize: 12 }}>
        {p.method}. Confidence = P(recommended side covers). Not the frozen BCW-RIDGE public cover %.
      </p>

      <h3 style={{ fontSize: 14, marginTop: 16 }}>Handicapper notes</h3>
      <p className="weekly-analysis">{ai.analysis}</p>
      <p className="muted" style={{ marginTop: 10, fontSize: 12 }}>
        {ai.disclaimer}
      </p>

      {card.news?.length ? (
        <>
          <h3 style={{ fontSize: 14, marginTop: 16 }}>Headlines used</h3>
          <ul className="weekly-news">
            {card.news.map((n) => (
              <li key={n.url}>
                <a href={n.url} target="_blank" rel="noreferrer">
                  {n.headline}
                </a>
                <span className="muted"> · {n.publisher}</span>
              </li>
            ))}
          </ul>
        </>
      ) : null}
    </section>
  )
}

export function weeklyMuLabel(card: WeeklyCard | undefined): string {
  if (!card) return 'Snapshot pending'
  const conf = card.projection.confidence_pct ?? card.ai.confidence_pct
  const lean = card.ai.recommendation_team
  return `Bet ${lean} · ${conf != null ? `${Number(conf).toFixed(1)}%` : '—'} conf`
}
