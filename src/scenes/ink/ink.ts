// "Ink and Water" (owner's pick, concept 5, Nov 10): dark water seen from above. Glowing inks (cyan, magenta, gold,
// violet, rose) drop in, bloom into fingered clouds, get carried by slow currents into marble filaments, then a slow
// vortex winds everything into one spiral galaxy of ink, and it settles. Differs from Ferrofluid (3D neon mirror
// spikes) and Orb Waves: flat top-down 2D fluid, warm + cool inks on deep navy, soft and painterly.
// The ink is truly advected: every pixel is traced back through the flow (currents + vortex) to where its fluid was
// when each drop landed, so the shapes stretch and fold like real ink.

export const ISTORY = {
  duration: 30,
  /** drops: x, y, landing time, size, colour index */
  drops: [
    // HOOK: six inks land almost together in a ring and bloom into each other on frame 0
    [0.210, 0.065, -0.9, 0.24, 0],
    [0.049, 0.215, -0.75, 0.24, 1],
    [-0.161, 0.150, -0.6, 0.24, 2],
    [-0.210, -0.065, -0.45, 0.24, 3],
    [-0.049, -0.215, -0.3, 0.24, 4],
    [0.161, -0.150, -0.15, 0.24, 5],
    [0.26, -0.5, 6.0, 0.2, 2],
    [0.0, 0.0, 15.2, 0.11, 6],
    // second wave (the reel opens at story 17 s, mid-whirlpool): fresh drops land in the marbled water
    [-0.3, 0.45, 26.5, 0.2, 0],
    [0.32, -0.2, 29.0, 0.2, 2],
    [-0.1, -0.6, 31.5, 0.18, 3],
    [0.15, 0.7, 34.0, 0.16, 5],
  ] as number[][],
  colours: [
    [0.1, 0.85, 1.0], // cyan
    [1.0, 0.12, 0.55], // magenta
    [1.0, 0.68, 0.12], // gold
    [0.55, 0.28, 1.0], // violet
    [0.2, 1.0, 0.7], // mint
    [1.0, 0.35, 0.45], // rose
    [1.0, 0.1, 0.75], // hot magenta (the last drop, into the eye of the vortex)
  ],
  vortex: [10.0, 15.0, 20.5, 25.5] as [number, number, number, number], // ramp in, hold, ramp out
  vortex2: [35.0, 39.0, 42.0, 45.0] as [number, number, number, number], // the final whirlpool
  fade: [44.4, 46.8] as [number, number],
};

const sm = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

/** Vortex strength 0..1 at time t. */
const win = (v: number[], t: number) => sm(v[0], v[1], t) * (1 - sm(v[2], v[3], t));
export const vortexAt = (t: number) => Math.max(0.75 * sm(-1, -0.2, t) * (1 - sm(2, 4.5, t)), win(ISTORY.vortex, t), win(ISTORY.vortex2, t));

/** Camera: slow push-in and a gentle turn with the vortex. */
export function camAt(t: number) {
  const zoom = 1.55 - 0.55 * sm(-0.5, 4.5, t) + 0.16 * sm(5, 16, t) - 0.1 * sm(20, 28, t) + 0.12 * sm(33, 41, t) - 0.04 * sm(42, 47, t);
  const ang = 0.012 * t + 0.25 * sm(10, 26, t) + 0.25 * sm(34, 46, t);
  return { zoom, ang };
}

/** Field energy 0..1 (sound level). */
export function energy(t: number) {
  let e = 0.2 + 0.5 * vortexAt(t);
  for (const d of ISTORY.drops) { const a = t - d[2]; if (a > 0 && a < 4) e += 0.3 * Math.exp(-a); }
  return Math.min(1, e) * (1 - sm(ISTORY.fade[0], ISTORY.fade[1], t));
}

