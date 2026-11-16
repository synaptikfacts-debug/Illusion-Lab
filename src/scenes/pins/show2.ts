// 0021 "4096 pins, one heartbeat" (owner, Nov 15: "let's do something like 0003 Singing Pins"; ice-blue look picked).
// Same machinery as show.ts (0011) with NEW pictures, a faster ~25 s structure and its own palette:
// ring ripple -> spiral -> hexagon flower -> crossing waves -> heartbeat ring -> dome, which melts into a flat mirror.
//
// Within a segment of length L (local time s):  phase = base*U(s) + delta_k*W(s) + ripple*dist*R(s)
// U: warped clock (fast at segment edges, still mid-segment), W: 0 at edges, 1 mid-segment (picture),
// R: ripple rings that vanish at the picture and the edges. At every segment edge all pins pass phase = integer at
// the same speed, so segments join seamlessly.

export type ShowImage = "ripple" | "spiral" | "hexflower" | "cross" | "heart" | "dome";

const ICE = ["#061a3d", "#2a6fd6", "#9fd8ff", "#ffffff"];
export const SHOW = {
  grid: 34, // 0021: ~900 bigger objects so each crystal reads (owner: different object)
  spacing: 0.178,
  maxHeight: 1.1,
  base: 6, // waves per segment (~1.5 per second): fast enough to race, far under the flash limit
  ripple: 2.6,
  segments: [
    { img: "ripple" as ShowImage, L: 4.0, tips: ICE },
    { img: "spiral" as ShowImage, L: 4.0, tips: ICE },
    { img: "hexflower" as ShowImage, L: 4.0, tips: ICE },
    { img: "cross" as ShowImage, L: 4.0, tips: ICE },
    { img: "heart" as ShowImage, L: 4.0, tips: ICE },
    { img: "dome" as ShowImage, L: 5.0, tips: ICE },
  ],
  /** frame 0 is already racing into the first picture */
  startAt: 0.3,
  hold: 1.2,
  melt: 2.8,
  fade: [23.4, 25.3] as [number, number],
  duration: 25.4,
};

const TAU = Math.PI * 2;
const sm = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

export function picture(img: ShowImage, u: number, v: number): number {
  const r = Math.hypot(u, v), a = Math.atan2(v, u);
  const c = (x: number) => Math.min(1, Math.max(0, x));
  switch (img) {
    case "ripple": // concentric rings fading outward
      return c(0.5 + 0.5 * Math.cos(r * 22) * Math.exp(-r * 0.9));
    case "spiral": // a four-arm spiral
      return c(Math.pow(0.5 + 0.5 * Math.cos(4 * a - r * 14), 2) * (1 - 0.35 * r));
    case "hexflower": { // six round petals around a hexagonal centre
      const petals = 0.5 + 0.5 * Math.cos(6 * a);
      const k = 0.35 + 0.4 * Math.pow(petals, 0.6);
      const body = sm(0.06, -0.06, r - k);
      return c(Math.max(0.08 + 0.92 * body * (0.75 + 0.25 * Math.cos(r * 18)), sm(0.18, 0.1, r)));
    }
    case "cross": { // two ring sources interfering
      const d1 = Math.hypot(u - 0.45, v), d2 = Math.hypot(u + 0.45, v);
      return c(0.5 + 0.25 * Math.cos(d1 * 20) + 0.25 * Math.cos(d2 * 20));
    }
    case "heart": // one bright ring (it beats - see heartAt)
      return c(0.1 + 0.9 * Math.exp(-Math.pow((r - 0.55) / 0.12, 2)));
    case "dome": // a perfect dome
      return c(Math.sqrt(Math.max(0, 1 - Math.pow(r / 0.85, 2))));
  }
}

export interface ShowPin {
  x: number;
  z: number;
  dist: number;
  delta: number[]; // phase offset per segment's picture
  target: number[];
}

export function layoutShow(): ShowPin[] {
  // 0021: a perfectly round disc of pins in a honeycomb (hex) pattern - not 0003's square wall (owner: not identical)
  const S = SHOW;
  const R = 3.05; // disc radius (world units), ~4,000 pins
  const sp = S.spacing, rowH = sp * 0.8660254;
  const pins: ShowPin[] = [];
  const rows = Math.ceil(R / rowH);
  for (let j = -rows; j <= rows; j++)
    for (let i = -rows - 1; i <= rows + 1; i++) {
      const x = (i + (((j % 2) + 2) % 2) * 0.5) * sp, z = j * rowH;
      const d = Math.hypot(x, z);
      if (d > R) continue;
      const pu = x / (R * 0.95), pv = -z / (R * 0.95);
      const target = S.segments.map((sg) => Math.min(1, Math.max(0, picture(sg.img, pu, pv))));
      pins.push({ x, z, dist: d / R, target, delta: target.map((tg) => Math.acos(1 - 2 * tg) / TAU) });
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
  // 0021: the whole wall always in frame (owner: no cut corners), a low, dramatic start, top-down-ish on each picture
  const w = showAt(t).w;
  const end = Math.min(1, Math.max(0, (t - 20) / 4));
  const hook = 1 - Math.min(1, t / 1.6);
  const el = ((20 + 26 * w * w * w + 14 * end * end - 6 * hook) * Math.PI) / 180; // low, side-on: a landscape, not a tray
  const yaw = Math.PI / 4 + 0.25 * Math.sin((2 * Math.PI * t) / 11) * (1 - w) + 0.1 * Math.sin((2 * Math.PI * t) / 25);
  const D = 25 + 2 * end - 4 * hook;
  return {
    pos: [Math.sin(yaw) * Math.cos(el) * D, Math.sin(el) * D, Math.cos(yaw) * Math.cos(el) * D],
    look: [0, 0.3 * (1 - w), 0],
    D,
  };
}
