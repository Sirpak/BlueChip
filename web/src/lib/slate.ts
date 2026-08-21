import { useEffect, useState } from 'react'
import { fetchSlate, type UpcomingGame } from './api'

export function useSlate() {
  const [games, setGames] = useState<UpcomingGame[]>([])
  const [status, setStatus] = useState('Loading slate…')
  const [count, setCount] = useState({ nfl: 0, cfb: 0 })

  useEffect(() => {
    let live = true
    fetchSlate()
      .then((s) => {
        if (!live) return
        setGames([...s.nfl, ...s.cfb])
        setCount(s.count)
        setStatus(`ESPN slate · ${s.count.nfl} NFL · ${s.count.cfb} CFB · cached window`)
      })
      .catch(() => {
        if (!live) return
        setStatus('Slate unavailable — start the API on :8000')
      })
    return () => {
      live = false
    }
  }, [])

  return { games, status, count }
}
