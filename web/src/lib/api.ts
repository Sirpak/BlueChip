export type League = 'NFL' | 'CFB'

export type UpcomingGame = {
  league: League
  game_id: string
  kickoff: string | null
  game_date: string | null
  week: number | null
  season: number | null
  season_type: string | null
  away_team: string
  home_team: string
  away_name: string
  home_name: string
  away_espn_id?: string | null
  home_espn_id?: string | null
  neutral: boolean
  matchup: string
  home_spread: number | null
  spread_label: string | null
  total_line: number | null
  book: string | null
  round: string | null
  status: string | null
}

export type Slate = {
  as_of: string
  horizon_days: number
  nfl: UpcomingGame[]
  cfb: UpcomingGame[]
  count: { nfl: number; cfb: number }
}

export async function fetchSlate(): Promise<Slate> {
  const res = await fetch('/games/upcoming', { credentials: 'include' })
  if (!res.ok) throw new Error(`slate ${res.status}`)
  return res.json() as Promise<Slate>
}

export type NewsBucket = 'availability' | 'analysis' | 'matchup' | 'update' | 'general'

export type GameNewsArticle = {
  id: string
  headline: string
  description: string | null
  url: string
  published: string | null
  source: string
  publisher?: string
  team_side: string
  team_abbr: string
  bucket: NewsBucket | string
  relevance_score: number
  image_url: string | null
  context_only: boolean
}

export type GameNews = {
  source: string
  sources?: string[]
  publishers?: string[]
  as_of: string
  disclaimer: string
  articles: GameNewsArticle[]
  by_bucket: Record<string, GameNewsArticle[]>
  count: number
}

export async function fetchGameNews(g: UpcomingGame): Promise<GameNews> {
  const q = new URLSearchParams({
    league: g.league,
    away_team: g.away_team,
    home_team: g.home_team,
    limit: '12',
  })
  if (g.away_espn_id) q.set('away_espn_id', g.away_espn_id)
  if (g.home_espn_id) q.set('home_espn_id', g.home_espn_id)
  if (g.away_name) q.set('away_name', g.away_name)
  if (g.home_name) q.set('home_name', g.home_name)
  const res = await fetch(`/api/games/news?${q}`, { credentials: 'include' })
  if (!res.ok) throw new Error(`news ${res.status}`)
  return res.json() as Promise<GameNews>
}

export type RankRow = {
  rank: number | null
  previous?: number | null
  team?: string | null
  name?: string | null
  espn_id?: string | null
  record?: string | null
  logo_url?: string | null
  team_url?: string | null
  strength?: number | null
  elo?: number | null
  srs?: number | null
  net_epa?: number | null
  as_of_season?: number | null
  as_of_week?: number | null
}

export type RankingsBundle = {
  as_of: string
  ap_top25: {
    poll: string
    season?: number
    week?: number
    source_url?: string
    rows: RankRow[]
    count: number
  }
  nfl_power_ranking_stories: {
    note: string
    articles: { headline: string; url: string; published: string | null; publisher: string }[]
    count: number
  }
  bcw_nfl_strength: {
    model: string
    status: string
    method?: string
    season_cap?: number
    disclaimer: string
    rows: RankRow[]
    count: number
  }
  bcw_cfb_strength: {
    status: string
    disclaimer: string
    rows: RankRow[]
    count: number
  }
}

export type DeskTeam = {
  espn_id: string | null
  abbr: string | null
  name: string | null
  slug?: string | null
  logo_url?: string | null
  team_url?: string | null
  league: League
}

export async function fetchRankings(): Promise<RankingsBundle> {
  const res = await fetch('/api/rankings', { credentials: 'include' })
  if (!res.ok) throw new Error(`rankings ${res.status}`)
  return res.json() as Promise<RankingsBundle>
}

export async function fetchTeams(league: League): Promise<{ teams: DeskTeam[]; count: number }> {
  const res = await fetch(`/api/teams?league=${league}`, { credentials: 'include' })
  if (!res.ok) throw new Error(`teams ${res.status}`)
  return res.json() as Promise<{ teams: DeskTeam[]; count: number }>
}

