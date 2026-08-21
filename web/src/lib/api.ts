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
