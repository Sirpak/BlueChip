import { Link } from 'react-router-dom'
import { useAuth } from '../lib/auth'

export function ProfilePage() {
  const { user } = useAuth()
  return (
    <>
      <div className="page-h">
        <h1>Profile</h1>
      </div>
      <section className="card">
        <p>
          <strong>{user?.display_name}</strong>
        </p>
        <p className="muted">
          {user?.username} · {user?.plan_label} · {user?.role}
        </p>
        <p className="muted">{user?.email}</p>
      </section>
    </>
  )
}

export function AccountPage() {
  return (
    <>
      <div className="page-h">
        <h1>Account</h1>
      </div>
      <section className="card">
        <p className="muted">Password reset and email verification ship with Cognito. Plan lives in this application database so Stripe can change it later without rewriting routes.</p>
      </section>
    </>
  )
}

export function SubscriptionPage() {
  const { user } = useAuth()
  return (
    <>
      <div className="page-h">
        <h1>Subscription</h1>
      </div>
      <section className="card">
        <p>
          Current plan: <strong>{user?.plan_label}</strong>
        </p>
        <p className="muted">Billing integration coming soon. Stripe will set <code>users.plan</code>; entitlements change immediately.</p>
        <Link className="btn btn-primary" to="/pricing">
          View plans
        </Link>
      </section>
    </>
  )
}

export function UsagePage() {
  const { user } = useAuth()
  const u = user?.usage
  return (
    <>
      <div className="page-h">
        <h1>Usage</h1>
      </div>
      <section className="card">
        <p>
          Ask BlueChip: <strong>{u?.ask_queries_used ?? 0}</strong> of {u?.ask_queries_limit ?? 10} this period
        </p>
        <p className="muted">{u?.ask_queries_remaining ?? 0} remaining. These are product quotas, not OpenAI tokens.</p>
      </section>
    </>
  )
}

export function SignupPage() {
  return (
    <div className="login-page">
      <div className="login-card">
        <h1>Create account</h1>
        <p className="muted">Signup ships with Cognito. Use a local demo account for now.</p>
        <Link className="btn btn-primary" to="/login">
          Sign in
        </Link>
      </div>
    </div>
  )
}

export function ComingSoonPage() {
  return (
    <>
      <div className="page-h">
        <h1>Billing coming soon</h1>
      </div>
      <section className="card">
        <p>Stripe Checkout is not wired yet. Local demo plans already switch entitlements when you sign in as demo_free, demo_pro, or demo_research.</p>
        <Link className="btn" to="/pricing">
          Back to pricing
        </Link>
      </section>
    </>
  )
}
