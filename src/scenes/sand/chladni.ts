// "Sand Song": coloured sand on a vibrating plate. Each tone makes the grains hop off the moving parts of the plate
// and gather on its still lines (Chladni figures). Abstract, physical, no pictures.
// Story (s): HOOK grains mid-air leaping into the first figure -> a new tone every ~3 s, each figure more complex ->
// a fast run of tones (climax) -> the grand final figure -> the tone stops, grains settle, camera rises, fade to cream.
// Positions are precomputed per figure (gradient descent onto the nodal lines) and animated in closed form.
import { rng } from "../../core/seed";

export const PW = 4.2, PH = 7.4; // plate size (world units), 9:16-ish

export interface Mode { n: number; m: number; s: 1 | -1; t: number; hop: number; freq: number }

export const SSTORY = {
  duration: 28,
  modes: [
    { n: 1, m: 3, s: -1, t: -0.45, hop: 0.55, freq: 196 },
    { n: 2, m: 4, s: 1, t: 2.8, hop: 0.32, freq: 247 },
    { n: 3, m: 5, s: -1, t: 5.6, hop: 0.3, freq: 294 },
    { n: 2, m: 7, s: 1, t: 8.4, hop: 0.3, freq: 330 },
    { n: 4, m: 7, s: -1, t: 11.2, hop: 0.28, freq: 392 },
    { n: 5, m: 8, s: 1, t: 13.6, hop: 0.26, freq: 440 },
    { n: 3, m: 9, s: -1, t: 15.3, hop: 0.24, freq: 494 },
    { n: 6, m: 9, s: 1, t: 16.6, hop: 0.24, freq: 587 },
    { n: 7, m: 10, s: -1, t: 17.8, hop: 0.22, freq: 659 },
    { n: 6, m: 11, s: 1, t: 19.4, hop: 0.42, freq: 784 }, // the grand final figure
  ] as Mode[],
  toneOff: 24.0,
  fade: [25.2, 27.8] as [number, number],
};

export const GRAIN_COLOURS: [number, number, number][] = [
  [0.91, 0.69, 0.29], // gold
  [0.77, 0.33, 0.18], // rust
  [0.82, 0.76, 0.66], // sand ivory
  [0.18, 0.65, 0.63], // turquoise
];

const PI = Math.PI;
export function chladni(md: Mode, x: number, y: number) {
  const u = (x + PW / 2) / PW, v = (y + PH / 2) / PH;
  return Math.cos(md.n * PI * u) * Math.cos(md.m * PI * v) + md.s * Math.cos(md.m * PI * u) * Math.cos(md.n * PI * v);
}
function grad(md: Mode, x: number, y: number): [number, number] {
  const u = (x + PW / 2) / PW, v = (y + PH / 2) / PH, n = md.n * PI, m = md.m * PI;
  const du = -n * Math.sin(n * u) * Math.cos(m * v) - md.s * m * Math.sin(m * u) * Math.cos(n * v);
  const dv = -m * Math.cos(n * u) * Math.sin(m * v) - md.s * n * Math.cos(m * u) * Math.sin(n * v);
  return [du / PW, dv / PH];
}

export interface Sand {
  count: number;
  /** settled positions per figure: pos[k][i*2..] (k = 0: the random start before the first tone) */
  pos: Float32Array[];
  delay: Float32Array; // per grain per figure: when it leaves (antinode grains first)
  colour: Uint8Array;
  size: Float32Array;
  seed: Float32Array;
}

let cache: Sand | null = null;

