// Singing pin wall: a grid of pins, each rising and falling with its own phase.
//   phase(t) = base * u(t) + delta * w(t) + ripple * dist * r(t)
// u(t): warped clock - fast at the loop point, standing still mid-loop (pins pause to hold the picture)
// w(t): 0 at the loop point, 1 mid-loop - brings in each pin's "picture" offset delta
// r(t): concentric ripple waves that vanish exactly when the picture forms and at the loop point
// Every term is periodic in L (base is even), so the reel loops seamlessly from any start offset.
// Pure TS: shared by the renderer and the melody generator.

export type PinImage = "eye" | "star" | "spiral" | "rings";

export interface PinParams {
  grid: number;
  spacing: number;
  maxHeight: number;
  loopSec: number;
  baseCycles: number; // even integer
  ripple: number; // ripple strength (cycles centre-to-corner)
  image: PinImage;
}

export interface Pin {
  x: number;
  z: number;
  u: number; // -1..1 across
  v: number; // -1..1 depth (top of the picture = far side)
  dist: number; // 0 centre .. 1 corner
  target: number; // 0..1 picture height
  delta: number; // phase offset that yields `target` mid-loop
  col: number; // grid column (for the musical scale)
  row: number;
}

const TAU = Math.PI * 2;
const smooth = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

/** Picture height (0..1) at u,v in -1..1 (v = +1 is the top of the picture as seen from the camera). */
export function picture(img: PinImage, u: number, v: number): number {
  const r = Math.hypot(u, v), a = Math.atan2(v, u);
  switch (img) {
    case "eye": {
      const lid = 0.62 * (1 - u * u * 1.05); // almond half-height
      const inEye = smooth(0.04, -0.04, Math.abs(v) - lid);
      const iris = smooth(0.46, 0.4, r);
      const pupil = smooth(0.19, 0.15, r);
      const glint = smooth(0.08, 0.05, Math.hypot(u - 0.13, v - 0.13));
      const striations = 0.85 + 0.15 * Math.cos(a * 26);
      let h = 0.06 + inEye * 0.42;
      h = h * (1 - iris) + iris * striations;
      h = h * (1 - pupil) + pupil * 0.0;
      return Math.max(h, glint);
    }
    case "star": {
      const k = 0.55 + 0.25 * Math.cos(a * 5);
      return 0.08 + 0.92 * smooth(0.05, -0.05, r - k);
    }
    case "spiral": {
      const s = 0.5 + 0.5 * Math.cos(a * 2 - r * 14);
      return (0.15 + 0.85 * s) * smooth(1.0, 0.85, r);
    }
    case "rings":
    default:
      return 0.5 + 0.5 * Math.cos(r * 18);
  }
}

export function layout(p: PinParams): Pin[] {
  const pins: Pin[] = [];
  const half = ((p.grid - 1) * p.spacing) / 2;
  for (let row = 0; row < p.grid; row++)
    for (let col = 0; col < p.grid; col++) {
      const u = (col / (p.grid - 1)) * 2 - 1;
      const v = 1 - (row / (p.grid - 1)) * 2;
      // picture drawn in screen space for the corner-on (45 deg) camera, so it reads upright
      const x = col * p.spacing - half, z = row * p.spacing - half;
      const pu = (x - z) / (half * 1.25), pv = -(x + z) / (half * 1.25);
      const target = Math.min(1, Math.max(0, picture(p.image, pu, pv)));
      pins.push({
        x,
        z,
        u,
        v,
        dist: Math.hypot(u, v) / Math.SQRT2,
        target,
        delta: Math.acos(1 - 2 * target) / TAU, // height = (1 - cos(2 pi delta)) / 2 = target
        col,
        row,
      });
    }
  return pins;
}

export const clockU = (t: number, L: number) => (t + (L / TAU) * Math.sin((TAU * t) / L)) / L;
export const clockW = (t: number, L: number) => (1 - Math.cos((TAU * t) / L)) / 2;
export const clockR = (t: number, L: number) => Math.sin((TAU * t) / L) ** 3;

export function phase(pin: Pin, p: PinParams, t: number): number {
  const L = p.loopSec;
  return p.baseCycles * clockU(t, L) + pin.delta * clockW(t, L) + p.ripple * pin.dist * clockR(t, L);
}

/** Pin height 0..maxHeight. */
export function height(pin: Pin, p: PinParams, t: number): number {
  return (p.maxHeight * (1 - Math.cos(TAU * phase(pin, p, t)))) / 2;
}

/** Times within one loop when the pin reaches its top (phase crosses k + 0.5), on a 2 ms grid. */
export function peakTimes(pin: Pin, p: PinParams): number[] {
  const out: number[] = [];
  const dt = 0.002;
  let prev = phase(pin, p, 0) - 0.5;
  for (let t = dt; t <= p.loopSec + 1e-9; t += dt) {
    const cur = phase(pin, p, t) - 0.5;
    if (Math.floor(cur) !== Math.floor(prev)) out.push(t - dt / 2);
    prev = cur;
  }
  return out;
}
