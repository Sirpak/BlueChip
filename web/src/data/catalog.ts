export type ModelStatus = 'production' | 'development' | 'baseline' | 'research' | 'validation' | 'future' | 'retired'

export type ModelMetric = {
  brier: string
  logLoss: string
  mae: string
  rmse: string
  ats: string
  n: string
  calibration: string
  lastTrained: string
  version: string
}

export type ModelEntry = {
  id: string
  name: string
  tagline: string
  status: ModelStatus
  predicts: string
  formula: string
  features: string[]
  training: string
  holdout: string
  marketFeatures: string
  validation: string
  limitations: string[]
  papers: { title: string; url?: string }[]
  performanceByYear?: { season: string; note: string }[]
  coefficients?: string
}

const emptyMetrics: ModelMetric = {
  brier: '—',
  logLoss: '—',
  mae: '—',
  rmse: '—',
  ats: '—',
  n: '—',
  calibration: '—',
  lastTrained: '—',
  version: '—',
}

export const PRODUCT_STATUS = {
  label: 'v0.1 Research Preview',
  items: [
    { label: 'Data live', live: true },
    { label: 'Models in development', live: false },
    { label: 'Market engine', live: true },
    { label: 'Ask BlueChip', live: false },
  ],
} as const

export const PRODUCTION_MODEL_ID = 'bcw-ridge-v0-1'

