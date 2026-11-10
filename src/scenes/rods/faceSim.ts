// "The Face": the chrome rod wall (same engine and look as "The Eye"), new story. A face built from rods.
// HOOK: frame 0 = the face staring at you with glowing eyes -> 0.6 s it SHATTERS (glowing shockwave + sparks) ->
// drops and ripples -> rising spiral -> 12.6 SNAP into the face with its eyes closed -> it WAKES (eyes open, glow) ->
// looks left and right -> slow smile -> WINKS at you -> big warm smile (laugh) -> calm, closes its eyes peacefully ->
// sinks back into the wall, last ember, glowing dust drifts up -> fade to black.
// Pure TS, deterministic, shared by picture, particles and sound.
import { rng } from "../../core/seed";
import type { ParticleData } from "../../gl/particleShader";
import { rodLayout, type RodSim } from "./sim";

export const FSTORY = {
  duration: 30.5,
  explode: 0.6,
  centre: { u: 0, v: 0.1 },
  sources: [
    { t: 1.75, u: 0, v: 0.1, a: 0.95 },
    { t: 2.45, u: -0.6, v: 1.25, a: 0.95 },
    { t: 3.0, u: 0.6, v: -1.25, a: 0.95 },
    { t: 3.55, u: 0.6, v: 1.25, a: 0.95 },
    { t: 4.1, u: -0.6, v: -1.25, a: 0.95 },
    { t: 4.9, u: 0, v: 0.7, a: 1.0 },
    { t: 5.6, u: -0.5, v: -0.4, a: 0.9 },
    { t: 6.3, u: 0.5, v: -0.4, a: 0.9 },
    { t: 7.2, u: 0, v: 0.1, a: 1.15 },
  ],
  spiral: [8.6, 12.6] as [number, number],
  snap: 12.6,
  wake: [13.4, 14.0] as [number, number], // eyes open
  look: [
    { t: 14.3, gx: 0, gy: 0 },
    { t: 14.9, gx: -1, gy: 0.1 },
    { t: 15.7, gx: -1, gy: 0.1 },
    { t: 16.3, gx: 1, gy: 0.1 },
    { t: 17.0, gx: 1, gy: 0.1 },
    { t: 17.5, gx: 0, gy: 0 },
  ],
  smile: [17.3, 18.5] as [number, number],
  wink: [19.0, 19.75] as [number, number], // left eye (screen right) closes and opens
  laugh: [20.3, 21.5] as [number, number], // big smile + mouth opens + glow pulse
  calm: [22.0, 22.8] as [number, number],
  close: [22.6, 24.0] as [number, number], // eyes close peacefully
  melt: [24.4, 26.6] as [number, number],
  lastPop: 26.6,
  lastLand: 27.05,
  ember: [27.05, 29.6] as [number, number],
  fade: [27.6, 30.1] as [number, number],
  base: 0.06,
};

const sm = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const bump = (u: number, v: number, cu: number, cv: number, r: number) => Math.exp(-(((u - cu) ** 2 + (v - cv) ** 2) / (r * r)));

function gaze(t: number) {
  const k = FSTORY.look;
  if (t <= k[0].t) return { gx: 0, gy: 0 };
  for (let j = 1; j < k.length; j++)
    if (t <= k[j].t) {
      const s = sm(k[j - 1].t, k[j].t, t);
      return { gx: lerp(k[j - 1].gx, k[j].gx, s), gy: lerp(k[j - 1].gy, k[j].gy, s) };
    }
  return { gx: 0, gy: 0 };
}

/** Expression state at time t. */
export function expression(t: number) {
  const S = FSTORY;
  const hook = t < S.explode;
  let open = hook ? 1 : sm(S.wake[0], S.wake[1], t);
  open *= 1 - sm(S.close[0], S.close[1], t);
  const [w0, w1] = S.wink, wm = (w0 + w1) / 2;
  const wink = t > w0 && t < w1 ? (t < wm ? sm(w0, w0 + 0.18, t) : 1 - sm(wm + 0.05, w1, t)) : 0;
  const smile = hook ? 0.35 : Math.max(sm(S.smile[0], S.smile[1], t) * 0.7, 0) * (1 - 0.45 * sm(S.calm[0], S.calm[1], t));
  const laugh = sm(S.laugh[0], S.laugh[0] + 0.4, t) * (1 - sm(S.laugh[1] - 0.2, S.laugh[1] + 0.4, t));
  const glowPulse = 1 + 0.5 * laugh * (0.5 + 0.5 * Math.sin((t - S.laugh[0]) * 9));
  return { open, wink, smile: Math.min(1, smile + 0.35 * laugh), mouthOpen: laugh, glowPulse, ...gaze(t) };
}

