import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { glossaryEntry } from '../lib/glossary'

type Props = {
  /** Glossary id or a known UI label */
  t: string
  children?: ReactNode
  className?: string
}

/**
 * Inline term with a hover/focus definition for non-technical readers.
 * Falls back to plain children if the term is unknown.
 */
export function Hint({ t, children, className }: Props) {
  const entry = glossaryEntry(t)
  const label = children ?? entry?.term ?? t
  if (!entry) {
    return <span className={className}>{label}</span>
  }
  return (
    <abbr className={`hint ${className ?? ''}`.trim()} tabIndex={0} data-tip={`${entry.term}: ${entry.short}`}>
      {label}
    </abbr>
  )
}

/** Small “?” that opens the About glossary for a term. */
export function HintLink({ t }: { t: string }) {
  const entry = glossaryEntry(t)
  if (!entry) return null
  return (
    <Link className="hint-link" to={`/about#${entry.id}`} title={`About ${entry.term}`} aria-label={`About ${entry.term}`}>
      ?
    </Link>
  )
}

export function HintLabel({ t, children }: { t: string; children?: ReactNode }) {
  return (
    <span className="hint-label">
      <Hint t={t}>{children}</Hint>
      <HintLink t={t} />
    </span>
  )
}
