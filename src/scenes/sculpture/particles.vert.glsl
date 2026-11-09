// Particle morph chain: sculpture surface -> burst -> spinning galaxy -> flowing torus knot
// -> beating heart -> vortex back onto the sculpture (frame-0 pose). Each stage has its own 0..1 progress;
// every particle gets its own delay so shapes dissolve and form as waves, not all at once.
attribute vec3 aStart;  // sculpture surface when the burst begins
attribute vec3 aHome;   // sculpture surface in the loop pose
attribute vec3 aEnd;    // galaxy (disc coords: x/z plane, y = thickness)
attribute vec4 aKnot;   // x = knot parameter (0..2pi), yzw = tube offset
attribute vec3 aHeart;  // heart surface
attribute vec4 aRnd;
attribute vec3 aCol;
uniform float uOut;     // burst -> galaxy
uniform float uKnot;    // galaxy -> knot
uniform float uHeart;   // knot -> heart
uniform float uBack;    // heart -> sculpture
uniform float uT;       // seconds since the transform began
uniform float uBeat;    // heart scale (lub-dub)
uniform float uRot;     // scene orbit: the heart counter-rotates so it always faces the camera
uniform float uPx;
uniform float uSize;
varying vec3 vCol;
varying float vA;

mat3 rotY(float a) { float c = cos(a), s = sin(a); return mat3(c, 0.0, -s, 0.0, 1.0, 0.0, s, 0.0, c); }
mat3 rotX(float a) { float c = cos(a), s = sin(a); return mat3(1.0, 0.0, 0.0, 0.0, c, s, 0.0, -s, c); }
mat3 rotZ(float a) { float c = cos(a), s = sin(a); return mat3(c, s, 0.0, -s, c, 0.0, 0.0, 0.0, 1.0); }

// stage progress with a per-particle delay (0 = early, 1 = late), eased
float stage(float p, float delay) {
  float x = clamp((p * 1.5 - delay * 0.5), 0.0, 1.0);
  return x * x * (3.0 - 2.0 * x);
}

vec3 knotPos(float u) {
  float R = 0.62, r = 0.27;
  float c3 = cos(3.0 * u);
  return vec3((R + r * c3) * cos(2.0 * u), (R + r * c3) * sin(2.0 * u), r * sin(3.0 * u));
}

void main() {
  float rr = length(aEnd.xz);
  float sOut = stage(uOut, aRnd.x);
  float sKnot = stage(uKnot, aKnot.x / 6.2832);
  float sHeart = stage(uHeart, aRnd.y);
  float sBack = stage(uBack, rr / 1.3);

  // burst: fly out along the surface normal-ish direction with turbulence
  vec3 dir = normalize(aStart + vec3(1e-4));
  vec3 turb = vec3(sin(aRnd.w * 40.0 + uT * 1.3), cos(aRnd.x * 50.0 + uT * 1.1), sin(aRnd.y * 60.0 + uT * 0.9)) * 0.22;
  vec3 mid = aStart + dir * (0.6 + aRnd.z * 1.2) + turb;
  vec3 gal = rotZ(0.28) * rotX(1.08) * (rotY(uT * (0.25 + 0.5 / (rr + 0.4))) * aEnd);
  vec3 pos = mix(mix(aStart, mid, sOut), mix(mid, gal, sOut), sOut);

  // knot: particles stream along the curve
  float u = aKnot.x + uT * 0.45;
  vec3 knot = rotX(0.35) * (knotPos(u) + aKnot.yzw);
  pos = mix(pos, knot, sKnot) + dir * sin(3.1416 * sKnot) * 0.35;

  vec3 heart = rotY(-uRot + sin(uT * 0.9) * 0.35) * (aHeart * uBeat);
  pos = mix(pos, heart, sHeart) + vec3(0.0, 0.0, 1.0) * sin(3.1416 * sHeart) * 0.4;

  // vortex back home: spiral in, outer particles last
  vec3 back = rotY((1.0 - sBack) * 4.0) * mix(pos * (1.0 - 0.5 * sBack), aHome, sBack * sBack);
  pos = mix(pos, back, sBack);

  vec4 mv = modelViewMatrix * vec4(pos, 1.0);
  gl_Position = projectionMatrix * mv;
  gl_PointSize = uSize * uPx * (0.5 + aRnd.z) / -mv.z;

  vec3 knotCol = (0.5 + 0.5 * cos(6.2832 * (u / 6.2832 * 2.0 + vec3(0.0, 0.33, 0.67)))) * 0.6;
  vec3 heartCol = mix(vec3(1.0, 0.22, 0.55), vec3(1.0, 0.78, 0.92), aRnd.z * 0.6) * 0.55;
  vec3 col = mix(aCol, knotCol, sKnot);
  col = mix(col, heartCol, sHeart);
  col = mix(col, aCol, sBack);
  vCol = col;
  vA = smoothstep(0.0, 0.06, sOut) * (1.0 - smoothstep(0.8, 1.0, sBack)) * (0.75 + 0.25 * sin(uT * 4.0 + aRnd.w * 80.0));
}
