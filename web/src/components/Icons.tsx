export function Icon({ d, size = 16 }: { d: string; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d={d} />
    </svg>
  )
}

export const I = {
  grid: 'M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z',
  calendar: 'M7 3v3M17 3v3M4 8h16M5 5h14a1 1 0 011 1v14a1 1 0 01-1 1H5a1 1 0 01-1-1V6a1 1 0 011-1z',
  search: 'M11 19a8 8 0 100-16 8 8 0 000 16zM21 21l-4.3-4.3',
  layers: 'M12 3l9 5-9 5-9-5 9-5zM3 12l9 5 9-5M3 17l9 5 9-5',
  trend: 'M4 19l6-6 4 4 6-8',
  users: 'M16 19v-1a4 4 0 00-4-4H8a4 4 0 00-4 4v1M12 11a3 3 0 100-6 3 3 0 000 6z',
  flask: 'M9 3h6M10 3v6L5 19h14l-5-10V3',
  book: 'M5 4h11a3 3 0 013 3v13H8a3 3 0 00-3 3V4z',
  plug: 'M9 7v4M15 7v4M8 11h8v3a4 4 0 01-8 0v-3zM12 18v3',
  db: 'M12 4c4 0 8 1.5 8 3.5S16 11 12 11 4 9.5 4 7.5 8 4 12 4zM4 7.5V12c0 2 4 3.5 8 3.5s8-1.5 8-3.5V7.5M4 12v4.5C4 18.5 8 20 12 20s8-1.5 8-3.5V12',
  cog: 'M12 15a3 3 0 100-6 3 3 0 000 6zM19.4 15a7.9 7.9 0 00.1-2l2-1.5-2-3.4-2.4.5a8 8 0 00-1.7-1L15 4h-6l-.4 3.6a8 8 0 00-1.7 1L6.5 8.1l-2 3.4 2 1.5a7.9 7.9 0 000 2l-2 1.5 2 3.4 2.4-.5a8 8 0 001.7 1L9 20h6l.4-3.6a8 8 0 001.7-1l2.4.5 2-3.4-2-1.5z',
  chat: 'M5 5h14a2 2 0 012 2v8a2 2 0 01-2 2H9l-4 4V7a2 2 0 012-2z',
  card: 'M3 10h18M7 15h4M3 6h18a2 2 0 012 2v10a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2z',
}
