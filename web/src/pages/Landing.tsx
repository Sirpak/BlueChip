import { Component, Suspense, lazy, useEffect, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ProductMock } from '../components/ProductMock'
import { I, Icon } from '../components/Icons'
import { brand } from '../brand'

const HeroField = lazy(async () => {
  const m = await import('../three/HeroField')
  return { default: m.HeroField }
})

const prompts = [
  'What is the impact of a receiver injury on the BUF offense?',
  'Why does BlueChip favor Buffalo −6.5?',
  'Compare Ohio State and Georgia EPA.',
  'Which games show the largest model–market disagreement?',
]

class WebGlGuard extends Component<{ children: ReactNode }, { ok: boolean }> {
  state = { ok: true }
  static getDerivedStateFromError() {
    return { ok: false }
  }
  componentDidCatch() {
    this.setState({ ok: false })
  }
  render() {
    if (!this.state.ok) return <div className="hero-fallback" />
    return this.props.children
  }
}

export function Landing() {
  const [scroll, setScroll] = useState(0)
  const [mouse, setMouse] = useState({ x: 0, y: 0 })
  const [q, setQ] = useState('')

  useEffect(() => {
    const onScroll = () => setScroll(Math.min(1, window.scrollY / 520))
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <>
      <section className="hero hero-full">
        <div className="hero-copy hero-copy-shell">
          <h1>Football intelligence, modeled.</h1>
          <p className="lede">
            Research NFL and college football using play-by-play data, probabilistic models, markets,
            injuries, weather, historical games, and AI-powered search.
          </p>
          <div className="hero-actions">
            <Link className="btn btn-primary" to="/desk">
              Explore the Platform
            </Link>
            <Link className="btn" to="/ask">
              Ask BlueChip
            </Link>
          </div>
        </div>
        <div
          className="hero-stage hero-stage-full"
          onMouseMove={(e) => {
            const r = e.currentTarget.getBoundingClientRect()
            setMouse({
              x: ((e.clientX - r.left) / r.width) * 2 - 1,
              y: ((e.clientY - r.top) / r.height) * 2 - 1,
            })
          }}
        >
          <WebGlGuard>
            <Suspense fallback={<div className="hero-fallback" />}>
              <HeroField scroll={scroll} mouse={mouse} />
            </Suspense>
          </WebGlGuard>
        </div>
      </section>

      <section className="ask-band">
        <div className="ask-box">
          <h2>Ask anything about NFL or college football</h2>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              window.location.href = `/ask?q=${encodeURIComponent(q || prompts[0])}`
            }}
          >
            <div className="search-wrap">
              <Icon d={I.search} size={16} />
              <input
                className="ask-input"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Ask anything about NFL or college football"
              />
            </div>
          </form>
          <div className="chips">
            {prompts.map((p) => (
              <Link key={p} className="chip" to={`/ask?q=${encodeURIComponent(p)}`}>
                {p}
              </Link>
            ))}
          </div>
          <div className="sample-answer">
            <div className="stats-row">
              <div className="stat">
                <span>BlueChip consensus</span>
                <b>56.2%</b>
              </div>
              <div className="stat">
                <span>Break-even (−110)</span>
                <b>52.38%</b>
              </div>
              <div className="stat">
                <span>Edge</span>
                <b className="good">+3.8 pp</b>
              </div>
            </div>
            <p style={{ margin: '0 0 10px', fontSize: 14, lineHeight: 1.55 }}>
              Illustrative Stern conversion from a projected home margin — not a published Ridge run.
              Cover probability ships with a calibration range and n once BCW-v0.1 clears its gates.
            </p>
            <span className="source-chip">BlueChip model run</span>
            <span className="source-chip">nflverse PBP</span>
            <span className="source-chip">Market snapshot</span>
            <span className="source-chip">NWS / injury (later)</span>
          </div>
        </div>
      </section>

      <section className="shot-band">
        <div className="shot-copy">
          <p className="eyebrow">Live research overlay</p>
          <h2>A terminal on the game, not a sportsbook skin.</h2>
          <p className="muted">
            Win probability, drive efficiency, and model notes sit on the slate. The published v0.1 number is
            still a pregame home margin — this overlay is the live WP track, not the Ridge freeze.
          </p>
          <Link className="btn btn-primary" to="/desk">
            Open the desk
          </Link>
        </div>
        <figure className="shot-frame">
          <img src="/images/macbook_with_NFL_game.png" alt="BlueChipWager live model overlay on a laptop during an NFL game" />
        </figure>
      </section>

      <section className="explainer-band">
        <div className="explainer-copy">
          <p className="eyebrow">How it works</p>
          <h2>How the model predicts a winner</h2>
          <p className="muted">
            In-game win probability is a logistic of score, clock, field position, down, and turnover state.
            Pregame cover % is a different problem: Stern maps a projected home margin through σ ≈ 13.5.
          </p>
        </div>
        <figure className="explainer-art">
          <img
            src="/images/how_we_pick_a_winner.png"
            alt="Infographic: real-time NFL win probability with a worked Chiefs–Bills example"
          />
        </figure>
      </section>

      <section className="gallery-band">
        <div className="page-h" style={{ marginBottom: 16 }}>
          <div>
            <p className="eyebrow">Product</p>
            <h2 style={{ margin: 0 }}>The research desk</h2>
            <p className="muted" style={{ margin: '8px 0 0' }}>
              Terminal preview of this week’s slate — HTML scaled into the frame, not a screenshot.
            </p>
          </div>
          <Link className="btn" to="/desk">
            Open the desk
          </Link>
        </div>
        <ProductMock />
      </section>

      <footer className="site-foot">
        <img className="brand-icon" src={brand.icon} alt="" width={28} height={28} />
        <span>BlueChipWager · football intelligence, modeled</span>
      </footer>
    </>
  )
}
