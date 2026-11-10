// "The Butterfly Domino": ~3400 obsidian dominoes whose faces form a butterfly once they fall.
// Story (s): HOOK finished glowing butterfly -> 0.6 every domino springs back up (rewind wave) -> a single line
// clicks up the centre -> at the centre the chain bursts into a swirling spiral that topples outward, revealing
// and lighting the butterfly -> the wings beat (wing dominoes lift and drop in waves) -> last slow beat, glow fades
// from the wingtips inward, body last -> fade to black. Pure TS, deterministic, shared by picture and sound.

/** Story time (tau). The VIDEO plays it through HOOK below: action first, a visible rewind, then the story. */
export const DSTORY = {
  duration: 31.8,
  rewind: [0.6, 1.55] as [number, number], // (never shown: the video rewinds itself, see HOOK)
  lane: { start: 2.2, step: 0.075 },
  bloom: { start: 0, speed: 0.62, swirl: 0.6 }, // start = set from the lane (when the chain reaches the centre)
  beats: [14.8, 16.0, 17.2, 19.0, 21.0, 23.0] as number[], // wing beats
  beatLen: [0.95, 0.95, 1.4, 1.6, 1.5, 2.1] as number[],
  beatAmp: [0.9, 0.9, 1.0, 1.1, 1.05, 1.2] as number[],
  fadeGlow: [25.2, 28.6] as [number, number], // = the dust dissolve (wingtips first, body last)
  fade: [29.2, 31.6] as [number, number],
  thetaMax: (88 * Math.PI) / 180,
};

/**
 * Real video time -> story time. 0-1.4 s: the swirl at its most dynamic (tau 6.6-8.0). 1.4-2.3 s: time runs
 * backwards fast to tau 2.0 (everything un-falls). Then the story plays from the fuse.
 */
export const HOOK = { from: 6.6, to: 8.0, rewindLen: 0.9, resume: 2.0 };
export const REAL_DURATION = DSTORY.duration + (HOOK.to - HOOK.from) + HOOK.rewindLen - HOOK.resume;
export function tauAt(t: number): number {
  const a = HOOK.to - HOOK.from;
  if (t < a) return HOOK.from + t;
  if (t < a + HOOK.rewindLen) {
    const x = (t - a) / HOOK.rewindLen;
    const e = x * x * (3 - 2 * x);
    return HOOK.to + (HOOK.resume - HOOK.to) * e;
  }
  return t - a - HOOK.rewindLen + HOOK.resume;
}

export interface DominoLayout {
  cols: number;
  rows: number;
  spacing: number;
  count: number;
  x: Float32Array;
  z: Float32Array;
  u: Float32Array; // picture coords: -1..1 across, up = far side
  v: Float32Array;
  dir: Float32Array; // fall direction (x, z) pairs
  trigger: Float32Array; // seconds when it starts to fall (after the rewind)
  rise: Float32Array; // seconds when it springs back up in the rewind
  lane: Uint8Array;
  colR: Float32Array; // face colour (picture)
  colG: Float32Array;
  colB: Float32Array;
  glow: Float32Array; // 0..1 how much the face glows once revealed
  wing: Float32Array; // 0..1 how much it lifts on a wing beat
  body: Float32Array; // 0..1 butterfly body (glows last)
}

export interface DominoSim {
  fps: number;
  frames: number;
  layout: DominoLayout;
  theta: Float32Array; // frames * count
  light: Float32Array; // frames * count, glow 0..1
  /** Landings (sound): time, domino, energy 0..1, kind 0 fall / 1 rise / 2 wing */
  hits: { t: number; i: number; e: number; k: number }[];
  fallTime: number;
}

const sm = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};
const mix = (a: number, b: number, t: number) => a + (b - a) * t;

function ellipse(u: number, v: number, cx: number, cy: number, rx: number, ry: number, rot: number) {
  const c = Math.cos(rot), s = Math.sin(rot);
  const x = (u - cx) * c + (v - cy) * s, y = -(u - cx) * s + (v - cy) * c;
  return Math.hypot(x / rx, y / ry); // < 1 inside
}