export const MODELS: ModelEntry[] = [
  {
    id: 'bcw-ridge-v0-1',
    name: 'BCW-RIDGE-v0.1',
    tagline: 'Published pregame expected margin (home − away)',
    status: 'development',
    predicts: 'Expected home margin μ before kickoff. Stern maps μ to P(win), P(cover), and push.',
    formula: 'ŷ = β₀ + Σⱼ βⱼ xⱼ   with L2 penalty  λ Σⱼ βⱼ²',
    features: [
      'EWMA opponent-adjusted EPA diffs (α=0.20, frozen on 2009–2022)',
      'Elo / SRS diffs',
      'Success-rate and explosive-play diffs',
      'Rest differential',
      'Home indicator',
    ],
    training: '2009–2022 walk-forward (development window)',
    holdout: '2023–2025 opens once after freeze',
    marketFeatures: 'None in PURE feature set',
    validation: 'Season walk-forward inside 2009–2022. Sacred holdout opened exactly once after features, α, λ, and metrics freeze.',
    limitations: [
      'Not published until ship gates pass (leakage, calibration, baseline beat, n, uncertainty).',
      'Continuous Normal around μ is Stage 1 — key numbers 3 and 7 are later.',
      'Desk cover % today is Stern + preview jitter, not this model.',
    ],
    papers: [
      { title: 'Stern (1991) — margin as Normal', url: 'https://www.jstor.org/stable/2983059' },
      { title: 'Lopez, Matthews & Baumer (2018) — EPA predictors' },
    ],
    performanceByYear: [],
    coefficients: 'Coefficients publish with model freeze.',
  },
  {
    id: 'bcw-elo',
    name: 'Elo',
    tagline: 'Recursive team-strength baseline',
    status: 'baseline',
    predicts: 'P(home win) from pre-update ratings. Rating diff also feeds Ridge.',
    formula: 'R_home ← R_home + K(actual − expected); expected uses HFA = 55 Elo pts',
    features: ['Pre-update Elo home/away', '25% regression to 1500 between seasons'],
    training: '1999–present walk (1999–2008 initializes)',
    holdout: 'Same sacred window as Ridge — not used for tuning',
    marketFeatures: 'None',
    validation: 'Written onto BCW-SNAP-v0.1 snapshots. Leaderboard metrics pending walk-forward report.',
    limitations: ['Reference baseline, not the published number.', 'No margin-of-victory scaling in v0.1.'],
    papers: [{ title: 'Moreland & Superdock — Elo-style margin ratings', url: 'https://arxiv.org/abs/1802.00527' }],
  },
  {
    id: 'bcw-srs',
    name: 'SRS',
    tagline: 'Opponent-adjusted point differential (Massey-style)',
    status: 'baseline',
    predicts: 'Expected margin ≈ SRS_home − SRS_away + HFA',
    formula: 'Linear SOS system: R_i − R_j ≈ home margin; mean-centered',
    features: ['Completed REG game margins only', 'Refit when calendar date changes'],
    training: 'Expanding window through prior games',
    holdout: 'Not used for v0.1 tuning',
    marketFeatures: 'None',
    validation: 'On snapshots. 2009–2022 smoke MAE ≈ 11.18 vs realized margin (not ATS leaderboard).',
    limitations: ['Extra baseline — not an ensemble member.', 'Does not replace Ridge as published μ.'],
    papers: [{ title: 'PFR Simple Rating System glossary' }],
  },
  {
    id: 'bcw-hfa',
    name: 'Mean + Home Field',
    tagline: 'Expanding mean home margin (HFA baseline)',
    status: 'baseline',
    predicts: 'μ ≈ historical average REG home margin',
    formula: 'μ = mean(home_margin) over completed REG games (default 2.0 until n ≥ 80)',
    features: ['None — intercept-only'],
    training: 'Expanding through prior REG games',
    holdout: 'Not used for tuning',
    marketFeatures: 'None',
    validation: 'Everything else must beat this on the real leaderboard.',
    limitations: ['HFA ~1.5–2.5 pts in modern NFL, not 3.', '2020 down-weight is post-freeze.'],
    papers: [{ title: 'Margin research foundation (008)' }],
  },
  {
    id: 'bcw-opp-adj-epa',
    name: 'Opponent-adjusted EPA',
    tagline: 'Ridge decomposition of team-game EPA',
    status: 'baseline',
    predicts: 'Off/def strength in EPA/play units; adj_pred_margin on snapshots',
    formula: 'off_epa ≈ Off_i + Def_j + HFA·home  (λ = 5)',
    features: ['Prior team-game EPA only', 'Date-change refit (Thu → Sun)'],
    training: 'Expanding prior games',
    holdout: 'Not used for tuning',
    marketFeatures: 'None',
    validation: 'Stored on BCW-SNAP-v0.1. Ridge chooses raw vs adj EPA on 2009–2022.',
    limitations: ['EPA/play ≠ points until Ridge maps features to μ.', 'No ST or QB layer in v0.1.'],
    papers: [{ title: 'ESPN FPI methodology (design reference)', url: 'https://www.espn.com/nfl/story/_/id/13539941/how-espn-nfl-football-power-index-was-developed-implemented' }],
  },
  {
    id: 'bcw-logistic',
    name: 'Logistic',
    tagline: 'Home-win probability classifier',
    status: 'research',
    predicts: 'P(home win) = σ(β₀ + βᵀx)',
    formula: 'Binary logistic with L2; pregame rolling x only',
    features: ['Elo diff', 'SRS diff', 'Adj-EPA diffs', 'Success-rate diff', 'Rest diff', 'Home'],
    training: '2009–2022 (next on path)',
    holdout: '2023–2025 once',
    marketFeatures: 'None',
    validation: 'Brier, log loss, calibration buckets — not headline accuracy.',
    limitations: ['Not implemented yet.', 'Winner accuracy ≠ ATS; cover needs F_M.'],
    papers: [{ title: 'Palomino et al. (2016)', url: 'https://arxiv.org/abs/1601.04302' }],
  },
  {
    id: 'bcw-lgbm',
    name: 'LightGBM',
    tagline: 'Structured ML margin / winner models',
    status: 'research',
    predicts: 'Research-only winner or margin after Ridge freeze',
    formula: 'Gradient boosted trees on snapshot superset',
    features: ['Smaller X than CFB 714-feature experiment', 'Same chronological folds as Ridge'],
    training: 'Post-freeze only',
    holdout: '2023–2025 once',
    marketFeatures: 'None in PURE v0.1',
    validation: 'Keep Ridge in production unless Brier/MAE/calibration improve stably.',
    limitations: ['Not in v0.1.', 'Desk must not show fake 56.2% from this model.'],
    papers: [{ title: 'CFBD LightGBM experiment', url: 'https://blog.collegefootballdata.com/predicting-spreads-gbdt/' }],
  },
  {
    id: 'bcw-prob-margin',
    name: 'Probabilistic Margin',
    tagline: 'Learned or empirical margin distribution',
    status: 'research',
    predicts: 'F_M(x) for P(cover), P(push) — not a single cover classifier',
    formula: 'NGBoost, Student-t, empirical residual, BALE-inspired',
    features: ['Ridge μ as location', 'Residual distribution from walk-forward errors'],
    training: 'After Ridge freeze',
    holdout: '2023–2025 once',
    marketFeatures: 'Benchmark vs close separately',
    validation: 'CRPS, log likelihood, spread-probability calibration.',
    limitations: ['Stage 2+.', 'Global σ=13.5 is Stern default, not final uncertainty.'],
    papers: [{ title: 'NFL margin as random variable (PMC10929675)' }],
  },
  {
    id: 'bcw-ensemble',
    name: 'Ensemble',
    tagline: 'Consensus across model families',
    status: 'future',
    predicts: 'Desk may show disagreement matrix — not averaged tout number',
    formula: 'BCW-CONSENSUS after OOS predictions exist for baselines + ML + distributions',
    features: ['Model outputs only'],
    training: 'Post v0.1',
    holdout: '—',
    marketFeatures: '—',
    validation: 'Never the published v0.1 number.',
    limitations: ['Future.', 'No ROI-weighted blending at launch.'],
    papers: [],
  },
  {
    id: 'bcw-wp-xgb',
    name: 'WP XGBoost',
    tagline: 'In-game win probability (nflfastR-class)',
    status: 'research',
    predicts: 'P(posteam wins | play state). Parallel live lab — not the pregame published number.',
    formula: 'Gradient boosted trees on down, distance, score, time, EPA features',
    features: ['Play-state features from nflfastR WP trainer', 'Not pregame snapshot features'],
    training: 'LOSO / season holdouts in ml/reference/nflfastr',
    holdout: 'Does not open the pregame 2023–2025 holdout',
    marketFeatures: 'Must not use vegas_wp in PURE pregame',
    validation: 'Compare to nflverse wp; MARKET WP vs vegas_wp is a separate experiment.',
    limitations: ['Live/in-game research only.', 'Must not mix with Ridge μ on the slate.'],
    papers: [{ title: 'nflfastR WP/EP', url: 'https://www.nflfastr.com/' }],
  },
]

