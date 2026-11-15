// 0018 "This liquid is hungry" - sequel to the best performer (0012 "This liquid came alive", 1,239 views): the same
// ferrofluid creature on black mirror glass now HUNTS polished steel beads. It reaches out with an arm, wraps a bead,
// pulls it in and swallows it (a gulp ring + heartbeat), and grows with every bead. Rendered by
// scripts/blender/ferro_alive.py (frames from scripts/gen-hungry-frames.ts).
//  0-1.2    HOOK: frame 0 the arm is already around a bead - it yanks it in and swallows it (gulp)
//  1.2-3.8  it turns toward the next bead, crawls, reaches, swallows
//  4.8-7.2  two more, faster - it is getting greedy
//  8.4-11   a BIG bead: it struggles, spikes rise, wraps it whole and swallows it
//  11.6-14.6 every remaining bead starts rolling toward it on its own - it gulps them in a chain
//  15-18    full: it swells, the heartbeat races, a crown of spikes rises
//  18.4-20  it splits into twins
//  20-23    the twins settle, a last slow heartbeat;  22.5-24.5 fade to black
import { sm } from "./score";

export const HUNGRY = { duration: 24.5, fade: [22.5, 24.4] as [number, number], R0: 0.027, crown: [15.6, 18.2] as [number, number], split: [18.4, 19.6] as [number, number] };
const TAU = Math.PI * 2;

export interface Bead { x: number; y: number; r: number; eat: number; big?: boolean; roll?: boolean; gain: number }
export const BEADS: Bead[] = [
  { x: 0.034, y: 0.018, r: 0.009, eat: 0.9, gain: 0.07 },
  { x: -0.045, y: 0.03, r: 0.0095, eat: 3.6, gain: 0.07 },
  { x: -0.01, y: -0.055, r: 0.009, eat: 5.6, gain: 0.06 },
  { x: 0.05, y: -0.04, r: 0.0085, eat: 6.8, gain: 0.06 },
  { x: 0.06, y: 0.045, r: 0.02, eat: 10.6, big: true, gain: 0.16 },
  { x: -0.075, y: 0.02, r: 0.0085, eat: 12.1, roll: true, gain: 0.035 },
  { x: -0.03, y: 0.075, r: 0.009, eat: 12.7, roll: true, gain: 0.035 },
  { x: 0.075, y: -0.02, r: 0.0085, eat: 13.2, roll: true, gain: 0.035 },
  { x: -0.06, y: -0.06, r: 0.0095, eat: 13.6, roll: true, gain: 0.035 },
  { x: 0.02, y: -0.08, r: 0.0085, eat: 14.0, roll: true, gain: 0.035 },
  { x: 0.08, y: 0.07, r: 0.009, eat: 14.4, roll: true, gain: 0.035 },
];

// where the body heads: toward the next bead it wants, settling in the middle at the end
const WAY: [number, number, number][] = [
  [0, 0.008, 0.004], [1.2, 0.012, 0.006], [3.0, -0.018, 0.016], [3.8, -0.02, 0.016], [5.0, -0.005, -0.022],
  [6.0, 0.008, -0.02], [7.2, 0.018, -0.012], [8.6, 0.024, 0.012], [10.8, 0.03, 0.02], [12.0, 0.01, 0.008], [15, 0, 0],
];
function centre(t: number): [number, number] {
  let i = 0;
  while (i < WAY.length - 2 && t > WAY[i + 1][0]) i++;
  const [t0, x0, y0] = WAY[i], [t1, x1, y1] = WAY[i + 1];
  const k = sm(t0, t1, t);
  return [x0 + (x1 - x0) * k, y0 + (y1 - y0) * k];
}

/** body radius: grows with every bead swallowed */
export function radiusAt(t: number) {
  let g = 0;
  for (const b of BEADS) g += b.gain * sm(b.eat, b.eat + 0.5, t);
  return HUNGRY.R0 * (1 + g);
}

/** a bead's position: rests, (rolls toward the body), is pulled in by the arm, sinks into the body */
export function beadAt(b: Bead, t: number): [number, number, number, number] | null {
  const [cx, cy] = centre(t);
  let x = b.x, y = b.y;
  if (b.roll) {
    const k = sm(11.4, b.eat, t) ** 1.6;
    x = b.x + (cx - b.x) * k * 0.85;
    y = b.y + (cy - b.y) * k * 0.85;
  }
  const pull = sm(b.eat - 0.35, b.eat + 0.15, t);
  x += (cx - x) * pull;
  y += (cy - y) * pull;
  const sink = sm(b.eat, b.eat + 0.45, t);
  if (sink >= 0.999) return null;
  // sphere creature (owner, Nov 15): the arm lifts the bead up into the ball's middle
  const z = b.r * (1 - sink) + pull * radiusAt(t) * 0.95;
  return [x, y, z, b.r * (1 - 0.35 * sink)];
}

