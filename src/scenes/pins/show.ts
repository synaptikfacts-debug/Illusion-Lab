// "Singing Pins: the long show" (owner, Nov 11: "I absolutely love that one - better quality, better effects, ~1 min").
// One continuous minute: a 64x64 wall of glowing pins races in waves, slows down and freezes into an abstract picture
// (rings -> star -> spiral -> mandala), dissolves back into waves, and at the end the mandala melts into a calm,
// flat mirror. Each picture has its own colour story. Pure TS: shared by the renderer and the sound generator.
//
// Within a segment of length L (local time s):  phase = base*U(s) + delta_k*W(s) + ripple*dist*R(s)
// U: warped clock (fast at segment edges, still mid-segment), W: 0 at edges, 1 mid-segment (picture),
// R: ripple rings that vanish at the picture and the edges. At every segment edge all pins pass phase = integer at
// the same speed, so segments join seamlessly.

import { picture as basePicture, type PinImage } from "./physics";

export type ShowImage = PinImage | "flower";

export const SHOW = {
  grid: 64,
  spacing: 0.094,
  maxHeight: 1.1,
  base: 12, // owner Nov 11: slower (was 20)
  ripple: 2.6,
  /** pictures in order, each segment's length (s) and its tip colours (low -> high) */
  segments: [
    { img: "rings" as ShowImage, L: 12, tips: ["#1c0f66", "#7a2fe0", "#1fc8f0", "#9ff4ff"] },
    { img: "star" as ShowImage, L: 13, tips: ["#4a0c4c", "#e0257a", "#f59a2a", "#ffd98a"] },
    { img: "spiral" as ShowImage, L: 13, tips: ["#08304c", "#16b48e", "#4fe6f0", "#b8fff4"] },
    { img: "flower" as ShowImage, L: 16, tips: ["#2c0e6a", "#b032e8", "#f05cc4", "#ffc2ee"] },
  ],
  /** where in the first segment the reel starts (fraction), so frame 0 is already racing */
  startAt: 0.16,
  /** after the last picture forms: hold, then melt to a flat mirror */
  hold: 2,
  melt: 5.5,
  fade: [55.6, 59.7] as [number, number],
  duration: 60,
};

const TAU = Math.PI * 2;
const sm = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

export function picture(img: ShowImage, u: number, v: number): number {
  if (img !== "flower") return basePicture(img, u, v);
  // mandala: six round petals with ringed ridges and a domed centre
  const r = Math.hypot(u, v), a = Math.atan2(v, u);
  const petals = 0.5 + 0.5 * Math.cos(a * 6);
  const k = 0.4 + 0.38 * Math.pow(petals, 0.7);
  const body = sm(0.05, -0.05, r - k);
  let h = 0.06 + 0.94 * body * (0.74 + 0.26 * Math.cos(r * 16));
  h = Math.max(h, sm(0.2, 0.13, r));
  return Math.min(1, h);
}

export interface ShowPin {
  x: number;
  z: number;
  dist: number;
  delta: number[]; // phase offset per segment's picture
  target: number[];
}

export function layoutShow(): ShowPin[] {
  const S = SHOW;
  const half = ((S.grid - 1) * S.spacing) / 2;
  const pins: ShowPin[] = [];
  for (let row = 0; row < S.grid; row++)
    for (let col = 0; col < S.grid; col++) {
      const x = col * S.spacing - half, z = row * S.spacing - half;
      const u = (col / (S.grid - 1)) * 2 - 1, v = 1 - (row / (S.grid - 1)) * 2;
      // pictures in screen space for the corner-on (45 deg) camera
      const pu = (x - z) / (half * 1.25), pv = -(x + z) / (half * 1.25);
      const target = S.segments.map((sg) => Math.min(1, Math.max(0, picture(sg.img, pu, pv))));
      pins.push({ x, z, dist: Math.hypot(u, v) / Math.SQRT2, target, delta: target.map((tg) => Math.acos(1 - 2 * tg) / TAU) });
    }
  return pins;
}

