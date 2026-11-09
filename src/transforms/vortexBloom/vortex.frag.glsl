// Placeholder transformation: the ring field twists into a vortex, gets pulled into the focus point,
// blooms once (single soft glow, not a strobe) and settles on the background colour.
precision highp float;
varying vec2 vUv;
uniform float uAspect;
uniform float uP;        // 0..1 transform progress
uniform float uTime;     // frozen ring time from the illusion
uniform float uSpeed;
uniform float uDensity;
uniform vec2 uFocus;
uniform vec3 uA;
uniform vec3 uB;
uniform vec3 uBg;
uniform vec3 uGlow;

void main() {
  vec2 p = vec2(vUv.x, 1.0 - vUv.y) - uFocus;
  p.x *= uAspect;
  float r = length(p);
  float a = atan(p.y, p.x);
  float pull = uP * uP;
  // Gentle twist + slow inward pull. Ring contrast fades as soon as things start moving, so no pixel
  // swings bright/dark more than ~1-2 times a second (the first version flickered ~16x/s and failed the flash check).
  a += pull * 4.0 * exp(-r * 2.5);
  float rr = r * (1.0 + pull * 1.5);
  float phase = rr * uDensity * 2.0 - uTime * uSpeed + sin(a * 3.0) * pull * 0.6;
  float s = smoothstep(0.1, 0.9, 0.5 + 0.5 * sin(phase * 6.2831853));
  s = 0.5 + (s - 0.5) * (1.0 - 0.75 * smoothstep(0.0, 0.3, uP));
  vec3 col = mix(uA, uB, s);
  float vig = smoothstep(0.95 - pull * 0.7, 0.25 - pull * 0.25, r);
  col = mix(uBg, col, clamp(vig, 0.0, 1.0));
  // one bloom centred on the focus, peaking at uP = 0.75
  float bloom = exp(-pow((uP - 0.75) / 0.12, 2.0));
  col += uGlow * bloom * exp(-r * 3.0) * 0.9;
  // settle to background
  col = mix(col, uBg, smoothstep(0.8, 1.0, uP));
  gl_FragColor = vec4(col, 1.0);
}
