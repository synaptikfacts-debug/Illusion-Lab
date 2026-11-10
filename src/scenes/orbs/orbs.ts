// "Orb Waves": the reference's core idea (thousands of glossy orbs, each bouncing at its own rhythm, folding into
// funnels, domes, waves and spirals, a click per bounce) with our own look, camera, hook and ending.
// Physics time p = video time + start offset (the video opens mid-way, already in a complex shape). At p = L every
// orb is back in phase: all bounce TOGETHER (climax), then the bounces die down and they come to rest (ending).
import { rng } from "../../core/seed";

export const OP = {
  count: 4600,
  discRadius: 3.0,
  ballRadius: 0.034,
  height: 1.15,
  L: 36, // phase loop
  base: 24, // bounces per loop (even)
  spread: 2.6,
  start: 0.3, // video starts at p = start * L
  duration: 30,
  settle: [25.6, 28.8] as [number, number], // video seconds: bounces die down
  fade: [27.6, 29.8] as [number, number],
};
export const SYNC_AT = OP.L * (1 - OP.start); // video time when every orb is in phase

export interface Orb { x: number; z: number; r01: number; ring: number; size: number; spiral: number }

const GOLDEN = Math.PI * (3 - Math.sqrt(5));

export function orbLayout(seed: number): Orb[] {
  const r = rng(seed, "orbs2");
  return Array.from({ length: OP.count }, (_, i) => {
    const r01 = Math.sqrt((i + 0.5) / OP.count);
    const a = i * GOLDEN;
    // ring weight + a little angular term: shapes become spirals, not only rings
    const spiral = 0.1 * Math.sin(a * 3 + r01 * 6);
    return { x: Math.cos(a) * r01 * OP.discRadius, z: Math.sin(a) * r01 * OP.discRadius, r01, ring: 1 - r01, size: OP.ballRadius * (0.85 + 0.3 * r()), spiral };
  });
}

const sm = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

export function phase(o: Orb, p: number) {
  const w = (1 - Math.cos((2 * Math.PI * p) / OP.L)) / 2;
  return (OP.base * p) / OP.L + OP.spread * (o.ring + o.spiral) * w;
}

export const amp = (v: number) => 1 - sm(OP.settle[0], OP.settle[1], v);

/** Orb state at VIDEO time v: height above the plate and squash amount (0..1). */
export function orbAt(o: Orb, v: number) {
  const p = v + OP.start * OP.L;
  const ph = phase(o, p);
  const s = ph - Math.round(ph); // -0.5..0.5, impact at +-0.5
  const A = amp(v);
  const y = OP.height * A * (1 - 4 * s * s);
  const near = 0.5 - Math.abs(s);
  const squash = A * 0.3 * Math.exp(-((near / 0.03) ** 2));
  return { y, squash };
}

/** Impact times (video seconds) for sound: phase crossings of k + 0.5, energy = current bounce amplitude. */
export function impacts(o: Orb): { t: number; e: number }[] {
  const out: { t: number; e: number }[] = [];
  const dt = 0.002, p0 = OP.start * OP.L;
  let prev = phase(o, p0) - 0.5;
  for (let v = dt; v <= OP.settle[1]; v += dt) {
    const cur = phase(o, p0 + v) - 0.5;
    if (Math.floor(cur) !== Math.floor(prev)) out.push({ t: v, e: amp(v) });
    prev = cur;
  }
  return out;
}
