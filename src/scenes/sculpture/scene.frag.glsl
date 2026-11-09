// Living liquid-chrome sculpture: ray-marched SDF (smooth-union core + orbiting droplets), iridescent
// thin-film colour, procedural studio reflections, halo glow, light rays + bokeh background, grain.
precision highp float;
varying vec2 vUv;
uniform float uAspect;
uniform float uTanHalf;
uniform float uTime;    // sculpture time (s)
uniform float uBgTime;  // background time (s)
uniform float uFrame;
uniform float uSeed;
uniform float uInv;     // 0..1 inverted colours (afterimage stare)
uniform float uGray;    // 0..1 grayscale (afterimage reveal)
uniform float uObj;     // 0..1 sculpture visibility
uniform float uBgMix;   // 0..1 neutral (colourless) background
uniform vec3 uBg0;
uniform vec3 uBg1;
uniform vec3 uTint;
uniform vec3 uTint2;
uniform vec4 uSat[6];   // droplets: orbit radius, speed, phase, size
uniform float uCamY;    // camera height: puts the sculpture on the focus point
uniform float uRot;     // whole-scene orbit angle (rad)
uniform float uScale;   // whole-scene scale (breathing push-in)
uniform float uShock;   // 0..1 shockwave progress (1 = none)

float hash(vec2 p) {
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}

float smin(float a, float b, float k) {
  float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);
  return mix(b, a, h) - k * h * (1.0 - h);
}

// keep in sync with sdf.ts
vec3 satPos(vec4 s, float t) {
  float a = s.z + t * s.y;
  return vec3(cos(a) * s.x, sin(a * 0.83 + s.z) * s.x * 0.75, sin(a) * s.x * 0.6);
}

float map(vec3 p) {
  float t = uTime;
  float d = length(p) - 0.62 * (1.0 + 0.05 * sin(t * 1.7));
  d += 0.03 * sin(p.x * 6.0 + t * 1.4) * sin(p.y * 5.0 - t * 1.2) * sin(p.z * 6.0 + t);
  for (int i = 0; i < 6; i++) {
    vec4 s = uSat[i];
    d = smin(d, length(p - satPos(s, t)) - s.w, 0.32);
  }
  return d;
}

float mapW(vec3 p) {
  float c = cos(uRot), s = sin(uRot);
  vec3 q = p / uScale;
  q = vec3(c * q.x - s * q.z, q.y, s * q.x + c * q.z);
  return map(q) * uScale;
}

vec3 calcNormal(vec3 p) {
  const vec2 e = vec2(0.0015, -0.0015);
  return normalize(e.xyy * mapW(p + e.xyy) + e.yyx * mapW(p + e.yyx) + e.yxy * mapW(p + e.yxy) + e.xxx * mapW(p + e.xxx));
}

vec3 env(vec3 r) {
  vec3 c = mix(uBg0 * 0.8, uBg1 * 1.6, smoothstep(-0.8, 0.9, r.y));
  c += vec3(2.2) * smoothstep(0.82, 0.97, r.y) * smoothstep(0.7, 0.25, abs(r.x));              // top softbox
  c += uTint * 2.4 * smoothstep(0.78, 0.95, r.x) * smoothstep(0.55, 0.0, abs(r.y - 0.1));       // right strip
  c += uTint2 * 2.0 * smoothstep(0.78, 0.95, -r.x) * smoothstep(0.6, 0.0, abs(r.y + 0.15));     // left strip
  c += vec3(0.7) * smoothstep(0.55, 1.0, r.z) * 0.45;                                           // fill from camera
  c += vec3(0.25, 0.5, 1.2) * smoothstep(0.3, 1.0, -r.y) * 0.6;                                 // floor bounce
  return c;
}

