// 0024 visual effects (owner, Nov 16: v2 motion test "boring, nothing happens at the start, almost no visual effects, just
// a ball"). Every effect has a physical cause in the mechanism and is computed from the same timeline as the bands:
//  GRIND SPARKS  each spinning dial grinds against its pawl and throws a stream of sparks (rate ~ spin speed) that arc
//                down and bounce on the floor
//  LOCK          a burst of sparks out of the notch, an energy pulse racing round the band, a shockwave across the floor,
//                a small arc jumping the seam
//  UNLOCK        a ring of sparks out of the equator, arcs across every slit, a big floor shockwave
//  IGNITE/FLARES the core erupts: sparks radiate, arcs lash out to the inner bands, shockwaves; energy motes orbit the core
// Story time drives everything, so in the cold-open rewind the sparks fly backwards into the sphere.
// Output: polylines {p, c, s, w} that scripts/blender/core_unlock.py turns into camera-facing emissive ribbons.
import { bandsAt, FINAL, IGNITE, INNER, OUTER, SCHED, SEAM_PULSE, sm } from "./core";

type V = [number, number, number];
export const CEN: V = [0, 0, 0.36];
export const FLARES = [12.05, 12.7, 13.35]; // core eruptions in the payoff (12.7 lands at 0.3 s in the cold open)
const G = 3.2, DRAG = 1.1;
const hash = (i: number) => { const x = Math.sin(i * 12.9898 + 78.233) * 43758.5453; return x - Math.floor(x); };
const deg = Math.PI / 180;
const add = (a: V, b: V): V => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const mul = (a: V, k: number): V => [a[0] * k, a[1] * k, a[2] * k];
const len = (a: V) => Math.hypot(a[0], a[1], a[2]);
const norm = (a: V): V => mul(a, 1 / (len(a) || 1));
type Band = ReturnType<typeof bandsAt>["outer"][number];

function rot(v: V, ax: V, a: number): V { // Rodrigues
  const c = Math.cos(a), s = Math.sin(a), d = v[0] * ax[0] + v[1] * ax[1] + v[2] * ax[2];
  const cr: V = [ax[1] * v[2] - ax[2] * v[1], ax[2] * v[0] - ax[0] * v[2], ax[0] * v[1] - ax[1] * v[0]];
  return [v[0] * c + cr[0] * s + ax[0] * d * (1 - c), v[1] * c + cr[1] * s + ax[1] * d * (1 - c), v[2] * c + cr[2] * s + ax[2] * d * (1 - c)];
}
/** a point in a band's local frame -> world (same matrix as the renderer: T(C) R(axis,angle) S(scale) T(lift) Rz(spin-90)) */
function bandPt(b: Band, p: V): V {
  const a = b.spin - Math.PI / 2, c = Math.cos(a), s = Math.sin(a);
  let q: V = [p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2] + b.lift / b.scale];
  q = mul(q, b.scale);
  q = rot(q, b.axis, b.angle);
  return add(q, CEN);
}
const sph = (r: number, lat: number, az: number): V => [r * Math.cos(lat) * Math.cos(az), r * Math.cos(lat) * Math.sin(az), r * Math.sin(lat)];
const midLat = (lats: number[], i: number) => ((lats[i] + lats[i + 1]) / 2) * deg;

interface Spark { t0: number; p0: V; v0: V; life: number; hot: number }
let SPARKS: Spark[] | null = null;
const PAWL_AZ = -75 * deg;