export function buildSand(seed: number, count = 60000): Sand {
  if (cache && cache.count === count) return cache;
  const r = rng(seed, "sand");
  const M = SSTORY.modes;
  const pos: Float32Array[] = [new Float32Array(count * 2)];
  const delay = new Float32Array(count * M.length);
  const colour = new Uint8Array(count), size = new Float32Array(count), sd = new Float32Array(count);
  for (let i = 0; i < count; i++) {
    pos[0][i * 2] = (r() - 0.5) * PW * 0.98;
    pos[0][i * 2 + 1] = (r() - 0.5) * PH * 0.98;
    // colour in soft bands so the figures show colour flows
    const band = Math.floor(((pos[0][i * 2 + 1] / PH + 0.5) * 4 + (r() - 0.5) * 1.2 + 4) % 4);
    colour[i] = r() < 0.25 ? Math.floor(r() * 4) : band;
    size[i] = 0.75 + r() * 0.5;
    sd[i] = r();
  }
  M.forEach((md, k) => {
    const prev = pos[k], next = new Float32Array(count * 2);
    for (let i = 0; i < count; i++) {
      // the vibration scatters the sand before it gathers: start the descent from a spread-out position
      let x = prev[i * 2], y = prev[i * 2 + 1];
      const f0 = Math.abs(chladni(md, x, y));
      if (r() < 0.55) { x = (r() - 0.5) * PW * 0.98; y = (r() - 0.5) * PH * 0.98; }
      else { x += (r() - 0.5) * 0.9; y += (r() - 0.5) * 0.9; }
      // the movement sweeps out from the centre as a ring (only part of the plate moves at once)
      void f0;
      delay[i * M.length + k] = Math.min(1, Math.hypot(x / (PW / 2), y / (PH / 2)) / 1.414) * 0.9 + r() * 0.1;
      for (let it = 0; it < 60; it++) {
        const f = chladni(md, x, y), [gx, gy] = grad(md, x, y);
        const g2 = gx * gx + gy * gy + 1e-4;
        let sx = -f * gx / g2 * 0.6, sy = -f * gy / g2 * 0.6;
        const L = Math.hypot(sx, sy);
        if (L > 0.06) { sx *= 0.06 / L; sy *= 0.06 / L; }
        x += sx + (r() - 0.5) * 0.004; y += sy + (r() - 0.5) * 0.004;
        x = Math.max(-PW / 2 + 0.02, Math.min(PW / 2 - 0.02, x));
        y = Math.max(-PH / 2 + 0.02, Math.min(PH / 2 - 0.02, y));
      }
      // lines have a little width
      const w = 0.035 * (r() + r() + r() - 1.5);
      const [gx, gy] = grad(md, x, y), gl = Math.hypot(gx, gy) + 1e-6;
      next[i * 2] = Math.max(-PW / 2 + 0.02, Math.min(PW / 2 - 0.02, x + (gx / gl) * w + (r() - 0.5) * 0.012));
      next[i * 2 + 1] = Math.max(-PH / 2 + 0.02, Math.min(PH / 2 - 0.02, y + (gy / gl) * w + (r() - 0.5) * 0.012));
    }
    pos.push(next);
  });
  cache = { count, pos, delay, colour, size, seed: sd };
  return cache;
}

/** Index of the current figure at time t and its start. */
export function modeAt(t: number) {
  const M = SSTORY.modes;
  let k = 0;
  while (k + 1 < M.length && t >= M[k + 1].t) k++;
  return k;
}

/** Grain i at time t: x, y (plate), h (height above the plate). */
export function grainAt(s: Sand, i: number, t: number): [number, number, number] {
  const M = SSTORY.modes;
  const k = modeAt(t);
  const md = M[k];
  const a = s.pos[k], b = s.pos[k + 1];
  const next = k + 1 < M.length ? M[k + 1].t : md.t + 2.6;
  const window = (next - md.t) * 0.9;
  const dur = Math.min(0.85, window * 0.5) * (0.85 + 0.3 * s.seed[i]);
  const d = s.delay[i * M.length + k] * Math.max(0, window - dur);
  const q = Math.min(1, Math.max(0, (t - md.t - d) / dur));
  const e = q * q * (3 - 2 * q);
  const x = a[i * 2] + (b[i * 2] - a[i * 2]) * e;
  const y = a[i * 2 + 1] + (b[i * 2 + 1] - a[i * 2 + 1]) * e;
  // hops: big at the start of a move, shrinking bounces
  let h = 0;
  if (q > 0 && q < 1) {
    const nb = 2, ph = q * nb;
    h = md.hop * 0.55 * (0.6 + 0.8 * s.seed[i]) * Math.abs(Math.sin(Math.PI * ph)) * Math.pow(1 - q, 1.5);
  }
  // while the tone plays, grains off the still lines keep dancing a little
  if (t < SSTORY.toneOff && q >= 1) {
    const f = Math.abs(chladni(md, x, y));
    void f; // grains rest on the lines (no dance: it flickered)
  }
  return [x, y, h];
}
