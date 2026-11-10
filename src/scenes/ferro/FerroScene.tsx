import { useFrame, useThree } from "@react-three/fiber";
import { ThreeCanvas } from "@remotion/three";
import React, { useMemo } from "react";
import { useVideoConfig } from "remotion";
import * as THREE from "three";
import { BokehPass } from "three/examples/jsm/postprocessing/BokehPass.js";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { OutputPass } from "three/examples/jsm/postprocessing/OutputPass.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { ShaderPass } from "three/examples/jsm/postprocessing/ShaderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { controls, FERRO_GLSL, FSTORY } from "./ferro";

/** Camera [t, px, py, pz, lx, ly, lz]: low and close on the spike ring (hook), rise over the growing field,
 *  top-down for the turning bloom, down to grazing for the crown, low for the melt and the calm mirror. */
const CAM: number[][] = [
  [0.0, 0.0, 0.85, 2.5, 0, 0.08, 0],
  [4.0, 0.7, 1.25, 3.0, 0, 0.05, 0],
  [8.0, -1.6, 1.6, 3.4, 0, 0, 0],
  [12.0, 1.2, 2.8, 2.6, 0, 0, 0],
  [15.5, 0.3, 4.3, 1.4, 0, 0, 0],
  [19.0, -0.5, 3.9, 1.7, 0, 0, 0],
  [21.4, 0.2, 0.9, 2.6, 0, 0.1, 0],
  [25.0, 0.0, 1.4, 4.2, 0, 0, 0],
  [30.0, 0.0, 2.0, 5.6, 0, 0, 0],
];

function camAt(t: number) {
  let j = 0;
  while (j < CAM.length - 2 && t > CAM[j + 1][0]) j++;
  const k0 = CAM[Math.max(0, j - 1)], k1 = CAM[j], k2 = CAM[j + 1], k3 = CAM[Math.min(CAM.length - 1, j + 2)];
  const x = Math.min(1, Math.max(0, (t - k1[0]) / (k2[0] - k1[0])));
  const s = x * x * (3 - 2 * x);
  const out: number[] = [];
  for (let c = 1; c <= 6; c++) {
    const p0 = k0[c], p1 = k1[c], p2 = k2[c], p3 = k3[c];
    out.push(0.5 * (2 * p1 + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s * s + (-p0 + 3 * p1 - 3 * p2 + p3) * s * s * s));
  }
  return out;
}

const VERT = /* glsl */ `
${FERRO_GLSL}
varying vec3 vWorld;
void main() {
  vec3 p = position;
  p.y = height(p.xz);
  vec4 w = modelMatrix * vec4(p, 1.0);
  vWorld = w.xyz;
  gl_Position = projectionMatrix * viewMatrix * w;
}`;

