/** Fan-friendly definitions for hover hints and the About page. */

export type GlossaryEntry = {
  id: string
  term: string
  short: string
  long?: string
  group: 'basics' | 'metrics' | 'models' | 'markets' | 'process'
}

export const GLOSSARY: GlossaryEntry[] = [
  {
    id: 'spread',
    term: 'Spread / line',
    short: 'The points the favorite is expected to win by. A “−7” home line means the market expects the home team to win by about 7.',
    long: 'On BlueChip, a positive home spread means the home team is favored (same convention as nflverse). The number next to a team is how many points they give (favorite) or get (underdog).',
    group: 'basics',
  },
  {
    id: 'cover',
    term: 'Cover',
    short: 'Did the favorite beat the spread, or did the underdog stay within the points?',
    long: 'If KC is −7 and wins by 10, KC covered. If they win by 3, the underdog covered. A push is an exact land on the number.',
    group: 'basics',
  },
  {
    id: 'ats',
    term: 'ATS',
    short: 'Against the spread — win/loss record versus the betting line, not just who won the game.',
    group: 'basics',
  },
  {
    id: 'mu',
    term: 'μ (projected margin)',
    short: 'Our model’s best guess for home score minus away score before kickoff.',
    long: 'Positive μ means we expect the home team to win. This is a research number until gates pass — not a public “lock.”',
    group: 'basics',
  },
  {
    id: 'research-preview',
    term: 'Research Preview',
    short: 'Honest work-in-progress output. Useful for learning, not a published betting recommendation.',
    group: 'basics',
  },
  {
    id: 'public-probability',
    term: 'Public probability / cover %',
    short: 'A published chance a team covers the spread. BlueChip will not show this until quality gates pass.',
    group: 'basics',
  },
  {
    id: 'holdout',
    term: 'Holdout (2023–2025)',
    short: 'Sealed test seasons we refuse to peek at while tuning. Like grading a final exam only once.',
    group: 'process',
  },
  {
    id: 'walk-forward',
    term: 'Walk-forward',
    short: 'Train on the past, predict the next week/season, then roll forward. Prevents cheating with future info.',
    group: 'process',
  },
  {
    id: 'leakage',
    term: 'Leakage',
    short: 'Accidentally using information you would not have known before kickoff. We block that in “PURE” models.',
    group: 'process',
  },
  {
    id: 'snapshot',
    term: 'Snapshot',
    short: 'A frozen pregame feature pack for one game — stats known before kickoff only.',
    group: 'process',
  },
  {
    id: 'pure',
    term: 'PURE model',
    short: 'Football fundamentals only (EPA, Elo, rest, home). No injuries, weather, or news inside the score.',
    group: 'process',
  },
  {
    id: 'context',
    term: 'CONTEXT',
    short: 'Helpful desk info (news, polls, weather later) that is shown to you but not mixed into the v0.1 PURE model.',
    group: 'process',
  },
  {
    id: 'epa',
    term: 'EPA',
    short: 'Expected Points Added — how much a play (or team) helps or hurts scoring chances versus average.',
    long: 'Higher offense EPA is better. Lower defense EPA allowed is better. Think “efficiency,” not just yards.',
    group: 'metrics',
  },
  {
    id: 'success-rate',
    term: 'Success rate',
    short: 'Share of plays that are “successful” (enough yards for the down). More stable than raw yards.',
    group: 'metrics',
  },
  {
    id: 'explosive',
    term: 'Explosive plays',
    short: 'Big chunk gains (long runs/passes). High explosive rate = more home-run plays.',
    group: 'metrics',
  },
  {
    id: 'net-epa',
    term: 'Net EPA',
    short: 'Offense EPA minus defense EPA allowed — a quick “are they better than average overall?” number.',
    group: 'metrics',
  },
  {
    id: 'brier',
    term: 'Brier score',
    short: 'How accurate probability forecasts are. Lower is better. 0 = perfect, 0.25 ≈ coin-flip on 50/50 games.',
    group: 'metrics',
  },
  {
    id: 'log-loss',
    term: 'Log loss',
    short: 'Another probability accuracy score that heavily punishes being confidently wrong. Lower is better.',
    group: 'metrics',
  },
  {
    id: 'mae',
    term: 'MAE',
    short: 'Mean Absolute Error — average points we miss the final margin by. Lower is better.',
    long: 'If MAE is ~10.5, we are typically about 10–11 points off the final home−away score difference.',
    group: 'metrics',
  },
  {
    id: 'rmse',
    term: 'RMSE',
    short: 'Like MAE but weights big misses more. Lower is better.',
    group: 'metrics',
  },
  {
    id: 'calibration',
    term: 'Calibration',
    short: 'When we say “60%,” does that side actually win about 60% of the time? Well-calibrated = trustworthy odds language.',
    group: 'metrics',
  },
  {
    id: 'n',
    term: 'n (sample size)',
    short: 'How many games went into the number. Small n = take it with a grain of salt.',
    group: 'metrics',
  },
  {
    id: 'ridge',
    term: 'Ridge (BCW-RIDGE)',
    short: 'Our main margin model: blends several team stats and gently shrinks wild coefficients so it does not overfit.',
    long: 'Published target is Ridge μ + Stern conversion. Elo/SRS are references, not an average of models.',
    group: 'models',
  },
  {
    id: 'stern',
    term: 'Stern',
    short: 'A classic way to turn a projected margin into win/cover chances using a bell curve of football margins.',
    group: 'models',
  },
  {
    id: 'elo',
    term: 'Elo',
    short: 'A rating that rises after wins and falls after losses. Bigger upsets move ratings more.',
    group: 'models',
  },
  {
    id: 'srs',
    term: 'SRS',
    short: 'Simple Rating System — strength rating based on margin of victory and quality of opponents.',
    group: 'models',
  },
  {
    id: 'hfa',
    term: 'HFA',
    short: 'Home-field advantage — the typical points boost for playing at home (modern NFL is often ~1.5–2.5, not 3).',
    group: 'models',
  },
  {
    id: 'opp-adj-epa',
    term: 'Opponent-adjusted EPA',
    short: 'EPA that tries to credit/debit how tough the opponent was — not just raw box-score efficiency.',
    group: 'models',
  },
  {
    id: 'logistic',
    term: 'Logistic model',
    short: 'A model aimed at win probability (who wins), not the exact point margin.',
    group: 'models',
  },
  {
    id: 'market-0',
    term: 'Market 0 / close',
    short: 'The closing sportsbook line — our hardest benchmark. Beating it is rare and must be proven carefully.',
    group: 'markets',
  },
  {
    id: 'no-vig',
    term: 'No-vig / de-vig',
    short: 'Remove the sportsbook’s built-in juice so two sides add to 100%. Fairer “true odds” for comparison.',
    group: 'markets',
  },
  {
    id: 'break-even',
    term: 'Break-even',
    short: 'The win rate you need to profit at a price. At −110, you need about 52.4% to break even long-term.',
    group: 'markets',
  },
  {
    id: 'edge',
    term: 'Edge',
    short: 'Our chance minus the market’s fair chance. Positive edge is theoretical value — not a guarantee.',
    group: 'markets',
  },
  {
    id: 'american-odds',
    term: 'American odds',
    short: '−110 means risk $110 to win $100. +150 means risk $100 to win $150.',
    group: 'markets',
  },
  {
    id: 'ap-top25',
    term: 'AP Top 25',
    short: 'College football media poll. Opinion ranking — not the same as our model strength list.',
    group: 'basics',
  },
  {
    id: 'power-rankings',
    term: 'Power rankings',
    short: 'A subjective 1–32 (or Top 25) ordering from writers or models. Ours is labeled Research Preview.',
    group: 'basics',
  },
  {
    id: 'bcw-strength',
    term: 'BCW strength',
    short: 'Our blend of Elo, SRS, and efficiency to rank teams — for research context, not a bet slip.',
    group: 'models',
  },
]