/** Butterfly picture at u,v: colour (sRGB 0..1), glow, wing weight, body weight. */
export function butterfly(u: number, v0: number) {
  const v = v0 / 1.25; // taller butterfly for the 9:16 frame
  const au = Math.abs(u);
  const up = ellipse(au, v, 0.47, 0.34, 0.52, 0.37, 0.42);
  const lo = ellipse(au, v, 0.33, -0.36, 0.34, 0.4, -0.38);
  const wingD = Math.min(up, lo);
  const body = ellipse(u, v, 0, 0.02, 0.055, 0.6, 0);
  const head = Math.hypot(u, v - 0.66) / 0.09;
  const ant = Math.min(
    Math.abs(au - (0.04 + (v - 0.7) * 0.55)) / 0.022 + (v < 0.72 || v > 1.12 ? 99 : 0),
    Math.hypot(au - (0.04 + 0.42 * 0.55), v - 1.12) / 0.045,
  );
  // wing pattern
  const hx = 0.05, hy = 0.08;
  const r = Math.hypot(au - hx, v - hy), a = Math.atan2(v - hy, au - hx);
  const vein = Math.abs(Math.sin(a * 7.0)) < 0.09 && r > 0.18 ? 1 : 0;
  const edge = wingD > 0.82 ? 1 : 0;
  const dot = edge && Math.abs(Math.sin(a * 16)) > 0.8 ? 1 : 0;
  const eye = Math.hypot(au - 0.66, v - 0.46);
  const eyeRing = eye > 0.07 && eye < 0.12 ? 1 : 0, eyeIn = eye <= 0.07 ? 1 : 0;
  const t = Math.min(1, r / 0.95);
  // deep violet -> magenta -> gold toward the tips
  let R = mix(mix(0.26, 0.92, sm(0.0, 0.55, t)), 1.0, sm(0.55, 1.0, t));
  let G = mix(mix(0.08, 0.16, sm(0.0, 0.55, t)), 0.72, sm(0.6, 1.0, t));
  let B = mix(mix(0.62, 0.62, sm(0.0, 0.55, t)), 0.22, sm(0.55, 1.0, t));
  let glow = 0.75 + 0.25 * t;
  if (vein || edge) { R = 0.05; G = 0.04; B = 0.09; glow = 0.08; }
  if (dot) { R = 1; G = 0.86; B = 0.6; glow = 0.45; }
  if (eyeRing) { R = 1; G = 0.72; B = 0.22; glow = 0.6; }
  if (eyeIn) { R = 0.1; G = 0.12; B = 0.4; glow = 0.5; }
  const inWing = wingD < 1 ? 1 : 0;
  const inBody = body < 1 || head < 1 || ant < 1 ? 1 : 0;
  if (inBody) return { r: 0.07, g: 0.06, b: 0.1, glow: 0.35, wing: 0, body: 1 };
  if (!inWing) {
    // dark field with a few faint stars
    const h = Math.abs(Math.sin(u * 412.7 + v0 * 191.3) * 43758.5) % 1;
    if (h > 0.965) return { r: 0.75, g: 0.8, b: 1.0, glow: 0.35 + 0.4 * (h - 0.965) / 0.035, wing: 0, body: 0 };
    return { r: 0.02, g: 0.03, b: 0.11, glow: 0, wing: 0, body: 0 };
  }
  return { r: R, g: G, b: B, glow, wing: Math.min(1, au / 0.95), body: 0 };
}

/** Precomputed fall curve (inverted pendulum about the front edge) + small landing bounce. */
function fallCurve() {
  const k = 3 * 9.81 / (2 * 0.095);
  let th = 0.07, w = 2.2, t = 0;
  const pts: number[] = [];
  const dt = 1 / 2000;
  while (th < DSTORY.thetaMax) {
    pts.push(th);
    w += k * Math.sin(th) * dt;
    th += w * dt;
    t += dt;
  }
  const T = t;
  return {
    T,
    at(tau: number) {
      if (tau <= 0) return 0;
      if (tau < T) return pts[Math.min(pts.length - 1, Math.floor(tau * 2000))];
      const b = tau - T;
      return DSTORY.thetaMax - 0.07 * Math.exp(-b * 14) * Math.abs(Math.sin(b * 34));
    },
  };
}

