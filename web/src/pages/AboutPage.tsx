import { Link } from 'react-router-dom'
import { GLOSSARY, GROUP_LABEL, type GlossaryEntry } from '../lib/glossary'

const INTRO = [
  {
    title: 'What BlueChip is',
    body: 'A football research desk — closer to a calm terminal than a “lock of the day” account. We show schedules, market lines, model research, and plain-language explanations so you can interpret the board without a stats degree.',
  },
  {
    title: 'How to read a game',
    body: 'Start with kickoff and the market spread. Then look at Research Preview numbers only as “what our models currently think,” not as a published cover percentage. If something says Not yet published, we are refusing to fake confidence.',
  },
  {
    title: 'What we will not claim yet',
    body: 'We do not publish a public “56% to cover” until leakage checks, baselines, calibration, sample size, and uncertainty labeling all pass. Beating Vegas is hard; our job is to be honest when we have not.',
  },
]

function Section({ group, rows }: { group: GlossaryEntry['group']; rows: GlossaryEntry[] }) {
  return (
    <section className="card about-section" id={group}>
      <h2>{GROUP_LABEL[group]}</h2>
      <div className="about-defs">
        {rows.map((e) => (
          <article key={e.id} className="about-def" id={e.id}>
            <h3>{e.term}</h3>
            <p>{e.short}</p>
            {e.long ? <p className="muted">{e.long}</p> : null}
          </article>
        ))}
      </div>
    </section>
  )
}

export function AboutPage() {
  const groups: GlossaryEntry['group'][] = ['basics', 'models', 'metrics', 'markets', 'process']
  return (
    <>
      <div className="page-h">
        <div>
          <h1>About BlueChip — plain English</h1>
          <p className="muted">
            Every metric and model explained for fans who want clarity, not jargon. Hover underlined terms anywhere on
            the desk for a short tip, or browse the full glossary below.
          </p>
        </div>
        <Link className="btn" to="/games">
          Back to Games
        </Link>
      </div>

      <div className="about-intro">
        {INTRO.map((block) => (
          <section className="card" key={block.title}>
            <h2>{block.title}</h2>
            <p>{block.body}</p>
          </section>
        ))}
      </div>

      <section className="card" style={{ marginTop: 12 }}>
        <h2>Models in one sentence each</h2>
        <ul className="about-one-liners">
          <li>
            <strong>Ridge</strong> — blends team efficiency and ratings into an expected point margin, carefully so it
            does not memorize noise.
          </li>
          <li>
            <strong>Stern</strong> — turns that margin into win/cover chances with a football-shaped bell curve.
          </li>
          <li>
            <strong>Elo</strong> — a ranking that updates after every game; good reference, not our published number.
          </li>
          <li>
            <strong>SRS</strong> — strength from margins and schedule difficulty; another baseline we must beat.
          </li>
          <li>
            <strong>HFA</strong> — the home boost baked into football; smaller today than old “3 points” folklore.
          </li>
          <li>
            <strong>EPA / opp-adj EPA</strong> — play-by-play efficiency, optionally adjusted for opponent quality.
          </li>
        </ul>
        <p className="muted" style={{ marginBottom: 0 }}>
          Deeper Model Lab cards live on <Link to="/models">Models</Link>. Research notes live on{' '}
          <Link to="/research">Research</Link>.
        </p>
      </section>

      <div className="about-toc card" style={{ marginTop: 12 }}>
        <h2>Jump to</h2>
        <div className="about-toc-links">
          {groups.map((g) => (
            <a key={g} href={`#${g}`}>
              {GROUP_LABEL[g]}
            </a>
          ))}
        </div>
      </div>

      {groups.map((g) => (
        <Section key={g} group={g} rows={GLOSSARY.filter((e) => e.group === g)} />
      ))}

      <section className="card" style={{ marginTop: 12 }}>
        <h2>Tips while you browse</h2>
        <ul className="about-one-liners">
          <li>Underlined words = hover for a definition.</li>
          <li>
            <span className="preview-flag" style={{ display: 'inline' }}>
              Research Preview
            </span>{' '}
            means “in progress,” not “guaranteed edge.”
          </li>
          <li>Lower Brier / MAE is better when you compare models.</li>
          <li>News and polls are CONTEXT for you — they are not secretly inside the PURE Ridge score today.</li>
        </ul>
      </section>
    </>
  )
}
