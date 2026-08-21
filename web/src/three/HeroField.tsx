import { Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { WilsonFootball } from './WilsonFootball'

type Props = {
  scroll: number
  mouse: { x: number; y: number }
}

export function HeroField(_props: Props) {
  return (
    <Canvas
      dpr={[1, 2]}
      gl={{ antialias: true, alpha: true }}
      camera={{ position: [0, 0.4, 3.4], fov: 35 }}
      onCreated={({ gl }) => {
        gl.setClearColor(0x000000, 0)
      }}
    >
      <ambientLight intensity={0.55} />
      <directionalLight position={[3, 4, 3]} intensity={1.1} />
      <directionalLight position={[-3, 2, -2]} intensity={0.35} />
      <Suspense fallback={null}>
        <WilsonFootball />
      </Suspense>
    </Canvas>
  )
}
