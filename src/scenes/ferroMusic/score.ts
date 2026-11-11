// "Ferrofluid vs Music" (0012) v4 - "the fluid comes alive" (owner, Nov 11: v3 "too boring, only piano and spikes,
// the music sounds childish - must attract everyone"). One timeline drives the ferrofluid, the light, the camera, the
// cinematic score and the SFX. Physics-inspired (Rosensweig spikes on a hex lattice, heights from a moving field).
//  0-2.5     HOOK mid-action: the pool spins in a spiral of spikes, faster and faster
//  2.5       SNAP: the field cuts out, everything collapses flat (deep boom), one ring runs out
//  3-10      a cluster of tall spikes WALKS across the pool on its own, like something alive under the surface
//  9.5-16    a second cluster appears; the two circle each other closer and closer and MERGE at 16
//  16-22     the whole pool spins up again; light shifts cyan -> violet -> ice
//  22        PAYOFF: every spike gathers into ONE giant tower in the centre (boom, horns, strings)
//  24.2-27.2 the tower melts into a black mirror;  27.4-30 ENDING: the last note rings out, fade to black
export const FM = {
  duration: 30,
  fade: [27.4, 29.9] as [number, number],
  rPool: 0.05,
  spacing: 0.0058,
  maxH: 0.032,
  snap: 2.5,
  walk: [3.0, 16.0] as [number, number],
  second: 9.5,
  merge: 16.0,
  spin2: [16.0, 22.0] as [number, number],
  tower: 22.0,
  melt: [24.2, 27.2] as [number, number],
};

export const sm = (a: number, b: number, x: number) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
const TAU = Math.PI * 2;

export interface Site { x: number; y: number; r: number; a: number }
export function sites(): Site[] {
  const out: Site[] = [];
  const rows = Math.floor(FM.rPool / (FM.spacing * 0.866)) + 2;
  for (let j = -rows; j <= rows; j++)
    for (let i = -rows - 1; i <= rows + 1; i++) {
      const x = (i + 0.5 * (((j % 2) + 2) % 2)) * FM.spacing, y = j * FM.spacing * 0.866;
      const r = Math.hypot(x, y);
      if (r < FM.rPool * 0.9) out.push({ x, y, r, a: Math.atan2(y, x) });
    }
  return out;
}

/** how fast the whole pool physically turns (rev/s): the fluid really spins, spikes and all (owner: 'more alive') */
function spinRate(t: number): number {
  let r = 0;
  if (t < FM.snap) r = 0.15 + 0.2 * Math.max(0, t);
  else r = 0.65 * Math.exp(-(t - FM.snap) / 0.35);
  const u = t - (FM.spin2[0] + 0.4);
  if (u > 0) r += sm(0, 1.2, u) * (0.12 + 0.058 * u) * (1 - sm(FM.tower, FM.melt[1], t) * 0.85) * (1 - sm(FM.melt[0], FM.melt[1], t));
  return Math.min(r, 0.7); // <= 0.7 rev/s: 2 arms pass < 1.5 times/s, far under the flash limit
}
const ROT: number[] = [];
/** accumulated rotation of the pool (rad) */
export function rotAt(t: number): number {
  const dt = 1 / 600;
  if (!ROT.length) { let a = 0; for (let i = 0; i <= FM.duration * 600 + 1; i++) { ROT.push(a); a += TAU * spinRate(i * dt) * dt; } }
  return ROT[Math.min(ROT.length - 1, Math.max(0, Math.round(t * 600)))];
}

/** spiral phase: accelerating spin (rad) */
const spinPhase = (t: number) => TAU * (0.3 * t + 0.11 * t * t);

/** cluster centres (m) at time t: the walker, then the pair that orbits in and merges */
export function clusters(t: number): { x: number; y: number; w: number }[] {
  const [w0, w1] = FM.walk;
  if (t < w0 - 0.2 || t > FM.merge + 1.2) return [];
  const walkA = (u: number) => -2.2 + 0.55 * u + 0.35 * Math.sin(0.7 * u);
  if (t < 10) {
    // the walker wanders on a slow looping path, as if steered by something under the dish
    const u = t - w0;
    const R = 0.02 + 0.007 * Math.sin(1.1 * u);
    const a = walkA(u);
    const out = [{ x: R * Math.cos(a), y: R * Math.sin(a), w: sm(w0, w0 + 0.7, t) }];
    // the second one rises on the far side
    const a0 = walkA(7);
    if (t >= FM.second) out.push({ x: 0.022 * Math.cos(a0 + Math.PI), y: 0.022 * Math.sin(a0 + Math.PI), w: sm(FM.second, FM.second + 0.6, t) });
    return out;
  }
  // from 10 s the two orbit each other, spiralling in, and merge at 16
  const u = t - 10;
  const k = sm(10, w1, t);
  const R0 = Math.hypot(0.02 + 0.007 * Math.sin(1.1 * 7), 0);
  const R = (0.5 * (R0 + 0.022)) * (1 - k) ** 0.8;
  const a = walkA(7) + 0.55 * u + 1.2 * u * k;
  const merged = 1 - sm(w1 + 0.4, w1 + 1.2, t);
  return [
    { x: R * Math.cos(a), y: R * Math.sin(a), w: merged },
    { x: R * Math.cos(a + Math.PI), y: R * Math.sin(a + Math.PI), w: merged },
  ];
}

export interface FrameState { amp: Float32Array; dome: [number, number]; lightA: number[]; lightB: number[] }

