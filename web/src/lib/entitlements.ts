import type { AuthUser } from './authApi'

const ALIASES: Record<string, string[]> = {
  ask_bluechip_limited: ['ask_bluechip'],
  models_basic: ['models_full'],
  teams_basic: ['teams_full'],
  research_preview: ['research'],
  backtests_preview: ['backtests_standard', 'backtests_advanced'],
  backtests_standard: ['backtests_advanced'],
}

export function can(user: AuthUser | null | undefined, name: string): boolean {
  if (!user) return false
  const held = user.entitlements ?? []
  if (held.includes('*')) return true
  if (held.includes(name)) return true
  return (ALIASES[name] ?? []).some((alt) => held.includes(alt))
}

export function planName(user: AuthUser | null | undefined): string {
  return user?.plan_label ?? 'Free Plan'
}
