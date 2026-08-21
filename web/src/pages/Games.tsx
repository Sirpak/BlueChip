import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { TeamMark } from '../components/Marks'
import { Hint } from '../components/Hint'
import { weeklyMuLabel } from '../components/WeeklyDeskCard'
import { SlateIntelligenceChip } from '../components/GameIntelligenceBrief'
import { fetchIntelligenceIndex, fetchWeeklySlate, type WeeklyCard, type WeeklySlate } from '../lib/api'
import { dateKey } from '../lib/preview'
import { useSlate } from '../lib/slate'

export function Games() {
  const { games, count } = useSlate()
  const [params, setParams] = useSearchParams()
  const league = (params.get('league') as 'All' | 'NFL' | 'CFB') || 'All'
  const [week, setWeek] = useState<number | 'all'>('all')
  const [stype, setStype] = useState<'all' | 'PRE' | 'REG' | 'POST'>('all')
  const [ask, setAsk] = useState('')
  const [weekly, setWeekly] = useState<Record<string, WeeklyCard>>({})
  const [bestCfb, setBestCfb] = useState<WeeklySlate['highest_confidence_cfb_week1']>()
  const [intelIndex, setIntelIndex] = useState<
    Record<string, { lean_team?: string; top_edges?: string[]; summary_short?: string }>
  >({})

  const weeks = useMemo(() => {
    const set = new Set<number>()
    for (const g of games) {
      if (g.week != null) set.add(g.week)
    }
    const found = [...set].sort((a, b) => a - b)
    return found.length ? found : Array.from({ length: 18 }, (_, i) => i + 1)
  }, [games])

  useEffect(() => {
    let live = true
    Promise.all([fetchWeeklySlate(), fetchIntelligenceIndex()])
      .then(([payload, intel]) => {
        if (!live) return
        setWeekly(payload.by_game_id || {})
        setBestCfb(payload.highest_confidence_cfb_week1)
        setIntelIndex(intel.packages || {})
      })
      .catch(() => {
        if (!live) return
        setWeekly({})
        setIntelIndex({})
      })
    return () => {
      live = false
    }
  }, [])

  const dates = useMemo(() => {
    const map = new Map<string, number>()
    for (const g of games) {
      const k = dateKey(g.kickoff, g.game_date)
      if (!k) continue
      map.set(k, (map.get(k) ?? 0) + 1)
    }
    return [...map.entries()].sort((a, b) => a[0].localeCompare(b[0]))
  }, [games])

  const selectedDate = params.get('date') || ''

  const filtered = useMemo(() => {
    return games
      .filter((g) => (league === 'All' ? true : g.league === league))
      .filter((g) => !selectedDate || dateKey(g.kickoff, g.game_date) === selectedDate)
      .filter((g) => week === 'all' || g.week === week)
      .filter((g) => stype === 'all' || g.season_type === stype)
      .map((g) => g)
  }, [games, league, selectedDate, week, stype])

  const selected = filtered[0]
  const contextGame = selected

  const setLeague = (v: string) => {
    params.set('league', v)
    setParams(params)
  }

  return (
    <>
      <div className="page-h">
        <div>
          <h1>Games</h1>
          <p className="muted">
            Schedules and <Hint t="spread">market lines</Hint>. Featured weekly cards show desk μ + AI handicapper.
            Confused by a term? <Link to="/about">About in plain English</Link>.
          </p>
        </div>
        <span className="preview-flag">
          {count.nfl} NFL · {count.cfb} CFB
        </span>
      </div>

      {bestCfb && (
        <div className="best-conf-banner">
          <span className="muted">Highest confidence · CFB Week 1</span>
          <b>
            Bet {bestCfb.recommendation_team} · {Number(bestCfb.confidence_pct).toFixed(1)}%
          </b>
          <span className="muted">
            {bestCfb.matchup}
            {bestCfb.spread_label ? ` · ${bestCfb.spread_label}` : ''}
          </span>
          <Link className="chip" to={`/games/${encodeURIComponent(bestCfb.game_id)}`}>
            Open preview
          </Link>
        </div>
      )}

      {Object.keys(weekly).length > 0 && (
        <section className="card" style={{ marginBottom: 12 }}>
          <div className="weekly-card-head">
            <div>
              <h2 style={{ margin: 0 }}>Featured weekly desk</h2>
              <p className="muted" style={{ margin: '4px 0 0' }}>
                Week 1 CFB/NFL — click any game for snapshot pending + bet lean + confidence %.
              </p>
            </div>
          </div>
          <div className="featured-grid">
            {Object.values(weekly)
              .filter((c) => c.featured || c.league === 'CFB')
              .sort(
                (a, b) =>
                  Number(b.projection.confidence_pct ?? 0) - Number(a.projection.confidence_pct ?? 0),
              )
              .slice(0, 12)
              .map((c) => (
              <Link key={c.game_id} className="featured-chip" to={`/games/${encodeURIComponent(c.game_id)}`}>
                <strong>
                  {c.away_team} @ {c.home_team}
                </strong>
                <span className="muted">{c.league} W{c.week ?? 1}</span>
                <SlateIntelligenceChip
                  lean={intelIndex[c.game_id]?.lean_team || c.ai.recommendation_team}
                  edges={intelIndex[c.game_id]?.top_edges}
                  market={c.spread_label}
                  mu={c.projection.mu_home}
                />
                <span className="weekly-mu">{weeklyMuLabel(c)}</span>
              </Link>
            ))}
          </div>
        </section>
      )}

      <div className="filters">
        <select className="filter-sel" value={league} onChange={(e) => setLeague(e.target.value)}>
          <option value="All">All leagues</option>
          <option value="NFL">NFL</option>
          <option value="CFB">College Football</option>
        </select>
        <select className="filter-sel" value={stype} onChange={(e) => setStype(e.target.value as typeof stype)}>
          <option value="all">All rounds</option>
          <option value="PRE">Preseason</option>
          <option value="REG">Regular</option>
          <option value="POST">Playoffs</option>
        </select>
        <select className="filter-sel" defaultValue="2026">
          <option>Season 2026</option>
          <option>Season 2025</option>
        </select>
        <select
          className="filter-sel"
          value={week === 'all' ? 'all' : String(week)}
          onChange={(e) => setWeek(e.target.value === 'all' ? 'all' : Number(e.target.value))}
        >
          <option value="all">All weeks</option>
          {weeks.map((w) => (
            <option key={w} value={w}>
              Week {w}
            </option>
          ))}
        </select>
        <select className="filter-sel" defaultValue="">
          <option value="">Conference</option>
          <option>AFC</option>
          <option>NFC</option>
          <option>SEC</option>
          <option>Big Ten</option>
        </select>
        <input className="filter-sel" placeholder="Team search" style={{ minWidth: 140 }} />
      </div>

      <div className="dates">
        <button type="button" className={`date-chip ${week === 'all' ? 'is-on' : ''}`} onClick={() => setWeek('all')}>
          <span>Wk</span>
          <b>All</b>
        </button>
        {weeks.slice(0, 18).map((w) => (
          <button key={w} type="button" className={`date-chip ${week === w ? 'is-on' : ''}`} onClick={() => setWeek(w)}>
            <span>Week</span>
            <b>{w}</b>
          </button>
        ))}
      </div>

      {dates.length > 0 && (
        <div className="dates" style={{ marginTop: 0 }}>
          {dates.slice(0, 10).map(([d, n]) => {
            const dt = new Date(`${d}T12:00:00`)
            return (
              <button
                key={d}
                type="button"
                className={`date-chip ${selectedDate === d ? 'is-on' : ''}`}
                onClick={() => {
                  params.set('date', d)
                  setParams(params)
                }}
              >
                <span>{dt.toLocaleDateString(undefined, { weekday: 'short' })}</span>
                <b>{dt.getDate()}</b>
                <span>{n}</span>
              </button>
            )
          })}
        </div>
      )}

      {selected && (
        <div className="grid-12" style={{ marginBottom: 12 }}>
          <section className="card">
            <h2>{selected.matchup}</h2>
            <p className="muted">BCW-RIDGE-PURE is a Research Preview. Public cover % is not published.</p>
          </section>
          <section className="card">
            <h2>Sit</h2>
            <div className="sit">
              <div>
                <strong>Spread</strong>
                {selected.spread_label ?? '—'}
              </div>
              <div>
                <strong>Total</strong>
                {selected.total_line ?? '—'}
              </div>
              <div>
                <strong>Public probability</strong>
                Not yet published
              </div>
            </div>
          </section>
        </div>
      )}

      <section className="card">
        <table className="board desk-only">
          <thead>
            <tr>
              <th>Game</th>
              <th>Spread</th>
              <th>Total</th>
              <th>BCW Research Preview</th>
              <th>Bet / confidence</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((g) => (
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
                        {g.away_name} {g.neutral ? 'vs' : '@'} {g.home_name}
                      </div>
                    </div>
                  </Link>
                </td>
                <td>{g.spread_label ?? '—'}</td>
                <td>{g.total_line ?? '—'}</td>
                <td className="muted">Snapshot pending</td>
                <td className={weekly[g.game_id] ? 'weekly-mu' : 'muted'}>
                  {weekly[g.game_id] ? weeklyMuLabel(weekly[g.game_id]) : '—'}
                </td>
                <td>
                  <Link className="chip" to={`/games/${encodeURIComponent(g.game_id)}`}>
                    Matchup
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="mobile-only">
          {filtered.slice(0, 10).map((g) => (
            <Link className="mobile-game" key={g.game_id} to={`/games/${encodeURIComponent(g.game_id)}`}>
              <strong>
                {g.away_team} @ {g.home_team}
              </strong>
              <div className="muted">
                {weekly[g.game_id]
                  ? `${g.spread_label} · ${weeklyMuLabel(weekly[g.game_id])}`
                  : `${g.spread_label} · probability not published`}
              </div>
            </Link>
          ))}
        </div>
      </section>

      <form
        className="ask-sticky"
        onSubmit={(e) => {
          e.preventDefault()
          const q = ask || `Ask BlueChip about ${contextGame?.matchup ?? 'this game'}`
          window.location.href = `/ask?q=${encodeURIComponent(q)}`
        }}
      >
        <input
          className="ask-input"
          value={ask}
          onChange={(e) => setAsk(e.target.value)}
          placeholder={`Ask BlueChip about ${contextGame?.matchup ?? 'this game'}`}
        />
        <Link className="btn btn-primary" to={`/ask?q=${encodeURIComponent(ask || `Ask BlueChip about ${contextGame?.matchup ?? 'this game'}`)}`}>
          Ask
        </Link>
      </form>
    </>
  )
}
