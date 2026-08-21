function gauss(x: number, mu: number, s: number) {
  return Math.exp(-0.5 * ((x - mu) / s) ** 2)
}

function path(mu: number, s: number, min: number, max: number, w: number, h: number, pad = 18) {
  const n = 72
  let peak = 0
  const xs: number[] = []
  for (let i = 0; i <= n; i += 1) {
    const x = min + ((max - min) * i) / n
    xs.push(x)
    peak = Math.max(peak, gauss(x, mu, s))
  }
  const xOf = (v: number) => ((v - min) / (max - min)) * w
  const yOf = (v: number) => h - pad - (gauss(v, mu, s) / peak) * (h - pad - 12)
  return `M0,${h - pad} ` + xs.map((x) => `L${xOf(x)},${yOf(x)}`).join(' ') + ` L${w},${h - pad} Z`
}

export function DualBell({ mu, line }: { mu: number; line: number }) {
  const w = 420
  const h = 148
  const min = -24
  const max = 24
  const xOf = (v: number) => ((v - min) / (max - min)) * w
  return (
    <svg className="chart" viewBox={`0 0 ${w} ${h}`} role="img" aria-label="Projected margin">
      <path d={path(line, 13.5, min, max, w, h)} fill="rgba(17, 24, 39, 0.10)" />
      <path d={path(mu, 13.5, min, max, w, h)} fill="rgba(5, 150, 105, 0.28)" />
      <line x1={xOf(line)} y1={10} x2={xOf(line)} y2={h - 16} stroke="#0f2744" strokeDasharray="3 3" />
      <line x1={xOf(mu)} y1={10} x2={xOf(mu)} y2={h - 16} stroke="#059669" />
      <text x={8} y={14} fontSize="10" fill="#6b7280">
        Market
      </text>
      <text x={w - 78} y={14} fontSize="10" fill="#059669">
        BlueChip μ
      </text>
    </svg>
  )
}

export function Reliability() {
  const w = 280
  const h = 120
  const pts = [0.1, 0.18, 0.28, 0.41, 0.52, 0.61, 0.7, 0.78, 0.86]
  const bw = w / pts.length - 4
  return (
    <svg className="chart" viewBox={`0 0 ${w} ${h}`} aria-label="Reliability">
      <line x1="0" y1={h} x2={w} y2="0" stroke="#d0d5dd" strokeDasharray="3 3" />
      {pts.map((p, i) => (
        <rect key={i} x={i * (w / pts.length) + 2} y={h - p * (h - 8)} width={bw} height={p * (h - 8)} fill="#93c5fd" rx="1" />
      ))}
      <polyline fill="none" stroke="#2563eb" strokeWidth="1.8" points={pts.map((p, i) => `${(i / 8) * w},${h - p * h}`).join(' ')} />
    </svg>
  )
}

export function Sparkline({ seed, up }: { seed: number; up: boolean }) {
  const w = 72
  const h = 22
  const pts: string[] = []
  let y = 11
  for (let i = 0; i < 12; i += 1) {
    y += ((seed >> (i % 8)) & 1 ? 1 : -1) * (up ? 1.1 : 0.8)
    y = Math.min(20, Math.max(3, y))
    pts.push(`${(i / 11) * w},${y}`)
  }
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} aria-hidden>
      <polyline fill="none" stroke={up ? '#2f7d57' : '#c4473a'} strokeWidth="1.6" points={pts.join(' ')} />
    </svg>
  )
}

export function Consensus({ rows }: { rows: { name: string; p: number }[] }) {
  return (
    <div className="dots">
      {rows.map((r) => (
        <div className="dot-row" key={r.name}>
          <span>{r.name}</span>
          <div className="dot-track">
            <span className="dot-mark" style={{ left: `calc(${(r.p - 0.46) / 0.16} * 100% - 7px)` }} />
          </div>
          <b>{(r.p * 100).toFixed(1)}%</b>
        </div>
      ))}
    </div>
  )
}
