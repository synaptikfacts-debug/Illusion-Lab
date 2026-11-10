// "Ferrofluid Bloom" (owner's pick, Nov 10): jet-black magnetic liquid with a mirror surface. An invisible magnet
// pulls the surface into a hexagonal field of sharp, concave spikes (real ferrofluid shape). Same family as the
// owner's favourite "Liquid Obsidian", new phenomena and palette (teal / electric violet / white ring lights).
// Story (s): HOOK a ring of spikes already standing -> magnet pulses send spike rings outward -> the field grows
// from the centre over the whole pool -> the spikes bloom into a slowly turning six-petal flower with a tall crown
// -> the magnet switches off: the spikes melt, one ripple runs out -> calm mirror, fade.
// The height field is GLSL (FERRO_GLSL); controls() gives its uniforms per frame (also used for the sound).

export const FSTORY = {
  duration: 30,
  /** pulse rings, each emitted from where the magnet is at that moment */
  pulses: [-0.9, 0.2, 1.3, 2.4, 3.5, 4.6, 5.7, 6.8],
  /** the gliding magnet: travels a figure-eight, then settles in the centre */
  glide: [0, 7.4] as [number, number],
  settle: 8.6,
  grow: [6.8, 11.5] as [number, number],
  bloom: [11.5, 15.0] as [number, number], // the field twists into spiral arms
  swirl: [12.5, 20.5] as [number, number], // ...and spins faster into a whirlpool (spike galaxy)
  crown: [40, 41] as [number, number], // (unused)
  off: 21.6,
  fade: [27.6, 29.8] as [number, number],
};

const sm = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

/** Magnet position on the pool (x, z). */
export function magAt(t: number): [number, number] {
  return [0 * t, 0]; // the magnet stays under the centre (calm, ordered)
}
export function magAtGlide(t: number): [number, number] {
  const S = FSTORY;
  // eases in over the first 1.5 s (no fast sweep on the first frames), then glides at full speed
  const te = t < 1.5 ? (t * t) / 3 : t - 0.75;
  const tt = Math.min(te, S.glide[1] - 0.75);
  const x = 1.15 * Math.sin(0.85 * tt + 0.4), z = 0.75 * Math.sin(1.7 * tt + 1.2);
  const k = sm(S.glide[1], S.settle, t); // glide home to the centre
  return [x * (1 - k), z * (1 - k)];
}

/** Uniform values at time t. */
export function controls(t: number) {
  const S = FSTORY;
  const on = 1 - sm(S.off, S.off + 0.9, t); // magnet strength
  return {
    grow: sm(S.grow[0], S.grow[1], t), // field radius growth
    bloom: sm(S.bloom[0], S.bloom[1], t),
    crown: sm(S.crown[0], S.crown[1], t),
    on,
    rot: 0.04 * t, // the lattice turns very slowly
    spin: 0.11 * Math.max(0, Math.min(t, S.off + 1) - 11.5) ** 2, // spiral arms sweep round, faster and faster
    swirl: sm(S.swirl[0], S.swirl[1], t) * on,
    melt: t - S.off, // seconds since the magnet switched off (negative before)
    mag: magAt(t),
    magOn: 0, // no travelling cluster (owner: too tall and confusing)
    pulses: S.pulses.flatMap((p) => { const [x, z] = magAt(Math.max(0, p)); return [x, z, p]; }),
  };
}

/** Overall field energy 0..1 at time t (sound level). */
export function energy(t: number) {
  const k = controls(t);
  let e = 0.25 + 0.45 * k.grow + 0.3 * k.bloom;
  for (const p of FSTORY.pulses) { const d = t - p; if (d > 0 && d < 2.5) e += 0.3 * Math.exp(-d * 1.4); }
  return Math.min(1, e) * k.on;
}

export const FERRO_GLSL = /* glsl */ `
uniform float uT, uGrow, uBloom, uCrown, uOn, uRot, uMelt, uSwirl, uSpin;
uniform vec3 uPulse[8];
uniform vec2 uMag;
uniform float uMagOn;
const float A = 0.17; // spike spacing

// nearest centre of a hexagonal lattice
vec2 hexCentre(vec2 p) {
  vec2 r = vec2(1.0, 1.7320508) * A;
  vec2 h = r * 0.5;
  vec2 a = mod(p, r) - h;
  vec2 b = mod(p - h, r) - h;
  return dot(a, a) < dot(b, b) ? p - a : p - b;
}

// how strongly the magnet pulls at point c (0..1.4)
float envelope(vec2 c) {
  float r = length(c), th = atan(c.y, c.x);
  float e = 0.0;
  // pulse rings travelling outward from where the magnet was when they fired (they cross and collide)
  for (int i = 0; i < 8; i++) {
    float d = uT - uPulse[i].z;
    if (d < 0.0 || d > 4.0) continue;
    float rr = length(c - uPulse[i].xy);
    float front = 0.3 + 0.8 * d;
    e += exp(-pow((rr - front) / 0.17, 2.0)) * exp(-d * 0.35) * 1.0;
  }
  // the travelling magnet drags a tall cluster of spikes
  float dm = length(c - uMag);
  e += uMagOn * 1.25 * exp(-dm * dm / 0.16);
  // a small mound of spikes at the centre once the magnet has settled
  e += (1.0 - uMagOn) * 0.55 * exp(-r * r / 0.18);
  // the field grows over the pool
  float R = mix(0.4, 2.3, uGrow);
  e = max(e, uGrow * 0.85 * (1.0 - smoothstep(R - 0.5, R, r)));
  // breathing waves roll through the field the whole time
  e *= 0.78 + 0.22 * sin(5.0 * r - 2.4 * uT);
  // spiral arms (a galaxy of spikes)
  float arms = 0.5 + 0.5 * cos(4.0 * (th - uRot) + 6.0 * log(r + 0.05) - uSpin);
  e *= mix(1.0, 0.02 + 1.2 * pow(arms, 3.0), uBloom);
  // crown: the centre rises tall
  e = min(e, 1.0);
  e += uCrown * 0.55 * exp(-r * r / 0.12);
  return e * uOn;
}

float height(vec2 p) {
  float rp = length(p);
  float ang = uRot; // crisp lattice (no warp: it smeared the spikes)
  float cr = cos(ang), sr = sin(ang);
  vec2 q = vec2(cr * p.x - sr * p.y, sr * p.x + cr * p.y);
  vec2 c = hexCentre(q);
  float e = envelope(c);
  float d = length(q - c);
  // concave ferrofluid spike: sharp tip, flaring base
  float s = pow(max(0.0, 1.0 - d / (A * 0.56)), 1.8);
  float h = e * 0.42 * s;
  // the fluid heaps up a little under the spikes
  h += 0.07 * envelope(p * 0.999);
  // the whirlpool: the liquid sinks in the middle as the galaxy spins
  h -= uSwirl * 0.2 / (1.0 + rp * rp * 3.0);
  // after the magnet switches off: a jet leaps from the centre and one big ring sweeps across the pool
  if (uMelt > 0.0) {
    float front = rp - 1.3 * uMelt;
    h += 0.09 * sin(12.0 * front) * exp(-pow(front / 0.4, 2.0)) * exp(-uMelt * 0.5);
    h += 0.42 * exp(-rp * rp / 0.012) * max(0.0, sin(uMelt * 3.0)) * exp(-uMelt * 1.4) * step(uMelt, 1.05);
    h -= 0.2 * exp(-rp * rp / 0.08) * exp(-uMelt * 2.5); // the whirlpool fills back in
  }
  return h;
}
`;