function buildSparks(): Spark[] {
  const out: Spark[] = [];
  let seed = 1;
  const r = () => hash(seed++);
  const rnd = (): V => { const z = 2 * r() - 1, a = r() * Math.PI * 2, q = Math.sqrt(1 - z * z); return [q * Math.cos(a), q * Math.sin(a), z]; };
  // grind streams while the dials spin
  for (const [shell, sp, starts, locks] of [[0, OUTER, SCHED.OUT_START, SCHED.OUT_LOCK], [1, INNER, SCHED.IN_START, SCHED.IN_LOCK]] as const) {
    const n = sp.lats.length - 1;
    for (let i = 0; i < n; i++) {
      for (let tau = starts[i]; tau < locks[i]; tau += 0.01) {
        const s1 = bandsAt(tau + 0.005)[shell ? "inner" : "outer"][i].spin, s0 = bandsAt(tau - 0.005)[shell ? "inner" : "outer"][i].spin;
        const w = (s1 - s0) / 0.01;
        const rate = (shell ? 45 : 70) * Math.min(1, Math.abs(w) / 4);
        let k = rate * 0.01;
        while (k > 0) {
          if (r() < k) {
            const lat = midLat(sp.lats, i) + (r() - 0.5) * 6 * deg;
            const p0 = add(sph(sp.r, lat, PAWL_AZ), CEN);
            const tan: V = mul([-Math.sin(PAWL_AZ), Math.cos(PAWL_AZ), 0], Math.sign(w));
            const v0 = add(add(mul(tan, 0.45 + 0.65 * r()), mul(norm(sph(1, lat, PAWL_AZ)), 0.1 + 0.3 * r())), add([0, 0, 0.15 * r()], mul(rnd(), 0.15)));
            out.push({ t0: tau + r() * 0.01, p0, v0, life: 0.45 + 0.6 * r(), hot: 1 });
          }
          k -= 1;
        }
      }
    }
  }
  // a burst out of a notch when a dial clacks into place, or when a band lands home
  const notchBurst = (tau: number, shell: number, i: number, n: number, speed: number) => {
    const sp = shell ? INNER : OUTER;
    const b = bandsAt(tau)[shell ? "inner" : "outer"][i];
    const lat = midLat(sp.lats, i);
    const p0 = bandPt(b, sph(sp.r, lat, 0));
    const nrm = norm(add(p0, mul(CEN, -1)));
    // sparks shear off ALONG the seam (sideways, both ways), not out of the notch at the lens - the first version sprayed
    // the macro camera with out-of-focus blobs and failed the flash check (3.5/s at 5.6 s)
    const tan = norm([-nrm[1], nrm[0], 0]);
    for (let k = 0; k < n; k++) {
      const side = r() < 0.5 ? 1 : -1;
      const v0 = add(add(mul(tan, side * speed * (0.5 + 0.8 * r())), mul(nrm, 0.12 * r())), [0, 0, 0.1 + 0.3 * r()]);
      out.push({ t0: tau + r() * 0.03, p0, v0, life: 0.4 + 0.5 * r(), hot: 1.2 });
    }
  };
  SCHED.OUT_LOCK.forEach((t, i) => notchBurst(t, 0, i, 34, 1));
  SCHED.IN_LOCK.forEach((t, i) => notchBurst(t, 1, i, 22, 0.8));
  SCHED.IN_HOME.forEach((t, i) => notchBurst(t, 1, i, 10, 0.5));
  SCHED.OUT_ORDER.forEach((b, k) => notchBurst(SCHED.OUT_HOME[k], 0, b, b === 7 ? 70 : 14, b === 7 ? 1.1 : 0.6));
  // unlock: a ring of sparks out of the equator slit
  for (const [tau, rr, n] of [[SCHED.OUT_OPEN + 0.2, OUTER.r, 170], [SCHED.IN_OPEN + 0.2, INNER.r, 110]] as const) {
    for (let k = 0; k < n; k++) {
      const az = r() * Math.PI * 2;
      const d = sph(1, (r() - 0.5) * 10 * deg, az);
      out.push({ t0: tau + r() * 0.12, p0: add(mul(d, rr * 1.05), CEN), v0: add(mul(d, 0.5 + 0.9 * r()), [0, 0, 0.2 + 0.3 * r()]), life: 0.6 + 0.7 * r(), hot: 1.1 });
    }
  }
  // the core erupts: ignition + flares
  for (const [tau, n, sp] of [[IGNITE, 240, 1.4], ...FLARES.map((f, i) => (i === 1 ? [f, 340, 1.6] : [f, 120, 1.1]) as [number, number, number])] as const) { // 12.7 = the cold-open eruption
    for (let k = 0; k < n; k++) {
      const d = norm(add(rnd(), [0, 0, 0.15]));
      out.push({ t0: tau + r() * 0.06, p0: add(mul(d, 0.03), CEN), v0: mul(d, sp * (0.5 + 0.8 * r())), life: 0.6 + 0.8 * r(), hot: 1.3 });
    }
  }
  return out;
}

