// "The Face" v2: a face of ~2000 floating frosted-glass cubes in a bright dawn sky (different world from 0004).
// Same story beats as faceSim (FSTORY times + face() expressions), but a different medium and motion:
//  hook: the glass face stares at you -> 0.6 s it bursts into a glass STORM that swirls around the camera ->
//  ribbons of cubes flow in 3D -> they tighten into a spinning TORNADO -> 12.6 they fly back and assemble the face
//  (centre first, overshoot) -> wakes, looks, smiles, winks, laughs -> closes its eyes -> the cubes lift off and drift
//  up into the light, the picture fades to white.
// Everything is closed-form in time (no stored simulation), deterministic, shared with the sound generator.
import { rng } from "../../core/seed";
import { face, FSTORY } from "../rods/faceSim";

export const GSTORY = {
  ...FSTORY,
  explode: 0.6,
  storm: [0.6, 8.6] as [number, number],
  tornado: [8.6, 12.4] as [number, number],
  snap: 12.6,
  drift: [24.2, 29.0] as [number, number],
  fade: [27.6, 30.2] as [number, number], // to white
  duration: 30.5,
};

export const W = 2.1; // world units per face unit
export const DEPTH = 1.6; // relief depth
export let CUBE = 0.082; // set from the grid by glassCubes()

export interface GlassCube {
  u: number;
  v: number;
  face: boolean; // part of the face (else ambient sky cube)
  r: number; // distance from the face centre (assembly order)
  // storm orbit
  R: number;
  th0: number;
  w: number;
  y0: number;
  ay: number;
  ph: number;
  // tumble
  ax: [number, number, number];
  spin: number;
  blast: [number, number, number];
  size: number;
  driftV: [number, number, number];
  driftT: number;
}

const sm = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};
const easeOutBack = (x: number) => {
  const c1 = 1.9, c3 = c1 + 1;
  return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2);
};

export function glassCubes(seed: number, cols = 48): GlassCube[] {
  const r = rng(seed, "glass");
  const out: GlassCube[] = [];
  const du = 2 / (cols - 1);
  CUBE = du * W * 0.95;
  for (let row = 0; ; row++) {
    const v = 1.62 - row * du;
    if (v < -1.42) break;
    for (let c = 0; c < cols; c++) {
      const u = -1 + c * du;
      const d = Math.hypot(u / 0.86, (v - 0.1) / 1.32);
      if (d > 1.02) continue;
      out.push(makeCube(u, v, true, r));
    }
  }
  // ambient sky cubes floating around (depth and sparkle)
  for (let k = 0; k < 520; k++) out.push(makeCube((r() - 0.5) * 5, (r() - 0.5) * 9, false, r));
  return out;
}

function makeCube(u: number, v: number, isFace: boolean, r: () => number): GlassCube {
  const a = r() * Math.PI * 2, b = Math.acos(r() * 2 - 1);
  const ax: [number, number, number] = [Math.sin(b) * Math.cos(a), Math.sin(b) * Math.sin(a), Math.cos(b)];
  const bl = 2.2 + r() * 3.2;
  const rr = Math.hypot(u, v - 0.1);
  return {
    u, v, face: isFace, r: rr,
    R: isFace ? 1.3 + r() * 2.6 : 2.5 + r() * 4.5,
    th0: r() * Math.PI * 2,
    w: (0.55 + r() * 0.6) * (r() < 0.15 ? -1 : 1),
    y0: isFace ? (r() - 0.5) * 6.5 : v * 1.4,
    ay: 0.2 + r() * 0.6,
    ph: r() * Math.PI * 2,
    ax,
    spin: 1.5 + r() * 4,
    blast: [(u / (rr + 0.1)) * bl * 0.6 + (r() - 0.5) * 2, ((v - 0.1) / (rr + 0.1)) * bl * 0.6 + (r() - 0.5) * 2, 1.5 + r() * 3.5],
    size: isFace ? 1 : 0.45 + r() * 0.7,
    driftV: [(r() - 0.5) * 0.8, 0.9 + r() * 1.4, (r() - 0.3) * 1.2],
    driftT: GSTORY.drift[0] + (isFace ? (1.4 - Math.min(1.4, rr)) * 0.4 + (1 - Math.min(1, Math.abs(u))) * 0.3 + r() * 1.6 : r() * 2),
  };
}

/** Face pose of a cube at time t (position, glow, hue, region colour). */
export function facePose(c: GlassCube, t: number) {
  const f = face(c.u, c.v, t);
  return { x: c.u * W, y: c.v * W, z: (f.h - 0.06) * DEPTH, g: f.g, hue: f.hue, h: f.h };
}

function stormPos(c: GlassCube, t: number): [number, number, number] {
  const S = GSTORY;
  const tight = sm(S.tornado[0], S.tornado[1], t);
  const R = c.R * (1 - 0.72 * tight) + 0.25 * tight;
  const th = c.th0 + c.w * t + 2.2 * tight * tight * (t - S.tornado[0]); // tornado speeds up
  const y = c.y0 * (1 - 0.25 * tight) + c.ay * Math.sin(th * 2 + c.ph) * (1 - tight);
  return [R * Math.cos(th), y, R * Math.sin(th) - 0.4];
}

export interface CubeState {
  x: number; y: number; z: number;
  qa: number; // tumble angle around c.ax
  scale: number;
  g: number; hue: number;
  landed: number; // 0..1 how assembled
}