/** Face height (0..1), glow and hue at u,v (u -1..1 across, v up). */
export function face(u: number, v: number, t: number) {
  const ex = expression(t);
  const cu = 0, cv = 0.1;
  const d = Math.hypot((u - cu) / 0.86, (v - cv) / 1.32);
  const inHead = sm(1.04, 0.96, d);
  let h = FSTORY.base + inHead * (0.16 + 0.3 * Math.sqrt(Math.max(0, 1 - d * d)));
  let g = 0, hue = 0, white = 0;
  // cheeks rise with the smile
  for (const s of [-1, 1]) h += inHead * (0.06 + 0.12 * ex.smile) * bump(u, v, s * 0.42, -0.28 + 0.04 * ex.smile, 0.24);
  // nose: ridge + tip + nostrils
  h += inHead * 0.16 * Math.exp(-((u / 0.065) ** 2)) * sm(0.36, 0.2, v) * sm(-0.32, -0.1, v);
  h += inHead * 0.24 * bump(u, v, 0, -0.27, 0.11);
  for (const s of [-1, 1]) h -= inHead * 0.09 * bump(u, v, s * 0.09, -0.34, 0.045);
  // eyes
  for (const s of [-1, 1]) {
    const ex0 = s * 0.37, ey0 = 0.3;
    const lid = s > 0 ? ex.open * (1 - ex.wink) : ex.open; // s > 0 = screen right eye winks
    const du = u - ex0, dv = v - ey0;
    const W = 0.28;
    const hA = Math.abs(du) < W ? (0.135 + 0.02 * ex.smile) * (1 - (du * du) / (W * W)) : 0;
    const op = hA * lid;
    // happy eyes: the lower lid lifts with the smile
    const inside = hA > 0 ? sm(0.02, -0.02, dv - op) * sm(0.02, -0.02, -dv - op * (1 - 0.4 * ex.smile)) : 0;
    h -= 0.1 * bump(u, v, ex0, ey0, 0.22) * inHead; // socket
    const rim = hA > 0 ? Math.exp(-(((dv - op) / 0.028) ** 2)) * sm(W, W - 0.06, Math.abs(du)) : 0;
    const gx = ex0 + ex.gx * 0.085, gy = ey0 + ex.gy * 0.04;
    const r = Math.hypot(u - gx, v - gy), a = Math.atan2(v - gy, u - gx);
    const iris = sm(0.135, 0.115, r), pup = sm(0.06, 0.045, r);
    const stri = 0.82 + 0.18 * Math.cos(a * 14 + r * 20);
    const glint = sm(0.03, 0.015, Math.hypot(u - gx - 0.04, v - gy - 0.04));
    h = lerp(h, 0.36, inside);
    h = lerp(h, lerp(lerp(0.36, 0.8 * stri, iris), 0.03, pup), inside);
    h = Math.max(h, inside * glint * 0.95);
    h = Math.max(h, 0.62 * rim);
    const ge = inside * iris * (1 - pup) * (0.55 + 0.45 * stri) * ex.glowPulse;
    if (ge > g) { g = ge; hue = 1 - sm(0.065, 0.125, r); }
    g = Math.max(g, inside * glint);
    white = Math.max(white, inside * (1 - iris));
    // brow: lifts with the smile, a little with the wink
    const by = 0.55 + 0.05 * ex.smile + 0.1 * (1 - (du * du) / 0.08);
    h += 0.24 * inHead * Math.exp(-(((v - by) / 0.04) ** 2)) * sm(0.3, 0.2, Math.abs(du));
  }
  // mouth: lips follow a smile curve; opens on the laugh
  const mw = 0.3 + 0.05 * ex.smile, mu = u / mw;
  if (Math.abs(mu) < 1) {
    const curve = -0.68 + 0.11 * ex.smile * mu * mu - 0.02 * ex.smile;
    const gap = 0.012 + 0.07 * ex.mouthOpen * (1 - mu * mu);
    const thick = 0.045 * (1 - 0.5 * mu * mu);
    const upper = Math.exp(-(((v - (curve + gap + thick * 0.6)) / thick) ** 2));
    const lower = Math.exp(-(((v - (curve - gap - thick * 0.8)) / (thick * 1.2)) ** 2));
    const lips = Math.max(upper, lower) * sm(1, 0.85, Math.abs(mu));
    h += inHead * 0.3 * lips;
    const inGap = sm(gap, gap * 0.5, Math.abs(v - curve)) * sm(1, 0.8, Math.abs(mu));
    h = lerp(h, 0.04, inGap * ex.mouthOpen);
    const lg = lips * (0.15 + 0.5 * ex.smile) * (0.6 + 0.4 * ex.glowPulse);
    if (lg > g) { g = lg; hue = 1; }
  }
  return { h, g: Math.min(1, g), hue, white };
}

