// 0019 "This liquid has a heartbeat" - the ferrofluid creature, but unmistakably LIQUID (owner, Nov 15: 0018 "doesn't
// look like a liquid"): it splashes, pulses into spikes and melts flat again, climbs into a tower that drips, and
// throws a sheet of drops that rains back. New stage: dark smoky glass with blurred city-style lights behind.
// Rendered by scripts/blender/ferro_alive.py (FERRO_LOOK=D, FERRO_DOMEH=0.25), frames from gen-heartbeat-frames.ts.
//  0-0.35   HOOK: a glossy black drop is falling at the lens's eye level; 0.35 it SPLASHES - a crown of spikes,
//           droplets flung up, a splash ring
//  1.6-5.5  every heartbeat makes the puddle jump into spikes and melt back into a flat black mirror
//  6-12     the heartbeat speeds up; the liquid climbs into a TOWER; drops drip off it and splash below
//  12.2     PAYOFF: the tower collapses and flings a sheet of drops into the air - they rain back, each with a ring
//  14-17.5  ripples settle; 16.6 one last slow heartbeat;  17.5-19.5 fade to black
import { sm } from "./score";

export const HB = { duration: 19.6, fade: [17.5, 19.5] as [number, number], impact: 0.35, tower: [7.0, 10.0] as [number, number], collapse: 12.2, R: 0.034 };
const TAU = Math.PI * 2;
const G = 0.9; // slow-motion gravity (m/s^2)
const hash = (i: number) => { const x = Math.sin(i * 12.9898 + 78.233) * 43758.5453; return x - Math.floor(x); };

export function beats(): { t: number; g: number }[] {
  const out = [1.6, 2.6, 3.6, 4.6, 5.5].map((t) => ({ t, g: 0.85 }));
  let t = 6.3, gap = 0.9;
  while (t < HB.collapse - 0.2) { out.push({ t, g: 0.6 + 0.4 * sm(6, 12, t) }); t += gap; gap = Math.max(0.42, gap * 0.9); }
  out.push({ t: HB.collapse, g: 1.2 }, { t: 16.6, g: 0.45 });
  return out;
}

interface Flight { t0: number; x0: number; y0: number; z0: number; vx: number; vy: number; vz: number; r: number }
/** every airborne drop in the reel (splash droplets, tower drips, the payoff rain) */
function flights(): Flight[] {
  const out: Flight[] = [];
  // the falling drop of the hook: from above, lands at the centre at t = impact
  const fallFrom = 0.03; // frame 0: the drop is already in view, just above the puddle
  const vz0 = -(fallFrom - G * HB.impact * HB.impact / 2) / HB.impact;
  out.push({ t0: 0, x0: 0, y0: 0, z0: fallFrom, vx: 0, vy: 0, vz: vz0, r: 0.0075 });
  // splash droplets
  for (let i = 0; i < 12; i++) {
    const a = (i / 12) * TAU + 0.3 * hash(i), s = 0.022 + 0.02 * hash(i + 40);
    out.push({ t0: HB.impact + 0.02, x0: 0.02 * Math.cos(a), y0: 0.02 * Math.sin(a), z0: 0.004, vx: Math.cos(a) * s, vy: Math.sin(a) * s, vz: 0.22 + 0.12 * hash(i + 7), r: 0.0022 + 0.0016 * hash(i + 3) });
  }
  // drips off the tower
  for (let i = 0; i < 7; i++) {
    const t0 = 8.6 + i * 0.48, a = i * 2.3;
    out.push({ t0, x0: 0.009 * Math.cos(a), y0: 0.009 * Math.sin(a), z0: towerH(t0) * 0.85, vx: Math.cos(a) * 0.012, vy: Math.sin(a) * 0.012, vz: 0.02, r: 0.0026 + 0.001 * hash(i + 90) });
  }
  // the payoff: the collapsing tower flings a sheet of drops
  for (let i = 0; i < 34; i++) {
    const a = i * 2.39996 + 0.2 * hash(i + 200), s = 0.025 + 0.06 * hash(i + 300);
    out.push({ t0: HB.collapse + 0.02 * hash(i), x0: 0.006 * Math.cos(a), y0: 0.006 * Math.sin(a), z0: 0.03, vx: Math.cos(a) * s, vy: Math.sin(a) * s, vz: 0.18 + 0.2 * hash(i + 400), r: 0.0018 + 0.0022 * hash(i + 500) });
  }
  return out;
}
const FLIGHTS = flights();
export const landings = () => FLIGHTS.map((f) => { const T = (f.vz + Math.sqrt(f.vz * f.vz + 2 * G * f.z0)) / G; return { t: f.t0 + T, x: f.x0 + f.vx * T, y: f.y0 + f.vy * T, r: f.r }; });

export function towerH(t: number) {
  const up = sm(HB.tower[0], HB.tower[1], t) * (1 - sm(HB.collapse - 0.05, HB.collapse + 0.35, t));
  return 0.055 * up * (1 + 0.04 * Math.sin(TAU * 1.3 * t));
}

