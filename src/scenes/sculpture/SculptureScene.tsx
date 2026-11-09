import { ThreeCanvas } from "@remotion/three";
import React, { useMemo } from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import * as THREE from "three";
import { rng } from "../../core/seed";
import { rgb } from "../../gl/ShaderPlane";
import pfrag from "./particles.frag.glsl";
import pvert from "./particles.vert.glsl";
import frag from "./scene.frag.glsl";
import { sampleHeart, sampleSurface, satellites } from "./sdf";

export const FOV = 35;
const TAN_HALF = Math.tan(((FOV / 2) * Math.PI) / 180);
const QUAD_VERT = `varying vec2 vUv; void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`;

export interface SculptureLook {
  bg0: string;
  bg1: string;
  tint: string;
  tint2: string;
}

export interface ParticleStages {
  out: number; // burst -> galaxy
  knot: number; // galaxy -> torus knot
  heart: number; // knot -> heart
  back: number; // heart -> sculpture
  beat: number; // heart scale
}

export interface SculptureState {
  time: number; // sculpture time (s)
  bgTime: number;
  rot?: number; // whole-scene orbit (rad)
  scale?: number;
  shock?: number; // 0..1 shockwave progress, 1 = none
  inv?: number;
  gray?: number;
  obj?: number;
  bgMix?: number;
  particles?: { stages: ParticleStages; t: number; startTime: number; homeTime: number; count: number };
}

/** Whole-reel camera motion that loops: one full orbit and a gentle push-in/out over `totalSec`. */
export function orbit(globalSec: number, totalSec: number, turns = 1) {
  const x = globalSec / totalSec;
  return { rot: Math.PI * 2 * turns * x, scale: 1 + 0.1 * Math.sin(Math.PI * x) ** 2 };
}

// Particle layouts are expensive (CPU SDF projection): cache per page.
const cache = new Map<string, THREE.BufferGeometry>();

function particleGeometry(seed: number, count: number, startTime: number, homeTime: number, look: SculptureLook) {
  const key = `${seed}|${count}|${startTime}|${homeTime}|${look.tint}|${look.tint2}`;
  const hit = cache.get(key);
  if (hit) return hit;
  const sats = satellites(seed);
  const start = sampleSurface(count, startTime, sats, seed);
  const home = sampleSurface(count, homeTime, sats, seed + 1);
  const heart = sampleHeart(count, seed);
  const end = new Float32Array(count * 3), knot = new Float32Array(count * 4);
  const rnd = new Float32Array(count * 4), col = new Float32Array(count * 3);
  const r = rng(seed, "galaxy");
  const gauss = () => (r() + r() + r() - 1.5) / 1.5;
  const t1 = rgb(look.tint), t2 = rgb(look.tint2);
  for (let i = 0; i < count; i++) {
    const core = r() < 0.16;
    const rad = core ? Math.abs(gauss()) * 0.18 : 0.12 + Math.pow(r(), 0.75) * 1.15;
    const arm = Math.floor(r() * 3);
    const ang = core ? r() * Math.PI * 2 : arm * ((Math.PI * 2) / 3) + rad * 3.4 + (gauss() * 0.32) / (rad + 0.35);
    end.set([Math.cos(ang) * rad, gauss() * (core ? 0.12 : 0.05 * (1.3 - rad)), Math.sin(ang) * rad], i * 3);
    knot.set([r() * Math.PI * 2, gauss() * 0.07, gauss() * 0.07, gauss() * 0.07], i * 4);
    rnd.set([r(), r(), r(), r()], i * 4);
    const k = 0.5 + 0.5 * Math.cos(Math.PI * 2 * (start[i * 3 + 1] * 0.45 + r() * 0.15));
    const c = core || r() < 0.08 ? [1, 0.93, 0.95] : [t1.x * k + t2.x * (1 - k), t1.y * k + t2.y * (1 - k), t1.z * k + t2.z * (1 - k)];
    const gain = core ? 0.5 : 0.6;
    col.set([c[0] * gain, c[1] * gain, c[2] * gain], i * 3);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(start, 3)); // required by three; real position comes from the shader
  g.setAttribute("aStart", new THREE.BufferAttribute(start, 3));
  g.setAttribute("aHome", new THREE.BufferAttribute(home, 3));
  g.setAttribute("aEnd", new THREE.BufferAttribute(end, 3));
  g.setAttribute("aKnot", new THREE.BufferAttribute(knot, 4));
  g.setAttribute("aHeart", new THREE.BufferAttribute(heart, 3));
  g.setAttribute("aRnd", new THREE.BufferAttribute(rnd, 4));
  g.setAttribute("aCol", new THREE.BufferAttribute(col, 3));
  g.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 10);
  cache.set(key, g);
  return g;
}

