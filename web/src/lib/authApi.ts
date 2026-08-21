export type AuthUser = {
  id: number
  username: string
  email: string | null
  display_name: string
  role: 'USER' | 'ADMIN'
  plan: 'FREE' | 'PRO' | 'RESEARCH' | 'INTERNAL'
  plan_label: string
  initials: string
  entitlements: string[]
  usage: {
    ask_queries_used: number
    ask_queries_limit: number
    ask_queries_remaining: number
  }
}

const creds: RequestCredentials = 'include'

export async function fetchMe(): Promise<AuthUser | null> {
  const res = await fetch('/api/auth/me', { credentials: creds })
  if (res.status === 401) return null
  if (!res.ok) throw new Error(`auth ${res.status}`)
  return res.json() as Promise<AuthUser>
}

export async function login(username: string, password: string): Promise<AuthUser> {
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    credentials: creds,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) {
    const detail = res.status === 401 ? 'Invalid username or password' : `Login failed (${res.status})`
    throw new Error(detail)
  }
  return res.json() as Promise<AuthUser>
}

export async function logout(): Promise<void> {
  await fetch('/api/auth/logout', { method: 'POST', credentials: creds })
}

export async function fetchUsage(): Promise<AuthUser['usage']> {
  const res = await fetch('/api/auth/usage', { credentials: creds })
  if (!res.ok) throw new Error(`usage ${res.status}`)
  return res.json() as Promise<AuthUser['usage']>
}

export async function fetchAdminHealth(): Promise<Record<string, unknown>> {
  const res = await fetch('/api/admin/health', { credentials: creds })
  if (res.status === 403) throw new Error('Admin access required')
  if (!res.ok) throw new Error(`admin health ${res.status}`)
  return res.json() as Promise<Record<string, unknown>>
}

export async function fetchAdminDashboard(): Promise<Record<string, unknown>> {
  const res = await fetch('/api/admin/dashboard', { credentials: creds })
  if (!res.ok) throw new Error(`admin dashboard ${res.status}`)
  return res.json() as Promise<Record<string, unknown>>
}

export async function fetchAdminModels(): Promise<Record<string, unknown>> {
  const res = await fetch('/api/admin/models', { credentials: creds })
  if (!res.ok) throw new Error(`admin models ${res.status}`)
  return res.json() as Promise<Record<string, unknown>>
}

export async function fetchAdminUsers(): Promise<Array<Record<string, unknown>>> {
  const res = await fetch('/api/admin/users', { credentials: creds })
  if (!res.ok) throw new Error(`admin users ${res.status}`)
  return res.json() as Promise<Array<Record<string, unknown>>>
}

export async function fetchAdminJson(path: string): Promise<Record<string, unknown>> {
  const res = await fetch(`/api/admin/${path}`, { credentials: creds })
  if (!res.ok) throw new Error(`admin ${path} ${res.status}`)
  return res.json() as Promise<Record<string, unknown>>
}