export function getModel(id: string): ModelEntry | undefined {
  return MODELS.find((m) => m.id === id)
}

export function metricsFor(model: ModelEntry): ModelMetric {
  if (model.status === 'production' || model.status === 'development') {
    return { ...emptyMetrics, version: model.id.toUpperCase(), lastTrained: 'Pending freeze' }
  }
  if (model.status === 'baseline') {
    return { ...emptyMetrics, version: 'BCW-SNAP-v0.1', lastTrained: 'On snapshots' }
  }
  return emptyMetrics
}

export const STATUS_LABEL: Record<ModelStatus, string> = {
  production: 'Production',
  development: 'In development',
  baseline: 'Baseline',
  research: 'Research',
  validation: 'Validation',
  future: 'Future',
  retired: 'Retired',
}

export type StudyCategory =
  | 'Model Research'
  | 'NFL Analytics'
  | 'CFB Analytics'
  | 'Market Research'
  | 'Probability & Calibration'
  | 'BlueChip Experiments'

export type Study = {
  id: string
  question: string
  hypothesis: string
  category: StudyCategory
  status: 'planned' | 'in_progress' | 'published'
}

export const RESEARCH_CATEGORIES: StudyCategory[] = [
  'Model Research',
  'NFL Analytics',
  'CFB Analytics',
  'Market Research',
  'Probability & Calibration',
  'BlueChip Experiments',
]

export const BLUECHIP_STUDIES: Study[] = [
  { id: 'adj-vs-raw', question: 'Does opponent-adjusted EPA outperform raw EPA?', hypothesis: 'Ridge(raw) vs Ridge(adj) decided on 2009–2022 before holdout opens.', category: 'Model Research', status: 'in_progress' },
  { id: 'ridge-lgbm', question: 'Ridge vs LightGBM on the same NFL snapshots?', hypothesis: 'Keep Ridge unless Brier/MAE/calibration improve stably.', category: 'Model Research', status: 'planned' },
  { id: 'elo-srs', question: 'Elo vs SRS as a margin baseline?', hypothesis: 'SRS is hard to beat by accident; Elo is a win-prob reference.', category: 'Model Research', status: 'planned' },
  { id: 'hfa-shrink', question: 'How much does home field matter / is HFA shrinking?', hypothesis: 'Modern HFA ~1.5–2.5; down-weight 2020.', category: 'NFL Analytics', status: 'planned' },
  { id: 'rest', question: 'Does short rest actually hurt NFL teams?', hypothesis: 'Rest diff ≥ 3 days moves margin ~0.3–0.5 pts.', category: 'NFL Analytics', status: 'planned' },
  { id: 'epa-recency', question: 'How stable is EPA after Week 4 (3 / 5 / 8 games)?', hypothesis: 'EWMA α and window choice matter; tune on 2009–2022 only.', category: 'NFL Analytics', status: 'in_progress' },
  { id: 'qb', question: 'How much does quarterback quality move a spread?', hypothesis: 'Largest situational swing (~7 pts) — CONTEXT, not v0.1 PURE.', category: 'NFL Analytics', status: 'planned' },
  { id: 'weather', question: 'Does weather materially affect totals?', hypothesis: 'Wind >15 mph affects pass EPA; forecast ≠ observation.', category: 'NFL Analytics', status: 'planned' },
  { id: 'start-year', question: 'Does 1999-era data improve current prediction?', hypothesis: 'Start-year A–D on one 2023–2025 pass after freeze.', category: 'NFL Analytics', status: 'planned' },
  { id: 'cfb-later', question: 'Which CFB features transfer after NFL gates?', hypothesis: 'Smaller X than CFBD 714-feature GBDT; same contract.', category: 'CFB Analytics', status: 'planned' },
  { id: 'market-close', question: 'How much of median margin does the close already explain?', hypothesis: 'Hunt narrow deviations vs Market 0; do not out-predict closes from scratch.', category: 'Market Research', status: 'published' },
  { id: 'key-numbers', question: 'How important are NFL key numbers 3 and 7?', hypothesis: 'Stage 2 ordered-logistic / empirical — not a reason to abandon Stern in v0.1.', category: 'Probability & Calibration', status: 'planned' },
  { id: 'residuals', question: 'Which residual distribution best models NFL margins?', hypothesis: 'Normal σ=13.5 is Stage 1; t / empirical / NGBoost later.', category: 'Probability & Calibration', status: 'planned' },
  { id: 'calibration', question: 'Calibration of BCW probabilities vs headline ATS%', hypothesis: 'Brier and calibration buckets beat a naked 56.2%.', category: 'Probability & Calibration', status: 'planned' },
  { id: 'snap-superset', question: 'Snapshot columns vs Ridge freeze subset', hypothesis: 'Store a superset; freeze one feature_version on 2009–2022.', category: 'BlueChip Experiments', status: 'in_progress' },
]