/** focusY: frame fraction (0 = top) where the sculpture centre sits. */
export const SculptureScene: React.FC<{ seed: number; look: SculptureLook; state: SculptureState; focusY?: number }> = ({
  seed,
  look,
  state,
  focusY = 0.5,
}) => {
  const { width, height } = useVideoConfig();
  const frame = useCurrentFrame();
  const camY = (focusY - 0.5) * 2 * 7 * TAN_HALF;
  const sats = useMemo(() => satellites(seed).map((s) => new THREE.Vector4(...s)), [seed]);

  const quad = useMemo(
    () =>
      new THREE.ShaderMaterial({
        vertexShader: QUAD_VERT,
        fragmentShader: frag,
        depthTest: false,
        depthWrite: false,
        uniforms: {
          uAspect: { value: width / height },
          uTanHalf: { value: TAN_HALF },
          uSeed: { value: seed % 997 },
          uSat: { value: sats },
          uBg0: { value: rgb(look.bg0) },
          uBg1: { value: rgb(look.bg1) },
          uTint: { value: rgb(look.tint) },
          uTint2: { value: rgb(look.tint2) },
          uCamY: { value: camY },
          uTime: { value: 0 },
          uBgTime: { value: 0 },
          uFrame: { value: 0 },
          uRot: { value: 0 },
          uScale: { value: 1 },
          uShock: { value: 1 },
          uInv: { value: 0 },
          uGray: { value: 0 },
          uObj: { value: 1 },
          uBgMix: { value: 0 },
        },
      }),
    [width, height, seed, sats, look.bg0, look.bg1, look.tint, look.tint2, camY],
  );
  const u = quad.uniforms;
  u.uTime.value = state.time;
  u.uBgTime.value = state.bgTime;
  u.uFrame.value = frame;
  u.uRot.value = state.rot ?? 0;
  u.uScale.value = state.scale ?? 1;
  u.uShock.value = state.shock ?? 1;
  u.uInv.value = state.inv ?? 0;
  u.uGray.value = state.gray ?? 0;
  u.uObj.value = state.obj ?? 1;
  u.uBgMix.value = state.bgMix ?? 0;

  const ps = state.particles;
  const points = useMemo(() => {
    if (!ps) return null;
    const geometry = particleGeometry(seed, ps.count, ps.startTime, ps.homeTime, look);
    const material = new THREE.ShaderMaterial({
      vertexShader: pvert,
      fragmentShader: pfrag,
      transparent: true,
      depthTest: false,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      uniforms: {
        uOut: { value: 0 },
        uKnot: { value: 0 },
        uHeart: { value: 0 },
        uBack: { value: 0 },
        uBeat: { value: 1 },
        uRot: { value: 0 },
        uT: { value: 0 },
        uPx: { value: height / (2 * TAN_HALF) },
        uSize: { value: 0.016 },
      },
    });
    return { geometry, material };
  }, [seed, ps?.count, ps?.startTime, ps?.homeTime, look, height]);
  if (points && ps) {
    const m = points.material.uniforms;
    m.uOut.value = ps.stages.out;
    m.uKnot.value = ps.stages.knot;
    m.uHeart.value = ps.stages.heart;
    m.uBack.value = ps.stages.back;
    m.uBeat.value = ps.stages.beat;
    m.uT.value = ps.t;
    m.uRot.value = state.rot ?? 0;
  }
  const s = state.scale ?? 1;

  return (
    <ThreeCanvas
      width={width}
      height={height}
      linear
      flat
      gl={{ antialias: false, preserveDrawingBuffer: true }}
      camera={{ fov: FOV, position: [0, camY, 7], rotation: [0, 0, 0], near: 0.1, far: 50 }}
    >
      <mesh frustumCulled={false} material={quad} renderOrder={-1}>
        <planeGeometry args={[2, 2]} />
      </mesh>
      {points && (
        <group rotation={[0, state.rot ?? 0, 0]} scale={[s, s, s]}>
          <points geometry={points.geometry} material={points.material} frustumCulled={false} renderOrder={1} />
        </group>
      )}
    </ThreeCanvas>
  );
};
