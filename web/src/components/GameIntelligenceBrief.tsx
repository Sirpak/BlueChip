import { useState } from 'react'
import type { GameIntelligencePackage } from '../lib/api'

function Why({ term, text }: { term: string; text: string }) {
  const [open, setOpen] = useState(false)
  return (
    <div style={{ marginTop: 6 }}>
      <button type="button" className="chip" onClick={() => setOpen((v) => !v)}>
        Why does {term} matter?
      </button>
      {open ? <p className="muted" style={{ marginTop: 6, fontSize: 13 }}>{text}</p> : null}
    </div>
  )
}

export function GameIntelligenceBrief({ pkg }: { pkg: GameIntelligencePackage }) {
  const g = pkg.game
  const cards = pkg.headline_cards || []
  const glossary = pkg.glossary || {}
  return (
    <section className="card gip-card">
      <div className="weekly-card-head">
        <div>
          <h2 style={{ margin: 0 }}>Game Intelligence Brief</h2>
          <p className="muted" style={{ margin: '4px 0 0' }}>
            {pkg.version} · cached · {pkg.generation_provider}/{pkg.generation_model} · no LLM on page view
          </p>
        </div>
        <span className="preview-flag">Research Preview</span>
      </div>

      <div className="bet-hero" style={{ marginTop: 12 }}>
        <div>
          <span className="muted">BlueChip leans</span>
          <b className="bet-team">{pkg.lean_team}</b>
          <span className="muted">{g.matchup}</span>
        </div>
        <div className="bet-conf">
          <span className="muted">Matchup logistic P(home)</span>
          <b>
            {pkg.matchup_logistic?.p_home_win != null
              ? `${(pkg.matchup_logistic.p_home_win * 100).toFixed(0)}%`
              : '—'}
          </b>
          <span className="muted" style={{ fontSize: 11 }}>
            unpublished / not a ship gate
          </span>
        </div>
      </div>

      <div className="gip-prose">{pkg.summary_full}</div>

      <h3 style={{ fontSize: 14, marginTop: 18 }}>Largest matchup edges</h3>
      <div className="edge-list">
        {cards.map((c) => (
          <div key={c.key} className="edge-row">
            <strong>
              {c.marks} {c.fan_line}
            </strong>
            <span className="muted">{c.label}</span>
            {c.percentile_hint ? <span className="muted">{c.percentile_hint}</span> : null}
            <Why term={c.title} text={c.why || glossary['EPA/play'] || ''} />
          </div>
        ))}
      </div>

      <h3 style={{ fontSize: 14, marginTop: 18 }}>How each team wins</h3>
      <div className="sit" style={{ gridTemplateColumns: '1fr 1fr' }}>
        <div>
          <strong>{g.home_team}</strong>
          {pkg.paths?.home}
        </div>
        <div>
          <strong>{g.away_team}</strong>
          {pkg.paths?.away}
        </div>
      </div>

      <h3 style={{ fontSize: 14, marginTop: 18 }}>BlueChip projection</h3>
      <div className="sit" style={{ gridTemplateColumns: '1fr 1fr 1fr' }}>
        <div>
          <strong>Market</strong>
          {g.spread_label ?? '—'}
        </div>
        <div>
          <strong>Desk μ (home)</strong>
          {pkg.projection?.mu_home != null
            ? `${pkg.projection.mu_home >= 0 ? '+' : ''}${pkg.projection.mu_home.toFixed(1)} Preview`
            : 'Snapshot pending'}
        </div>
        <div>
          <strong>Win probability</strong>
          Unavailable until validation
        </div>
      </div>

      <h3 style={{ fontSize: 14, marginTop: 18 }}>What changed this week</h3>
      <ul className="weekly-news">
        {(pkg.events || []).slice(0, 6).map((e) => (
          <li key={`${e.event_type}-${e.structured_fact}`}>
            <span className="muted">[{e.event_type}]</span> {e.structured_fact}
            {e.source_url ? (
              <>
                {' '}
                <a href={e.source_url} target="_blank" rel="noreferrer">
                  source
                </a>
              </>
            ) : null}
          </li>
        ))}
      </ul>

      <h3 style={{ fontSize: 14, marginTop: 18 }}>What could make BlueChip wrong?</h3>
      <ul className="weekly-news">
        {(pkg.risks || []).map((r) => (
          <li key={r}>{r}</li>
        ))}
      </ul>

      <Why term="MATCHUP SIGNAL" text={glossary['MATCHUP SIGNAL'] || ''} />
      <Why term="EPA/play" text={glossary['EPA/play'] || ''} />

      <p className="muted" style={{ marginTop: 12, fontSize: 12 }}>
        AI explains cached evidence only. Hash {pkg.source_set_hash}. Regenerates when model, market, edges, or events
        change — not on every page view.
      </p>
    </section>
  )
}

export function SlateIntelligenceChip({
  lean,
  edges,
  market,
  mu,
}: {
  lean?: string
  edges?: string[]
  market?: string | null
  mu?: number | null
}) {
  if (!lean) return null
  return (
    <div className="slate-intel">
      <div>
        <strong>BlueChip: {lean} lean</strong>
      </div>
      <div className="muted" style={{ fontSize: 12 }}>
        {(edges || []).slice(0, 3).join(' · ') || 'Edges pending'}
      </div>
      <div className="muted" style={{ fontSize: 12 }}>
        Market {market ?? '—'}
        {mu != null ? ` · BCW μ ${mu >= 0 ? '+' : ''}${mu.toFixed(1)} Preview` : ' · Snapshot pending'}
      </div>
    </div>
  )
}