export interface Blob { x: number; y: number; R: number }
export function blobsAt(t: number): Blob[] {
  const R = radiusAt(t);
  const [cx, cy] = centre(t);
  const [s0, s1] = HUNGRY.split;
  if (t > s0) {
    const sep = sm(s0, s1, t);
    const d = 0.034 * sep, a = 0.6;
    const r = R * (1 - 0.21 * sep);
    return [{ x: cx + d * Math.cos(a), y: cy + d * Math.sin(a), R: r }, { x: cx - d * Math.cos(a), y: cy - d * Math.sin(a), R: r }];
  }
  const out: Blob[] = [{ x: cx, y: cy, R: R }];
  // the arm: a lobe that reaches toward the bead it is about to eat, then pulls back with it
  for (const b of BEADS) {
    if (b.roll) continue;
    const t0 = b.eat - (b.big ? 0.9 : 0.55);
    const out_ = sm(t0, t0 + 0.22, t);
    const whip = 1 + 0.3 * Math.exp(-Math.max(0, t - t0 - 0.22) * 9) * Math.sin(Math.max(0, t - t0 - 0.22) * 30);
    const reach = out_ * whip * (1 - sm(b.eat - 0.15, b.eat + 0.25, t));
    if (reach < 0.02) continue;
    const pos = beadAt(b, t);
    if (!pos) continue;
    const k = 0.78 * reach;
    out.push({ x: cx + (pos[0] - cx) * k, y: cy + (pos[1] - cy) * k, R: R * (b.big ? 0.75 : 0.55) * reach });
  }
  return out;
}

export function heartbeats(): { t: number; g: number }[] {
  const out: { t: number; g: number }[] = [];
  for (const b of BEADS) out.push({ t: b.eat + 0.12, g: b.big ? 1 : b.roll ? 0.45 : 0.7 }); // a gulp on every bead
  let t = 15.2, gap = 0.75;
  while (t < HUNGRY.crown[1]) { out.push({ t, g: 0.7 + 0.3 * sm(15, 18, t) }); t += gap; gap = Math.max(0.36, gap * 0.88); }
  out.push({ t: 20.6, g: 0.45 }, { t: 21.9, g: 0.3 });
  return out.sort((a, b) => a.t - b.t);
}

const LIGHTS: [number, number[], number[]][] = [
  [0, [0.1, 0.75, 1.0], [1.0, 0.1, 0.6]],
  [8, [0.25, 0.35, 1.0], [1.0, 0.2, 0.7]],
  [11.5, [0.6, 0.25, 1.0], [0.1, 0.8, 1.0]],
  [16, [0.6, 0.85, 1.0], [1.0, 0.1, 0.55]],
  [20, [0.25, 0.5, 1.0], [0.7, 0.2, 1.0]],
];
function lights(t: number) {
  let i = 0;
  while (i < LIGHTS.length - 2 && t > LIGHTS[i + 1][0]) i++;
  const [t0, a0, b0] = LIGHTS[i], [t1, a1, b1] = LIGHTS[i + 1];
  const k = sm(t0, t1, t);
  return { a: a0.map((v, j) => v + (a1[j] - v) * k), b: b0.map((v, j) => v + (b1[j] - v) * k) };
}

