// "The Eye": a wall of chrome rods driven by a scripted target field + real spring physics.
// Story (seconds): pop -> colliding ripples -> rising spiral -> SNAP into an eye -> the eye lives (looks, blinks,
// pupil widens) -> eye closes -> wall melts flat -> last rod drops = THE END. Start state == end state (loops too).
// Pure TS and deterministic: the renderer and the sound generator read the same simulation.

export const STORY = {
  duration: 23,
  pop: 0.0,
  sources: [
    { t: 0.15, u: 0, v: 0, a: 1.0 },
    { t: 1.35, u: 0, v: 0, a: 0.8 },
    { t: 3.2, u: -0.6, v: 1.25, a: 0.95 },
    { t: 3.9, u: 0.6, v: -1.25, a: 0.95 },
    { t: 4.6, u: 0.6, v: 1.25, a: 0.95 },
    { t: 5.3, u: -0.6, v: -1.25, a: 0.95 },
    { t: 6.1, u: 0, v: 0, a: 1.1 },
  ],
  spiral: [7.0, 11.0] as [number, number],
  snap: 11.0,
  look: [
    { t: 11.6, gx: 0, gy: 0 },
    { t: 12.6, gx: -0.24, gy: 0.02 },
    { t: 13.6, gx: -0.24, gy: 0.02 },
    { t: 14.1, gx: 0.24, gy: -0.02 },
    { t: 15.0, gx: 0.24, gy: -0.02 },
    { t: 15.5, gx: 0, gy: 0.04 },
  ],
  blink: [15.85, 16.35] as [number, number],
  dilate: [16.6, 17.4] as [number, number],
  close: [17.9, 19.3] as [number, number],
  melt: [19.6, 21.2] as [number, number],
  lastPop: 21.25,
  lastLand: 21.7,
  base: 0.06,
};

export interface RodLayout {
  n: number; // columns
  rows: number;
  spacing: number;
  u: Float32Array; // -1..1 screen right
  v: Float32Array; // -1..1 screen up (far side of the wall)
  x: Float32Array;
  z: Float32Array;
}

export interface RodSim {
  fps: number;
  frames: number;
  count: number;
  layout: RodLayout;
  height: Float32Array; // frames * count, 0..~1.15
  glow: Float32Array; // frames * count, 0..1 emissive amount
  hue: Float32Array; // frames * count, 0 = teal, 1 = amber
  /** Clacks: a rod finishing a fast move (sound source). time s, rod index, energy 0..1 */
  clacks: { t: number; i: number; e: number }[];
  speed: Float32Array; // frames: mean |velocity| of the wall
}

const sm = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

/** Tall wall (rows > cols) so it fills a 9:16 frame. u: -1..1 across, v: same scale, 0 at the centre row. */
export function rodLayout(n = 31, rows = 55, spacing = 0.14): RodLayout {
  const c = n * rows;
  const L: RodLayout = { n, rows, spacing, u: new Float32Array(c), v: new Float32Array(c), x: new Float32Array(c), z: new Float32Array(c) };
  const hx = ((n - 1) * spacing) / 2, hz = ((rows - 1) * spacing) / 2;
  for (let r = 0; r < rows; r++)
    for (let k = 0; k < n; k++) {
      const i = r * n + k;
      L.u[i] = (k / (n - 1)) * 2 - 1;
      L.v[i] = ((rows - 1) / 2 - r) * (2 / (n - 1));
      L.x[i] = k * spacing - hx;
      L.z[i] = r * spacing - hz; // row 0 (top of the picture) is the far side -> top of the screen
    }
  return L;
}

/** Gaze at time t (smooth between keys). */
function gaze(t: number) {
  const k = STORY.look;
  if (t <= k[0].t) return { gx: k[0].gx, gy: k[0].gy };
  for (let j = 1; j < k.length; j++)
    if (t <= k[j].t) {
      const s = sm(k[j - 1].t, k[j].t, t);
      return { gx: lerp(k[j - 1].gx, k[j].gx, s), gy: lerp(k[j - 1].gy, k[j].gy, s) };
    }
  return { gx: k[k.length - 1].gx, gy: k[k.length - 1].gy };
}