export async function fetchTeamNews(
  team: DeskTeam,
): Promise<GameNews & { team_url?: string | null; name?: string }> {
  const q = new URLSearchParams({
    league: team.league,
    espn_id: team.espn_id || '',
    abbr: team.abbr || 'TEAM',
    limit: '12',
  })
  if (team.name) q.set('name', team.name)
  const res = await fetch(`/api/teams/news?${q}`, { credentials: 'include' })
  if (!res.ok) throw new Error(`team news ${res.status}`)
  return res.json()
}

export type WeeklyCard = {
  game_id: string
  league: League
  week?: number | null
  matchup?: string
  away_team: string
  home_team: string
  away_name?: string
  home_name?: string
  away_espn_id?: string | null
  home_espn_id?: string | null
  spread_label?: string | null
  home_spread?: number | null
  total_line?: number | null
  featured?: boolean
  projection: {
    model_id: string
    method: string
    mu_home: number
    p_home_win: number
    p_home_cover: number | null
    edge_vs_minus_110: number | null
    model_lean: string
    model_lean_team: string
    confidence_pct?: number
    label: string
  }
  news: { headline: string; publisher: string; bucket: string; url: string }[]
  ai: {
    provider: string
    model: string
    analysis: string
    confidence: string
    confidence_pct?: number
    recommendation_team: string
    recommendation_side: string
    disclaimer: string
  }
}

export type WeeklySlate = {
  available: boolean
  published_at?: string
  title?: string
  counts?: { nfl: number; cfb: number; total: number; ai_enriched?: number }
  highest_confidence?: {
    game_id: string
    league: League
    matchup: string
    recommendation_team: string
    confidence_pct: number
    spread_label?: string | null
  }
  highest_confidence_cfb_week1?: {
    game_id: string
    league: League
    matchup: string
    recommendation_team: string
    confidence_pct: number
    spread_label?: string | null
  }
  cards?: WeeklyCard[]
  by_game_id?: Record<string, WeeklyCard>
  message?: string
}

export async function fetchWeeklySlate(): Promise<WeeklySlate> {
  const res = await fetch('/api/weekly/slate', { credentials: 'include' })
  if (!res.ok) throw new Error(`weekly ${res.status}`)
  return res.json() as Promise<WeeklySlate>
}

export async function fetchWeeklyGame(gameId: string): Promise<{ available: boolean; card?: WeeklyCard }> {
  const q = new URLSearchParams({ game_id: gameId })
  const res = await fetch(`/api/weekly/game?${q}`, { credentials: 'include' })
  if (!res.ok) throw new Error(`weekly game ${res.status}`)
  return res.json()
}

export type GameIntelligencePackage = {
  game_id: string
  version: string
  generated_at: string
  source_set_hash: string
  lean_team: string
  summary_short: string
  summary_full: string
  generation_provider?: string
  generation_model?: string
  game: {
    matchup?: string
    home_team: string
    away_team: string
    spread_label?: string | null
  }
  projection?: { mu_home?: number; confidence_pct?: number; model_lean_team?: string }
  headline_cards?: {
    key: string
    marks: string
    fan_line: string
    title: string
    label: string
    why?: string
    percentile_hint?: string | null
  }[]
  slate_edges?: string[]
  matchup_logistic?: { p_home_win?: number; lean?: string; model_id?: string }
  paths?: { home?: string; away?: string }
  risks?: string[]
  events?: {
    event_type: string
    structured_fact: string
    source_url?: string
    publisher?: string
  }[]
  glossary?: Record<string, string>
  levels?: {
    slate?: {
      lean?: string
      top_edges?: string[]
      market?: string | null
      mu?: number | null
      confidence_pct?: number | null
    }
  }
}

export async function fetchIntelligenceIndex(): Promise<{
  available: boolean
  packages?: Record<string, { game_id: string; lean_team?: string; top_edges?: string[]; summary_short?: string }>
}> {
  const res = await fetch('/api/intelligence/index', { credentials: 'include' })
  if (!res.ok) throw new Error(`intel index ${res.status}`)
  return res.json()
}

export async function fetchIntelligenceGame(
  gameId: string,
): Promise<{ available: boolean; package?: GameIntelligencePackage }> {
  const q = new URLSearchParams({ game_id: gameId })
  const res = await fetch(`/api/intelligence/game?${q}`, { credentials: 'include' })
  if (!res.ok) throw new Error(`intel game ${res.status}`)
  return res.json()
}