function target(u: number, v: number, t: number, base: number) {
  const S = FSTORY;
  let h = base, g = 0, hue = 0;
  const r = Math.hypot(u - S.centre.u, v - S.centre.v);
  if (t < S.explode) return face(u, v, t);
  const dE = t - S.explode;
  if (dE < 2.4) {
    const front = 2.7 * dE;
    const passed = sm(-0.06, 0.06, front - r);
    const e0 = face(u, v, S.explode);
    const shock = Math.exp(-(((r - front) / 0.17) ** 2)) * Math.exp(-dE * 0.7);
    const rnd = Math.abs((Math.sin(u * 127.1 + v * 311.7) * 43758.5453) % 1);
    const launch = (0.35 + 0.65 * rnd) * Math.exp(-(((dE - r / 2.7 - 0.07) / 0.11) ** 2)) * Math.exp(-dE * 0.5);
    h = lerp(e0.h, base, passed) + 1.05 * shock + 0.75 * launch;
    g = lerp(e0.g, 0, passed) + 0.95 * shock;
    hue = lerp(e0.hue, 0, passed);
  }
  if (t < S.snap + 1.0) {
    const wfade = 1 - sm(S.spiral[0] - 0.5, S.spiral[0] + 0.8, t);
    if (wfade > 0)
      for (const s of S.sources) {
        const dt = t - s.t;
        if (dt < 0 || dt > 3.2) continue;
        const d = Math.hypot(u - s.u, v - s.v);
        const front = d - 0.95 * dt;
        h += wfade * s.a * 0.75 * Math.exp(-((front / 0.11) ** 2)) * Math.exp(-dt * 0.55) * (1 - 0.35 * Math.min(1, d));
        if (dt < 0.3 && d < 0.06) h += (1 - dt / 0.3) * 0.9 * s.a;
      }
    const sp = sm(S.spiral[0], S.spiral[1] - 0.3, t);
    if (sp > 0) {
      const th = Math.atan2(v - S.centre.v, u);
      const T = t - S.spiral[0];
      const ph = 3 * th + 10 * r - (2.2 * T + 0.55 * T * T);
      const arm = 0.5 + 0.5 * Math.cos(ph);
      h = lerp(h, base + (0.15 + 0.75 * arm * arm) * (1 - 0.45 * Math.min(1, r)), sp);
      g = sp * 0.55 * arm * arm * sm(9.0, 10.9, t);
      hue = 0;
    }
  }
  const tSnap = S.snap + 0.36 * r;
  if (t >= tSnap) {
    const e = face(u, v, t);
    h = e.h; g = e.g; hue = e.hue;
    const m = sm(S.melt[0] + (2.1 - r) * 0.85, S.melt[0] + (2.1 - r) * 0.85 + 0.9, t);
    h = lerp(h, base, m);
    g = lerp(g, 0, m);
  }
  if (t > S.lastPop - 0.05 && Math.hypot(u, v - 0.1) < 0.03) {
    if (t < S.lastLand) h = Math.max(h, 0.45 * sm(S.lastPop, S.lastPop + 0.25, t));
    g = Math.max(g, 0.85 * sm(S.lastPop, S.lastPop + 0.3, t) * (1 - sm(S.ember[0] + 0.6, S.ember[1], t)));
    hue = 1;
  }
  return { h, g, hue };
}

let cache: { key: string; sim: RodSim } | null = null;

