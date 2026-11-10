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
import { controls, type Drop, LSTORY, WAVES_GLSL } from "./waves";

/** Camera keys [t, px, py, pz, lx, ly, lz]. Low and close on the hook crater; orbit the interference; above the
 *  star and down into the vortex; grazing for the collapse ring and the calm mirror; ease away. */
const CAM: number[][] = [
  [0.0, 0.0, 0.8, 3.0, 0, -0.08, 0],
  [1.4, 0.6, 1.4, 4.6, 0, 0, 0],
  [4.0, 2.8, 2.0, 5.0, 0, 0, 0],
  [7.0, -3.0, 1.7, 4.6, 0, 0, 0],
  [10.8, 0, 3.2, 5.4, 0, 0, 0],
  [12.6, 0, 7.4, 2.2, 0, 0, 0],
  [15.2, 0.6, 7.6, 1.6, 0, 0, 0],
  [17.8, 0, 6.0, 0.9, 0, 0, 0],
  [21.0, 0, 4.6, 0.7, 0, -0.1, 0],
  [22.3, 0.2, 2.1, 4.3, 0, 0.15, 0],
  [24.6, 1.5, 1.15, 5.6, 0, 0, 0],
  [27.2, 2.0, 1.5, 7.0, 0, 0, 0],
  [30.0, 2.2, 2.1, 8.4, 0, 0, 0],
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
${WAVES_GLSL}
varying vec3 vWorld;
void main() {
  vec3 p = position;
  p.y = height(p.xz);
  vec4 w = modelMatrix * vec4(p, 1.0);
  vWorld = w.xyz;
  gl_Position = projectionMatrix * viewMatrix * w;
}`;

// Obsidian liquid: black base, Fresnel reflections of a neon studio (hot pink, violet, warm white, a touch of orange).
const FRAG = /* glsl */ `
${WAVES_GLSL}
uniform vec3 uCam;
varying vec3 vWorld;
vec3 env(vec3 R) {
  float el = R.y, az = atan(R.x, -R.z);
  vec3 c = mix(vec3(0.004, 0.002, 0.01), vec3(0.05, 0.02, 0.09), smoothstep(-0.05, 0.5, el));
  float band = smoothstep(0.02, 0.08, el) * smoothstep(0.42, 0.3, el);
  c += vec3(3.2, 0.28, 1.5) * band * smoothstep(0.42, 0.22, abs(az - 0.55));   // hot pink softbox
  c += vec3(0.9, 0.45, 3.2) * band * smoothstep(0.5, 0.28, abs(az + 1.05));    // violet softbox
  c += vec3(3.0, 1.1, 0.3) * band * smoothstep(0.16, 0.06, abs(az - 2.35));    // small orange accent
  // ceiling: thin concentric neon rings (crisp coloured lines in top-down views)
  c += vec3(3.2, 0.35, 1.7) * smoothstep(0.012, 0.0, abs(el - 0.70)) * 0.9;
  c += vec3(1.0, 0.55, 3.4) * smoothstep(0.012, 0.0, abs(el - 0.80)) * 0.9;
  c += vec3(2.8, 2.5, 2.3) * smoothstep(0.008, 0.0, abs(el - 0.89)) * 0.8;
  c += vec3(3.0, 0.9, 0.35) * smoothstep(0.006, 0.0, abs(el - 0.95)) * 0.7;
  c += vec3(1.4, 0.5, 1.6) * smoothstep(0.12, 0.0, abs(el - 0.06)) * 0.35;     // horizon glow
  return c;
}
void main() {
  vec2 p = vWorld.xz;
  float e = 0.006;
  float h0 = height(p);
  vec3 n = normalize(vec3(-(height(p + vec2(e, 0.0)) - h0) / e, 1.0, -(height(p + vec2(0.0, e)) - h0) / e));
  vec3 V = normalize(vWorld - uCam);
  vec3 R = reflect(V, n);
  float cosv = max(dot(-V, n), 0.0);
  float fres = 0.035 + 0.965 * pow(1.0 - cosv, 5.0);
  vec3 col = env(R) * (0.25 + 0.75 * fres) * 1.15;
  col += vec3(0.012, 0.008, 0.02);                       // obsidian body
  col += vec3(0.5, 0.15, 0.6) * smoothstep(-0.05, -0.35, h0) * 0.12;  // faint violet in deep troughs
  float d = length(vWorld - uCam);
  col *= exp(-max(0.0, d - 7.0) * 0.07);                 // fall off into darkness
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

const Contents: React.FC<{ drops: Drop[]; t: number; dpr: number; zoom: number }> = ({ drops, t, dpr, zoom }) => {
  const { gl, scene, camera, size } = useThree();

  const mesh = useMemo(() => {
    scene.background = new THREE.Color("#020104");
    gl.toneMapping = THREE.ACESFilmicToneMapping;
    gl.toneMappingExposure = 1.0;
    const geo = new THREE.PlaneGeometry(26, 26, 700, 700);
    geo.rotateX(-Math.PI / 2);
    const mat = new THREE.ShaderMaterial({
      vertexShader: VERT,
      fragmentShader: FRAG,
      uniforms: {
        uDrops: { value: drops.map((d) => new THREE.Vector4(d.x, d.z, d.t, d.a)) },
        uT: { value: 0 }, uStand: { value: 0 }, uVort: { value: 0 }, uRot: { value: 0 }, uPulse: { value: 1 },
        uCam: { value: new THREE.Vector3() },
      },
    });
    const m = new THREE.Mesh(geo, mat);
    m.frustumCulled = false;
    // far surface (coarse, same shader) so the liquid reaches the horizon and fades into darkness
    const far = new THREE.PlaneGeometry(220, 220, 220, 220);
    far.rotateX(-Math.PI / 2);
    const fm = new THREE.Mesh(far, mat);
    fm.position.y = -0.004;
    fm.frustumCulled = false;
    m.add(fm);
    return m;
  }, [drops, gl, scene]);

  const composer = useMemo(() => {
    const w = size.width, h = size.height;
    const c = new EffectComposer(gl);
    c.setPixelRatio(dpr);
    c.setSize(w, h);
    c.addPass(new RenderPass(scene, camera));
    const bokeh = new BokehPass(scene, camera, { focus: 4, aperture: 0.002, maxblur: 0.01 });
    c.addPass(bokeh);
    c.addPass(new UnrealBloomPass(new THREE.Vector2(w * dpr, h * dpr), 0.7, 0.55, 0.85));
    c.addPass(new OutputPass());
    const post = new ShaderPass(POST);
    c.addPass(post);
    return { c, bokeh, post };
  }, [gl, scene, camera, size.width, size.height, dpr]);

  const [cx, cy, cz, lx, ly, lz] = camAt(t);
  camera.position.set(lx + (cx - lx) * zoom, ly + (cy - ly) * zoom, lz + (cz - lz) * zoom);
  camera.lookAt(lx, ly, lz);
  camera.updateMatrixWorld();
  const u = (mesh.material as THREE.ShaderMaterial).uniforms;
  const k = controls(t);
  u.uT.value = t; u.uStand.value = k.stand; u.uVort.value = k.vort; u.uRot.value = k.rot; u.uPulse.value = k.pulse;
  u.uCam.value.copy(camera.position);
  const focus = camera.position.distanceTo(new THREE.Vector3(lx, ly, lz));
  const b = composer.bokeh.uniforms as Record<string, THREE.IUniform>;
  b.focus.value = focus;
  b.aperture.value = 0.003 / Math.max(1, focus * 0.55);
  const fx = Math.min(1, Math.max(0, (t - LSTORY.fade[0]) / (LSTORY.fade[1] - LSTORY.fade[0])));
  composer.post.uniforms.uFade.value = 1 - fx * fx * (3 - 2 * fx);

  useFrame(() => composer.c.render(), 1);
  return <primitive object={mesh} />;
};

export const LiquidScene: React.FC<{ drops: Drop[]; t: number; dpr?: number; zoom?: number }> = ({ dpr = 2, zoom = 1, ...props }) => {
  const { width, height } = useVideoConfig();
  return (
    <ThreeCanvas width={width} height={height} dpr={dpr} gl={{ antialias: true, preserveDrawingBuffer: true, powerPreference: "high-performance" }} camera={{ fov: 34, near: 0.05, far: 80, position: [0, 2, 5] }}>
      <Contents {...props} dpr={dpr} zoom={zoom} />
    </ThreeCanvas>
  );
};