const U = (s: number, L: number) => (s + (L / TAU) * Math.sin((TAU * s) / L)) / L;
const W = (s: number, L: number) => (1 - Math.cos((TAU * s) / L)) / 2;
const R = (s: number, L: number) => Math.sin((TAU * s) / L) ** 3;

/** Where the show is at video time t: segment index, local time, picture weight w (0..1), melt (0..1). */
export function showAt(t: number) {
  const S = SHOW;
  let s = t + S.startAt * S.segments[0].L;
  const last = S.segments.length - 1;
  for (let k = 0; k < last; k++) {
    if (s < S.segments[k].L) return { k, s, L: S.segments[k].L, w: W(s, S.segments[k].L), melt: 0, frozen: false };
    s -= S.segments[k].L;
  }
  const L = S.segments[last].L;
  if (s < L / 2) return { k: last, s, L, w: W(s, L), melt: 0, frozen: false };
  const after = s - L / 2;
  return { k: last, s: L / 2, L, w: 1, melt: sm(S.hold, S.hold + S.melt, after), frozen: true, after };
}

export function phaseAt(pin: ShowPin, t: number): number {
  const st = showAt(t);
  if (st.frozen) {
    // as the mandala melts, one slow, gentle ring wave runs out from the centre across the wall
    const a = (st.after ?? 0) - SHOW.hold;
    const front = a * 0.2;
    const ring = a > 0 ? 0.22 * Math.exp(-(((pin.dist - front) / 0.09) ** 2)) * Math.exp(-a * 0.12) : 0;
    return SHOW.base * 0.5 + pin.delta[st.k] * (1 - st.melt) + ring;
  }
  return SHOW.base * U(st.s, st.L) + pin.delta[st.k] * W(st.s, st.L) + SHOW.ripple * pin.dist * R(st.s, st.L);
}

export const heightAt = (pin: ShowPin, t: number) => (SHOW.maxHeight * (1 - Math.cos(TAU * phaseAt(pin, t)))) / 2;

/** Video times at which each picture locks in (mid-segment). */
export function lockTimes(): number[] {
  const S = SHOW;
  const out: number[] = [];
  let start = -S.startAt * S.segments[0].L;
  for (const sg of S.segments) { out.push(start + sg.L / 2); start += sg.L; }
  return out;
}

/** Tip colour stops at time t (cross-fades between segments around each edge). */
export function tipsAt(t: number): { a: string[]; b: string[]; mix: number } {
  const S = SHOW;
  let start = -S.startAt * S.segments[0].L;
  for (let k = 0; k < S.segments.length; k++) {
    const end = start + S.segments[k].L;
    if (t < end || k === S.segments.length - 1) {
      const next = S.segments[Math.min(k + 1, S.segments.length - 1)].tips;
      return { a: S.segments[k].tips, b: next, mix: k === S.segments.length - 1 ? 0 : sm(end - 1.6, end + 0.4, t) };
    }
    start = end;
  }
  return { a: S.segments[0].tips, b: S.segments[0].tips, mix: 0 };
}

/** Camera (three.js axes, y up): corner-on, tilts over the top as each picture forms, slow drift; ends high/wide. */
export function camShow(t: number): { pos: [number, number, number]; look: [number, number, number]; D: number } {
  const w = showAt(t).w;
  const end = Math.min(1, Math.max(0, (t - 48) / 10));
  const el = ((30 + 36 * w * w * w + 12 * end * end) * Math.PI) / 180;
  const yaw = Math.PI / 4 + 0.22 * Math.sin((2 * Math.PI * t) / 23) * (1 - w) + 0.12 * Math.sin((2 * Math.PI * t) / 60);
  const D = 23 + 3 * end;
  return {
    pos: [Math.sin(yaw) * Math.cos(el) * D, Math.sin(el) * D, Math.cos(yaw) * Math.cos(el) * D],
    look: [0, 0.35 * (1 - w), 0],
    D,
  };
}
