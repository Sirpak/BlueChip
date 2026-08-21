import { useState } from 'react'

const NFL: Record<string, string> = {
  ARI: 'ari', ATL: 'atl', BAL: 'bal', BUF: 'buf', CAR: 'car', CHI: 'chi', CIN: 'cin', CLE: 'cle',
  DAL: 'dal', DEN: 'den', DET: 'det', GB: 'gb', HOU: 'hou', IND: 'ind', JAX: 'jax', JAC: 'jax',
  KC: 'kc', LV: 'lv', LAC: 'lac', LAR: 'lar', MIA: 'mia', MIN: 'min', NE: 'ne', NO: 'no',
  NYG: 'nyg', NYJ: 'nyj', PHI: 'phi', PIT: 'pit', SEA: 'sea', SF: 'sf', TB: 'tb', TEN: 'ten',
  WAS: 'wsh', WSH: 'wsh', LA: 'lar',
}

export function TeamMark({ abbr, league }: { abbr: string; league: string }) {
  const [fail, setFail] = useState(false)
  const espn = league === 'NFL' ? NFL[abbr.toUpperCase()] : null
  if (espn && !fail) {
    return (
      <img
        className="logo"
        alt=""
        width={22}
        height={22}
        src={`https://a.espncdn.com/i/teamlogos/nfl/500/${espn}.png`}
        onError={() => setFail(true)}
      />
    )
  }
  return <span className="logo-fb">{abbr.slice(0, 3)}</span>
}

export function Confidence({ level }: { level: 'Low' | 'Medium' | 'High' }) {
  return <span className={`pill pill-${level.toLowerCase()}`}>{level}</span>
}
