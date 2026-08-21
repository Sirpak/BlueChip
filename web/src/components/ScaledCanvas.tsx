import { useEffect, useRef, useState, type ReactNode } from 'react'

type Props = {
  width?: number
  children: ReactNode
  className?: string
}

/** Fixed-width design canvas, uniformly CSS-scaled into a responsive frame. */
export function ScaledCanvas({ width = 1440, children, className }: Props) {
  const frameRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLDivElement>(null)
  const [scale, setScale] = useState(1)
  const [naturalH, setNaturalH] = useState(720)

  useEffect(() => {
    const frame = frameRef.current
    const canvas = canvasRef.current
    if (!frame || !canvas) return

    const measure = () => {
      const next = frame.clientWidth / width
      setScale(next)
      setNaturalH(canvas.offsetHeight)
    }

    const ro = new ResizeObserver(measure)
    ro.observe(frame)
    ro.observe(canvas)
    measure()
    return () => ro.disconnect()
  }, [width])

  return (
    <div
      ref={frameRef}
      className={`scaled-frame ${className ?? ''}`}
      style={{ height: naturalH * scale }}
    >
      <div
        ref={canvasRef}
        className="scaled-canvas"
        style={{
          width,
          transform: `scale(${scale})`,
          transformOrigin: 'top left',
        }}
      >
        {children}
      </div>
    </div>
  )
}
