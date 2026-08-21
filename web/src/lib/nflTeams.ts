/** Current 32 NFL franchises + historical abbr → current code. */

export const NFL_FRANCHISE_CANON: Record<string, string> = {
  STL: 'LAR',
  LA: 'LAR',
  OAK: 'LV',
  LVR: 'LV',
  SD: 'LAC',
  JAC: 'JAX',
  WSH: 'WAS',
}

export function canonicalizeNflTeam(abbr: string | null | undefined): string {
  if (!abbr) return ''
  const key = abbr.trim().toUpperCase()
  return NFL_FRANCHISE_CANON[key] ?? key
}
