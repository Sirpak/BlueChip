import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { BLUECHIP_STUDIES, EXTERNAL_RESEARCH, RESEARCH_CATEGORIES, type StudyCategory } from '../data/catalog'

const STUDY_STATUS: Record<string, string> = {
  planned: 'Planned',
  in_progress: 'In progress',
  published: 'Published',
}

export function ResearchPage() {
  const [cat, setCat] = useState<StudyCategory | 'All'>('All')
  const studies = useMemo(
    () => (cat === 'All' ? BLUECHIP_STUDIES : BLUECHIP_STUDIES.filter((s) => s.category === cat)),
    [cat],
  )

  return (
    <>
      <div className="page-h">
        <div>
          <h1>BlueChip Research</h1>
          <p className="muted">Why BlueChip models football this way. Not a betting tip sheet.</p>
        </div>
      </div>

      <div className="research-intro card">
        <p>
          <strong>Models</strong> = what BlueChip currently computes.{' '}
          <strong>Research</strong> = what we tested, what the evidence says, and how ideas become features.
        </p>
      </div>

      <h2 className="section-h">BlueChip studies</h2>
      <div className="filters">
        <button type="button" className={`chip ${cat === 'All' ? 'is-on' : ''}`} onClick={() => setCat('All')}>
          All
        </button>
        {RESEARCH_CATEGORIES.map((c) => (
          <button key={c} type="button" className={`chip ${cat === c ? 'is-on' : ''}`} onClick={() => setCat(c)}>
            {c}
          </button>
        ))}
      </div>
      <p className="muted section-lede">
        Each study: Question → Dataset → Method → Mathematics → Results → Charts → Limitations → Conclusion → Sources →
        How BlueChip uses this.
      </p>
      <div className="feed research-feed">
        {studies.map((s) => (
          <article key={s.id}>
            <span className="badge">{STUDY_STATUS[s.status]}</span>
            <span className="source-chip" style={{ marginLeft: 6 }}>
              {s.category}
            </span>
            <h3>{s.question}</h3>
            <p className="muted">
              <strong>Hypothesis:</strong> {s.hypothesis}
            </p>
          </article>
        ))}
      </div>

      <h2 className="section-h">External research</h2>
      <p className="muted section-lede">Summaries with sources — the same library Ask BlueChip will search later.</p>
      <div className="research-external">
        {EXTERNAL_RESEARCH.map((r) => (
          <article key={r.id} className="card research-paper">
            <div className="research-paper-head">
              <h3>{r.title}</h3>
              <span className="source-chip">{r.source}</span>
            </div>
            <p>{r.summary}</p>
            <div className="research-bcw">
              <strong>How BlueChip uses this idea</strong>
              <p>{r.bcwUse}</p>
            </div>
            {r.url && (
              <a href={r.url} target="_blank" rel="noreferrer" className="btn" style={{ marginTop: 10 }}>
                Read source
              </a>
            )}
          </article>
        ))}
      </div>

      <section className="card research-sources">
        <h2>Data sources</h2>
        <p className="muted">
          Canonical NFL: nflverse PBP and schedules (1999–2025). Market 0: nflverse_pfr historical close. CFB: CFBD
          after NFL gates. Live books: Odds API later. Weather: NWS/NOAA when situational layer ships.
        </p>
        <Link className="btn" to="/models">
          See Model Lab
        </Link>
      </section>

      <section className="card dev-access">
        <h2>Developer access / API</h2>
        <p className="muted">
          Programmatic access is a Research-tier feature. OpenAPI at <a href="/docs">/docs</a>.
        </p>
        <Link className="btn" to="/pricing">
          See plans
        </Link>
      </section>
    </>
  )
}
