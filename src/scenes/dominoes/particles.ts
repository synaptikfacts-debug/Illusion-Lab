// Deterministic particles for the domino story, all on the GPU: every particle is a closed-form path of story time,
// so the picture can play forwards, rewind, or jump to any frame. Pure TS (the sound generator reads spawn times).
//  sparks: a small burst from every coloured face as it lands
//  scales: golden dust shed from the wings at the top of every beat
//  dissolve: at the end the butterfly comes apart into rising golden dust, wingtips first, body last
import { rng } from "../../core/seed";
import { DSTORY, type DominoSim } from "./sim";

export interface Particles {
  count: number;
  p: Float32Array; // start position xyz
  v: Float32Array; // velocity xyz
  t: Float32Array; // t0, life, gravity, wobble
  c: Float32Array; // colour rgb (linear-ish, can exceed 1)
  s: Float32Array; // size (world units)
  kind: Uint8Array; // 0 spark, 1 scale dust, 2 dissolve
}

const mix = (a: number, b: number, t: number) => a + (b - a) * t;

/** Time each domino starts to dissolve (same rule as its glow fade in sim.ts). */
export function dissolveTime(u: number, v: number, body: number) {
  const S = DSTORY;
  if (body) return S.fadeGlow[1] - 0.4;
  return mix(S.fadeGlow[1], S.fadeGlow[0], Math.min(1, Math.hypot(u, v * 0.8))) - 1.0;
}

export function buildParticles(sim: DominoSim, seed: number): Particles {
  const L = sim.layout;
  const r = rng(seed, "particles");
  const P: number[] = [], V: number[] = [], T: number[] = [], C: number[] = [], Sz: number[] = [], K: number[] = [];
  const add = (p: number[], v: number[], t: number[], c: number[], s: number, k: number) => {
    P.push(...p); V.push(...v); T.push(...t); C.push(...c); Sz.push(s); K.push(k);
  };
  for (let i = 0; i < L.count; i++) {
    const dx = L.dir[i * 2], dz = L.dir[i * 2 + 1];
    const fx = L.x[i] + dx * 0.05, fz = L.z[i] + dz * 0.05;
    const g = L.glow[i];
    const col = [L.colR[i], L.colG[i], L.colB[i]];
    const bright = (m: number) => col.map((x) => x * m + 0.25);
    // sparks on landing (coloured faces + stars + the fuse)
    if (g > 0.15) {
      const land = L.trigger[i] + sim.fallTime;
      const n = L.lane[i] ? 6 : 3;
      for (let k = 0; k < n; k++) {
        const a = r() * Math.PI * 2, up = 0.7 + r() * 0.9, out = 0.25 + r() * 0.45;
        add([fx, 0.02, fz], [dx * out + Math.cos(a) * 0.25, up, dz * out + Math.sin(a) * 0.25], [land + r() * 0.03, 0.45 + r() * 0.4, -3.2, 0],
          bright(2.6), 0.02 + r() * 0.018, 0);
      }
    }
    // golden scale dust on every wing beat
    if (L.wing[i] > 0.1 && g > 0.3 && r() < 0.8)
      DSTORY.beats.forEach((b, j) => {
        if (r() > 0.6) return;
        const t0 = b + L.wing[i] * 0.22 + DSTORY.beatLen[j] * (0.35 + r() * 0.25);
        add([fx, 0.06, fz], [(r() - 0.5) * 0.18, 0.22 + r() * 0.35, (r() - 0.5) * 0.18], [t0, 1.8 + r() * 1.2, -0.04, 1],
          [2.0 + r() * 0.5, 1.45 + r() * 0.35, 0.55], 0.016 + r() * 0.014, 1);
      });
    // the dissolve
    if (g > 0.15) {
      const td = dissolveTime(L.u[i], L.v[i], L.body[i]);
      const n = L.body[i] ? 7 : 6;
      for (let k = 0; k < n; k++)
        add([fx + (r() - 0.5) * 0.05, 0.04, fz + (r() - 0.5) * 0.05],
          [(r() - 0.5) * 0.12 + L.u[i] * 0.06, 0.25 + r() * 0.45, (r() - 0.5) * 0.12 - L.v[i] * 0.04],
          [td + r() * 0.9, 2.6 + r() * 1.4, 0.12, 1],
          [mix(col[0], 1.0, 0.45) * 1.9, mix(col[1], 0.78, 0.45) * 1.9, mix(col[2], 0.4, 0.45) * 2.3], 0.018 + r() * 0.02, 2);
    }
  }
  const f = (a: number[]) => Float32Array.from(a);
  return { count: Sz.length, p: f(P), v: f(V), t: f(T), c: f(C), s: f(Sz), kind: Uint8Array.from(K) };
}