const BY_ID = Object.fromEntries(GLOSSARY.map((e) => [e.id, e])) as Record<string, GlossaryEntry>

/** Map common UI labels → glossary ids */
export const LABEL_HINTS: Record<string, string> = {
  'EPA / play': 'epa',
  'Pass EPA': 'epa',
  'Rush EPA': 'epa',
  'Defensive EPA': 'epa',
  'Success rate': 'success-rate',
  'Explosive rate': 'explosive',
  'Net EPA': 'net-epa',
  EPA: 'epa',
  Elo: 'elo',
  SRS: 'srs',
  HFA: 'hfa',
  'Opp-adj EPA': 'opp-adj-epa',
  Brier: 'brier',
  'Log loss': 'log-loss',
  MAE: 'mae',
  RMSE: 'rmse',
  ATS: 'ats',
  'ATS vs close': 'ats',
  n: 'n',
  N: 'n',
  Spread: 'spread',
  Market: 'market-0',
  'Market 0': 'market-0',
  'No-vig': 'no-vig',
  'De-vig': 'no-vig',
  'Break-even': 'break-even',
  Edge: 'edge',
  Stern: 'stern',
  Ridge: 'ridge',
  'BCW-RIDGE': 'ridge',
  'BCW Research Preview': 'research-preview',
  'Public probability': 'public-probability',
  'Cover %': 'public-probability',
  Holdout: 'holdout',
  Snapshot: 'snapshot',
  PURE: 'pure',
  CONTEXT: 'context',
  Calibration: 'calibration',
  μ: 'mu',
  Strength: 'bcw-strength',
  'AP Top 25': 'ap-top25',
  'Power rankings': 'power-rankings',
}

export function glossaryEntry(idOrLabel: string): GlossaryEntry | undefined {
  if (BY_ID[idOrLabel]) return BY_ID[idOrLabel]
  const mapped = LABEL_HINTS[idOrLabel]
  if (mapped) return BY_ID[mapped]
  const lower = idOrLabel.toLowerCase()
  return GLOSSARY.find((e) => e.term.toLowerCase() === lower || e.id === lower)
}

export const GROUP_LABEL: Record<GlossaryEntry['group'], string> = {
  basics: 'Football & betting basics',
  metrics: 'Numbers on the desk',
  models: 'What our models do',
  markets: 'Odds & market language',
  process: 'How we keep results honest',
}