function sparkPos(s: Spark, a: number): V {
  let p: V = [...s.p0], v: V = [...s.v0];
  const dt = 0.01;
  for (let x = 0; x < a; x += dt) {
    const h = Math.min(dt, a - x);
    v = [v[0] * (1 - DRAG * h), v[1] * (1 - DRAG * h), v[2] * (1 - DRAG * h) - G * h];
    p = add(p, mul(v, h));
    if (p[2] < 0.001) { p[2] = 0.001; v = [v[0] * 0.55, v[1] * 0.55, -v[2] * 0.3]; }
  }
  return p;
}

export interface Line { p: number[]; c: V; s: number; w: number; t?: number }
const HOT: V = [0.85, 0.95, 1.0], CY: V = [0.25, 0.75, 1.0], VI: V = [0.55, 0.28, 1.0];
const mix = (a: V, b: V, k: number): V => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k];
const flat = (pts: V[]) => pts.flatMap((p) => p.map((x) => Math.round(x * 1e5) / 1e5));

/** jagged lightning between two points (midpoint displacement), reshaped `seed` times per second */
function bolt(a: V, b: V, seed: number, rough = 0.28): V[] {
  let pts: V[] = [a, b];
  let amp = len(add(b, mul(a, -1))) * rough;
  let k = 0;
  for (let lvl = 0; lvl < 4; lvl++) {
    const nx: V[] = [pts[0]];
    for (let i = 0; i < pts.length - 1; i++) {
      const m = mul(add(pts[i], pts[i + 1]), 0.5);
      const j: V = [(hash(seed * 31 + k++) - 0.5) * amp, (hash(seed * 31 + k++) - 0.5) * amp, (hash(seed * 31 + k++) - 0.5) * amp];
      nx.push(add(m, j), pts[i + 1]);
    }
    pts = nx;
    amp *= 0.5;
  }
  return pts;
}