/** everything ferro_alive.py reads for one frame */
export function hungryFrame(t: number) {
  const bs = blobsAt(t);
  const rings: number[][] = [];
  for (const h of heartbeats()) {
    for (const [off, gg] of [[0, 1], [0.22, 0.6]] as const) {
      const age = t - (h.t + off);
      if (age < 0 || age > 1.4) continue;
      rings.push([-1, 0.07 * age, 0.012 * h.g * gg * Math.exp(-age * 2.2) * Math.min(1, age / 0.05)]);
    }
  }
  const beads: number[][] = [];
  for (const b of BEADS) {
    const p = beadAt(b, t);
    if (p) beads.push(p);
    // a small ring where a rolling bead hits the body
    const age = t - b.eat;
    if (age > 0 && age < 0.8) rings.push([-2, 0.05 * age, 0.004 * Math.exp(-age * 3.5), b.x, b.y]);
  }
  const fade = 1 - sm(20.2, 22.4, t);
  const crown = sm(HUNGRY.crown[0], HUNGRY.crown[0] + 0.6, t) * (1 - sm(HUNGRY.crown[1] - 0.3, HUNGRY.split[1], t));
  const big = sm(9.4, 10.0, t) * (1 - sm(10.8, 11.4, t)); // struggle spikes on the big bead
  const greedy = sm(11.4, 12, t) * (1 - sm(14.4, 15, t));
  let glow = 1;
  for (const h of heartbeats()) { const a = t - h.t; if (a > 0 && a < 1.2) glow += 0.28 * h.g * Math.exp(-a * 4.5) * Math.min(1, a / 0.04); }
  // the arm leans the spikes toward the bead it wants
  const [cx, cy] = centre(t);
  let lx = 0, ly = 0;
  for (const b of BEADS) {
    if (b.roll) continue;
    const w = sm(b.eat - 1.2, b.eat - 0.5, t) * (1 - sm(b.eat, b.eat + 0.4, t));
    const d = Math.hypot(b.x - cx, b.y - cy) || 1;
    lx += ((b.x - cx) / d) * 0.25 * w;
    ly += ((b.y - cy) / d) * 0.25 * w;
  }
  const L = lights(t);
  // camera: follows the creature, closer for the big bead, wider for the chain and the twins
  const yaw = (-14 + 28 * sm(0, HUNGRY.duration, t)) * (Math.PI / 180);
  const dist = 0.62 - 0.06 * big + 0.08 * greedy + 0.3 * sm(18.0, 19.8, t) + 0.04 * sm(21, 24, t); // the whole ball, its arm, the beads and both twins in frame
  const tilt = (54 + 6 * crown + 4 * big) * (Math.PI / 180); // the sphere reads round from a 3/4 side view
  return {
    yaw, dist, tilt, look: [cx * 0.8, cy * 0.8 + 0.02, radiusAt(t) * 0.9 + 0.006 * crown], // centred in the 9:16 frame
    blobs: bs.map((b) => [b.x, b.y, b.R]),
    rings,
    base: (0.0034 + 0.0015 * greedy) * fade + 0.0004,
    wave: [1, 0, 330, -TAU * 1.4 * t, 0.003 * greedy],
    crown: Math.max(crown, 0.45 * big),
    lean: [lx, ly],
    jumpers: [],
    beads,
    noDrops: true,
    glow,
    lightA: L.a,
    lightB: L.b,
  };
}

// ---- v2 edit (owner, Nov 15: "everyone will swipe in the 2-3rd sec - I want a good hook") ----
export const SPEED = 1.45;
export const COLD = 1.0; // cold open on the climax (story 16.6 -> 17.1)
export const REWIND = 0.8; // fast rewind back to story 0
export const REAL_DURATION = COLD + REWIND + HUNGRY.duration / SPEED;
/** story time -> real time (for sounds of story events) */
export const sToR = (s: number) => COLD + REWIND + s / SPEED;
/** real time -> story time */
export function rToS(r: number): number {
  if (r < COLD) return 16.6 + 0.5 * r;
  if (r < COLD + REWIND) { const k = (r - COLD) / REWIND; return 17.1 * (1 - k * k * (3 - 2 * k)); }
  return (r - COLD - REWIND) * SPEED;
}
/** the frame at REAL time r: the story frame, plus the cold-open harpoon at the lens and the pounces */
export function hungryReal(r: number) {
  const st = rToS(r);
  const fr = hungryFrame(st) as ReturnType<typeof hungryFrame> & { hop: number };
  const R = radiusAt(st);
  // cold open: a spike-harpoon fires straight at the camera, then the rewind pulls it back
  const harp = sm(0.25, 0.45, r) * (1 - sm(0.75, 1.15, r));
  if (harp > 0.01) {
    const [cx, cy] = [fr.blobs[0][0], fr.blobs[0][1]];
    const dx = -Math.sin(fr.yaw), dy = -Math.cos(fr.yaw); // toward the camera
    fr.blobs.push([cx + dx * 0.045 * harp, cy + dy * 0.045 * harp, R * 1.05 * harp]); // stops short of the lens: sharp, not a blur
  }
  // pounces: the ball leaps onto some beads (a hop arc in story time)
  let hop = 0;
  for (const [te, hgt] of [[3.6, 0.9], [6.8, 1.1], [10.6, 0.6]] as [number, number][]) {
    const a = (st - (te - 0.45)) / 0.55;
    if (a > 0 && a < 1) hop += hgt * R * Math.sin(Math.PI * a);
  }
  fr.hop = hop;
  // big spikes early (owner, Nov 15: "I want to see the bigger spikes after the start, not wait that long"):
  // it bristles angrily right after the rewind, and again as it spots the big bead
  const bristle = Math.max(sm(2.0, 2.3, r) * (1 - sm(3.1, 3.6, r)), 0.85 * sm(6.3, 6.6, r) * (1 - sm(7.3, 7.7, r)));
  fr.crown = Math.max(fr.crown, bristle);
  // camera: closer and lower in the cold open; pulls back as the ball grows so beads and twins stay in frame
  const grow = R / HUNGRY.R0;
  const cold = 1 - sm(COLD - 0.1, COLD + 0.4, r);
  fr.dist = fr.dist * (0.85 + 0.25 * (grow - 1)) * (1 - 0.3 * cold);
  fr.tilt = fr.tilt + 0.12 * cold;
  return fr;
}

/** real times of the early bristles (for the sound) */
export const BRISTLES: [number, number][] = [[2.0, 3.6], [6.3, 7.7]];