// emerald palette (owner: new colours vs the purple reels): emerald, teal, icy white
const LIGHTS: [number, number[], number[]][] = [
  [0, [0.0, 1.0, 0.55], [0.0, 0.8, 0.85]],
  [6, [0.2, 1.0, 0.7], [0.6, 1.0, 0.95]],
  [12, [0.0, 0.9, 0.9], [0.0, 1.0, 0.5]],
  [17, [0.1, 0.8, 0.6], [0.5, 1.0, 0.9]],
];
function lights(t: number) {
  let i = 0;
  while (i < LIGHTS.length - 2 && t > LIGHTS[i + 1][0]) i++;
  const [t0, a0, b0] = LIGHTS[i], [t1, a1, b1] = LIGHTS[i + 1];
  const k = sm(t0, t1, t);
  return { a: a0.map((v, j) => v + (a1[j] - v) * k), b: b0.map((v, j) => v + (b1[j] - v) * k) };
}

export function heartbeatFrame(t: number) {
  const alive = 1 - sm(HB.fade[0] - 0.5, HB.fade[1], t);
  // the puddle: small before the drop lands, spreads on impact, breathes with every beat
  let R = HB.R * (0.82 + 0.18 * sm(HB.impact, HB.impact + 0.4, t));
  let crown = 0;
  const rings: number[][] = [];
  for (const b of beats()) {
    const a = t - b.t;
    if (a > 0 && a < 1.3) {
      crown = Math.max(crown, b.g * Math.min(1, a / 0.07) * Math.exp(-a * 3.2)); // jumps into spikes, melts flat
      rings.push([-1, 0.07 * a, 0.01 * b.g * Math.exp(-a * 2.2) * Math.min(1, a / 0.05)]);
    }
    R *= 1 + (a > 0 && a < 0.6 ? 0.05 * b.g * Math.sin(Math.PI * a / 0.6) : 0);
  }
  // the splash of the hook: a big crown burst and a ring
  const ai = t - HB.impact;
  if (ai > 0 && ai < 1.4) {
    crown = Math.max(crown, 1.15 * Math.min(1, ai / 0.06) * Math.exp(-ai * 2.6));
    rings.push([-1, 0.09 * ai, 0.016 * Math.exp(-ai * 2.4)]);
  }
  // splash rings where airborne drops land
  for (const l of landings()) {
    const a = t - l.t;
    if (a > 0 && a < 0.9) rings.push([-2, 0.05 * a, (0.0035 + l.r) * Math.exp(-a * 3.5), l.x, l.y]);
  }
  // airborne drops (stretched along their velocity)
  const jumpers: number[][] = [];
  for (const f of FLIGHTS) {
    const a = t - f.t0;
    if (a < 0) continue;
    const T = (f.vz + Math.sqrt(f.vz * f.vz + 2 * G * f.z0)) / G;
    if (a > T) continue;
    const vz = f.vz - G * a;
    const sp = Math.hypot(f.vx, f.vy, vz);
    jumpers.push([f.x0 + f.vx * a, f.y0 + f.vy * a, f.z0 + f.vz * a - 0.5 * G * a * a + f.r * 0.8, f.r, 1 + 1.4 * Math.min(1, sp / 0.4), Math.atan2(f.vy, f.vx), Math.atan2(vz, Math.hypot(f.vx, f.vy) + 1e-6)]);
  }
  const tower = towerH(t);
  let glow = 1;
  for (const b of beats()) { const a = t - b.t; if (a > 0 && a < 1.2) glow += 0.3 * b.g * Math.exp(-a * 4.5) * Math.min(1, a / 0.04); }
  const L = lights(t);
  const u = sm(0, HB.duration, t);
  const tw = sm(HB.tower[0] - 1, HB.tower[1], t) * (1 - sm(HB.collapse + 0.5, HB.collapse + 2.5, t));
  return {
    yaw: (-16 + 32 * u) * (Math.PI / 180),
    dist: 0.36 + 0.06 * tw + 0.05 * sm(HB.collapse, HB.collapse + 0.6, t) * (1 - sm(14, 16, t)) + 0.03 * sm(17, 19.5, t),
    tilt: (77 - 4 * tw) * (Math.PI / 180), // low enough that the city lights fill the top of the frame (no flat edge band)
    look: [0, 0.006, 0.012 + 0.45 * tower + 0.012 * (1 - sm(0.3, 0.8, t))],
    blobs: [[0, 0, R]],
    rings,
    base: 0.00015, // between beats it is a smooth, glossy black mirror (liquid)
    wave: [1, 0, 330, 0, 0],
    crown: crown * alive,
    lean: [0, 0],
    jumpers,
    beads: [],
    noDrops: true,
    tower,
    glow,
    lightA: L.a,
    lightB: L.b,
  };
}
