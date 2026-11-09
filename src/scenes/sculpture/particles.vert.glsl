// 60k particles: sculpture surface -> burst -> spinning galaxy -> back onto the sculpture (loop pose).
attribute vec3 aStart;  // surface when the burst begins
attribute vec3 aHome;   // surface in the loop pose (frame 0)
attribute vec3 aEnd;    // galaxy position (disc coords: x/z plane, y = thickness)
attribute vec4 aRnd;
attribute vec3 aCol;
uniform float uP;       // 0..1 transform progress
uniform float uT;       // seconds since transform start
uniform float uPx;      // pixels per world unit at depth 1
uniform float uSize;
varying vec3 vCol;
varying float vA;

mat3 rotY(float a) { float c = cos(a), s = sin(a); return mat3(c, 0.0, -s, 0.0, 1.0, 0.0, s, 0.0, c); }
mat3 rotX(float a) { float c = cos(a), s = sin(a); return mat3(1.0, 0.0, 0.0, 0.0, c, s, 0.0, -s, c); }
mat3 rotZ(float a) { float c = cos(a), s = sin(a); return mat3(c, s, 0.0, -s, c, 0.0, 0.0, 0.0, 1.0); }

void main() {
  float tOut = smoothstep(0.02 + aRnd.x * 0.16, 0.42 + aRnd.x * 0.12, uP);

  vec3 dir = normalize(aStart + vec3(1e-4));
  vec3 turb = vec3(sin(aRnd.w * 40.0 + uT * 1.3), cos(aRnd.x * 50.0 + uT * 1.1), sin(aRnd.y * 60.0 + uT * 0.9)) * 0.22;
  vec3 mid = aStart + dir * (0.5 + aRnd.z * 1.1) + turb;
  // galaxy spins faster near the core
  float rr = length(aEnd.xz);
  // inner galaxy returns first, outer arms last: reads as a vortex pulling in
  float tBack = smoothstep(0.62 + rr * 0.1, 0.8 + rr * 0.11, uP);
  float e = tBack * tBack * (3.0 - 2.0 * tBack);
  vec3 gal = rotZ(0.28) * rotX(1.08) * (rotY(uT * (0.25 + 0.5 / (rr + 0.4))) * aEnd);

  vec3 a = mix(aStart, mid, tOut);
  vec3 b = mix(mid, gal, tOut);
  vec3 pos = mix(a, b, tOut);
  // swirl back home
  vec3 back = rotY((1.0 - e) * 4.0) * mix(gal * (1.0 - 0.6 * e), aHome, e * e);
  pos = mix(pos, back, e);

  vec4 mv = modelViewMatrix * vec4(pos, 1.0);
  gl_Position = projectionMatrix * mv;
  gl_PointSize = uSize * uPx * (0.5 + aRnd.z) / -mv.z;
  vA = smoothstep(0.0, 0.06, tOut) * (1.0 - smoothstep(0.82, 1.0, e)) * (0.7 + 0.3 * sin(uT * 4.0 + aRnd.w * 80.0));
  vCol = aCol;
}