export const INK_GLSL = /* glsl */ `
uniform float uT;
uniform vec4 uDrop[12];   // x, y, landing time, size
uniform vec3 uCol[12];
uniform float uVortT[8];
uniform vec2 uView;      // half extents of the view
uniform float uZoom, uAng;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p) {
  vec2 i = floor(p), f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}
float fbm(vec2 p) {
  float s = 0.0, a = 0.5;
  for (int i = 0; i < 5; i++) { s += a * vnoise(p); p = p * 2.03 + vec2(1.7, 9.2); a *= 0.5; }
  return s;
}
float vortexS(float t) {
  // a quick pinwheel spin of the opening burst, then the big vortex later
  float hook = 0.75 * smoothstep(-1.0, -0.2, t) * (1.0 - smoothstep(2.0, 4.5, t));
  float v1 = smoothstep(uVortT[0], uVortT[1], t) * (1.0 - smoothstep(uVortT[2], uVortT[3], t));
  float v2 = smoothstep(uVortT[4], uVortT[5], t) * (1.0 - smoothstep(uVortT[6], uVortT[7], t));
  return max(hook, max(v1, v2));
}
// gentle divergence-free currents (stream function = sum of moving sine waves)
vec2 current(vec2 x, float t) {
  vec2 v = vec2(0.0);
  vec2 k; float ph;
  k = vec2(3.1, 1.2); ph = dot(k, x) + 0.31 * t + 0.4; v += 0.0095 * cos(ph) * vec2(k.y, -k.x);
  k = vec2(-1.4, 4.2); ph = dot(k, x) - 0.27 * t + 2.1; v += 0.0080 * cos(ph) * vec2(k.y, -k.x);
  k = vec2(5.3, -3.6); ph = dot(k, x) + 0.22 * t + 4.0; v += 0.0042 * cos(ph) * vec2(k.y, -k.x);
  k = vec2(-7.9, -6.1); ph = dot(k, x) + 0.35 * t + 1.3; v += 0.0021 * cos(ph) * vec2(k.y, -k.x);
  return v;
}
vec2 rot(vec2 p, float a) { float c = cos(a), s = sin(a); return vec2(c * p.x - s * p.y, s * p.x + c * p.y); }

// trace pixel x at time uT back through the flow; q[i] = where its fluid was when drop i landed
void backtrace(vec2 x, out vec2 q[12]) {
  for (int i = 0; i < 12; i++) q[i] = vec2(99.0);
  // FIXED time grid (steps at multiples of H): every frame integrates the same path, so nothing jitters or steps
  const float H = 0.2;
  float t0 = -1.8;
  float tau = uT;
  float dt = tau - floor(tau / H - 1e-4) * H; // first partial step lands on the grid
  for (int k = 0; k < 250; k++) {
    if (tau <= t0) break;
    for (int i = 0; i < 12; i++) {
      if (uDrop[i].z <= tau && uDrop[i].z > tau - dt) q[i] = x;
    }
    float s = 0.5 * (vortexS(tau) + vortexS(tau - dt));
    float r2 = dot(x, x);
    x = rot(x, -s * dt * 0.11 / (r2 + 0.05));
    x -= current(x, tau - 0.5 * dt) * dt * 3.6;
    tau -= dt;
    dt = H;
  }
  for (int i = 0; i < 12; i++) if (q[i].x > 90.0 && uDrop[i].z <= uT) q[i] = x;
}

// water surface ripples from each drop (height), for refraction + soft highlights
float ripples(vec2 p) {
  float h = 0.0;
  for (int i = 0; i < 12; i++) {
    float a = uT - uDrop[i].z;
    if (a < 0.0 || a > 6.0) continue;
    float r = length(p - uDrop[i].xy), f = r - 0.32 * a;
    h += 0.012 * sin(f * 48.0) * exp(-f * f / 0.012) * exp(-a * 0.7) / (1.0 + 4.0 * r);
  }
  return h;
}

// ink density + colour (albedo) at a point of the water
float inkField(vec2 ps, out vec3 alb) {
  vec2 q[12];
  backtrace(ps, q);
  vec3 hsum = vec3(0.0); float wsum = 0.0, D = 0.0;
  for (int i = 0; i < 12; i++) {
    float a = uT - uDrop[i].z;
    if (a < 0.0) continue;
    vec2 d = q[i] - uDrop[i].xy;
    float r = length(d), th = atan(d.y, d.x);
    float R = 0.85 * uDrop[i].w * (sqrt(1.0 - exp(-a * 1.3)) + 0.04 * a);
    // billowing edge: big lobes + small cauliflower curls (real ink front)
    float fing = 1.0 + 0.025 * sin(7.0 * th + float(i) * 2.3);
    float n = fbm(q[i] * 4.5 + float(i) * 7.1);
    float curl = fbm(q[i] * 13.0 - float(i) * 2.9) - 0.5;
    float rr = r * fing * (0.86 + 0.3 * n) + R * 0.16 * curl;
    float w = 0.008 + 0.006 * a;
    float body = smoothstep(R + w, R - w * 2.0, rr);
    // wispy thinning toward the edge, denser front ring, smoky layers and fine fibres inside
    float edge = smoothstep(R + w, R - 0.25 * R, rr);
    float front = exp(-pow((R - rr) / (0.03 + 0.008 * a), 2.0));
    float smoke = pow(fbm(q[i] * 5.0 - float(i) * 3.3), 1.6) * 1.6;
    float fine = 0.7 + 0.3 * fbm(q[i] * 28.0 + float(i));
    float fib = pow(1.0 - abs(2.0 * fbm(q[i] * 16.0 + float(i) * 4.7) - 1.0), 4.0);
    float dens = body * (0.25 + 0.75 * edge) * (0.6 * smoke * fine + 0.3 * fib + (0.3 + 0.7 * exp(-a * 0.35)) * smoothstep(0.0, 0.5, a) * front) * (0.8 + 0.2 * exp(-a * 0.5)) * 1.6;
    float wt = dens * dens * dens * dens + 1e-6;
    hsum += uCol[i] * wt; wsum += wt; D += dens;
  }
  alb = hsum / wsum;
  return D;
}

vec3 shade(vec2 uv) {
  vec2 p = rot((uv - 0.5) * 2.0 * uView / uZoom, uAng);
  // water surface ripples (refraction + soft highlight)
  float e = 0.002;
  float h0 = ripples(p);
  vec2 g = vec2(ripples(p + vec2(e, 0.0)) - h0, ripples(p + vec2(0.0, e)) - h0) / e;
  vec2 ps = p + g * 0.06;
  // studio water: near black with one soft pool of light
  vec3 bg = vec3(0.003, 0.004, 0.008) + vec3(0.016, 0.022, 0.034) * exp(-dot(p - vec2(-0.15, 0.45), p - vec2(-0.15, 0.45)) / 0.9);
  // volumetric ink: density here, its gradient (shape) and the density toward the light (self-shadow)
  vec3 alb, a2;
  float D = inkField(ps, alb);
  if (D < 0.002) {
    vec3 n3 = normalize(vec3(-g * 1.2, 1.0));
    return bg + vec3(0.5, 0.6, 0.75) * pow(max(dot(n3, normalize(vec3(-0.35, 0.45, 1.0))), 0.0), 140.0) * 0.12;
  }
  const float E = 0.004;
  float Dx = inkField(ps + vec2(E, 0.0), a2);
  float Dy = inkField(ps + vec2(0.0, E), a2);
  vec3 L = normalize(vec3(-0.55, 0.6, 0.6));
  float Ds = inkField(ps + L.xy * 0.035, a2);
  vec3 n = normalize(vec3(-(Dx - D) / E * 0.009, -(Dy - D) / E * 0.009, 1.0));
  float diff = 0.3 + 0.7 * max(dot(n, L), 0.0);
  float shadow = exp(-max(0.0, Ds - D * 0.6) * 1.4);
  // Beer-Lambert: thin ink is pale and translucent, thick ink deep and saturated
  float op = 1.0 - exp(-D * 1.15);
  vec3 deep = pow(alb, vec3(1.0 + 0.9 * min(D, 2.5)));
  vec3 light = vec3(1.0, 0.97, 0.92) * 1.15;
  vec3 ink = deep * light * diff * (0.45 + 0.55 * shadow);
  ink += alb * light * 0.55 * (1.0 - op); // light glowing through the thin, translucent smoke // light scattering through the thin wisps
  vec3 col = mix(bg, ink, op);
  // soft highlight of the ripples on top
  vec3 n3 = normalize(vec3(-g * 1.2, 1.0));
  col += vec3(0.5, 0.6, 0.75) * pow(max(dot(n3, normalize(vec3(-0.35, 0.45, 1.0))), 0.0), 140.0) * 0.12;
  return col;
}
`;