// v6: no warm/brown tones (owner) - cyan, ultramarine, violet, magenta, ice
const LIGHTS: [number, number[], number[]][] = [
  [0, [0.1, 0.75, 1.0], [1.0, 0.1, 0.6]],
  [10, [0.25, 0.35, 1.0], [1.0, 0.2, 0.7]],
  [16, [0.6, 0.25, 1.0], [0.1, 0.8, 1.0]],
  [20, [0.6, 0.85, 1.0], [1.0, 0.1, 0.55]],
  [23, [0.15, 0.7, 1.0], [0.7, 0.2, 1.0]],
  [27, [0.25, 0.5, 1.0], [0.7, 0.2, 1.0]],
];
function lightsAt(t: number) {
  let i = 0;
  while (i < LIGHTS.length - 2 && t > LIGHTS[i + 1][0]) i++;
  const [t0, a0, b0] = LIGHTS[i], [t1, a1, b1] = LIGHTS[i + 1];
  const k = sm(t0, t1, t);
  return { a: a0.map((v, j) => v + (a1[j] - v) * k), b: b0.map((v, j) => v + (b1[j] - v) * k) };
}

export function stateAt(ss: Site[], t: number): FrameState {
  const amp = new Float32Array(ss.length);
  const alive = 1 - sm(FM.melt[0], FM.melt[1], t);
  // spiral 1 (hook), cut at the snap; spiral 2 builds from the merge to the tower
  const sp1 = 1 - sm(FM.snap, FM.snap + 0.22, t);
  const sp2 = sm(FM.spin2[0] + 0.4, FM.spin2[0] + 3.5, t) * (1 - sm(FM.tower - 0.25, FM.tower + 0.35, t));
  // spin 2 accelerates more gently so its arms never flicker past the 3 flashes/s photosensitivity limit
  const u2 = t - FM.spin2[0] + 1.2;
  const ph1 = spinPhase(t), ph2 = TAU * (0.25 * u2 + 0.035 * u2 * u2) + 1.3;
  const snapAge = t - FM.snap;
  const ring = snapAge > 0 && snapAge < 2 ? 0.0065 * Math.exp(-snapAge * 1.8) : 0;
  const quiet = sm(FM.snap, FM.snap + 0.2, t) * (1 - sm(3.0, 3.8, t)); // the pool goes flat after the snap
  const cl = clusters(t);
  const th = rotAt(t), cth = Math.cos(th), sth = Math.sin(th);
  const tower = sm(FM.tower - 0.15, FM.tower + 0.5, t) * alive;
  for (let k = 0; k < ss.length; k++) {
    const s = ss[k];
    const wx = s.x * cth - s.y * sth, wy = s.x * sth + s.y * cth; // site in the world (the pool turns)
    const env = Math.exp(-((s.r / 0.04) ** 6));
    // a living shimmer: the pool never rests while the field is on
    let h = (0.0012 + 0.0009 * Math.sin(5 * s.a + s.r * 310 + t * 2.6)) * alive * (1 - 0.85 * quiet);
    if (sp1 > 0) { const c = 0.5 + 0.5 * Math.cos(2 * s.a - 170 * s.r + 0 * ph1); h += sp1 * env * (0.0008 + 0.019 * c ** 8); }
    if (sp2 > 0) { const c = 0.5 + 0.5 * Math.cos(2 * s.a + 170 * s.r + 0 * ph2 + 1.3); h += sp2 * env * (0.0008 + 0.021 * c ** 8); }
    if (ring > 0) h += ring * Math.exp(-(((s.r - 0.06 * snapAge) / 0.006) ** 2));
    for (const c of cl) {
      const d2 = (wx - c.x) ** 2 + (wy - c.y) ** 2;
      const boost = 1 + 0.35 * sm(FM.merge - 0.6, FM.merge, t);
      h += c.w * (0.021 * boost * Math.exp(-d2 / 0.0095 ** 2) + 0.004 * Math.exp(-d2 / 0.02 ** 2));
    }
    if (tower > 0) h = h * (1 - 0.7 * tower * (1 - Math.exp(-((s.r / 0.02) ** 2)))) + tower * 0.03 * Math.exp(-((s.r / 0.014) ** 2)) * (1 + 0.04 * Math.sin(TAU * 1.1 * t + s.r * 500));
    amp[k] = FM.maxH * Math.tanh(h / FM.maxH);
  }
  const L = lightsAt(t);
  return { amp, dome: [0.011 * tower, 0.014], lightA: L.a, lightB: L.b };
}

/** camera: low and close, a slow orbit; follows the walking cluster a little; rises for the tower (blender axes, m) */
export function camAt(t: number) {
  // v5 (owner: 'too zoomed, show more, look professional'): a wide 3/4 product shot of the whole dish on a glossy
  // floor, a slow cinematic orbit, a gentle push-in for the tower, then easing away for the ending
  const u = sm(0, FM.duration, t);
  const yaw = (-22 + 44 * u) * (Math.PI / 180);
  const tw = sm(FM.tower - 2, FM.tower + 1.0, t) * (1 - sm(25.5, 29.5, t));
  const dist = 0.5 - 0.1 * tw + 0.05 * sm(26, 30, t);
  const tilt = (58 + 6 * tw) * (Math.PI / 180);
  return { yaw, dist, tilt, look: [0, 0, 0.004 + 0.008 * tw], rot: rotAt(t) };
}