export function dominoLayout(cols = 44, rows = 78, spacing = 0.1): DominoLayout {
  const count = cols * rows;
  const f = (n: number) => new Float32Array(n);
  const L: DominoLayout = {
    cols, rows, spacing, count, x: f(count), z: f(count), u: f(count), v: f(count), dir: f(count * 2),
    trigger: f(count), rise: f(count), lane: new Uint8Array(count), colR: f(count), colG: f(count), colB: f(count),
    glow: f(count), wing: f(count), body: f(count),
  };
  const hx = ((cols - 1) * spacing) / 2, hz = ((rows - 1) * spacing) / 2;
  const laneCol = Math.floor(cols / 2), centreRow = Math.round(rows * 0.47);
  const cz = centreRow * spacing - hz, cx = laneCol * spacing - hx;
  let laneEnd = 0;
  for (let r = 0; r < rows; r++)
    for (let c = 0; c < cols; c++) {
      const i = r * cols + c;
      const x = c * spacing - hx, z = r * spacing - hz;
      L.x[i] = x; L.z[i] = z;
      L.u[i] = x / hx;
      L.v[i] = -(z - cz) / hx;
      if (c === laneCol && r >= centreRow) {
        L.lane[i] = 1;
        L.dir[i * 2] = 0; L.dir[i * 2 + 1] = -1; // toward the far side (up the screen)
        L.trigger[i] = DSTORY.lane.start + (rows - 1 - r) * DSTORY.lane.step;
        laneEnd = Math.max(laneEnd, L.trigger[i]);
      }
      const p = butterfly(L.u[i], L.v[i]);
      L.colR[i] = p.r; L.colG[i] = p.g; L.colB[i] = p.b; L.glow[i] = p.glow; L.wing[i] = p.wing; L.body[i] = p.body;
      if (L.lane[i]) { L.colR[i] = 1; L.colG[i] = 0.78; L.colB[i] = 0.38; L.glow[i] = 0.85; L.body[i] = 1; } // a burning fuse
    }
  const bloom = laneEnd + 0.12;
  DSTORY.bloom.start = bloom;
  let rmax = 0;
  for (let i = 0; i < count; i++) rmax = Math.max(rmax, Math.hypot(L.x[i] - cx, L.z[i] - cz));
  for (let i = 0; i < count; i++) {
    const dx = L.x[i] - cx, dz = L.z[i] - cz, r = Math.hypot(dx, dz) + 1e-6;
    if (!L.lane[i]) {
      const ang = Math.atan2(dz, dx) + 0.55; // swirl: falls outward with a twist
      L.dir[i * 2] = Math.cos(ang); L.dir[i * 2 + 1] = Math.sin(ang);
      const ph = Math.atan2(dz, dx) / (2 * Math.PI);
      const arms = DSTORY.bloom.swirl * (((ph * 3 - r * 0.8) % 1) + 1) % 1;
      L.trigger[i] = bloom + r / DSTORY.bloom.speed + arms;
    }
    // rewind order: reverse of the fall (outer first, the lane last, top of the lane first)
    L.rise[i] = L.lane[i]
      ? DSTORY.rewind[1] - 0.05 - (L.trigger[i] - DSTORY.lane.start) * 0.08
      : DSTORY.rewind[0] + (1 - r / rmax) * 0.62;
  }
  return L;
}

let cache: { key: string; sim: DominoSim } | null = null;

export function simulateDominoes(fps: number, cols = 44, rows = 78, spacing = 0.1): DominoSim {
  const key = `${fps}|${cols}|${rows}|${spacing}`;
  if (cache?.key === key) return cache.sim;
  const L = dominoLayout(cols, rows, spacing);
  const fc = fallCurve();
  const frames = Math.round(DSTORY.duration * fps);
  const theta = new Float32Array(frames * L.count), light = new Float32Array(frames * L.count);
  const hits: DominoSim["hits"] = [];
  const S = DSTORY;
  const riseLen = 0.2;

  for (let i = 0; i < L.count; i++) {
    const land = L.trigger[i] + fc.T;
    hits.push({ t: land, i, e: L.lane[i] ? 1 : 0.55 + 0.45 * L.glow[i], k: 0 });
    hits.push({ t: L.rise[i] + riseLen, i, e: 0.4, k: 1 });
    const glowEnd = mix(S.fadeGlow[1], S.fadeGlow[0], Math.min(1, Math.hypot(L.u[i], L.v[i] * 0.8)));
    for (let f = 0; f < frames; f++) {
      const t = f / fps;
      let th: number;
      if (t < L.rise[i]) th = S.thetaMax; // hook: finished picture
      else if (t < L.rise[i] + riseLen) th = S.thetaMax * (1 - sm(0, 1, (t - L.rise[i]) / riseLen)) ** 1.6;
      else th = fc.at(t - L.trigger[i]);
      // wing beats: lift from the body outward
      let lift = 0;
      if (L.wing[i] > 0)
        S.beats.forEach((b, j) => {
          const len = S.beatLen[j], d = t - b - L.wing[i] * 0.22;
          if (d > 0 && d < len) lift = Math.max(lift, Math.sin((Math.PI * d) / len) ** 2 * (0.25 + 0.75 * L.wing[i]) * S.beatAmp[j]);
        });
      th -= lift * 0.95;
      theta[f * L.count + i] = th;
      // glow: on in the hook, off after the rewind, back on as each face lands, pulses with the beats, fades at the end
      const on = t < L.rise[i] + 0.1 ? 1 : sm(land, land + 0.3, t);
      const end = L.body[i] ? 1 - sm(S.fadeGlow[1] - 0.2, S.fade[1] - 0.6, t) : 1 - sm(glowEnd - 1.2, glowEnd, t);
      // the fuse burns out below the butterfly once the burst starts
      const burnt = L.lane[i] && L.v[i] < -0.8 ? 1 - 0.85 * sm(S.bloom.start + 0.3, S.bloom.start + 2.5, t) : 1;
      light[f * L.count + i] = L.glow[i] * on * end * burnt * (1 + 0.6 * lift);
    }
  }
  S.beats.forEach((b, j) => {
    for (let i = 0; i < L.count; i += 3) if (L.wing[i] > 0.15) hits.push({ t: b + S.beatLen[j] + L.wing[i] * 0.22, i, e: 0.25 * L.wing[i], k: 2 });
  });
  hits.sort((a, b) => a.t - b.t);
  const sim = { fps, frames, layout: L, theta, light, hits, fallTime: fc.T };
  cache = { key, sim };
  return sim;
}
