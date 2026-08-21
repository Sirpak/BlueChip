/** Illustrative Stern-style preview. Not BCW-RIDGE-v0.1. */

const SIGMA = 13.5

function erf(x: number): number {
  const sign = x < 0 ? -1 : 1
  const ax = Math.abs(x)
  const t = 1 / (1 + 0.3275911 * ax)
  const y =
    1 -
    ((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t - 0.284496736) * t + 0.254829592) *
      t *
      Math.exp(-ax * ax)
  return sign * y
}

export function normCdf(z: number): number {
  return 0.5 * (1 + erf(z / Math.SQRT2))
}

export function hash32(s: string): number {
  let h = 2166136261
  for (let i = 0; i < s.length; i += 1) {
    h ^= s.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return h >>> 0
}

/** nflverse: positive spread_line ⇒ home favored. Betting home_spread: negative ⇒ home favored. */
export function spreadLineFromBetting(homeSpread: number): number {
  return -homeSpread
}

export function pHomeWin(muHome: number, sigma = SIGMA): number {
  return 1 - normCdf((0.5 - muHome) / sigma)
}

export function pHomeCover(muHome: number, spreadLine: number, sigma = SIGMA): number {
  return 1 - normCdf((spreadLine + 0.5 - muHome) / sigma)
}

export type PreviewModel = {
  preview: true
  spreadLine: number | null
  muHome: number | null
  winHome: number | null
  coverHome: number | null
  coverTicket: number | null
  favorite: string | null
  edgePp: number | null
  confidence: 'Low' | 'Medium' | 'High'
  modelsFavor: number
}

const BREAK_EVEN = 0.5238

export function previewModel(gameId: string, homeSpread: number | null, home: string, away: string): PreviewModel {
  if (homeSpread == null || Number.isNaN(homeSpread)) {
    return {
      preview: true,
      spreadLine: null,
      muHome: null,
      winHome: null,
      coverHome: null,
      coverTicket: null,
      favorite: null,
      edgePp: null,
      confidence: 'Low',
      modelsFavor: 0,
    }
  }
  const spreadLine = spreadLineFromBetting(homeSpread)
  const jitter = ((hash32(gameId) % 31) - 15) / 10
  const muHome = spreadLine + jitter
  const winHome = pHomeWin(muHome)
  const coverHome = pHomeCover(muHome, spreadLine)
  const homeFav = spreadLine > 0
  const coverTicket = homeFav ? coverHome : 1 - coverHome
  const favorite = homeFav ? home : away
  const edgePp = (coverTicket - BREAK_EVEN) * 100
  const absEdge = Math.abs(edgePp)
  const confidence: PreviewModel['confidence'] = absEdge >= 4 ? 'High' : absEdge >= 2 ? 'Medium' : 'Low'
  const modelsFavor = 3 + (hash32(gameId + 'm') % 4)
  return {
    preview: true,
    spreadLine,
    muHome,
    winHome,
    coverHome,
    coverTicket,
    favorite,
    edgePp,
    confidence,
    modelsFavor: Math.min(6, modelsFavor),
  }
}

export function fmtPct(p: number | null, digits = 1): string {
  if (p == null) return '—'
  return `${(p * 100).toFixed(digits)}%`
}

export function fmtEdge(pp: number | null): string {
  if (pp == null) return '—'
  const sign = pp > 0 ? '+' : ''
  return `${sign}${pp.toFixed(1)}pp`
}

export function fmtMu(mu: number | null, home: string, away: string): string {
  if (mu == null) return '—'
  if (Math.abs(mu) < 0.05) return 'Pick'
  if (mu > 0) return `${home} -${Math.abs(mu).toFixed(1)}`
  return `${away} -${Math.abs(mu).toFixed(1)}`
}

export function kickoffLocal(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

export function dateKey(iso: string | null, fallback: string | null): string {
  if (iso) return iso.slice(0, 10)
  return fallback ?? ''
}
