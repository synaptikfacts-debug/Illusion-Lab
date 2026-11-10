// "Liquid Obsidian": a mirror-black liquid surface reflecting neon light. Pure abstract physics, no pictures.
// Story (s): HOOK mid-impact crater ring -> drops + interference -> accelerating rain -> six-fold standing-wave
// star (cymatics) -> whirlpool vortex -> COLLAPSE (jet + giant ring) -> calm mirror, one last drop -> fade.
// The same height field is written in GLSL (WAVES_GLSL) for the picture and described here for sound timing.
import { rng } from "../../core/seed";

export interface Drop { x: number; z: number; t: number; a: number }

export const LSTORY = {
  duration: 30.0,
  rain: [7.0, 10.9] as [number, number],
  stand: [11.0, 16.6] as [number, number],
  vortex: [15.6, 22.0] as [number, number],
  collapse: 22.0,
  lastDrop: 25.6,
  fade: [27.2, 29.7] as [number, number],
};

export function drops(seed: number): Drop[] {
  const r = rng(seed, "drops");
  const d: Drop[] = [
    { x: 0, z: 0, t: -0.3, a: 1.2 }, // the hook: already mid-impact on frame 0
    { x: 1.6, z: -1.2, t: 1.3, a: 0.8 },
    { x: -1.5, z: -0.6, t: 2.0, a: 0.8 },
    { x: 0.3, z: 1.4, t: 2.7, a: 0.9 },
    { x: -0.8, z: 1.0, t: 3.6, a: 0.6 },
    { x: 1.0, z: 0.2, t: 4.3, a: 0.7 },
    { x: 0, z: -1.6, t: 5.0, a: 0.8 },
    { x: -1.6, z: 0.5, t: 5.8, a: 0.6 },
  ];
  // accelerating rain
  let t = LSTORY.rain[0], gap = 0.42;
  while (d.length < 22 && t < LSTORY.rain[1]) {
    const ang = r() * Math.PI * 2, rad = 0.3 + r() * 2.0;
    d.push({ x: Math.cos(ang) * rad, z: Math.sin(ang) * rad, t, a: 0.35 + r() * 0.25 });
    t += gap;
    gap = Math.max(0.13, gap * 0.86);
  }
  d.push({ x: 0, z: 0, t: LSTORY.collapse, a: 1.6 }); // the collapse: jet + giant ring
  d.push({ x: 0.45, z: -0.35, t: LSTORY.lastDrop, a: 0.35 }); // the last drop
  while (d.length < 24) d.push({ x: 0, z: 0, t: 999, a: 0 });
  return d.slice(0, 24);
}

const sm = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

/** Global wave controls at time t (uniforms). */
export function controls(t: number) {
  const S = LSTORY;
  const stand = sm(S.stand[0], S.stand[0] + 2.0, t) * (1 - sm(S.stand[1] - 1.4, S.stand[1], t));
  const vort = sm(S.vortex[0], S.vortex[0] + 2.6, t) * (1 - sm(S.collapse - 0.35, S.collapse + 0.05, t));
  return { stand, vort, rot: 0.06 * t, pulse: 0.65 + 0.35 * Math.cos(t * 2.4) };
}

export const WAVES_GLSL = /* glsl */ `
uniform vec4 uDrops[24];
uniform float uT, uStand, uVort, uRot, uPulse;
float height(vec2 p) {
  float h = 0.0;
  for (int i = 0; i < 24; i++) {
    vec4 d = uDrops[i];
    float dt = uT - d.z;
    if (dt < 0.0 || dt > 7.0 || d.w <= 0.0) continue;
    float r = length(p - d.xy);
    float front = r - 1.55 * dt;
    float w = 0.28 + 0.32 * dt;
    // ring train behind the front
    h += d.w * 0.16 * sin(13.0 * front) * exp(-pow((front + 0.35 * w) / w, 2.0)) * exp(-dt * 0.5) / (1.0 + 1.1 * r);
    // crater + rebound jet at the impact point
    h -= d.w * 0.42 * exp(-r * r / 0.07) * exp(-dt * 5.0) * sin(min(dt * 14.0, 3.14159));
    h += d.w * 0.34 * exp(-r * r / 0.012) * max(0.0, sin((dt - 0.22) * 5.5)) * exp(-dt * 2.6) * step(0.22, dt);
  }
  // six-fold standing-wave star (cymatics), slowly turning
  if (uStand > 0.0) {
    float s = 0.0;
    for (int j = 0; j < 6; j++) {
      float a = float(j) * 0.5235988 + uRot;
      s += cos(7.5 * (p.x * cos(a) + p.y * sin(a)));
    }
    h += uStand * uPulse * 0.03 * s * exp(-dot(p, p) * 0.06);
  }
  // whirlpool vortex with spiral arms
  if (uVort > 0.0) {
    float r = length(p), th = atan(p.y, p.x);
    h -= uVort * 0.62 / (1.0 + r * r * 2.2);
    h += uVort * 0.055 * sin(5.0 * th + 7.0 * log(r + 0.06) - uT * 5.0) * exp(-r * 0.35) * smoothstep(0.0, 0.45, r);
  }
  return h;
}
`;
