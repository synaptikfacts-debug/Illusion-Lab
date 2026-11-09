// Analytic bounce field. Each orb's bounce phase (in bounces) is
//   phi(t) = base * t/L + spread * ring * w(t),   w(t) = (1 - cos(2 pi t / L)) / 2
// so all orbs share the same phase at t = 0 and t = L (flat disc, seamless loop), while in between the
// phase offset across the disc grows smoothly (funnel -> cylinder -> dome -> waves) and then unwinds.
// Height inside one bounce is a parabola in phase, so every orb moves like a real elastic bounce.
// Pure TS: shared by the renderer and the click-track generator.
import { rng } from "../../core/seed";

export interface BounceParams {
  count: number;
  discRadius: number;
  ballRadius: number;
  height: number; // drop height of the orb bottom above the plate
  loopSec: number;
  baseBounces: number; // bounces per loop (integer: keeps the loop seamless)
  spread: number; // max phase difference centre-to-edge, in bounces, reached mid-loop
  centerFast: boolean; // true: centre leads (funnel first); false: edge leads (dome first)
  sizeJitter: number;
}

export interface Orb {
  x: number;
  z: number;
  r01: number;
  ring: number; // 0..1 weight of the phase offset
  size: number;
}

const GOLDEN = Math.PI * (3 - Math.sqrt(5));

export function layout(p: BounceParams, seed: number): Orb[] {
  const r = rng(seed, "orbs");
  return Array.from({ length: p.count }, (_, i) => {
    const r01 = Math.sqrt((i + 0.5) / p.count);
    const a = i * GOLDEN;
    return {
      x: Math.cos(a) * r01 * p.discRadius,
      z: Math.sin(a) * r01 * p.discRadius,
      r01,
      ring: p.centerFast ? 1 - r01 : r01,
      size: p.ballRadius * (1 + (r() - 0.5) * p.sizeJitter),
    };
  });
}

export function phase(o: Orb, p: BounceParams, t: number): number {
  const w = (1 - Math.cos((2 * Math.PI * t) / p.loopSec)) / 2;
  return (p.baseBounces * t) / p.loopSec + p.spread * o.ring * w;
}

/** Bounces per second right now (always > 0 when baseBounces > pi * spread). */
export function rate(o: Orb, p: BounceParams, t: number): number {
  const dw = (Math.PI / p.loopSec) * Math.sin((2 * Math.PI * t) / p.loopSec);
  return p.baseBounces / p.loopSec + p.spread * o.ring * dw;
}

/** Height of the orb bottom above the plate, and seconds to the nearest impact. Phase 0 = top of a bounce. */
export function orbState(o: Orb, p: BounceParams, t: number): { y: number; toImpact: number } {
  const ph = phase(o, p, t);
  const s = ph - Math.round(ph); // -0.5..0.5, impact at +-0.5
  return { y: p.height * (1 - 4 * s * s), toImpact: (0.5 - Math.abs(s)) / Math.max(1e-3, rate(o, p, t)) };
}

/** Impact times within one loop (phase crossing k + 0.5), found on a 1 ms grid and interpolated. */
export function impactTimes(o: Orb, p: BounceParams): number[] {
  const out: number[] = [];
  const dt = 0.001;
  let prev = phase(o, p, 0) - 0.5;
  for (let t = dt; t <= p.loopSec + 1e-9; t += dt) {
    const cur = phase(o, p, t) - 0.5;
    if (Math.floor(cur) > Math.floor(prev)) {
      const k = Math.floor(cur);
      out.push(t - dt + (dt * (k - prev)) / (cur - prev));
    }
    prev = cur;
  }
  return out;
}