export function simulateFace(fps: number, n = 45, rows = 80, spacing = 0.096): RodSim {
  const key = `${fps}|${n}|${rows}|${spacing}`;
  if (cache?.key === key) return cache.sim;
  const layout = rodLayout(n, rows, spacing);
  const count = n * rows;
  const frames = Math.round(FSTORY.duration * fps);
  const height = new Float32Array(frames * count), glow = new Float32Array(frames * count), hue = new Float32Array(frames * count);
  const speed = new Float32Array(frames);
  const clacks: RodSim["clacks"] = [];
  const sub = 6, dt = 1 / (fps * sub);
  const k = (2 * Math.PI * 3.4) ** 2, c = 2 * 0.32 * Math.sqrt(k);
  const y = new Float32Array(count), vel = new Float32Array(count), peak = new Float32Array(count);
  const gs = new Float32Array(count), hs = new Float32Array(count);
  for (let i = 0; i < count; i++) {
    const e0 = face(layout.u[i], layout.v[i], 0);
    y[i] = e0.h; gs[i] = e0.g; hs[i] = e0.hue;
  }
  for (let f = 0; f < frames; f++) {
    let sp = 0;
    for (let s = 0; s < sub; s++) {
      const t = (f * sub + s) * dt;
      for (let i = 0; i < count; i++) {
        const T = target(layout.u[i], layout.v[i], t, FSTORY.base);
        const a = k * (T.h - y[i]) - c * vel[i];
        const v0 = vel[i];
        vel[i] += a * dt;
        y[i] += vel[i] * dt;
        if (y[i] < 0) { y[i] = 0; if (vel[i] < 0) vel[i] = -vel[i] * 0.25; }
        peak[i] = Math.max(peak[i], Math.abs(vel[i]));
        if (Math.sign(v0) !== Math.sign(vel[i]) && peak[i] > 1.2) {
          clacks.push({ t, i, e: Math.min(1, (peak[i] - 1.2) / 6) });
          peak[i] = 0;
        }
        if (s === sub - 1) {
          gs[i] += (T.g - gs[i]) * 0.35;
          hs[i] = T.hue;
          sp += Math.abs(vel[i]);
        }
      }
    }
    for (let i = 0; i < count; i++) {
      const o = f * count + i;
      height[o] = y[i];
      glow[o] = Math.min(1, gs[i] + Math.min(0.14, Math.abs(vel[i]) * 0.025));
      hue[o] = hs[i];
    }
    speed[f] = sp / count;
  }
  const sim = { fps, frames, count, layout, height, glow, hue, clacks, speed };
  cache = { key, sim };
  return sim;
}

/** Sparks on the shatter and the snap, glowing dust rising from the eyes and lips as the face closes and sinks. */
export function faceParticles(sim: RodSim, seed: number): ParticleData {
  const L = sim.layout, r = rng(seed, "face-parts");
  const P: number[] = [], V: number[] = [], T: number[] = [], C: number[] = [], Sz: number[] = [];
  const add = (p: number[], v: number[], t: number[], c: number[], s: number) => { P.push(...p); V.push(...v); T.push(...t); C.push(...c); Sz.push(s); };
  const S = FSTORY, H = 1.05;
  for (let i = 0; i < sim.count; i++) {
    const u = L.u[i], v = L.v[i], x = L.x[i], z = L.z[i];
    const rr = Math.hypot(u - S.centre.u, v - S.centre.v);
    const f0 = face(u, v, 0), fl = face(u, v, 20.6);
    // shatter sparks (more from the glowing eyes)
    const nS = (f0.g > 0.3 ? 4 : 0) + (r() < 0.22 ? 1 : 0);
    for (let k = 0; k < nS; k++) {
      const a = r() * Math.PI * 2, out = 0.3 + r() * 0.6;
      const te = S.explode + rr / 2.7 + r() * 0.04;
      const teal = f0.g > 0.3 ? f0.hue : 0;
      add([x, f0.h * H + 0.05, z], [Math.cos(a) * out + (u / (rr + 0.05)) * 0.35, 1.1 + r() * 1.4, Math.sin(a) * out - (v / (rr + 0.05)) * 0.35],
        [te, 0.55 + r() * 0.5, -4.2, 0], [lerp(0.6, 2.4, teal) + 0.6, lerp(2.0, 1.5, teal), lerp(2.6, 0.6, teal)], 0.02 + r() * 0.02);
    }
    // snap sparks where features land
    if (fl.g > 0.25 || (fl.h > 0.5 && r() < 0.3)) {
      const ts = S.snap + 0.36 * rr;
      for (let k = 0; k < 2; k++)
        add([x, fl.h * H + 0.04, z], [(r() - 0.5) * 0.5, 0.7 + r() * 0.8, (r() - 0.5) * 0.5], [ts + 0.08, 0.5 + r() * 0.3, -3.5, 0],
          [2.2, 2.0, 1.6], 0.016 + r() * 0.014);
    }
    // closing / sinking dust from what glowed during the laugh
    if (fl.g > 0.2) {
      const tm = S.close[0] + r() * (S.melt[1] - S.close[0]);
      for (let k = 0; k < 3; k++)
        add([x + (r() - 0.5) * 0.04, fl.h * H * 0.6 + 0.04, z + (r() - 0.5) * 0.04], [(r() - 0.5) * 0.12, 0.25 + r() * 0.4, (r() - 0.5) * 0.12],
          [tm + r() * 0.6, 2.6 + r() * 1.3, 0.1, 1], [lerp(0.7, 2.3, fl.hue), lerp(1.9, 1.5, fl.hue), lerp(2.3, 0.6, fl.hue)], 0.016 + r() * 0.016);
    }
  }
  const f = (a: number[]) => Float32Array.from(a);
  return { count: Sz.length, p: f(P), v: f(V), t: f(T), c: f(C), s: f(Sz) };
}