export type ExternalResearch = {
  id: string
  title: string
  source: string
  url?: string
  summary: string
  bcwUse: string
}

export const EXTERNAL_RESEARCH: ExternalResearch[] = [
  {
    id: 'fpi',
    title: 'ESPN FPI methodology',
    source: 'ESPN',
    url: 'https://www.espn.com/nfl/story/_/id/13539941/how-espn-nfl-football-power-index-was-developed-implemented',
    summary: 'Opponent-adjusted EPA off/def + ST; QB when backup; travel and rest as game factors.',
    bcwUse: 'Design reference for opp-adj EPA and future Power Index — not a v0.1 feature dump.',
  },
  {
    id: 'nflfastr',
    title: 'nflfastR EP / WP research',
    source: 'nflverse',
    url: 'https://www.nflfastr.com/',
    summary: 'Expected points and win probability from historical play states.',
    bcwUse: 'Parallel WP/EP replication lab — not the pregame launch model.',
  },
  {
    id: 'srs',
    title: 'Simple Rating System (SRS)',
    source: 'Pro-Football-Reference',
    summary: 'Iterative strength-of-schedule adjusted point differential.',
    bcwUse: 'BCW-SRS baseline on snapshots; must beat HFA on leaderboard.',
  },
  {
    id: 'elo',
    title: 'Elo-style margin ratings',
    source: 'Moreland & Superdock',
    url: 'https://arxiv.org/abs/1802.00527',
    summary: 'Ratings that target margins, not only W/L.',
    bcwUse: 'BCW-ELO reference; margin-Elo is post-v0.1.',
  },
  {
    id: 'margin-dist',
    title: 'NFL margin distribution',
    source: 'PMC10929675',
    summary: 'Margin as a random variable; quantiles vs spread.',
    bcwUse: 'Motivates Probabilistic Margin / F_M instead of cover classifiers.',
  },
  {
    id: 'cfbd-gbdt',
    title: 'CFBD LightGBM experiment',
    source: 'CollegeFootballData',
    url: 'https://blog.collegefootballdata.com/predicting-spreads-gbdt/',
    summary: '17k CFB games; winner AUC ~0.87; margin RMSE ~15.7.',
    bcwUse: 'CFB blueprint after NFL gates — smaller feature set first on NFL.',
  },
  {
    id: 'calibration',
    title: 'Calibration vs accuracy',
    source: 'BlueChip 004',
    summary: 'Well-calibrated probabilities beat flashy wrong confidence.',
    bcwUse: 'Ship gates require calibration buckets before public cover %.',
  },
  {
    id: 'market-prior',
    title: 'Close captures median variation',
    source: 'PMC10306238',
    url: 'https://pmc.ncbi.nlm.nih.gov/articles/PMC10306238/',
    summary: 'Closing line explains most median-outcome variation — hunt narrow deviations.',
    bcwUse: 'Market 0 is the prior and hardest benchmark; edge = model p − no-vig p.',
  },
]
