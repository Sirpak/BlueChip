import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import { brand } from '../brand'
import { I, Icon } from '../components/Icons'
import { UserMenu } from '../components/UserMenu'
import { fetchAdminDashboard, fetchAdminHealth, fetchAdminJson, fetchAdminModels, fetchAdminUsers } from '../lib/authApi'

const ADMIN_NAV = [
  ['', 'Dashboard', I.grid],
  ['health', 'System health', I.cog],
  ['pipeline', 'Data pipeline', I.db],
  ['models', 'Model ops', I.layers],
  ['experiments', 'Experiments', I.flask],
  ['predictions', 'Predictions', I.trend],
  ['users', 'Users', I.users],
  ['logs', 'Logs', I.book],
] as const

export function AdminShell() {
  return (
    <div className="desk admin-desk">
      <aside className="side">
        <Link to="/desk" className="brand">
          <img className="brand-icon" src={brand.icon} alt="" width={28} height={28} />
          <strong>Admin</strong>
        </Link>
        <nav>
          {ADMIN_NAV.map(([path, label, d]) => (
            <NavLink key={path || 'root'} to={path ? `/admin/${path}` : '/admin'} end={!path}>
              <Icon d={d} />
              {label}
            </NavLink>
          ))}
        </nav>
        <footer className="side-foot">
          <strong>Administrator</strong>
          <p className="muted" style={{ fontSize: 11, margin: '8px 0 0' }}>
            Not visible to USER accounts.
          </p>
        </footer>
      </aside>
      <div>
        <div className="topbar">
          <span className="preview-flag">Admin Console</span>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'center' }}>
            <Link className="btn" to="/desk">
              Back to desk
            </Link>
            <UserMenu />
          </div>
        </div>
        <div className="desk-main">
          <Outlet />
        </div>
      </div>
    </div>
  )
}

export function AdminDashboardPage() {
  const [dash, setDash] = useState<Record<string, unknown> | null>(null)
  const [health, setHealth] = useState<Record<string, unknown> | null>(null)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([fetchAdminDashboard(), fetchAdminHealth()])
      .then(([d, h]) => {
        setDash(d)
        setHealth(h)
      })
      .catch((e) => setErr(e instanceof Error ? e.message : 'Failed to load admin data'))
  }, [])

  if (err) {
    return (
      <section className="card">
        <h1>Access denied</h1>
        <p className="muted">{err}</p>
        <Link className="btn" to="/desk">
          Return to desk
        </Link>
      </section>
    )
  }

  return (
    <>
      <div className="page-h">
        <h1>Admin dashboard</h1>
      </div>
      <div className="kpis">
        <article className="kpi">
          <span>Deployed version</span>
          <b>{String(dash?.deployed_version ?? '—')}</b>
        </article>
        <article className="kpi">
          <span>Users</span>
          <b>{String(dash?.users ?? '—')}</b>
        </article>
        <article className="kpi">
          <span>Games in DB</span>
          <b>{String((health?.database as { games?: number })?.games ?? '—')}</b>
        </article>
        <article className="kpi">
          <span>Feature snapshots</span>
          <b>{String((health?.database as { feature_snapshots?: number })?.feature_snapshots ?? '—')}</b>
        </article>
      </div>
      <section className="card">
        <h2>Application status</h2>
        <pre className="admin-pre">{JSON.stringify(health, null, 2)}</pre>
      </section>
      <p className="muted">Pipeline jobs, model registry, logs, and cost dashboards — Sprint E.</p>
    </>
  )
}

export function AdminPlaceholder({ title }: { title: string }) {
  return (
    <section className="card">
      <h1>{title}</h1>
      <p className="muted">Placeholder — entitlement and route exist; deep UI later.</p>
    </section>
  )
}

