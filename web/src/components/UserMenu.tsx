import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { brand } from '../brand'
import { useAuth } from '../lib/auth'

export function UserMenu() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('click', onDoc)
    return () => document.removeEventListener('click', onDoc)
  }, [])

  if (!user) return null

  const signOut = async () => {
    await logout()
    navigate('/login')
  }

  const isFree = user.plan === 'FREE'
  const isResearch = user.plan === 'RESEARCH' || user.role === 'ADMIN'

  return (
    <div className="user-menu" ref={ref}>
      <button type="button" className="user-menu-btn" onClick={() => setOpen((v) => !v)} aria-haspopup="menu">
        <span className="user-avatar">{user.initials}</span>
        <span className="user-menu-name">{user.initials}</span>
      </button>
      {open && (
        <div className="user-menu-pop" role="menu">
          <div className="user-menu-identity">
            <strong>{user.display_name}</strong>
            <span className="muted">{user.plan_label}</span>
          </div>
          <Link to="/profile" onClick={() => setOpen(false)}>
            Profile
          </Link>
          {isFree ? (
            <Link to="/pricing" onClick={() => setOpen(false)}>
              Upgrade to Pro
            </Link>
          ) : (
            <Link to="/subscription" onClick={() => setOpen(false)}>
              Subscription
            </Link>
          )}
          <Link to="/account" onClick={() => setOpen(false)}>
            Account
          </Link>
          <Link to="/usage" onClick={() => setOpen(false)}>
            Usage
          </Link>
          {isResearch && (
            <Link to="/backtests" onClick={() => setOpen(false)}>
              Exports
            </Link>
          )}
          <Link to="/settings" onClick={() => setOpen(false)}>
            Settings
          </Link>
          <Link to="/research" onClick={() => setOpen(false)}>
            Help
          </Link>
          {user.role === 'ADMIN' && (
            <>
              <span className="user-menu-muted">Administrator</span>
              <Link to="/admin" className="user-menu-admin" onClick={() => setOpen(false)}>
                Admin Console
              </Link>
            </>
          )}
          <button type="button" className="user-menu-signout" onClick={() => void signOut()}>
            Sign Out
          </button>
        </div>
      )}
    </div>
  )
}

export function LoginPage() {
  const { login, user, loading } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!loading && user) navigate('/desk', { replace: true })
  }, [loading, user, navigate])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await login(username.trim(), password)
      navigate('/desk')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <Link to="/" className="brand login-brand">
          <img className="brand-icon" src={brand.icon} alt="" width={36} height={36} />
          <strong>BlueChipWager</strong>
        </Link>
        <h1>Welcome back</h1>
        <p className="muted">Sign in to the research desk.</p>
        <form onSubmit={(e) => void submit(e)}>
          <label>
            Email or username
            <input
              className="ask-input"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </label>
          <label>
            Password
            <input
              className="ask-input"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
          {error && <p className="login-error">{error}</p>}
          <button className="btn btn-primary login-submit" type="submit" disabled={busy}>
            {busy ? 'Signing in…' : 'Sign In'}
          </button>
        </form>
        <div className="login-links">
          <span className="muted">Forgot password?</span>
          <Link to="/signup" className="muted">
            Don&apos;t have an account? Create account
          </Link>
        </div>
        <div className="login-divider">
          <span>or</span>
        </div>
        <button className="btn login-google" type="button" disabled title="Google sign-in ships with Cognito">
          Continue with Google
        </button>
        <p className="login-foot muted">
          Local demos: <code>demo_free</code> / <code>demo_pro</code> / <code>demo_research</code> / <code>admin</code>
        </p>
      </div>
    </div>
  )
}
