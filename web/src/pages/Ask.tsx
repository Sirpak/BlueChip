import { useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { I, Icon } from '../components/Icons'
import { useAuth } from '../lib/auth'
import { can } from '../lib/entitlements'

type Chat = { id: string; title: string; preview: string }

export function Ask() {
  const { user, refresh } = useAuth()
  const remaining = user?.usage?.ask_queries_remaining
  const limit = user?.usage?.ask_queries_limit
  const used = user?.usage?.ask_queries_used
  const [params] = useSearchParams()

  const initial = params.get('q') || 'Why does BlueChip favor Buffalo -6.5?'

  const [q, setQ] = useState('')

  const [sent, setSent] = useState(initial)

  const [active, setActive] = useState('new')



  const chats: Chat[] = useMemo(

    () => [

      { id: 'new', title: 'New chat', preview: 'Start a grounded question…' },

      { id: 'buf', title: 'BUF −6.5 vs market', preview: initial.slice(0, 48) },

    ],

    [initial],

  )



  const answer = useMemo(

    () => ({

      body: `BlueChip does not publish a cover percentage until leakage, baseline, calibration, uncertainty, and n gates pass. For “${sent}”, the desk can quote a Stern illustration only — not BCW-RIDGE-v0.1. The LLM must retrieve saved model output or an approved tool; it must not invent a BCW prediction.`,

      sources: ['Stern conversion · app/markets', 'ESPN scoreboard (tagged espn)', 'v0.1 freeze · docs/roadmap/04-bcw-v0.1.md'],

    }),

    [sent],

  )



  return (

    <div className="ask-layout">

      <aside className="ask-sidebar card">

        <button type="button" className="btn btn-primary" style={{ width: '100%' }} onClick={() => setActive('new')}>

          New Chat

        </button>

        <div className="ask-chat-list">

          {chats.map((c) => (

            <button

              key={c.id}

              type="button"

              className={`ask-chat-item ${active === c.id ? 'is-on' : ''}`}

              onClick={() => setActive(c.id)}

            >

              <strong>{c.title}</strong>

              <span className="muted">{c.preview}</span>

            </button>

          ))}

        </div>

        <p className="muted" style={{ fontSize: 11, marginTop: 12 }}>

          Later tools: Models · SQL/Data · Research · Deep Research

        </p>

      </aside>



      <div className="ask-main">

        <h1 style={{ fontSize: 22, fontWeight: 650, letterSpacing: '-0.02em', marginBottom: 8 }}>Ask BlueChip</h1>

        <p className="muted">
          {can(user, 'ask_bluechip') || can(user, 'ask_bluechip_limited')
            ? `${remaining ?? 0} of ${limit ?? 10} questions remaining this period (${used ?? 0} used).`
            : 'Ask is not on this plan.'}
        </p>
        {(remaining ?? 1) <= 0 && (
          <p>
            You&apos;ve used your included monthly research. <Link to="/pricing">Upgrade to Pro</Link>
          </p>
        )}

        <p className="muted">Grounded answers with sources. LLM is the interface, not the moat.</p>

        <div className="msg msg-user">{sent}</div>

        <div className="msg msg-ai">

          <p style={{ marginTop: 0 }}>{answer.body}</p>

          {answer.sources.map((s) => (

            <span className="source-chip" key={s}>

              {s}

            </span>

          ))}

          <div className="ask-actions">

            <button type="button" className="chip" disabled title="Feedback ships with Product">

              👍

            </button>

            <button type="button" className="chip" disabled title="Feedback ships with Product">

              👎

            </button>

            <button type="button" className="chip" onClick={() => navigator.clipboard?.writeText(answer.body)}>

              Copy

            </button>

          </div>

        </div>

        <form

          className="ask-sticky ask-sticky-fixed"

          onSubmit={(e) => {
            e.preventDefault()
            if (!q.trim()) return
            if ((remaining ?? 0) <= 0) return
            void fetch('/api/ask/query', {
              method: 'POST',
              credentials: 'include',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ question: q.trim() }),
            }).then(() => void refresh())
            setSent(q.trim())
            setQ('')
          }}

        >

          <Icon d={I.search} size={16} />

          <input

            className="ask-input"

            value={q}

            onChange={(e) => setQ(e.target.value)}

            placeholder="Ask anything about teams, games, models, markets or football research…"

          />

          <button className="btn btn-primary" type="submit">

            Send

          </button>

        </form>

      </div>

    </div>

  )

}


