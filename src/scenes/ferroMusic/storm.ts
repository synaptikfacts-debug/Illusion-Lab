// 0023 v2 "This liquid became a storm" (owner, Nov 16: v1 mercury drops "super childish"; wants "spikes, brutal,
// beautiful, catchy" - like the effects of 0018). A whole black lake of magnetic liquid (no creature, no small objects):
// spike waves, a vortex, a twisting spiked tornado that collapses into a giant ring. Crimson + steel white, dark stage.
// Rendered by scripts/blender/ferro_alive.py (FERRO_LOOK=E, FERRO_DOME=0, FERRO_DOMEH=0, FERRO_JUMPERS=40).
//  0-0.7    HOOK: a wall of huge spikes races straight at the lens and crests over it
//  0.7-1.6  fast rewind to a calm mirror
//  2.2      one bass hit: a ring of spikes bursts out from the centre
//  3.6-7    spike fronts rip across the lake (left -> right, then back)
//  7-11     the spikes start to turn: a vortex, faster and faster
//  11-14    a twisting tornado of spikes rises out of the vortex
//  14.0     COLLAPSE: the tower falls, droplets fly, a giant ring of spikes races outward
//  15-20    aftershocks fade, the lake goes still, fade to black
import { sm } from "./score";

export const STORM = { duration: 20, fade: [18.2, 19.9] as [number, number], collapse: 14.0 };
const TAU = Math.PI * 2;
const hash = (i: number) => { const x = Math.sin(i * 12.9898 + 78.233) * 43758.5453; return x - Math.floor(x); };
const G = 0.9;

export const HITS = [2.2, 3.6, 5.2, 14.0]; // the moments the sound hits hardest

function flights() {
  const out: { t0: number; x0: number; y0: number; z0: number; vx: number; vy: number; vz: number; r: number }[] = [];
  for (let i = 0; i < 40; i++) {
    const a = i * 2.39996, sp = 0.04 + 0.07 * hash(i);
    out.push({ t0: STORM.collapse + 0.03 * hash(i + 9), x0: 0.008 * Math.cos(a), y0: 0.008 * Math.sin(a), z0: 0.03 + 0.03 * hash(i + 3), vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, vz: 0.12 + 0.2 * hash(i + 5), r: 0.0018 + 0.0022 * hash(i + 7) });
  }
  return out;
}
const FL = flights();
export const landings = () => FL.map((f) => { const T = (f.vz + Math.sqrt(f.vz * f.vz + 2 * G * f.z0)) / G; return { t: f.t0 + T, x: f.x0 + f.vx * T, y: f.y0 + f.vy * T, r: f.r }; });

export function stormFrame(t: number) {
  const rings: number[][] = [];
  // photosensitivity (failed 5.5/s on v2 preview): crests spaced wide, few rows, so no point flickers > ~2x per second
  const front = (cx: number, cy: number, t0: number, speed: number, amp: number, n = 2) => {
    const a = t - t0;
    if (a < 0 || a > 2.2) return;
    for (let k = 0; k < n; k++) rings.push([-2, speed * a - k * 0.07, amp * (1 - 0.25 * k) * Math.min(1, a / 0.1) * (1 - sm(1.6, 2.2, a)), cx, cy]);
  };
  // HOOK: the wall races at the lens (from far behind, +y), then the rewind pulls it back
  if (t < 1.6) {
    // rises IN PLACE (a travelling wall swept dark crests over the bright lake: flash check 8/s)
    const up = sm(-0.35, 0.3, t) * (1 - sm(0.7, 1.5, t));
    for (let j = 0; j < 2; j++) rings.push([-2, 0.56 - j * 0.06, 0.034 * (1 - 0.2 * j) * up, 0, 0.6]);
  }
  // the bass hit: a ring from the centre
  const ah = t - 2.2;
  if (ah > 0 && ah < 1.6) rings.push([-1, 0.075 * ah, 0.022 * Math.exp(-ah * 1.4)]);
  // fronts rip across: left -> right, then right -> left
  front(-0.6, 0.0, 3.6, 0.3, 0.026);
  front(0.6, 0.05, 5.2, 0.3, 0.028);
  // the collapse: a giant ring races outward, plus aftershocks
  for (const [t0, a0] of [[STORM.collapse, 0.034], [STORM.collapse + 0.6, 0.02], [STORM.collapse + 1.4, 0.012]] as [number, number][]) {
    const a = t - t0;
    if (a > 0 && a < 2.5) rings.push([-1, 0.07 * a, a0 * Math.exp(-a * 0.9)]);
  }
  // the vortex and the tornado
  const v = sm(7.0, 8.5, t) * (1 - sm(STORM.collapse - 0.1, STORM.collapse + 0.3, t));
  const spin = 0.9 * Math.max(0, t - 7) + 0.14 * Math.max(0, t - 7) ** 2; // arms pass a point < ~1.2x per second
  const towerUp = sm(11.0, 13.6, t) * (1 - sm(STORM.collapse - 0.05, STORM.collapse + 0.35, t));
  // droplets thrown by the collapse
  const jumpers: number[][] = [];
  for (const f of FL) {
    const a = t - f.t0;
    if (a < 0) continue;
    const T = (f.vz + Math.sqrt(f.vz * f.vz + 2 * G * f.z0)) / G;
    if (a > T) continue;
    const vz = f.vz - G * a;
    jumpers.push([f.x0 + f.vx * a, f.y0 + f.vy * a, f.z0 + f.vz * a - 0.5 * G * a * a + f.r, f.r, 1 + 1.3 * Math.min(1, Math.hypot(f.vx, f.vy, vz) / 0.4), Math.atan2(f.vy, f.vx), Math.atan2(vz, Math.hypot(f.vx, f.vy) + 1e-6)]);
  }
  for (const l of landings()) { const a = t - l.t; if (a > 0 && a < 0.9) rings.push([-2, 0.05 * a, (0.004 + l.r) * Math.exp(-a * 3.5), l.x, l.y]); }
  const alive = 1 - sm(17.5, 19.5, t);
  let glow = 1;
  for (const h of HITS) { const a = t - h; if (a > 0 && a < 1.2) glow += 0.12 * Math.exp(-a * 4) * Math.min(1, a / 0.04); }
  // camera: low over the lake; in the hook almost at water level; rises with the tornado; eases back at the end
  const hook = 1 - sm(1.0, 2.4, t);
  const tw = sm(10.5, 13.2, t) * (1 - sm(14.5, 16.5, t));
  return {
    yaw: (-8 + 16 * sm(0, 20, t)) * (Math.PI / 180),
    dist: 0.2 + 0.05 * (1 - hook) + 0.06 * tw + 0.05 * sm(14, 15, t) * (1 - sm(16, 18, t)) + 0.02 * sm(17, 20, t),
    tilt: (80 - 6 * (1 - hook) - 12 * tw) * (Math.PI / 180),
    look: [0, 0.01 + 0.03 * hook, 0.008 + 0.03 * tw],
    blobs: [[0, 0, 0.088]],
    rings,
    base: 1e-5, // a float, never an int (the renderer adds into it)
    wave: [1, 0, 330, 0, 0],
    swirl: [0.016 * v * alive, 3, -spin],
    crown: 0.9 * towerUp * alive,
    tower: 0.07 * towerUp,
    lean: [0, 0],
    jumpers,
    beads: [],
    noDrops: true,
    glow,
    lightA: [1.0, 0.06, 0.1],
    lightB: [1.0, 0.95, 0.92],
  };
}
