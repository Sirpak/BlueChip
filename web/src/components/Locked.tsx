import { Link } from 'react-router-dom'

export function UpgradeCard({
  title,
  plan = 'Pro',
  children,
}: {
  title: string
  plan?: string
  children?: string
}) {
  return (
    <section className="card upgrade-card">
      <h2>{title}</h2>
      <p className="muted">{children ?? `Available with BlueChip ${plan}.`}</p>
      <Link className="btn btn-primary" to="/pricing">
        Unlock {plan}
      </Link>
    </section>
  )
}

export function LockMark() {
  return (
    <span className="nav-lock" aria-hidden>
      🔒
    </span>
  )
}
