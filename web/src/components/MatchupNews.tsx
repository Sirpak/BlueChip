import { useEffect, useState } from 'react'
import { fetchGameNews, type GameNews, type GameNewsArticle, type UpcomingGame } from '../lib/api'

const BUCKET_LABEL: Record<string, string> = {
  availability: 'Availability',
  analysis: 'Analysis',
  matchup: 'Matchup',
  update: 'Updates',
  general: 'Other',
}

function timeLabel(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

function NewsRow({ article }: { article: GameNewsArticle }) {
  return (
    <a className="news-row" href={article.url} target="_blank" rel="noreferrer">
      <div className="news-row-main">
        <div className="news-row-meta">
          <span className={`news-bucket news-bucket-${article.bucket}`}>
            {BUCKET_LABEL[article.bucket] ?? article.bucket}
          </span>
          <span className="muted">{article.publisher || article.source}</span>
          <span className="muted">{article.team_abbr}</span>
          {article.published ? <span className="muted">{timeLabel(article.published)}</span> : null}
        </div>
        <strong>{article.headline}</strong>
        {article.description ? <p className="muted news-desc">{article.description}</p> : null}
      </div>
      <span className="news-open" aria-hidden>
        →
      </span>
    </a>
  )
}

export function MatchupNews({ game }: { game: UpcomingGame }) {
  const [data, setData] = useState<GameNews | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let live = true
    setLoading(true)
    setError(null)
    fetchGameNews(game)
      .then((payload) => {
        if (!live) return
        setData(payload)
      })
      .catch(() => {
        if (!live) return
        setError('News feed unavailable right now.')
      })
      .finally(() => {
        if (live) setLoading(false)
      })
    return () => {
      live = false
    }
  }, [game.game_id, game.away_espn_id, game.home_espn_id, game.league])

  return (
    <section className="card" style={{ marginTop: 12 }}>
      <h2>Latest news &amp; analysis</h2>
      <p className="muted" style={{ marginTop: 0 }}>
        Multi-source desk feed (ESPN + Google News aggregate — FOX, Yahoo, CBS, AP, and others when
        available). Ranked: availability → analysis → matchup → updates. Not used in BCW-RIDGE PURE.
      </p>
      {loading ? <p className="muted">Loading news…</p> : null}
      {error ? <p className="muted">{error}</p> : null}
      {!loading && !error && data && data.count === 0 ? (
        <p className="muted">No recent ESPN articles for these teams in the current window.</p>
      ) : null}
      {data && data.articles.length > 0 ? (
        <div className="news-list">
          {data.articles.map((a) => (
            <NewsRow key={a.id} article={a} />
          ))}
        </div>
      ) : null}
      {data?.disclaimer ? (
        <p className="muted" style={{ marginTop: 12, fontSize: 12 }}>
          {data.disclaimer}
        </p>
      ) : null}
    </section>
  )
}
