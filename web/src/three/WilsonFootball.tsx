import { useMemo, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import { Center, useGLTF } from '@react-three/drei'
import * as THREE from 'three'
import type { Group } from 'three'

const MODEL_URL = '/models/wilson-football.glb'

/** Scene units tuned for camera at z=3.4 over football_field.png */
const GROUND_Y = -0.58
const START_Y = 1.9
const DROP = 0.85
const BOUNCE = 1.1
const EXIT = 1.25
const PAUSE = 0.35

type BounceProfile = {
  // -1: up-left, 0: straight-up, 1: up-right
  bounceDir: -1 | 0 | 1
  tipStrike: boolean
  speedFactor: number
  // X/Y are intentionally near-zero to avoid "frisbee/spiral" spin.
  tiltBiasX: number
  tiltBiasY: number
  // Primary tumbling axis for end-over-end: rotate about scene-Z.
  pitchDir: 1 | -1
  pitchSpeed: number
  firstBounceAmp: number
  secondBounceRatio: number
  firstBounceDur: number
  secondBounceDur: number
  wobbleAmpZ: number
  wobbleAmpX: number
  wobbleFreq: number
  wobblePhase: number
  bouncePushX: number
  bouncePushZ: number
  exitVelX: number
  exitVelY: number
  exitVelZ: number
  squashAmp: number
  stretchAmp: number
}

function randomProfile(): BounceProfile {
  const bounceRand = Math.random()
  const bounceDir: -1 | 0 | 1 = bounceRand < 1 / 3 ? -1 : bounceRand < 2 / 3 ? 0 : 1
  const tipStrike = Math.random() < 0.42
  const firstBounceAmp = tipStrike ? THREE.MathUtils.randFloat(0.58, 0.84) : THREE.MathUtils.randFloat(0.85, 1.15)
  const secondBounceRatio = tipStrike ? THREE.MathUtils.randFloat(0.14, 0.3) : THREE.MathUtils.randFloat(0.22, 0.4)
  const bouncePushX =
    bounceDir === 0
      ? THREE.MathUtils.randFloat(-0.12, 0.12)
      : THREE.MathUtils.randFloat(tipStrike ? 0.9 : 0.45, tipStrike ? 1.55 : 0.95) * bounceDir
  const bouncePushZ = THREE.MathUtils.randFloat(tipStrike ? 0.7 : 0.35, tipStrike ? 1.35 : 0.9) * (Math.random() < 0.5 ? -1 : 1)
  return {
    bounceDir,
    tipStrike,
    // >1 is faster, <1 is slower for the whole cycle.
    speedFactor: THREE.MathUtils.randFloat(0.8, 1.3),
    tiltBiasX: THREE.MathUtils.randFloat(-0.04, 0.04),
    tiltBiasY: THREE.MathUtils.randFloat(-0.04, 0.04),
    pitchDir: Math.random() < 0.5 ? -1 : 1,
    pitchSpeed: THREE.MathUtils.randFloat(3.5, 6),
    firstBounceAmp,
    secondBounceRatio,
    firstBounceDur: THREE.MathUtils.randFloat(0.56, 0.64),
    secondBounceDur: THREE.MathUtils.randFloat(0.34, 0.42),
    wobbleAmpZ: THREE.MathUtils.randFloat(0.32, 0.62),
    wobbleAmpX: THREE.MathUtils.randFloat(0.1, 0.28),
    wobbleFreq: THREE.MathUtils.randFloat(1.05, 1.85),
    wobblePhase: THREE.MathUtils.randFloat(0, Math.PI * 2),
    bouncePushX,
    bouncePushZ,
    // Launch out-of-scene after bounce finishes.
    exitVelX: bounceDir === 0 ? THREE.MathUtils.randFloat(-0.45, 0.45) : THREE.MathUtils.randFloat(2.4, 4.2) * bounceDir,
    exitVelY: THREE.MathUtils.randFloat(2.7, 4.6),
    exitVelZ: THREE.MathUtils.randFloat(0.8, 2.1) * (Math.random() < 0.5 ? -1 : 1),
    squashAmp: THREE.MathUtils.randFloat(0.2, 0.34),
    stretchAmp: THREE.MathUtils.randFloat(0.12, 0.22),
  }
}

/** Parabolic arc peaking at mid-segment. */
function arcHeight(localT: number, duration: number, peak: number): number {
  if (localT <= 0 || localT >= duration) return 0
  const p = localT / duration
  return peak * 4 * p * (1 - p)
}

/** Two bounces: one high, one small. */
function bounceHeight(bt: number, profile: BounceProfile, bounceDur: number): number {
  const durScale = bounceDur / BOUNCE
  const { firstBounceDur, secondBounceDur, firstBounceAmp, secondBounceRatio } = profile
  const firstDur = firstBounceDur * durScale
  const secondDur = secondBounceDur * durScale
  if (bt < firstDur) {
    return arcHeight(bt, firstDur, firstBounceAmp)
  }
  const bt2 = bt - firstDur
  if (bt2 < secondDur) {
    return arcHeight(bt2, secondDur, firstBounceAmp * secondBounceRatio)
  }
  return 0
}

/** Prominent random back-and-forth while airborne during bounce. */
function bounceWobble(bt: number, profile: BounceProfile, height: number, bounceDur: number): { x: number; z: number } {
  const tn = bt / bounceDur
  const airborne = height / profile.firstBounceAmp
  const envelope = THREE.MathUtils.clamp(0.25 + airborne * 0.85, 0, 1)

  const primary = Math.sin(tn * Math.PI * profile.wobbleFreq + profile.wobblePhase)
  const cross = Math.cos(tn * Math.PI * profile.wobbleFreq * 1.45 + profile.wobblePhase * 0.6)
  const push = THREE.MathUtils.smoothstep(tn, 0.08, 0.72)

  const sharpKick = profile.tipStrike ? Math.max(0, 1 - Math.abs(tn - 0.08) / 0.1) : 0
  return {
    x: cross * profile.wobbleAmpX * envelope * 0.4 + profile.bouncePushX * push + profile.bouncePushX * sharpKick * 0.35,
    z: primary * profile.wobbleAmpZ * envelope * 0.55 + profile.bouncePushZ * push * 0.42 + profile.bouncePushZ * sharpKick * 0.22,
  }
}

/** Squash at first and second impacts. */
function bounceSquash(bt: number, profile: BounceProfile, bounceDur: number): { sx: number; sy: number } {
  const durScale = bounceDur / BOUNCE
  const impacts = [0, profile.firstBounceDur * durScale]
  let squash = 0
  for (const impact of impacts) {
    const dist = Math.abs(bt - impact)
    squash = Math.max(squash, Math.max(0, 1 - dist / 0.11))
  }
  squash *= profile.squashAmp
  const stretch = Math.max(0, squash - 0.45) * profile.stretchAmp
  return {
    sx: 1 + squash * 0.55,
    sy: 1 - squash * 0.75 + stretch * 0.25,
  }
}

function tumbleRotation(t: number, profile: BounceProfile) {
  return {
    rotX: 0.12 + profile.tiltBiasX,
    rotY: 0.35 + profile.tiltBiasY,
    // Primary end-over-end pitch: continuous, time-integrated rotation about scene-Z.
    rotZ: t * profile.pitchSpeed * profile.pitchDir,
  }
}

export function WilsonFootball() {
  const group = useRef<Group>(null)
  const cycleRef = useRef(0)
  const cycleStartRef = useRef<number | null>(null)
  const profileRef = useRef<BounceProfile>(randomProfile())
  const { scene } = useGLTF(MODEL_URL)

  const model = useMemo(() => {
    const cloned = scene.clone(true)
    const box = new THREE.Box3().setFromObject(cloned)
    const size = box.getSize(new THREE.Vector3())

    // Normalize the GLB so its longest "tip-to-tip" axis is local X.
    // The animation math assumes that pitching around scene-Z flips the tips end-over-end.
    if (size.z > size.x && size.z >= size.y) {
      cloned.rotation.y = Math.PI / 2
    } else if (size.y > size.x && size.y >= size.z) {
      cloned.rotation.z = Math.PI / 2
    }

    const correctedBox = new THREE.Box3().setFromObject(cloned)
    const correctedSize = correctedBox.getSize(new THREE.Vector3())
    const longest = Math.max(correctedSize.x, correctedSize.y, correctedSize.z) || 1
    cloned.scale.setScalar(0.9 / longest)
    cloned.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        child.castShadow = true
        child.receiveShadow = true
      }
    })
    return cloned
  }, [scene])

  useFrame(({ clock }) => {
    const g = group.current
    if (!g) return

    const absoluteT = clock.elapsedTime
    if (cycleStartRef.current == null) {
      cycleStartRef.current = absoluteT
    }

    let profile = profileRef.current
    const speed = profile.speedFactor
    const dropDur = DROP / speed
    const bounceDur = BOUNCE / speed
    const exitDur = EXIT / speed
    const pauseDur = PAUSE / speed
    const cycleDur = dropDur + bounceDur + exitDur + pauseDur

    let t = absoluteT - cycleStartRef.current
    if (t >= cycleDur) {
      cycleRef.current += 1
      cycleStartRef.current = absoluteT
      profile = randomProfile()
      profileRef.current = profile
      t = 0
      // eslint-disable-next-line no-console
      console.debug('[football-loop]', {
        bounce: profile.bounceDir === -1 ? 'up-left' : profile.bounceDir === 1 ? 'up-right' : 'up',
        strike: profile.tipStrike ? 'tip' : 'flat',
        speed: profile.speedFactor.toFixed(2),
      })
    }

    const tumble = tumbleRotation(t, profile)

    let x = 0
    let y = START_Y
    let z = 0
    let rotX = tumble.rotX
    let rotY = tumble.rotY
    let rotZ = tumble.rotZ
    let sx = 1
    let sy = 1

    if (t < dropDur) {
      const p = t / dropDur
      const fall = p * p
      y = THREE.MathUtils.lerp(START_Y, GROUND_Y, fall)
    } else if (t < dropDur + bounceDur) {
      const bt = t - dropDur
      const height = bounceHeight(bt, profile, bounceDur)
      y = GROUND_Y + height

      const wobble = bounceWobble(bt, profile, height, bounceDur)
      x = wobble.x
      z = wobble.z

      const squash = bounceSquash(bt, profile, bounceDur)
      sx = squash.sx
      sy = squash.sy
    } else if (t < dropDur + bounceDur + exitDur) {
      const et = t - dropDur - bounceDur
      const p = et / exitDur
      // Ballistically pop out of scene after final bounce.
      x = profile.exitVelX * et
      y = GROUND_Y + 0.03 + profile.exitVelY * et - 1.8 * et * et
      z = profile.exitVelZ * et
      // Keep end-over tumble active while it exits.
      rotZ = tumble.rotZ + p * profile.pitchDir * 1.1
    } else {
      const et = exitDur
      x = profile.exitVelX * et
      y = GROUND_Y + 0.03 + profile.exitVelY * et - 1.8 * et * et
      z = profile.exitVelZ * et
    }

    g.position.set(x, y, z)
    g.rotation.set(rotX, rotY, rotZ)
    g.scale.set(sx, sy, sx)
  })

  return (
    <group ref={group}>
      <Center>
        <primitive object={model} />
      </Center>
    </group>
  )
}

useGLTF.preload(MODEL_URL)
