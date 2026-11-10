// GPU particle shader shared by scenes. Each particle is a closed-form path of time: p0 + v*age + gravity + wobble.
// Attributes: aP (start), aV (velocity), aT (t0, life, gravity, wobble), aC (colour), aS (size, world units).
import * as THREE from "three";

export interface ParticleData {
  count: number;
  p: Float32Array;
  v: Float32Array;
  t: Float32Array;
  c: Float32Array;
  s: Float32Array;
}

export const PVERT = `
attribute vec3 aP; attribute vec3 aV; attribute vec4 aT; attribute vec3 aC; attribute float aS;
uniform float uT; uniform float uPx;
varying vec3 vC; varying float vA;
void main() {
  float age = uT - aT.x;
  if (age < 0.0 || age > aT.y) { gl_Position = vec4(2.0, 2.0, 2.0, 1.0); gl_PointSize = 0.0; vA = 0.0; return; }
  vec3 p = aP + aV * age + vec3(0.0, 0.5 * aT.z * age * age, 0.0);
  p += aT.w * vec3(sin(age * 2.3 + aP.x * 7.0), 0.0, cos(age * 1.9 + aP.z * 5.0)) * age * 0.12;
  p.y = max(p.y, 0.005);
  vec4 mv = modelViewMatrix * vec4(p, 1.0);
  gl_Position = projectionMatrix * mv;
  gl_PointSize = aS * uPx / -mv.z;
  float k = age / aT.y;
  vA = smoothstep(0.0, 0.06, k) * (1.0 - smoothstep(0.5, 1.0, k));
  vC = aC;
}`;

export const PFRAG = `
varying vec3 vC; varying float vA;
void main() {
  vec2 c = gl_PointCoord - 0.5;
  float a = exp(-dot(c, c) * 14.0) * vA;
  if (a < 0.01) discard;
  gl_FragColor = vec4(vC * a, a);
}`;

export function makeParticlePoints(d: ParticleData, pxPerUnit: number): THREE.Points {
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(d.p, 3));
  g.setAttribute("aP", new THREE.BufferAttribute(d.p, 3));
  g.setAttribute("aV", new THREE.BufferAttribute(d.v, 3));
  g.setAttribute("aT", new THREE.BufferAttribute(d.t, 4));
  g.setAttribute("aC", new THREE.BufferAttribute(d.c, 3));
  g.setAttribute("aS", new THREE.BufferAttribute(d.s, 1));
  g.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 50);
  const m = new THREE.ShaderMaterial({
    vertexShader: PVERT,
    fragmentShader: PFRAG,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
    uniforms: { uT: { value: 0 }, uPx: { value: pxPerUnit } },
  });
  const p = new THREE.Points(g, m);
  p.frustumCulled = false;
  return p;
}