vec3 background(vec2 q) {
  vec3 c = mix(uBg0, uBg1, smoothstep(-0.9, 0.9, q.y));
  c += uTint * 0.22 * exp(-length(q) * 2.6);
  float ang = atan(q.x, 1.1 - q.y);
  float rays = pow(0.5 + 0.5 * sin(ang * 13.0 + uBgTime * 0.25), 8.0) * 0.6
             + pow(0.5 + 0.5 * sin(ang * 21.0 - uBgTime * 0.17), 10.0) * 0.5;
  c += mix(uTint, vec3(1.0), 0.3) * rays * 0.07 * smoothstep(-0.4, 0.9, q.y);
  for (int l = 0; l < 3; l++) {
    float fl = float(l);
    float sc = 5.0 + fl * 4.0;
    vec2 g = q * sc + vec2(uSeed * 0.37 + fl * 3.1, -uBgTime * (0.06 + 0.04 * fl));
    vec2 id = floor(g);
    vec2 f = fract(g) - 0.5;
    float h = hash(id + fl * 17.0 + uSeed);
    vec2 o = (vec2(hash(id + 3.1), hash(id + 7.7)) - 0.5) * 0.5;
    float rr = 0.06 + 0.12 * hash(id + 11.0);
    float m = smoothstep(rr, rr * 0.35, length(f - o)) * step(0.72, h);
    float tw = 0.75 + 0.25 * sin(uBgTime * 1.5 + h * 40.0);
    c += mix(uTint, uTint2, hash(id + 5.0)) * m * tw * (0.24 - 0.05 * fl);
  }
  return c;
}

void main() {
  vec2 q = vUv - 0.5;
  q.x *= uAspect;
  vec3 ro = vec3(0.0, uCamY, 7.0);
  vec3 rd = normalize(vec3((vUv - 0.5) * 2.0 * vec2(uAspect, 1.0) * uTanHalf, -1.0));
  vec3 bg = background(q);
  {
    vec2 c = vec2(0.0, -uCamY / (7.0 * uTanHalf) * 0.5);
    float r = length(q - c);
    float R = uShock * 1.25;
    float ring = exp(-pow((r - R) / 0.018, 2.0)) + 0.35 * exp(-pow((r - R * 0.8) / 0.05, 2.0));
    bg += mix(uTint, vec3(1.0), 0.45) * ring * pow(1.0 - uShock, 2.0) * 0.55;
  }
  float glow = 0.0;
  float hit = 0.0;
  vec3 obj = vec3(0.0);

  float b = dot(ro, rd);
  float h = b * b - (dot(ro, ro) - 3.6 * uScale * uScale);
  if (h > 0.0 && uObj > 0.001) {
    float t = -b - sqrt(h);
    float tmax = -b + sqrt(h);
    for (int i = 0; i < 96; i++) {
      vec3 p = ro + rd * t;
      float d = mapW(p);
      glow += exp(-d * 9.0) * 0.016;
      if (d < 0.0008) { hit = 1.0; break; }
      t += d * 0.9;
      if (t > tmax) break;
    }
    if (hit > 0.5) {
      vec3 p = ro + rd * t;
      vec3 n = calcNormal(p);
      float ndv = max(dot(n, -rd), 0.0);
      float fr = pow(1.0 - ndv, 3.0);
      vec3 film = 0.5 + 0.5 * cos(6.2831 * (vec3(0.0, 0.33, 0.67) + ndv * 1.3 + p.y * 0.35 + uTime * 0.04));
      vec3 refl = env(reflect(rd, n));
      float ao = 0.0, sc = 1.0;
      for (int k = 1; k <= 4; k++) {
        float hh = 0.05 * float(k);
        ao += (hh - mapW(p + n * hh)) * sc;
        sc *= 0.6;
      }
      ao = clamp(1.0 - 2.5 * ao, 0.35, 1.0);
      obj = refl * mix(film, vec3(1.0), 0.3) * 0.9 + film * fr * 1.1 + film * 0.08;
      obj *= ao;
      obj += uTint * pow(fr, 2.0) * 0.5;
    }
  }
  obj = 1.0 - exp(-obj * 1.25);

  float luma = dot(obj, vec3(0.299, 0.587, 0.114));
  vec3 inv = clamp(mix(vec3(1.0 - luma), 1.0 - obj, 1.9), 0.0, 1.0);
  vec3 o = mix(mix(obj, inv, uInv), vec3(luma), uGray);

  float bgL = dot(bg, vec3(0.299, 0.587, 0.114));
  bg = mix(bg, vec3(bgL * 0.7 + 0.03), uBgMix);
  vec3 glowCol = mix(uTint, uTint2, 0.4);
  vec3 col = bg + glowCol * glow * uObj * (1.0 - uBgMix);
  col = mix(col, o, hit * uObj);

  col *= 1.0 - 0.35 * pow(length(q * vec2(1.0, 0.75)), 2.0);
  col += (hash(gl_FragCoord.xy + uFrame * 13.1) - 0.5) * 0.025;
  gl_FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}
