// 0012 v7 "This liquid came alive" - the ferrofluid behaves like a living creature (owner, Nov 11: "make it more alive,
// the spinning is too much, treat this like a matter of life"). No mechanical rotation: the puddle itself MOVES
// (metaball outline: it reaches, crawls, splits in two, merges), its spikes ride with it and lean where it goes, and it
// has a HEARTBEAT - every beat sends a ring of spikes rushing outward (and a deep soft lub-dub on the soundtrack).
//  0-2.6     HOOK: frame 0 is mid-heartbeat - a ring of tall spikes rushing out, two more strong beats
//  2.6-5     it notices something: a pseudopod reaches out to the right, spikes lean toward it
//  5-10      it crawls across the mirror, a ripple running along its back
//  10-15.2   it splits in two; the halves drift apart and answer each other's heartbeats (call and response)
//  15.2-16   they rush back together and MERGE (a shockwave ring of spikes)
//  16-22     the heartbeat speeds up, the spikes grow and lift
//  22        PAYOFF: the CROWN - a tower of the tallest spikes, breathing
//  24.3-27.5 one long exhale: the spikes sink, it settles into a round black mirror; one last faint heartbeat
//  27.5-30   ENDING: fade to black
import { sm } from "./score";

export const LIFE = {
  duration: 30,
  fade: [27.5, 29.9] as [number, number],
  reach: 2.6,
  crawl: [5, 10] as [number, number],
  split: 10,
  merge: 15.2,
  build: [16, 22] as [number, number],
  crown: 22,
  exhale: [24.3, 27.5] as [number, number],
  R: 0.042,
};

const TAU = Math.PI * 2;

/** heartbeat times (the first beat of each lub-dub pair) and which blob beats (0 both / main, 1 = left, 2 = right) */
export function beats(): { t: number; who: number; g: number }[] {
  const out: { t: number; who: number; g: number }[] = [];
  for (const t of [-0.25, 0.95, 2.05]) out.push({ t, who: 0, g: 1 });
  for (const t of [3.6, 5.1, 6.6, 8.1, 9.4]) out.push({ t, who: 0, g: 0.55 });
  // split: call and response
  [10.9, 12.0, 13.1, 14.1].forEach((t, i) => { out.push({ t, who: 1, g: 0.7 }); out.push({ t: t + 0.5, who: 2, g: 0.7 }); });
  // build: accelerating
  let t = 16.6, gap = 1.0;
  while (t < LIFE.crown - 0.3) { out.push({ t, who: 0, g: 0.7 + 0.3 * sm(16.5, 22, t) }); t += gap; gap = Math.max(0.42, gap * 0.86); }
  // after the crown: slow breathing beats, then the last faint one
  for (const tb of [23.1, 24.3]) out.push({ t: tb, who: 0, g: 0.45 });
  out.push({ t: 26.4, who: 0, g: 0.25 });
  return out.sort((a, b) => a.t - b.t);
}

export interface Blob { x: number; y: number; R: number }

/** the creature's body: one or two metaball blobs (m, world xy) */
export function blobs(t: number): Blob[] {
  const R = LIFE.R;
  // crawl path of the body centre
  const cx = 0.03 * sm(LIFE.crawl[0], LIFE.crawl[1], t) * (1 - sm(LIFE.split, LIFE.merge + 0.8, t));
  const cy = 0.012 * Math.sin(TAU * sm(LIFE.crawl[0], LIFE.crawl[1], t) * 0.5) * (1 - sm(LIFE.split, LIFE.merge, t));
  const reachOut = sm(LIFE.reach, LIFE.reach + 1.4, t) * (1 - sm(LIFE.crawl[0] + 1.5, LIFE.crawl[1], t));
  if (t < LIFE.split) {
    const main = { x: cx, y: cy, R: R * (1 - 0.18 * reachOut) };
    // the pseudopod: a smaller lobe pulled out to the right, which the body then follows
    const pod = { x: cx + 0.034 * reachOut + 0.004 * Math.sin(TAU * t * 0.8), y: cy + 0.004 * Math.sin(TAU * t * 0.5), R: R * 0.55 * reachOut };
    return reachOut > 0.02 ? [main, pod] : [main];
  }
  // split: two halves drift apart, slowly circle, then rush back together
  const sep = sm(LIFE.split, LIFE.split + 1.6, t) * (1 - sm(LIFE.merge - 0.7, LIFE.merge, t));
  const a = Math.PI / 2 + 0.35 * sm(LIFE.split, LIFE.merge, t);
  const d = 0.034 * sep;
  const r = R * (1 - 0.25 * sep);
  const mx = cx * (1 - sm(LIFE.split, LIFE.merge, t)), my = 0;
  return [
    { x: mx + d * Math.cos(a), y: my + d * Math.sin(a), R: r },
    { x: mx - d * Math.cos(a), y: my - d * Math.sin(a), R: r },
  ];
}

