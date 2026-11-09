// Placeholder illusion: soft concentric rings drifting outward (motion-aftereffect style).
// Low-contrast sine rings so no pixel flickers hard: keeps the flash check green.
precision highp float;
varying vec2 vUv;
uniform float uAspect;
uniform float uTime;     // seconds of ring motion (frozen during the reveal)
uniform float uSpeed;    // rings per second passing a point
uniform float uDensity;  // rings across half the frame height
uniform float uGray;     // 0..1 desaturation
uniform vec2 uFocus;     // frame fractions, y down
uniform vec3 uA;
uniform vec3 uB;
uniform vec3 uBg;

void main() {
  vec2 p = vec2(vUv.x, 1.0 - vUv.y) - uFocus;
  p.x *= uAspect;
  float r = length(p);
  float phase = r * uDensity * 2.0 - uTime * uSpeed;
  float s = 0.5 + 0.5 * sin(phase * 6.2831853);
  s = smoothstep(0.1, 0.9, s);
  vec3 col = mix(uA, uB, s);
  float vig = smoothstep(0.95, 0.25, r);
  col = mix(uBg, col, vig);
  float g = dot(col, vec3(0.299, 0.587, 0.114));
  col = mix(col, vec3(g), uGray);
  gl_FragColor = vec4(col, 1.0);
}
