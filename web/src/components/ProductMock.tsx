import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { brand } from '../brand'
import { DualBell } from './Charts'
import { I, Icon } from './Icons'
import { Confidence, TeamMark } from './Marks'
import { ScaledCanvas } from './ScaledCanvas'
import { fmtEdge, fmtMu, fmtPct, kickoffLocal, previewModel } from '../lib/preview'
import { useSlate } from '../lib/slate'

const NAV = [
  ['Overview', I.grid],
  ['Games', I.calendar],
  ['Ask BlueChip', I.chat],
  ['Models', I.layers],
  ['Markets', I.trend],
  ['Teams', I.users],
  ['Backtests', I.flask],
  ['Research', I.book],
  ['Pricing', I.card],
  ['Settings', I.cog],
] as const

/** Product UI mock — real HTML of the desk, not an iframe and not a PNG. */
export function ProductMock() {
  const { games, count, status } = useSlate()
  const rows = useMemo(
    () => games.slice(0, 7).map((g) => ({ g, p: previewModel(g.game_id, g.home_spread, g.home_team, g.away_team) })),
    [games],
  )
  const selected = rows[0]
  const disagreements = rows.filter((r) => Math.abs(r.p.edgePp ?? 0) >= 2).length
  const modeled = count.nfl + count.cfb

  return (
    <div className="chrome">
      <div className="chrome-bar">
        <span className="chrome-dots" aria-hidden>
          <i />
          <i />
          <i />
        </span>
        <div className="chrome-url">
          <img src={brand.icon} alt="" width={12} height={12} />
          app.bluechipwager.com/desk
        </div>
        <span className="chrome-label">Product preview</span>
      </div>
      <ScaledCanvas width={1440}>
        <div className="desk desk-mock" aria-hidden>
          <aside className="side">
            <div className="brand">
              <img className="brand-icon" src={brand.icon} alt="" width={28} height={28} />
              <strong>BlueChipWager</strong>
            </div>
            <nav>
              {NAV.map(([label, d], i) => (
                <span key={label} className={i === 0 ? 'is-on' : ''}>
                  <Icon d={d} />
                  {label}
                </span>
              ))}
            </nav>
            <footer className="side-foot">
              <strong>v0.1 Research Preview</strong>
              <ul>
                <li className="is-live">
                  <i /> Data live
                </li>
                <li>
                  <i /> Models in development
                </li>
              </ul>
            </footer>
          </aside>
          <div>
            <div className="topbar">
              <div className="seg">
                <button className="is-on" type="button">
                  All
                </button>
                <button type="button">NFL</button>
                <button type="button">CFB</button>
              </div>
              <div className="search-wrap" style={{ flex: 1, maxWidth: 280 }}>
                <Icon d={I.search} size={15} />
                <input className="ask-input" readOnly tabIndex={-1} value="Search teams, games, papers…" />
              </div>
              <div className="health-dot" title={status}>
                <i />
                Data health 99.8%
              </div>
            </div>
            <div className="desk-main" style={{ paddingBottom: 24 }}>
              <div className="page-h">
                <div>
                  <h1>Football Research Desk</h1>
                  <p className="muted">
                    {modeled ? `${count.nfl} NFL + ${count.cfb} FBS in the ESPN window` : 'Loading this week’s slate…'}
                  </p>
                </div>
                <span className="preview-flag">Preview overlay · not BCW-RIDGE-v0.1</span>
              </div>
              <div className="kpis">
                <article className="kpi">
                  <span>Games modeled</span>
                  <b>{modeled || '—'}</b>
                </article>
                <article className="kpi">
                  <span>Models active</span>
                  <b>7</b>
                </article>
                <article className="kpi">
                  <span>Market disagreements</span>
                  <b>{modeled ? disagreements : '—'}</b>
                </article>
                <article className="kpi">
                  <span>Data health</span>
                  <b className="good">99.8%</b>
                </article>
              </div>
              <section className="card">
                <h2>This week’s board</h2>
                <table className="board">
                  <thead>
                    <tr>
                      <th>Game</th>
                      <th>Kickoff</th>
                      <th>Market</th>
                      <th>BlueChip margin</th>
                      <th>Win %</th>
                      <th>Cover %</th>
                      <th>Edge</th>
                      <th>Confidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.length === 0 && (
                      <tr>
                        <td colSpan={8} className="muted">
                          {status}
                        </td>
                      </tr>
                    )}
                    {rows.map(({ g, p }) => (
                      <tr key={g.game_id}>
                        <td>
                          <div className="game-cell">
                            <div className="logos">
                              <TeamMark abbr={g.away_team} league={g.league} />
                              <TeamMark abbr={g.home_team} league={g.league} />
                            </div>
                            <strong>
                              {g.away_team} {g.neutral ? 'vs' : '@'} {g.home_team}
                            </strong>
                          </div>
                        </td>
                        <td>{kickoffLocal(g.kickoff)}</td>
                        <td>{g.spread_label ?? '—'}</td>
                        <td>{fmtMu(p.muHome, g.home_team, g.away_team)}</td>
                        <td>{fmtPct(p.winHome)}</td>
                        <td>{fmtPct(p.coverTicket)}</td>
                        <td className={(p.edgePp ?? 0) >= 0 ? 'good' : 'bad'}>{fmtEdge(p.edgePp)}</td>
                        <td>
                          <Confidence level={p.confidence} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </section>
              <div className="grid-3">
                <section className="card">
                  <h2>Model status</h2>
                  <p className="muted" style={{ marginTop: 0, fontSize: 12 }}>
                    Ridge in development · baselines on snapshots
                  </p>
                  <ul className="detail-list" style={{ fontSize: 12, margin: 0 }}>
                    <li>BCW-RIDGE-v0.1 — In development</li>
                    <li>Elo / SRS / HFA — Baseline</li>
                  </ul>
                </section>
                <section className="card">
                  <h2>Projected margin</h2>
                  <DualBell mu={selected?.p.muHome ?? 3.2} line={selected?.p.spreadLine ?? 2.5} />
                </section>
                <section className="card">
                  <h2>Ask BlueChip</h2>
                  <p className="muted" style={{ marginTop: 0, fontSize: 12 }}>
                    Grounded on the desk, not a RAG opinion.
                  </p>
                  <div className="sample-answer" style={{ marginTop: 0 }}>
                    <div className="stat">
                      <span>Cover (preview)</span>
                      <b>{fmtPct(selected?.p.coverTicket ?? 0.562)}</b>
                    </div>
                  </div>
                </section>
              </div>
            </div>
          </div>
        </div>
      </ScaledCanvas>
      <Link className="chrome-hit" to="/desk">
        <span>Open the live desk</span>
      </Link>
    </div>
  )
}