// Jet-black mirror liquid lit by a studio of teal and electric-violet softboxes plus thin white ring lights overhead
// (the ring lights draw crisp concentric highlights on every spike).
const FRAG = /* glsl */ `
${FERRO_GLSL}
uniform vec3 uCam;
varying vec3 vWorld;
vec3 envOld(vec3 R) {
  float el = R.y, az = atan(R.x, -R.z);
  vec3 c = mix(vec3(0.001, 0.001, 0.003), vec3(0.008, 0.008, 0.016), smoothstep(-0.05, 0.6, el));
  float band = smoothstep(0.03, 0.1, el) * smoothstep(0.5, 0.36, el);
  c += vec3(0.2, 2.4, 2.2) * band * smoothstep(0.45, 0.22, abs(az - 0.7));   // teal softbox
  c += vec3(1.7, 0.5, 3.4) * band * smoothstep(0.5, 0.28, abs(az + 1.2));    // electric violet softbox
  c += vec3(0.5, 0.32, 1.0) * band * smoothstep(0.9, 0.5, abs(abs(az) - 3.14159)); // soft panel behind the camera
  // soft coloured dome overhead: teal on one side, violet on the other, so spikes catch colour from any angle
  c += mix(vec3(0.05, 0.3, 0.32), vec3(0.28, 0.1, 0.42), 0.5 + 0.5 * sin(az * 2.0)) * smoothstep(0.3, 0.55, el) * smoothstep(1.0, 0.75, el);
  c += vec3(2.6, 2.5, 2.4) * smoothstep(0.010, 0.0, abs(el - 0.62)) * 0.9;   // ring lights
  c += vec3(2.0, 2.2, 2.6) * smoothstep(0.008, 0.0, abs(el - 0.78)) * 0.8;
  c += vec3(1.2, 2.4, 2.4) * smoothstep(0.006, 0.0, abs(el - 0.9)) * 0.6;
  c += vec3(0.5, 0.9, 1.4) * smoothstep(0.06, 0.0, abs(el - 0.04)) * 0.08;    // faint horizon glow
  // below the horizon: the glowing pool itself (violet/teal bounce), so downward-facing spike sides are never dead black
  c += mix(vec3(0.16, 0.42, 0.44), vec3(0.42, 0.18, 0.62), 0.5 + 0.5 * sin(az * 1.5)) * smoothstep(0.02, -0.35, el) * 0.38;
  return c;
}
// one neon ring, anti-aliased: widened by the pixel footprint (fw) with its energy kept, so it never shimmers
float ring(float el, float c, float w, float fw) {
  float ww = w + fw;
  return smoothstep(ww, 0.0, abs(el - c)) * (w / ww);
}
vec3 env(vec3 R, float fw) {
  float el = R.y, az = atan(R.x, -R.z);
  vec3 c = vec3(0.002, 0.002, 0.005);
  float lo = 1.0;
  // below the horizon: a soft, blurred reflection of the rings in the pool (never a sharp contour soup)
  if (el < 0.0) { el = -el * 1.6; fw += 0.05; lo = 0.22; }
  c += vec3(3.4, 0.25, 1.6) * ring(el, 0.10, 0.012, fw) * 0.9;   // hot magenta
  c += vec3(0.2, 2.8, 3.2) * ring(el, 0.19, 0.012, fw) * 0.9;    // cyan
  c += vec3(1.6, 0.5, 3.6) * ring(el, 0.29, 0.012, fw) * 0.9;    // violet
  c += vec3(3.4, 1.4, 0.3) * ring(el, 0.40, 0.010, fw) * 0.8;    // amber
  c += vec3(3.0, 0.5, 2.0) * ring(el, 0.53, 0.009, fw) * 0.6;    // rose
  c += vec3(0.3, 2.6, 2.4) * ring(el, 0.67, 0.010, fw) * 0.7;    // teal
  c += vec3(3.0, 0.4, 2.2) * ring(el, 0.82, 0.010, fw) * 0.6;    // pink
  c += vec3(2.6, 2.6, 2.6) * ring(el, 0.93, 0.006, fw) * 0.5;    // white crown ring
  // a few vertical neon strips around the room (above the horizon only)
  float sw = 0.02 + fw * 3.0;
  float strips = smoothstep(sw, 0.0, abs(sin(az * 3.0 + 0.6))) * (0.02 / sw) * smoothstep(0.0, 0.08, el) * smoothstep(0.6, 0.3, el);
  c += mix(vec3(0.3, 2.4, 2.8), vec3(2.8, 0.4, 2.2), 0.5 + 0.5 * sin(az)) * strips * 0.55 * step(0.0, R.y);
  c *= lo;
  // a faint coloured glow so nothing is dead black
  c += mix(vec3(0.03, 0.10, 0.12), vec3(0.10, 0.03, 0.14), 0.5 + 0.5 * sin(az * 2.0)) * smoothstep(0.0, 0.6, R.y) * 0.6;
  return c;
}
void main() {
  vec2 p = vWorld.xz;
  float e = 0.0025;
  float h0 = height(p);
  vec3 n = normalize(vec3(-(height(p + vec2(e, 0.0)) - h0) / e, 1.0, -(height(p + vec2(0.0, e)) - h0) / e));
  vec3 V = normalize(vWorld - uCam);
  vec3 R = reflect(V, n);
  float cosv = max(dot(-V, n), 0.0);
  float fres = 0.04 + 0.96 * pow(1.0 - cosv, 5.0);
  float fw = min(0.08, fwidth(R.y) * 1.2); // how much the reflection changes across one pixel
  vec3 col = env(R, fw) * (0.3 + 0.7 * fres) * 1.1;
  // sharp glints from two small key lights: crisp highlight lines down every spike
  vec3 L1 = normalize(vec3(0.6, 0.55, 0.6)), L2 = normalize(vec3(-0.7, 0.45, 0.3));
  col += vec3(0.4, 2.2, 2.0) * pow(max(dot(R, L1), 0.0), 180.0 / (1.0 + fw * 60.0));
  col += vec3(1.8, 0.6, 2.8) * pow(max(dot(R, L2), 0.0), 180.0 / (1.0 + fw * 60.0));
  col += vec3(0.004, 0.005, 0.009);
  float d = length(vWorld - uCam);
  col *= exp(-max(0.0, d - 6.0) * 0.08);
  gl_FragColor = vec4(col, 1.0);
}`;

