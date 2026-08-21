import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { can } from '../lib/entitlements'
import { UpgradeCard } from '../components/Locked'
import { Hint, HintLabel } from '../components/Hint'
import {
  fetchRankings,
  fetchTeamNews,
  fetchTeams,
  type DeskTeam,
  type GameNewsArticle,
  type League,
  type RankingsBundle,
  type RankRow,
} from '../lib/api'

type Tab = 'rankings' | 'team-news'

function RankTable({
  rows,
  mode,
}: {
  rows: RankRow[]
  mode: 'ap' | 'bcw'
}) {
  return (
    <div className="rank-table">
      <div className="rank-head">
        <span>#</span>
        <span>Team</span>
        {mode === 'bcw' ? (
          <>
            <span>
              <HintLabel t="bcw-strength">Strength</HintLabel>
            </span>
            <span>
              <HintLabel t="Elo">Elo</HintLabel>
            </span>
            <span>
              <HintLabel t="SRS">SRS</HintLabel>
            </span>
            <span>
              <HintLabel t="Net EPA">Net EPA</HintLabel>
            </span>
          </>
        ) : (
          <>
            <span>Record</span>
            <span />
            <span />
            <span />
          </>
        )}
      </div>
      {rows.map((r) => (
        <div className="rank-row" key={`${r.rank}-${r.team || r.name}`}>
          <span className="rank-num">{r.rank}</span>
          <span className="rank-team">
            {r.logo_url ? <img src={r.logo_url} alt="" width={22} height={22} /> : null}
            {r.team_url ? (
              <a href={r.team_url} target="_blank" rel="noreferrer">
                <strong>{r.team || r.name}</strong>
                {r.name && r.team && r.name !== r.team ? <span className="muted"> {r.name}</span> : null}
              </a>
            ) : (
              <strong>{r.team || r.name}</strong>
            )}
          </span>
          {mode === 'bcw' ? (
            <>
              <span>{r.strength ?? '—'}</span>
              <span>{r.elo ?? '—'}</span>
              <span>{r.srs ?? '—'}</span>
              <span>{r.net_epa ?? '—'}</span>
            </>
          ) : (
            <>
              <span>{r.record ?? '—'}</span>
              <span />
              <span />
              <span />
            </>
          )}
        </div>
      ))}
    </div>
  )
}

function NewsList({ articles }: { articles: GameNewsArticle[] }) {
  return (
    <div className="news-list">
      {articles.map((a) => (
        <a key={a.id} className="news-row" href={a.url} target="_blank" rel="noreferrer">
          <div className="news-row-main">
            <div className="news-row-meta">
              <span className={`news-bucket news-bucket-${a.bucket}`}>{a.bucket}</span>
              <span className="muted">{a.publisher || a.source}</span>
            </div>
            <strong>{a.headline}</strong>
            {a.description ? <p className="muted news-desc">{a.description}</p> : null}
          </div>
          <span className="news-open">→</span>
        </a>
      ))}
    </div>
  )
}