export function fxFrame(tau: number): Line[] {
  SPARKS ??= buildSparks();
  const L: Line[] = [];
  const B = bandsAt(tau);
  // sparks
  for (const s of SPARKS) {
    const a = tau - s.t0;
    if (a <= 0 || a > s.life) continue;
    const f = a / s.life;
    const p2 = sparkPos(s, a), p1 = sparkPos(s, Math.max(0, a - 0.018)), p0 = sparkPos(s, Math.max(0, a - 0.05));
    const c = f < 0.35 ? mix(HOT, CY, f / 0.35) : mix(CY, VI, (f - 0.35) / 0.65);
    L.push({ p: flat([p0, p1, p2]), c, s: 30 * s.hot * (1 - f) ** 1.4, w: 0.0011, t: 1 });
  }
  // floor shockwaves
  const rings: [number, number, number][] = [
    ...SCHED.OUT_LOCK.map((t) => [t, 5, 0.55] as [number, number, number]),
    ...SCHED.IN_LOCK.map((t) => [t, 3.5, 0.45] as [number, number, number]),
    [SEAM_PULSE, 9, 0.8], [SCHED.OUT_OPEN + 0.2, 10, 0.9], [SCHED.IN_OPEN + 0.2, 8, 0.8], [IGNITE, 14, 1.0],
    ...FLARES.map((f) => [f, 9, 0.9] as [number, number, number]), [FINAL, 9, 0.8],
  ];
  for (const [t0, s0, v] of rings) {
    const a = tau - t0;
    if (a <= 0 || a > 1.1) continue;
    const rad = 0.09 + v * a, pts: V[] = [];
    for (let k = 0; k <= 128; k++) { const q = (k / 128) * Math.PI * 2; pts.push([rad * Math.cos(q), rad * Math.sin(q), 0.0015]); }
    L.push({ p: flat(pts), c: mix(CY, VI, a / 1.1), s: s0 * (1 - a / 1.1) ** 2, w: 0.003 + 0.012 * a });
  }
  // energy pulse racing round a band after it locks (along its upper edge, both ways from the notch)
  const pulses = (shell: number, locks: number[]) => locks.forEach((t0, i) => {
    const a = tau - t0;
    if (a <= 0 || a > 0.5) return;
    const sp = shell ? INNER : OUTER, b = (shell ? B.inner : B.outer)[i];
    const lat = sp.lats[i + 1] * deg - 0.6 * deg;
    for (const dir of [1, -1]) {
      const pts: V[] = [];
      for (let k = 0; k <= 16; k++) { const q = dir * (a * 7 - 0.5 + 0.5 * (k / 16)); pts.push(bandPt(b, sph(sp.r * 1.003, lat, q))); }
      L.push({ p: flat(pts), c: CY, s: 16 * (1 - a / 0.5), w: 0.0022 });
    }
  });
  pulses(0, SCHED.OUT_LOCK);
  pulses(1, SCHED.IN_LOCK);
  // seam crackle: a short arc jumps the gap at the notch when a dial locks
  SCHED.OUT_LOCK.forEach((t0, i) => {
    const a = tau - t0;
    if (a <= 0 || a > 0.18 || i >= 7) return;
    const p = bandPt(B.outer[i], sph(OUTER.r * 1.01, OUTER.lats[i + 1] * deg - 4 * deg, 0.04));
    const q = bandPt(B.outer[i + 1], sph(OUTER.r * 1.01, OUTER.lats[i + 1] * deg + 4 * deg, -0.04));
    L.push({ p: flat(bolt(p, q, Math.floor(tau * 30) + i * 7, 0.6)), c: HOT, s: 14, w: 0.0012 });
  });
  // arcs: across the slits while the shells unlock, and from the core to the inner bands while it burns
  const slot = Math.floor(tau * 24);
  const unlockArcs = (t0: number, shell: number) => {
    const a = tau - t0;
    if (a <= 0 || a > 0.7) return;
    const sp = shell ? INNER : OUTER, bs = shell ? B.inner : B.outer;
    for (let k = 0; k < 4; k++) {
      const i = Math.floor(hash(slot * 13 + k + shell * 50) * (bs.length - 1));
      const az = hash(slot * 17 + k) * Math.PI * 2;
      const p = bandPt(bs[i], sph(sp.r, sp.lats[i + 1] * deg - 2 * deg, az)), q = bandPt(bs[i + 1], sph(sp.r, sp.lats[i + 1] * deg + 2 * deg, az + 0.1));
      L.push({ p: flat(bolt(p, q, slot * 5 + k, 0.5)), c: mix(HOT, VI, hash(slot + k)), s: 12 * (1 - a / 0.7), w: 0.0012 });
    }
  };
  unlockArcs(SCHED.OUT_OPEN + 0.25, 0);
  unlockArcs(SCHED.IN_OPEN + 0.25, 1);
  const burn = sm(IGNITE - 0.2, IGNITE + 0.3, tau) * (1 - sm(13.6, 14.4, tau));
  if (burn > 0.01) {
    const flareBoost = FLARES.reduce((m, f) => Math.max(m, Math.exp(-(((tau - f) / 0.15) ** 2))), Math.exp(-(((tau - IGNITE) / 0.25) ** 2)));
    const n = 2 + Math.round(4 * flareBoost);
    for (let k = 0; k < n; k++) {
      const i = Math.floor(hash(slot * 7 + k) * 6);
      const az = hash(slot * 11 + k) * Math.PI * 2;
      const sp = INNER, b = B.inner[i];
      const q = bandPt(b, sph(sp.r - sp.t, midLat(sp.lats, i), az));
      const d = norm(add(q, mul(CEN, -1)));
      const p = add(CEN, mul(d, 0.026));
      L.push({ p: flat(bolt(p, q, slot * 3 + k, 0.35)), c: mix(HOT, VI, 0.3 * hash(slot * 5 + k)), s: (9 + 10 * flareBoost) * burn, w: 0.0013 });
    }
    // energy motes orbiting the core
    for (let k = 0; k < 90; k++) {
      const rr = 0.045 + 0.11 * hash(k * 3 + 1), w = (2.2 + 3 * hash(k * 3 + 2)) * (hash(k + 9) > 0.5 ? 1 : -1);
      const ax = norm([hash(k * 5 + 3) - 0.5, hash(k * 5 + 4) - 0.5, 1.4 * (hash(k * 5 + 5) - 0.5)]);
      const base = norm([ax[1], -ax[0], 0.0001]);
      const ph = hash(k * 7) * Math.PI * 2 + w * tau;
      const pts: V[] = [];
      for (let j = 0; j <= 4; j++) pts.push(add(CEN, mul(rot(base, ax, ph - Math.sign(w) * 0.07 * j), rr)));
      L.push({ p: flat(pts), c: mix(CY, VI, hash(k * 13)), s: 9 * burn * (0.6 + 0.4 * Math.sin(tau * 3 + k)), w: 0.0011 });
    }
  }
  return L;
}