export function cubeAt(c: GlassCube, t: number): CubeState {
  const S = GSTORY;
  const tumble = c.spin * t;
  if (!c.face) {
    const [sx, sy, sz] = stormPos(c, t * 0.35);
    const k = sm(S.drift[0], S.duration, t);
    return { x: sx, y: sy + k * 3, z: sz - 2.5, qa: tumble * 0.3, scale: c.size * (1 - 0.6 * k), g: 0, hue: 0, landed: 0 };
  }
  if (t < S.explode) {
    const p = facePose(c, t);
    return { x: p.x, y: p.y, z: p.z, qa: 0, scale: 1, g: p.g, hue: p.hue, landed: 1 };
  }
  const tSnap = S.snap + 0.38 * c.r;
  let x: number, y: number, z: number, qa: number, landed = 0, g = 0, hue = 0;
  if (t < tSnap) {
    // burst -> storm
    const dt = t - S.explode;
    const p0 = facePose(c, S.explode);
    const k = 1 - Math.exp(-3.2 * dt);
    const bx = p0.x + c.blast[0] * k, by = p0.y + c.blast[1] * k, bz = p0.z + c.blast[2] * k;
    const [sx, sy, sz] = stormPos(c, t);
    const w = sm(0.25, 2.2, dt);
    x = bx + (sx - bx) * w; y = by + (sy - by) * w; z = bz + (sz - bz) * w;
    qa = tumble;
    g = p0.g * Math.exp(-dt * 3);
    hue = p0.hue;
  } else {
    // assemble with overshoot
    const p = facePose(c, t);
    const q = Math.min(1, (t - tSnap) / 0.6);
    const e = easeOutBack(q);
    const [sx, sy, sz] = stormPos(c, tSnap);
    x = sx + (p.x - sx) * e; y = sy + (p.y - sy) * e; z = sz + (p.z - sz) * e;
    qa = tumble * (1 - sm(0, 1, q)) + (1 - sm(0, 1, q)) * 0;
    if (q >= 1) qa = 0;
    landed = q;
    g = p.g * q;
    hue = p.hue;
    // ending: lift off and drift up into the light
    if (t > c.driftT) {
      const d = t - c.driftT;
      x += c.driftV[0] * d * d * 0.35; y += c.driftV[1] * d * d * 0.35; z += c.driftV[2] * d * d * 0.35;
      qa = c.spin * 0.25 * d * d;
      g *= Math.exp(-d * 1.2);
    }
  }
  const sc = t > c.driftT ? Math.max(0, 1 - (t - c.driftT) * 0.28) : 1;
  return { x, y, z, qa, scale: sc, g, hue, landed };
}

/** Region tint for a face cube (pearl skin, rose lips, lavender brows, sapphire irises, indigo pupils). */
export function regionColour(c: GlassCube): [number, number, number] {
  if (!c.face) return [0.95, 0.9, 1.0];
  const f0 = face(c.u, c.v, 20.6); // laughing face: lips/eyes well defined
  const fN = face(c.u, c.v, 15.0);
  const lips = f0.hue > 0.5 && f0.g > 0.12 && c.v < -0.4;
  const iris = fN.g > 0.25 && c.v > 0.1;
  if (iris) return [0.3, 0.48, 1.0]; // sapphire
  if (lips) return [1.0, 0.42, 0.58];
  if (fN.h < 0.08 && c.v > 0.1 && c.v < 0.45 && Math.abs(c.u) > 0.2) return [0.3, 0.22, 0.55]; // pupils / sockets
  for (const s of [-1, 1]) {
    const du = c.u - s * 0.37, by = 0.55 + 0.1 * (1 - (du * du) / 0.08);
    if (Math.abs(c.v - by) < 0.04 && Math.abs(du) < 0.27) return [0.55, 0.42, 0.9]; // brows
  }
  return [1.0, 0.93, 0.92]; // pearl skin
}

/** Sparkles: white glints from the burst, a small glint on every cube landing, light motes in the ending. */
export function glassParticles(cubes: GlassCube[], seed: number) {
  const r = rng(seed, "glass-parts");
  const P: number[] = [], V: number[] = [], T: number[] = [], C: number[] = [], Sz: number[] = [];
  const add = (p: number[], v: number[], t: number[], c: number[], s: number) => { P.push(...p); V.push(...v); T.push(...t); C.push(...c); Sz.push(s); };
  for (const c of cubes) {
    if (!c.face) continue;
    const p0 = facePose(c, GSTORY.explode);
    if (r() < 0.6) add([p0.x, p0.y, p0.z + 0.05], [c.blast[0] * 0.6 + (r() - 0.5), c.blast[1] * 0.6 + (r() - 0.5), c.blast[2] * 0.5], [GSTORY.explode + r() * 0.08, 0.6 + r() * 0.6, -1.5, 0], [2.4, 2.3, 2.5], 0.035 + r() * 0.03);
    const tl = GSTORY.snap + 0.38 * c.r + 0.6;
    const p1 = facePose(c, tl);
    if (r() < 0.45) add([p1.x, p1.y, p1.z + 0.06], [(r() - 0.5) * 0.4, 0.3 + r() * 0.5, 0.3 + r() * 0.4], [tl - 0.1, 0.35 + r() * 0.3, -1, 0], [2.6, 2.4, 2.2], 0.03 + r() * 0.025);
    if (r() < 0.5) add([p1.x, p1.y, p1.z], [(r() - 0.5) * 0.3, 0.6 + r() * 0.8, (r() - 0.5) * 0.3], [c.driftT + r() * 0.8, 2.5 + r() * 1.5, 0.2, 1], [2.2, 2.0, 2.4], 0.035 + r() * 0.03);
  }
  const f = (a: number[]) => Float32Array.from(a);
  return { count: Sz.length, p: f(P), v: f(V), t: f(T), c: f(C), s: f(Sz) };
}