export function Teams() {
  const { user } = useAuth()
  const allowed = can(user, 'teams_basic')
  const [tab, setTab] = useState<Tab>('rankings')
  const [league, setLeague] = useState<League>('NFL')
  const [rankings, setRankings] = useState<RankingsBundle | null>(null)
  const [teams, setTeams] = useState<DeskTeam[]>([])
  const [selectedId, setSelectedId] = useState<string>('')
  const [news, setNews] = useState<GameNewsArticle[]>([])
  const [teamUrl, setTeamUrl] = useState<string | null>(null)
  const [status, setStatus] = useState('Loading…')
  const [error, setError] = useState<string | null>(null)

  const selected = useMemo(
    () => teams.find((t) => t.espn_id === selectedId) || teams[0] || null,
    [teams, selectedId],
  )

  useEffect(() => {
    if (!allowed) return
    let live = true
    setError(null)
    fetchRankings()
      .then((payload) => {
        if (live) setRankings(payload)
      })
      .catch(() => {
        if (live) setError('Rankings unavailable.')
      })
    return () => {
      live = false
    }
  }, [allowed])

  useEffect(() => {
    if (!allowed) return
    let live = true
    setStatus(`Loading ${league} teams…`)
    fetchTeams(league)
      .then((payload) => {
        if (!live) return
        setTeams(payload.teams)
        setSelectedId(payload.teams[0]?.espn_id || '')
        setStatus(`${payload.count} ${league} teams`)
      })
      .catch(() => {
        if (live) setStatus('Team directory unavailable')
      })
    return () => {
      live = false
    }
  }, [allowed, league])

  useEffect(() => {
    if (!allowed || !selected?.espn_id) {
      setNews([])
      return
    }
    let live = true
    fetchTeamNews(selected)
      .then((payload) => {
        if (!live) return
        setNews(payload.articles || [])
        setTeamUrl(payload.team_url || selected.team_url || null)
      })
      .catch(() => {
        if (live) setNews([])
      })
    return () => {
      live = false
    }
  }, [allowed, selected])

  if (!allowed) {
    return (
      <>
        <div className="page-h">
          <h1>Teams</h1>
        </div>
        <UpgradeCard title="Teams" plan="Free">
          Sign in to browse rankings and team news.
        </UpgradeCard>
      </>
    )
  }

  return (
    <>
      <div className="page-h">
        <div>
          <h1>Teams &amp; rankings</h1>
          <p className="muted">
            <Hint t="ap-top25">AP Top 25</Hint>, NFL{' '}
            <Hint t="power-rankings">power-ranking</Hint> coverage,{' '}
            <Hint t="bcw-strength">BCW strength</Hint>, and per-team news. Plain-English glossary:{' '}
            <Link to="/about">About</Link>.
          </p>
        </div>
        <span className="preview-flag">Research Preview</span>
      </div>

      <div className="matchup-tabs" role="tablist">
        {(
          [
            ['rankings', 'Rankings'],
            ['team-news', 'Team news'],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={tab === id}
            className={`matchup-tab ${tab === id ? 'is-on' : ''}`}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </div>

      {error ? <p className="muted">{error}</p> : null}

      {tab === 'rankings' && (
        <div className="rank-grid">
          <section className="card">
            <h2>BCW NFL strength</h2>
            <p className="muted">
              Our preseason / carry-in list from snapshot Elo + SRS + net EPA (
              {rankings?.bcw_nfl_strength.method || 'model blend'}). Not a published betting board.
            </p>
            {rankings?.bcw_nfl_strength.rows?.length ? (
              <RankTable rows={rankings.bcw_nfl_strength.rows} mode="bcw" />
            ) : (
              <p className="muted">Building from snapshots…</p>
            )}
            {rankings?.bcw_nfl_strength.disclaimer ? (
              <p className="muted" style={{ marginTop: 12, fontSize: 12 }}>
                {rankings.bcw_nfl_strength.disclaimer}
              </p>
            ) : null}
          </section>

          <section className="card">
            <h2>AP Top 25 (CFB)</h2>
            <p className="muted">
              Live ESPN poll feed
              {rankings?.ap_top25.season ? ` · ${rankings.ap_top25.season}` : ''}
              {rankings?.ap_top25.source_url ? (
                <>
                  {' '}
                  ·{' '}
                  <a href={rankings.ap_top25.source_url} target="_blank" rel="noreferrer">
                    ESPN rankings
                  </a>
                </>
              ) : null}
            </p>
            {rankings?.ap_top25.rows?.length ? (
              <RankTable rows={rankings.ap_top25.rows} mode="ap" />
            ) : (
              <p className="muted">Loading AP poll…</p>
            )}
          </section>

          <section className="card">
            <h2>NFL power rankings (press)</h2>
            <p className="muted">
              {rankings?.nfl_power_ranking_stories.note ||
                'Latest power-ranking stories from ESPN and other outlets.'}
            </p>
            <div className="news-list" style={{ marginTop: 12 }}>
              {(rankings?.nfl_power_ranking_stories.articles || []).map((a) => (
                <a key={a.url} className="news-row" href={a.url} target="_blank" rel="noreferrer">
                  <div className="news-row-main">
                    <div className="news-row-meta">
                      <span className="muted">{a.publisher}</span>
                    </div>
                    <strong>{a.headline}</strong>
                  </div>
                  <span className="news-open">→</span>
                </a>
              ))}
              {!rankings?.nfl_power_ranking_stories.articles?.length ? (
                <p className="muted">No recent power-ranking stories found.</p>
              ) : null}
            </div>
          </section>

          <section className="card">
            <h2>BCW CFB strength</h2>
            <p className="muted">
              {rankings?.bcw_cfb_strength.disclaimer ||
                'Queued until NFL gates pass and CFB ingest starts.'}
            </p>
          </section>
        </div>
      )}

      {tab === 'team-news' && (
        <>
          <div className="team-toolbar">
            <div className="matchup-tabs" style={{ marginBottom: 0 }}>
              {(['NFL', 'CFB'] as const).map((v) => (
                <button
                  key={v}
                  type="button"
                  className={`matchup-tab ${league === v ? 'is-on' : ''}`}
                  onClick={() => setLeague(v)}
                >
                  {v}
                </button>
              ))}
            </div>
            <select
              className="team-select"
              value={selected?.espn_id || ''}
              onChange={(e) => setSelectedId(e.target.value)}
            >
              {teams.map((t) => (
                <option key={t.espn_id || t.abbr || ''} value={t.espn_id || ''}>
                  {t.name || t.abbr}
                </option>
              ))}
            </select>
            <span className="muted">{status}</span>
          </div>

          <section className="card" style={{ marginTop: 12 }}>
            <div className="page-h" style={{ marginBottom: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                {selected?.logo_url ? (
                  <img src={selected.logo_url} alt="" width={36} height={36} />
                ) : null}
                <div>
                  <h2 style={{ margin: 0 }}>{selected?.name || 'Team'}</h2>
                  <p className="muted" style={{ margin: 0 }}>
                    {selected?.abbr} · ESPN team feed
                    {teamUrl ? (
                      <>
                        {' '}
                        ·{' '}
                        <a href={teamUrl} target="_blank" rel="noreferrer">
                          Open ESPN page
                        </a>
                      </>
                    ) : null}
                  </p>
                </div>
              </div>
            </div>
            {news.length ? <NewsList articles={news} /> : <p className="muted">No articles yet for this team.</p>}
          </section>
        </>
      )}
    </>
  )
}