const POST = {
  uniforms: { tDiffuse: { value: null }, uFade: { value: 1 } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `uniform sampler2D tDiffuse; uniform float uFade; varying vec2 vUv;
    void main(){ vec4 c = texture2D(tDiffuse, vUv); vec2 d = (vUv - 0.5) * vec2(1.0, 1.25);
    c.rgb *= 1.0 - 0.4 * smoothstep(0.3, 0.9, length(d));
    float e = smoothstep(0.0, 1.0, uFade * 1.6 - length(d) * 0.9);
    c.rgb *= mix(uFade * uFade, 1.0, e * uFade); gl_FragColor = c; }`,
};

const Contents: React.FC<{ t: number; dpr: number; zoom: number }> = ({ t, dpr, zoom }) => {
  const { gl, scene, camera, size } = useThree();

  const mats = useMemo(() => {
    scene.background = new THREE.Color("#020205");
    gl.toneMapping = THREE.ACESFilmicToneMapping;
    gl.toneMappingExposure = 1.0;
    const mat = new THREE.ShaderMaterial({
      vertexShader: VERT,
      fragmentShader: FRAG,
      uniforms: {
        uT: { value: 0 }, uSwirl: { value: 0 }, uSpin: { value: 0 }, uGrow: { value: 0 }, uBloom: { value: 0 }, uCrown: { value: 0 }, uOn: { value: 1 }, uRot: { value: 0 }, uMelt: { value: -1 },
        uPulse: { value: FSTORY.pulses.map(() => new THREE.Vector3()) },
        uMag: { value: new THREE.Vector2() },
        uMagOn: { value: 1 },
        uCam: { value: new THREE.Vector3() },
      },
    });
    // fine mesh where the spikes are, coarse mesh out to the horizon
    const inner = new THREE.PlaneGeometry(6, 6, 1000, 1000);
    inner.rotateX(-Math.PI / 2);
    const mesh = new THREE.Mesh(inner, mat);
    mesh.frustumCulled = false;
    const far = new THREE.PlaneGeometry(200, 200, 200, 200);
    far.rotateX(-Math.PI / 2);
    const fm = new THREE.Mesh(far, mat);
    fm.position.y = -0.003;
    fm.frustumCulled = false;
    mesh.add(fm);
    return { mat, mesh };
  }, [gl, scene]);

  const composer = useMemo(() => {
    const w = size.width, h = size.height;
    const c = new EffectComposer(gl);
    c.setPixelRatio(dpr);
    c.setSize(w, h);
    c.addPass(new RenderPass(scene, camera));
    const bokeh = new BokehPass(scene, camera, { focus: 3, aperture: 0.002, maxblur: 0.01 });
    c.addPass(bokeh);
    c.addPass(new UnrealBloomPass(new THREE.Vector2(w * dpr, h * dpr), 0.45, 0.4, 1.1));
    c.addPass(new OutputPass());
    const post = new ShaderPass(POST);
    c.addPass(post);
    return { c, bokeh, post };
  }, [gl, scene, camera, size.width, size.height, dpr]);

  let [cx, cy, cz, lx, ly, lz] = camAt(t);
  {
    const [mx, mz] = controls(t).mag;
    const w = 0; // steady camera (no chase)
    cx += mx * w; lx += mx * w; cz += mz * w; lz += mz * w;
  }
  camera.position.set(lx + (cx - lx) * zoom, ly + (cy - ly) * zoom, lz + (cz - lz) * zoom);
  camera.lookAt(lx, ly, lz);
  camera.updateMatrixWorld();
  const u = mats.mat.uniforms, k = controls(t);
  void FSTORY;
  u.uT.value = t; u.uSwirl.value = k.swirl; u.uSpin.value = k.spin; u.uGrow.value = k.grow; u.uBloom.value = k.bloom; u.uCrown.value = k.crown; u.uOn.value = k.on; u.uRot.value = k.rot; u.uMelt.value = k.melt;
  u.uCam.value.copy(camera.position);
  u.uMag.value.set(k.mag[0], k.mag[1]);
  u.uMagOn.value = k.magOn;
  (u.uPulse.value as THREE.Vector3[]).forEach((v, i) => v.set(k.pulses[i * 3], k.pulses[i * 3 + 1], k.pulses[i * 3 + 2]));
  const b = composer.bokeh.uniforms as Record<string, THREE.IUniform>;
  b.focus.value = camera.position.distanceTo(new THREE.Vector3(lx, ly, lz));
  b.aperture.value = 0.003 / Math.max(1, b.focus.value * 0.55);
  const fx = Math.min(1, Math.max(0, (t - FSTORY.fade[0]) / (FSTORY.fade[1] - FSTORY.fade[0])));
  composer.post.uniforms.uFade.value = 1 - fx * fx * (3 - 2 * fx);
  useFrame(() => composer.c.render(), 1);
  return <primitive object={mats.mesh} />;
};

export const FerroScene: React.FC<{ t: number; dpr?: number; zoom?: number }> = ({ dpr = 2, zoom = 1, ...props }) => {
  const { width, height } = useVideoConfig();
  return (
    <ThreeCanvas width={width} height={height} dpr={dpr} gl={{ antialias: true, preserveDrawingBuffer: true, powerPreference: "high-performance" }} camera={{ fov: 34, near: 0.03, far: 80, position: [0, 1, 3] }}>
      <Contents {...props} dpr={dpr} zoom={zoom} />
    </ThreeCanvas>
  );
};