export function AdminJsonPage({ title, path }: { title: string; path: string }) {
  const [data, setData] = useState<Record<string, unknown> | null>(null)
  const [err, setErr] = useState<string | null>(null)
  useEffect(() => {
    fetchAdminJson(path)
      .then(setData)
      .catch((e) => setErr(e instanceof Error ? e.message : 'Failed to load'))
  }, [path])
  if (err) {
    return (
      <section className="card">
        <h1>{title}</h1>
        <p className="muted">{err}</p>
      </section>
    )
  }
  return (
    <>
      <div className="page-h">
        <h1>{title}</h1>
      </div>
      <section className="card">
        <pre className="admin-pre">{JSON.stringify(data, null, 2)}</pre>
      </section>
    </>
  )
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, padding: '6px 0', borderBottom: '1px solid #eee' }}>
      <span className="muted">{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

export function AdminModelsPage() {
  const [data, setData] = useState<Record<string, unknown> | null>(null)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    fetchAdminModels()
      .then(setData)
      .catch((e) => setErr(e instanceof Error ? e.message : 'Failed to load model ops'))
  }, [])

  if (err) {
    return (
      <section className="card">
        <h1>Model operations</h1>
        <p className="muted">{err}</p>
      </section>
    )
  }

  const wf = data?.walk_forward as Record<string, unknown> | undefined
  const models = (wf?.models ?? {}) as Record<string, Record<string, unknown>>
  const ridge = models['BCW-RIDGE-v0.1'] as Record<string, unknown> | undefined

  return (
    <>
      <div className="page-h">
        <h1>Model operations</h1>
        <p className="muted">Walk-forward on 2009–2022 REG. Holdout 2023–2025 stays closed.</p>
      </div>
      <section className="card">
        <h2>Walk-forward artifact</h2>
        {!data?.artifact_exists ? (
          <p className="muted">
            No artifact yet. Run <code>python -m ml.pregame.walk_forward</code> on the server.
          </p>
        ) : (
          <>
            <MetricRow label="Experiment" value={String(wf?.experiment_id ?? '—')} />
            <MetricRow label="Games" value={String(wf?.n_games ?? '—')} />
            <MetricRow label="Ran at" value={String(wf?.ran_at ?? '—')} />
            {ridge && (
              <>
                <h3 style={{ marginTop: 20 }}>Ridge raw vs adj EPA (OOS)</h3>
                <MetricRow
                  label="Recommended variant"
                  value={String(ridge.recommended_variant ?? '—')}
                />
                <MetricRow
                  label="Adj MAE"
                  value={String((ridge.adj_epa as { mae?: number })?.mae?.toFixed(2) ?? '—')}
                />
                <MetricRow
                  label="Raw MAE"
                  value={String((ridge.raw_epa as { mae?: number })?.mae?.toFixed(2) ?? '—')}
                />
              </>
            )}
            <pre className="admin-pre" style={{ marginTop: 16 }}>
              {JSON.stringify(wf, null, 2)}
            </pre>
          </>
        )}
      </section>
    </>
  )
}

export function AdminUsersPage() {
  const [users, setUsers] = useState<Array<Record<string, unknown>>>([])
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    fetchAdminUsers()
      .then(setUsers)
      .catch((e) => setErr(e instanceof Error ? e.message : 'Failed to load users'))
  }, [])

  if (err) {
    return (
      <section className="card">
        <h1>Users</h1>
        <p className="muted">{err}</p>
      </section>
    )
  }

  return (
    <>
      <div className="page-h">
        <h1>Users</h1>
      </div>
      <section className="card">
        <table className="board">
          <thead>
            <tr>
              <th>Username</th>
              <th>Email</th>
              <th>Role</th>
              <th>Plan</th>
              <th>Active</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={String(u.id)}>
                <td>{String(u.username)}</td>
                <td>{String(u.email ?? '—')}</td>
                <td>{String(u.role)}</td>
                <td>{String(u.plan ?? '—')}</td>
                <td>{u.is_active ? 'yes' : 'no'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  )
}
