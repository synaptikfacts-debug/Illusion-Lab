// "Marble Cascade": a Galton board. Glossy marbles pour from a funnel through rows of chrome pins (each pin hit
// = left or right, a click), fall into bins and stack into a rainbow bell curve. The last marble is gold and lands on
// the top of the peak. Closed-form in time, deterministic, shared by picture and sound.
import { rng } from "../../core/seed";

export const GB = {
  rows: 14,
  s: 0.36, // pin spacing
  dy: 0.27, // row spacing
  r: 0.027, // marble radius
  perLevel: 6,
  count: 3000,
  emit: [-3.2, 17.0] as [number, number],
  step: 0.085, // seconds per pin row
  goldAt: 19.6,
  duration: 27,
  fade: [24.4, 26.8] as [number, number],
  topY: 3.4, // first pin row
};
export const BINS = GB.rows + 1;
export const floorY = () => GB.topY - GB.rows * GB.dy - 0.25 - 4.9; // bin floor
export const binX = (b: number) => (b - GB.rows / 2) * GB.s;

export interface Marble {
  t0: number; // release time
  path: Uint8Array; // pin choices (0 left, 1 right)
  bin: number;
  slot: number; // arrival order in its bin
  land: number; // time it lands on its stack
  hue: number; // 0..1 by release time
  gold: boolean;
  jit: number;
}

const g = 9.81 * 0.55;

export function buildMarbles(seed: number): Marble[] {
  const r = rng(seed, "galton");
  const ms: Marble[] = [];
  for (let i = 0; i < GB.count; i++) {
    const t0 = GB.emit[0] + (i / (GB.count - 1)) * (GB.emit[1] - GB.emit[0]) + (r() - 0.5) * 0.012;
    const path = new Uint8Array(GB.rows);
    let p = 0;
    for (let k = 0; k < GB.rows; k++) { path[k] = r() < 0.5 ? 0 : 1; p += path[k]; }
    ms.push({ t0, path, bin: p, slot: 0, land: 0, hue: i / GB.count, gold: false, jit: r() });
  }
  // the gold marble: straight down the middle onto the peak
  const gp = new Uint8Array(GB.rows);
  for (let k = 0; k < GB.rows; k++) gp[k] = k % 2;
  ms.push({ t0: GB.goldAt, path: gp, bin: GB.rows / 2, slot: 0, land: 0, hue: 0, gold: true, jit: 0.5 });
  // landing times + slots (arrival order per bin)
  const byBin: Marble[][] = Array.from({ length: BINS }, () => []);
  for (const m of ms) {
    const fallTop = GB.topY - GB.rows * GB.dy;
    m.land = m.t0 + 0.32 + GB.rows * GB.step + fallTime(fallTop, 0); // refined below
    byBin[m.bin].push(m);
  }
  for (const list of byBin) {
    list.sort((a, b) => a.land - b.land);
    list.forEach((m, n) => {
      m.slot = n;
      const [, sy] = stackPos(m.bin, n);
      m.land = m.t0 + 0.32 + GB.rows * GB.step + fallTime(GB.topY - GB.rows * GB.dy, sy);
    });
  }
  return ms;
}

function fallTime(y0: number, y1: number) {
  return Math.sqrt((2 * Math.max(0.01, y0 - y1)) / g);
}

export function stackPos(bin: number, slot: number): [number, number] {
  const L = GB.perLevel, level = Math.floor(slot / L), col = slot % L;
  const off = level % 2 ? GB.r * 0.5 : -GB.r * 0.5;
  const x = binX(bin) + (col - (L - 1) / 2) * GB.r * 2.02 + off;
  const y = floorY() + GB.r + level * GB.r * 1.86;
  return [x, y];
}

/** Marble position at time t (null = not yet released). */
export function marbleAt(m: Marble, t: number): [number, number] | null {
  if (t < m.t0) return null;
  let tt = t - m.t0;
  // funnel drop to the first pin
  const fun = 0.32;
  const yTop = GB.topY + 0.9;
  if (tt < fun) {
    const u = tt / fun;
    return [(1 - u) * (m.jit - 0.5) * 0.25, yTop - (yTop - GB.topY - GB.r) * u * u];
  }
  tt -= fun;
  // pins
  if (tt < GB.rows * GB.step) {
    const k = Math.floor(tt / GB.step), u = tt / GB.step - k;
    let p = 0;
    for (let j = 0; j < k; j++) p += m.path[j];
    const x0 = (p - k / 2) * GB.s, x1 = (p + m.path[k] - (k + 1) / 2) * GB.s;
    const y0 = GB.topY - k * GB.dy + GB.r;
    const x = x0 + (x1 - x0) * u;
    const y = y0 + 0.05 * Math.sin(Math.PI * u) - GB.dy * u * u;
    return [x, y];
  }
  tt -= GB.rows * GB.step;
  // free fall into the bin, sliding to its slot
  const [sx, sy] = stackPos(m.bin, m.slot);
  const yS = GB.topY - GB.rows * GB.dy + GB.r;
  const T = m.land - (m.t0 + fun + GB.rows * GB.step);
  if (tt < T) {
    const u = tt / T;
    const x0 = binX(m.bin);
    return [x0 + (sx - x0) * Math.min(1, u * 1.4), yS - (yS - sy) * u * u];
  }
  // landed: a tiny settle bounce
  const d = t - m.land;
  return [sx, sy + 0.012 * Math.exp(-d * 12) * Math.abs(Math.sin(d * 40))];
}

/** Hit events for sound: pin clicks + landings. */
export function events(ms: Marble[]) {
  const pins: { t: number; x: number }[] = [];
  const lands: { t: number; x: number; level: number; gold: boolean }[] = [];
  for (const m of ms) {
    let p = 0;
    for (let k = 0; k < GB.rows; k++) {
      pins.push({ t: m.t0 + 0.32 + k * GB.step, x: (p - k / 2) * GB.s });
      p += m.path[k];
    }
    lands.push({ t: m.land, x: binX(m.bin), level: Math.floor(m.slot / GB.perLevel), gold: m.gold });
  }
  return { pins, lands };
}