/** Lid openness 0..1. */
function lid(t: number) {
  const [b0, b1] = STORY.blink;
  const bm = (b0 + b1) / 2;
  let o = 1;
  if (t > b0 && t < b1) o = t < bm ? 1 - sm(b0, bm, t) : sm(bm, b1, t);
  if (t > STORY.close[0]) o = Math.min(o, 1 - sm(STORY.close[0], STORY.close[1], t));
  return o;
}

/** Eye height (0..1), glow and hue at screen point u,v. */
export function eye(u: number, v: number, t: number) {
  const { gx, gy } = gaze(t);
  const L = lid(t);
  const pupil = lerp(0.15, 0.24, sm(STORY.dilate[0], STORY.dilate[1], t));
  const W = 0.92;
  const hA = Math.abs(u) < W ? 0.56 * (1 - (u * u) / (W * W)) : 0;
  const open = hA * L;
  const inside = sm(0.035, -0.035, Math.abs(v) - open) * (hA > 0 ? 1 : 0);
  // lid rim: raised edge along the opening (stays as a closed-eye line)
  const rim = hA > 0 ? Math.exp(-(((Math.abs(v) - open) / 0.045) ** 2)) * sm(W, W - 0.15, Math.abs(u)) : 0;
  // upper crease
  const crease = hA > 0 ? Math.exp(-(((v - (hA * 1.0 + 0.16)) / 0.05) ** 2)) * 0.5 : 0;
  const r = Math.hypot(u - gx, v - gy), a = Math.atan2(v - gy, u - gx);
  const iris = sm(0.34, 0.3, r), pup = sm(pupil + 0.025, pupil - 0.01, r);
  const glint = sm(0.065, 0.035, Math.hypot(u - gx - 0.11, v - gy - 0.11));
  const stri = 0.82 + 0.18 * Math.cos(a * 22 + r * 6);
  // eyebrow: soft raised arc above the eye, lifts a little when the pupil widens
  const lift = 0.06 * sm(STORY.dilate[0], STORY.dilate[1], t) * (1 - sm(STORY.close[0], STORY.close[1], t));
  const browY = 0.74 + lift + 0.32 * (1 - (u * u) / 0.9);
  const brow = Math.abs(u) < 1.0 ? Math.exp(-(((v - browY) / 0.07) ** 2)) * sm(1.0, 0.75, Math.abs(u)) * sm(-0.95, -0.6, u) : 0;
  let h = 0.16 + 0.12 * crease + 0.5 * brow; // skin
  let g = 0, hue = 0;
  // sclera inside the opening
  h = lerp(h, 0.42, inside);
  // iris + pupil (only inside)
  const ih = lerp(0.42, 0.9 * stri, iris);
  h = lerp(h, lerp(ih, 0.02, pup), inside);
  g = inside * iris * (1 - pup) * (0.55 + 0.45 * stri);
  hue = 1 - sm(pupil + 0.02, 0.29, r); // amber near the pupil, teal outside
  h = Math.max(h, inside * glint * 1.0);
  g = Math.max(g, inside * glint);
  h = Math.max(h, 0.72 * rim * (0.4 + 0.6 * (1 - L) + 0.6 * L));
  return { h, g: Math.min(1, g), hue };
}