export interface LifeFrame {
  blobs: number[][]; // [x, y, R]
  rings: number[][]; // [blob index or -1 = body centre, radius, amp]
  base: number;
  wave: number[]; // [dirx, diry, k, phase, amp]
  crown: number;
  lean: number[]; // [lx, ly]
  jumpers: number[][]; // [x, y, z, radius, stretch, yaw, pitch] of every droplet in the air (or resting on the mirror)
  glow: number; // neon brightness: the creature glows a little on every heartbeat
}

/** everything the renderer needs for the fluid at time t */
export function lifeAt(t: number): LifeFrame {
  const bs = blobs(t);
  const alive = 1 - sm(LIFE.exhale[0], LIFE.exhale[1], t);
  const rings: number[][] = [];
  for (const b of beats()) {
    for (const [off, gg] of [[0, 1], [0.22, 0.6]] as const) { // lub-dub
      const age = t - (b.t + off);
      if (age < 0 || age > 1.6) continue;
      const radius = 0.075 * age;
      const amp = 0.013 * b.g * gg * Math.exp(-age * 2.0) * Math.min(1, age / 0.05);
      const idx = b.who === 0 ? -1 : bs.length > 1 ? b.who - 1 : -1;
      rings.push([idx, radius, amp]);
    }
  }
  const build = sm(LIFE.build[0], LIFE.crown, t) * alive;
  const crown = sm(LIFE.crown - 0.12, LIFE.crown + 0.45, t) * alive * (1 + 0.05 * Math.sin(TAU * 0.45 * (t - LIFE.crown)));
  // the crawl ripple runs along the body in the direction of travel
  const crawling = sm(LIFE.crawl[0] - 0.5, LIFE.crawl[0] + 0.5, t) * (1 - sm(LIFE.crawl[1] - 0.6, LIFE.crawl[1] + 0.4, t));
  const lean = [0.25 * sm(LIFE.reach, LIFE.reach + 1, t) * (1 - sm(LIFE.split - 1, LIFE.split, t)), 0];
  const J = jumpersAt(t);
  for (const r of J.rings) rings.push(r);
  let glow = 1;
  for (const b of beats()) { const age = t - b.t; if (age > 0 && age < 1.2) glow += 0.32 * b.g * Math.exp(-age * 4.5) * Math.min(1, age / 0.04); }
  return {
    blobs: bs.map((b) => [b.x, b.y, b.R]),
    rings,
    jumpers: J.drops,
    glow,
    base: (0.0032 + 0.004 * build) * alive + 0.0004,
    wave: [1, 0, 330, -TAU * 1.4 * t, 0.006 * crawling],
    crown,
    lean,
  };
}

// --- details that keep people watching (owner, Nov 11: "add details that make everyone stay") ---
// Droplets LEAP out of the creature now and then (a spike flicks a bead up, it arcs in slow motion and drops back in
// with a tiny splash ring), and at the crown a burst of beads sprays out onto the mirror; during the exhale the
// creature slowly pulls them all back home.
const G = 1.1; // slow-motion gravity (m/s^2) so a leap reads clearly
export interface Leap { t: number; a: number; d: number; up: number; out: number; r: number; home: boolean }
export function leaps(): Leap[] {
  const out: Leap[] = [];
  const small: [number, number][] = [[1.25, 0.6], [4.2, -0.4], [6.1, 2.4], [7.7, 1.2], [8.9, -2.0], [11.6, 2.8], [12.7, -0.9], [13.9, 1.8], [17.4, 0.3], [18.6, -2.4], [19.7, 1.4], [20.9, -1.0], [25.2, 0.9]];
  small.forEach(([t, a], i) => out.push({ t, a, d: 0.012 + 0.006 * (i % 3), up: 0.3 + 0.05 * (i % 2), out: 0.012 + 0.004 * (i % 2), r: 0.0024 + 0.0006 * (i % 3), home: true }));
  // the crown burst: beads spray out in all directions and land on the mirror
  for (let i = 0; i < 12; i++) out.push({ t: LIFE.crown + 0.06 + 0.03 * (i % 4), a: (i / 12) * TAU + 0.2, d: 0.006, up: 0.27 + 0.035 * (i % 3), out: 0.085 + 0.02 * (i % 2), r: 0.0026 + 0.0008 * (i % 3), home: false });
  return out;
}
function centroid(t: number) {
  const bs = blobs(t);
  let x = 0, y = 0, w = 0;
  for (const b of bs) { x += b.x * b.R; y += b.y * b.R; w += b.R; }
  return { x: x / w, y: y / w };
}
export function jumpersAt(t: number): { drops: number[][]; rings: number[][]; landings: { t: number; burst: boolean }[] } {
  const drops: number[][] = [], rings: number[][] = [], landings: { t: number; burst: boolean }[] = [];
  for (const L of leaps()) {
    const c0 = centroid(L.t);
    const x0 = c0.x + Math.cos(L.a) * L.d, y0 = c0.y + Math.sin(L.a) * L.d, z0 = 0.012;
    const T = (L.up + Math.sqrt(L.up * L.up + 2 * G * z0)) / G; // flight time until it lands at z = 0
    landings.push({ t: L.t + T, burst: !L.home });
    const age = t - L.t;
    if (age < 0) continue;
    const vx = Math.cos(L.a) * L.out / T, vy = Math.sin(L.a) * L.out / T;
    if (age <= T) {
      const z = z0 + L.up * age - 0.5 * G * age * age;
      const vz = L.up - G * age;
      const sp = Math.hypot(vx, vy, vz);
      drops.push([x0 + vx * age, y0 + vy * age, Math.max(z, 0) + L.r * 0.8, L.r, 1 + 1.2 * Math.min(1, sp / 0.35), Math.atan2(vy, vx), Math.atan2(vz, Math.hypot(vx, vy))]);
      continue;
    }
    const lx = x0 + vx * T, ly = y0 + vy * T, la = age - T;
    // the splash ring where it lands
    if (la < 0.9) rings.push([-2, 0.05 * la, (L.home ? 0.0045 : 0.0025) * Math.exp(-la * 3.5), lx, ly]);
    if (L.home) continue;
    // burst beads rest on the mirror, wobble a little, then get pulled home in the exhale
    const pull = sm(LIFE.exhale[0] + 0.3 + 0.1 * (L.a % 1), LIFE.exhale[1] - 0.6, t);
    const c = centroid(t);
    const px = lx + (c.x - lx) * pull ** 2, py = ly + (c.y - ly) * pull ** 2;
    if (pull < 0.97) drops.push([px, py, L.r * 0.55, L.r, 1 + 0.5 * pull * (1 - pull) * 4, Math.atan2(c.y - py, c.x - px), 0]);
  }
  return { drops, rings, landings };
}

