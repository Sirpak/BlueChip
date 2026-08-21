import { hash32 } from './preview'

export type CmpMetric = {
  name: string
  home: number
  away: number
  unit: 'epa' | 'rate' | 'text'
  note?: string
}

function signed(h: number, i: number, scale: number) {
  const v = ((h >> (i * 3)) & 31) / 31
  return (v - 0.42) * scale
}

export function comparisonMetrics(gameId: string): CmpMetric[] {
  const h = hash32(gameId)
  const h2 = hash32(gameId + 'b')
  return [
    { name: 'EPA / play', home: signed(h, 0, 0.22), away: signed(h2, 0, 0.22), unit: 'epa' },
    { name: 'Pass EPA', home: signed(h, 1, 0.28), away: signed(h2, 1, 0.28), unit: 'epa' },
    { name: 'Rush EPA', home: signed(h, 2, 0.18), away: signed(h2, 2, 0.18), unit: 'epa' },
    { name: 'Success rate', home: 0.42 + signed(h, 3, 0.12), away: 0.42 + signed(h2, 3, 0.12), unit: 'rate' },
    { name: 'Defensive EPA', home: signed(h, 4, 0.2), away: signed(h2, 4, 0.2), unit: 'epa' },
    { name: 'Explosive rate', home: 0.09 + Math.abs(signed(h, 5, 0.06)), away: 0.09 + Math.abs(signed(h2, 5, 0.06)), unit: 'rate' },
  ]
}

export function fmtMetric(m: CmpMetric, side: 'home' | 'away'): string {
  const v = m[side]
  if (m.unit === 'rate') return `${(v * 100).toFixed(1)}%`
  return `${v >= 0 ? '+' : ''}${v.toFixed(3)}`
}