/** Target height for one rod at time t (before spring physics). */
function target(u: number, v: number, t: number, base: number): { h: number; g: number; hue: number } {
  const S = STORY;
  let h = base, g = 0, hue = 0;
  const r = Math.hypot(u, v);

  if (t < S.snap + 0.8) {
    // ripples (fade out as the spiral takes over)
    const wfade = 1 - sm(S.spiral[0] - 0.5, S.spiral[0] + 0.8, t);
    if (wfade > 0)
      for (const s of S.sources) {
        const dt = t - s.t;
        if (dt < 0 || dt > 3.2) continue;
        const d = Math.hypot(u - s.u, v - s.v);
        const front = d - 0.95 * dt;
        h += wfade * s.a * 0.75 * Math.exp(-((front / 0.11) ** 2)) * Math.exp(-dt * 0.55) * (1 - 0.35 * Math.min(1, d));
        if (dt < 0.3 && d < 0.07) h += (1 - dt / 0.3) * 0.9 * s.a; // the source rod itself pops
      }
    // spiral build
    const sp = sm(S.spiral[0], S.spiral[1] - 0.3, t);
    if (sp > 0) {
      const th = Math.atan2(v, u);
      const T = t - S.spiral[0];
      const ph = 3 * th + 10 * r - (2.2 * T + 0.55 * T * T);
      const arm = 0.5 + 0.5 * Math.cos(ph);
      h = lerp(h, base + (0.15 + 0.75 * arm * arm) * (1 - 0.45 * Math.min(1, r)), sp);
      g = sp * 0.55 * arm * arm * sm(9.0, 10.9, t);
      hue = 0;
    }
  }

  // snap into the eye: cascade from the centre outward
  const tSnap = S.snap + 0.36 * r;
  if (t >= tSnap) {
    const e = eye(u, v, t);
    h = e.h;
    g = e.g;
    hue = e.hue;
    // melt: outside in, centre last
    const m = sm(S.melt[0] + (2.1 - r) * 0.62, S.melt[0] + (2.1 - r) * 0.62 + 0.5, t);
    h = lerp(h, base, m);
    g = lerp(g, 0, m);
  }

  // the last rod: small pop then down
  if (t > S.lastPop - 0.05 && r < 0.05) {
    if (t < S.lastLand) h = Math.max(h, 0.7 * sm(S.lastPop, S.lastPop + 0.12, t));
  }
  return { h, g, hue };
}

let cache: { key: string; sim: RodSim } | null = null;

export function simulate(fps: number, n = 31, rows = 55, spacing = 0.14): RodSim {
  const key = `${fps}|${n}|${rows}|${spacing}`;
  if (cache?.key === key) return cache.sim;
  const layout = rodLayout(n, rows, spacing);
  const count = n * rows;
  const frames = Math.round(STORY.duration * fps);
  const height = new Float32Array(frames * count), glow = new Float32Array(frames * count), hue = new Float32Array(frames * count);
  const speed = new Float32Array(frames);
  const clacks: RodSim["clacks"] = [];
  const sub = 8, dt = 1 / (fps * sub);
  const k = (2 * Math.PI * 3.4) ** 2, c = 2 * 0.32 * Math.sqrt(k);
  const y = new Float32Array(count).fill(STORY.base), vel = new Float32Array(count);
  const peak = new Float32Array(count); // fastest speed since the last direction change
  const gs = new Float32Array(count), hs = new Float32Array(count);

  // frame 0 starts mid-pop (the centre rod is already rising: motion on frame 1)
  for (let i = 0; i < count; i++)
    if (Math.hypot(layout.u[i], layout.v[i]) < 0.05) { y[i] = 0.3; vel[i] = 5.5; }

  for (let f = 0; f < frames; f++) {
    let sp = 0;
    for (let s = 0; s < sub; s++) {
      const t = (f * sub + s) * dt;
      for (let i = 0; i < count; i++) {
        const T = target(layout.u[i], layout.v[i], t, STORY.base);
        const a = k * (T.h - y[i]) - c * vel[i];
        const v0 = vel[i];
        vel[i] += a * dt;
        y[i] += vel[i] * dt;
        if (y[i] < 0) { y[i] = 0; if (vel[i] < 0) vel[i] = -vel[i] * 0.25; }
        peak[i] = Math.max(peak[i], Math.abs(vel[i]));
        // a fast move ends (velocity flips sign): the rod "clacks"
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