/** light colours (no warm tones) */
const LIGHTS: [number, number[], number[]][] = [
  [0, [0.1, 0.75, 1.0], [1.0, 0.1, 0.6]],
  [10, [0.25, 0.35, 1.0], [1.0, 0.2, 0.7]],
  [16, [0.6, 0.25, 1.0], [0.1, 0.8, 1.0]],
  [21, [0.6, 0.85, 1.0], [1.0, 0.1, 0.55]],
  [24, [0.15, 0.7, 1.0], [0.7, 0.2, 1.0]],
  [28, [0.25, 0.5, 1.0], [0.7, 0.2, 1.0]],
];
export function lightsAt(t: number) {
  let i = 0;
  while (i < LIGHTS.length - 2 && t > LIGHTS[i + 1][0]) i++;
  const [t0, a0, b0] = LIGHTS[i], [t1, a1, b1] = LIGHTS[i + 1];
  const k = sm(t0, t1, t);
  return { a: a0.map((v, j) => v + (a1[j] - v) * k), b: b0.map((v, j) => v + (b1[j] - v) * k) };
}

/** camera: the whole creature centred, following it gently; a slow drift (no spinning); closer for the crown */
export function lifeCam(t: number) {
  const bs = blobs(t);
  let fx = 0, fy = 0, w = 0;
  for (const b of bs) { fx += b.x * b.R; fy += b.y * b.R; w += b.R; }
  fx /= w; fy /= w;
  const tw = sm(LIFE.crown - 2.5, LIFE.crown + 0.8, t) * (1 - sm(25, 29, t));
  const spread = bs.length > 1 ? Math.hypot(bs[0].x - bs[1].x, bs[0].y - bs[1].y) : 0;
  const yaw = (-12 + 24 * sm(0, LIFE.duration, t)) * (Math.PI / 180);
  // two cinematic close-ups: the reaching arm, and the moment the halves merge
  // (the merge close-up was removed: the fast push over the spike pattern failed the photosensitivity check)
  const cu1 = sm(2.9, 3.6, t) * (1 - sm(4.6, 5.4, t)), cu2 = 0;
  const cu = Math.max(cu1, cu2);
  const tgx = cu1 > cu2 ? 0.03 : fx, tgy = cu1 > cu2 ? 0 : fy;
  fx += (tgx - fx) * cu1 * 0.8; fy += (tgy - fy) * cu1 * 0.8;
  const dist = (0.36 + 1.6 * spread * 0.5 - 0.06 * tw + 0.04 * sm(26, 30, t)) * (1 - 0.4 * cu);
  const tilt = (56 + 6 * tw + 10 * cu) * (Math.PI / 180);
  return { yaw, dist, tilt, look: [fx, fy, 0.004 + 0.009 * tw + 0.004 * cu] };
}

/** the creature's story moments under the names the score uses (scripts/gen-music-ferromusic.ts) */
export const FM_EVENTS = {
  snap: LIFE.reach,
  walk: LIFE.crawl,
  second: LIFE.split,
  merge: LIFE.merge,
  spin2: [LIFE.build[0], LIFE.crown] as [number, number],
  tower: LIFE.crown,
  melt: LIFE.exhale,
  fade: LIFE.fade,
};
