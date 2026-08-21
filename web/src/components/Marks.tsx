import { useState } from 'react'
import { canonicalizeNflTeam } from '../lib/nflTeams'

/** NFL abbr → ESPN CDN slug. CFB uses numeric espn_id (ncaa/500/{id}.png). */
const NFL: Record<string, string> = {
  ARI: 'ari', ATL: 'atl', BAL: 'bal', BUF: 'buf', CAR: 'car', CHI: 'chi', CIN: 'cin', CLE: 'cle',
  DAL: 'dal', DEN: 'den', DET: 'det', GB: 'gb', HOU: 'hou', IND: 'ind', JAX: 'jax',
  KC: 'kc', LV: 'lv', LAC: 'lac', LAR: 'lar', MIA: 'mia', MIN: 'min', NE: 'ne', NO: 'no',
  NYG: 'nyg', NYJ: 'nyj', PHI: 'phi', PIT: 'pit', SEA: 'sea', SF: 'sf', TB: 'tb', TEN: 'ten',
  WAS: 'wsh',
}

/** CFB logo id catalog (reference): https://gist.github.com/saiemgilani/c6596f0e1c8b148daabc2b7f1e6f6add */

function logoSrc(league: string, abbr: string, espnId?: string | null): string | null {
  if (league === 'CFB' && espnId) {
    return `https://a.espncdn.com/i/teamlogos/ncaa/500/${espnId}.png`
  }
  if (league === 'NFL') {
    const slug = NFL[canonicalizeNflTeam(abbr)]
    return slug ? `https://a.espncdn.com/i/teamlogos/nfl/500/${slug}.png` : null
  }
  return null
}

export function TeamMark({
  abbr,
  league,
  espnId,
}: {
  abbr: string
  league: string
  espnId?: string | null
}) {
  const [fail, setFail] = useState(false)
  const display = league === 'NFL' ? canonicalizeNflTeam(abbr) || abbr : abbr
  const src = logoSrc(league, display, espnId)
  if (src && !fail) {
    return (
      <img
        className="logo"
        alt=""
        width={22}
        height={22}
        src={src}
        onError={() => setFail(true)}
      />
    )
  }
  return <span className="logo-fb">{display.slice(0, 3)}</span>
}

export function Confidence({ level }: { level: 'Low' | 'Medium' | 'High' }) {
  return <span className={`pill pill-${level.toLowerCase()}`}>{level}</span>
}
