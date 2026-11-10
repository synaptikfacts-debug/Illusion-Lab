import { useFrame, useThree } from "@react-three/fiber";
import { ThreeCanvas } from "@remotion/three";
import React, { useMemo } from "react";
import { useVideoConfig } from "remotion";
import * as THREE from "three";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { BokehPass } from "three/examples/jsm/postprocessing/BokehPass.js";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { OutputPass } from "three/examples/jsm/postprocessing/OutputPass.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { ShaderPass } from "three/examples/jsm/postprocessing/ShaderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { Reflector } from "three/examples/jsm/objects/Reflector.js";
import { angleAt, PD, pivotX, pivotY, SYNC_AT } from "./pendulum";

const TRAIL = 7; // light-trail samples per sphere
const TRAIL_DT = 0.03; // seconds between samples
const MOTES = 700;

/** Soft volumetric light beam (additive cone, brightest at the top, fading down and at the edges). */
const BEAM_FRAG = `varying vec2 vUv; uniform vec3 uColor; uniform float uStrength;
  void main(){ float edge = sin(vUv.x * 3.14159); float fall = pow(vUv.y, 1.6);
  gl_FragColor = vec4(uColor * edge * edge * fall * uStrength, 1.0); }`;
const BEAM_VERT = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`;

/** Camera [t, x, y, z, lookX, lookY]: a 3/4 view down the rows (so each tier reads as a snake/helix), slowly
 *  swinging round toward the front, end-on for the sync line-up, easing back as they hang still. */
const CAM: number[][] = [
  [0, -4.6, 6.0, 4.2, 0.4, -0.5],
  [9, -3.4, 6.6, 4.8, 0.2, -0.5],
  [18, -5.2, 5.8, 3.6, 0.5, -0.5],
  [SYNC_AT, -6.4, 5.2, 3.0, 0.7, -0.5],
  [30, -7.2, 6.2, 3.8, 0.5, -0.5],
];

function camAt(t: number) {
  let j = 0;
  while (j < CAM.length - 2 && t > CAM[j + 1][0]) j++;
  const a = CAM[j], b = CAM[j + 1];
  const x = Math.min(1, Math.max(0, (t - a[0]) / (b[0] - a[0])));
  const s = x * x * (3 - 2 * x);
  return a.slice(1).map((v, i) => v + (b[i + 1] - v) * s);
}

const POST = {
  uniforms: { tDiffuse: { value: null }, uFade: { value: 1 } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `uniform sampler2D tDiffuse; uniform float uFade; varying vec2 vUv;
    void main(){ vec4 c = texture2D(tDiffuse, vUv); vec2 d = (vUv - 0.5) * vec2(1.0, 1.25);
    c.rgb *= 1.0 - 0.4 * smoothstep(0.3, 0.9, length(d));
    float e = smoothstep(0.0, 1.0, uFade * 1.6 - length(d) * 0.9);
    c.rgb *= mix(uFade * uFade, 1.0, e * uFade); gl_FragColor = c; }`,
};

const M = new THREE.Matrix4(), Q = new THREE.Quaternion(), P = new THREE.Vector3(), S = new THREE.Vector3(), X = new THREE.Vector3(1, 0, 0);
const N = PD.tiers * PD.cols;

const Contents: React.FC<{ t: number; dpr: number; zoom: number }> = ({ t, dpr, zoom }) => {
  const { gl, scene, camera, size } = useThree();

  useMemo(() => {
    const pmrem = new THREE.PMREMGenerator(gl);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.03).texture;
    scene.environmentIntensity = 0.45;
    const c = document.createElement("canvas");
    c.width = 4; c.height = 512;
    const g = c.getContext("2d")!;
    const gr = g.createLinearGradient(0, 0, 0, 512);
    gr.addColorStop(0, "#0b0c11"); gr.addColorStop(0.55, "#14151c"); gr.addColorStop(1, "#08080b");
    g.fillStyle = gr; g.fillRect(0, 0, 4, 512);
    const tex = new THREE.CanvasTexture(c);
    tex.colorSpace = THREE.SRGBColorSpace;
    scene.background = tex;
    scene.fog = new THREE.Fog("#101117", 12, 26);
    pmrem.dispose();
    gl.toneMapping = THREE.ACESFilmicToneMapping;
    gl.toneMappingExposure = 0.95;
  }, [gl, scene]);

  const parts = useMemo(() => {
    const bobs = new THREE.InstancedMesh(
      new THREE.SphereGeometry(PD.bob, 32, 24),
      new THREE.MeshPhysicalMaterial({ roughness: 0.12, metalness: 0.15, clearcoat: 1, clearcoatRoughness: 0.05 }),
      N,
    );
    bobs.castShadow = true;
    bobs.frustumCulled = false;
    const threadGeo = new THREE.CylinderGeometry(0.004, 0.004, 1, 6);
    threadGeo.translate(0, -0.5, 0); // hangs down from the pivot
    const threads = new THREE.InstancedMesh(threadGeo, new THREE.MeshStandardMaterial({ color: "#8a8f9c", roughness: 0.4, metalness: 0.6 }), N);
    threads.frustumCulled = false;
    // calm colour drift along each row: moonlight blue -> soft teal -> warm amber; each tier a touch different
    const stops = [new THREE.Color("#7fa6ff"), new THREE.Color("#5fd1c4"), new THREE.Color("#ffc27a")];
    const col = new THREE.Color();
    for (let j = 0; j < PD.tiers; j++)
      for (let k = 0; k < PD.cols; k++) {
        const x = Math.min(0.999, k / (PD.cols - 1) * 0.85 + j * 0.03);
        const f = x * (stops.length - 1), i = Math.floor(f);
        col.copy(stops[i]).lerp(stops[i + 1], f - i);
        bobs.setColorAt(j * PD.cols + k, col);
      }
    bobs.instanceColor!.needsUpdate = true;
    const add = () => new THREE.MeshBasicMaterial({ blending: THREE.AdditiveBlending, transparent: true, depthWrite: false, toneMapped: false });
    // light trails: fading, shrinking ghost copies along each sphere's recent path
    const trails = new THREE.InstancedMesh(new THREE.SphereGeometry(PD.bob * 0.7, 12, 8), add(), N * TRAIL);
    trails.frustumCulled = false;
    // glow shells that brighten as a sphere sweeps through the bottom of its swing
    const glows = new THREE.InstancedMesh(new THREE.SphereGeometry(PD.bob * 1.25, 16, 12), add(), N);
    glows.frustumCulled = false;
    const base: THREE.Color[] = [];
    for (let i = 0; i < N; i++) { const c0 = new THREE.Color(); bobs.getColorAt(i, c0); base.push(c0); }
    trails.setColorAt(0, col.setRGB(0, 0, 0));
    glows.setColorAt(0, col.setRGB(0, 0, 0));
    // dust motes drifting slowly through the light
    const r = (n: number) => { const x = Math.sin(n * 127.1) * 43758.5453; return x - Math.floor(x); };
    const mp = new Float32Array(MOTES * 3), mphase = new Float32Array(MOTES);
    for (let m = 0; m < MOTES; m++) {
      mp[m * 3] = (r(m) - 0.5) * 11; mp[m * 3 + 1] = (r(m + 99) - 0.5) * 8; mp[m * 3 + 2] = (r(m + 199) - 0.5) * 6;
      mphase[m] = r(m + 299) * 6.28;
    }
    const moteGeo = new THREE.BufferGeometry();
    moteGeo.setAttribute("position", new THREE.BufferAttribute(mp.slice(), 3));
    const motes = new THREE.Points(moteGeo, new THREE.PointsMaterial({ color: "#ffe6c4", size: 0.018, transparent: true, opacity: 0.55, blending: THREE.AdditiveBlending, depthWrite: false }));
    motes.frustumCulled = false;
    // soft light beams from above
    const beamMat = (c: string, k: number) => new THREE.ShaderMaterial({ vertexShader: BEAM_VERT, fragmentShader: BEAM_FRAG, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, uniforms: { uColor: { value: new THREE.Color(c) }, uStrength: { value: k } } });
    const beams = [
      new THREE.Mesh(new THREE.ConeGeometry(2.6, 10, 48, 1, true), beamMat("#ffd9a8", 0.05)),
      new THREE.Mesh(new THREE.ConeGeometry(2.0, 10, 48, 1, true), beamMat("#9fbcff", 0.04)),
    ];
    beams[0].position.set(-1.4, 1.2, -0.3); beams[0].rotation.z = 0.12;
    beams[1].position.set(2.2, 1.2, -0.8); beams[1].rotation.z = -0.1;
    beams.forEach((b) => (b.frustumCulled = false));
    // dark glossy mirror floor
    const floorY = pivotY(PD.tiers - 1) - PD.L - 0.55;
    const mirror = new Reflector(new THREE.PlaneGeometry(30, 30), { textureWidth: 1024, textureHeight: 1024, color: new THREE.Color("#2a2c36") });
    mirror.rotation.x = -Math.PI / 2;
    mirror.position.y = floorY;
    return { bobs, threads, trails, glows, base, motes, mp, mphase, beams, mirror, floorY };
  }, []);

  const composer = useMemo(() => {
    const w = size.width, h = size.height;
    const c = new EffectComposer(gl);
    c.setPixelRatio(dpr);
    c.setSize(w, h);
    c.addPass(new RenderPass(scene, camera));
    const bokeh = new BokehPass(scene, camera, { focus: 8, aperture: 0.001, maxblur: 0.008 });
    c.addPass(bokeh);
    c.addPass(new UnrealBloomPass(new THREE.Vector2(w * dpr, h * dpr), 0.12, 0.4, 1.6));
    c.addPass(new OutputPass());
    const post = new ShaderPass(POST);
    c.addPass(post);
    return { c, bokeh, post };
  }, [gl, scene, camera, size.width, size.height, dpr]);

  for (let j = 0; j < PD.tiers; j++)
    for (let k = 0; k < PD.cols; k++) {
      const i = j * PD.cols + k, th = angleAt(j, k, t), px = pivotX(k), py = pivotY(j);
      Q.setFromAxisAngle(X, th);
      M.compose(P.set(px, py, 0), Q, S.set(1, PD.L, 1));
      parts.threads.setMatrixAt(i, M);
      M.compose(P.set(px, py - PD.L * Math.cos(th), PD.L * Math.sin(th)), Q.identity(), S.set(1, 1, 1));
      parts.bobs.setMatrixAt(i, M);
    }
  parts.bobs.instanceMatrix.needsUpdate = true;
  parts.threads.instanceMatrix.needsUpdate = true;
  // trails + glow
  const C2 = new THREE.Color();
  for (let j = 0; j < PD.tiers; j++)
    for (let k = 0; k < PD.cols; k++) {
      const i = j * PD.cols + k, px = pivotX(k), py = pivotY(j), amp = Math.abs(PD.theta) + 1e-6;
      const th0 = angleAt(j, k, t);
      const glow = Math.exp(-((th0 / amp) ** 2) * 6) * (Math.min(1, Math.abs(angleAt(j, k, t) - angleAt(j, k, t - 0.03)) / 0.02));
      M.compose(P.set(px, py - PD.L * Math.cos(th0), PD.L * Math.sin(th0)), Q.identity(), S.set(1, 1, 1));
      parts.glows.setMatrixAt(i, M);
      parts.glows.setColorAt(i, C2.copy(parts.base[i]).multiplyScalar(0.35 * glow));
      for (let s2 = 1; s2 <= TRAIL; s2++) {
        const th = angleAt(j, k, t - s2 * TRAIL_DT), f = 1 - s2 / (TRAIL + 1);
        M.compose(P.set(px, py - PD.L * Math.cos(th), PD.L * Math.sin(th)), Q.identity(), S.setScalar(0.4 + 0.6 * f));
        const ti = i * TRAIL + s2 - 1;
        parts.trails.setMatrixAt(ti, M);
        parts.trails.setColorAt(ti, C2.copy(parts.base[i]).multiplyScalar(0.13 * f * f));
      }
    }
  for (const m of [parts.trails, parts.glows]) { m.instanceMatrix.needsUpdate = true; m.instanceColor!.needsUpdate = true; }
  // motes drift slowly
  const pos = (parts.motes.geometry.getAttribute("position") as THREE.BufferAttribute).array as Float32Array;
  for (let m = 0; m < MOTES; m++) {
    const ph = parts.mphase[m];
    pos[m * 3] = parts.mp[m * 3] + 0.25 * Math.sin(t * 0.21 + ph);
    pos[m * 3 + 1] = parts.mp[m * 3 + 1] + 0.18 * Math.sin(t * 0.17 + ph * 1.7) + 0.03 * t;
    pos[m * 3 + 2] = parts.mp[m * 3 + 2] + 0.2 * Math.cos(t * 0.19 + ph);
  }
  parts.motes.geometry.getAttribute("position").needsUpdate = true;

  const [cx, cy, cz, lx, ly] = camAt(t);
  camera.position.set(lx + (cx - lx) * zoom, ly + (cy - ly) * zoom, cz * zoom);
  camera.lookAt(lx, ly, 0);
  camera.updateMatrixWorld();
  const b = composer.bokeh.uniforms as Record<string, THREE.IUniform>;
  b.focus.value = camera.position.distanceTo(new THREE.Vector3(lx, ly, 0));
  b.aperture.value = 0.0024 / Math.max(1, b.focus.value * 0.6);
  const fx = Math.min(1, Math.max(0, (t - PD.fade[0]) / (PD.fade[1] - PD.fade[0])));
  composer.post.uniforms.uFade.value = 1 - fx * fx * (3 - 2 * fx);
  // render twice so the mirror floor has its reflection ready on the very first frame of each page
  useFrame(() => { composer.c.render(); composer.c.render(); }, 1);

  const len = PD.cols * PD.spacing + 0.5;
  return (
    <>
      <hemisphereLight args={["#c9d2ff", "#0b0b10", 0.25]} />
      <directionalLight position={[-3, 8, 5]} intensity={2.0} color="#fff1e0" castShadow shadow-mapSize={[2048, 2048]} shadow-camera-left={-6} shadow-camera-right={6} shadow-camera-top={6} shadow-camera-bottom={-6} />
      <pointLight position={[6, 1, -4]} intensity={10} color="#5f8cff" />
      <primitive object={parts.threads} />
      <primitive object={parts.bobs} />
      <primitive object={parts.trails} />
      <primitive object={parts.glows} />
      <primitive object={parts.motes} />
      <primitive object={parts.mirror} />
      {/* a dark brushed-metal bar for every tier */}
      {Array.from({ length: PD.tiers }, (_, j) => (
        <mesh key={j} position={[0, pivotY(j) + 0.02, 0]} rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.03, 0.03, len, 16]} />
          <meshStandardMaterial color="#3a3d47" metalness={0.9} roughness={0.35} />
        </mesh>
      ))}
    </>
  );
};

export const PendulumScene: React.FC<{ t: number; dpr?: number; zoom?: number }> = ({ dpr = 2, zoom = 1, ...props }) => {
  const { width, height } = useVideoConfig();
  return (
    <ThreeCanvas width={width} height={height} dpr={dpr} shadows="soft" gl={{ antialias: true, preserveDrawingBuffer: true, powerPreference: "high-performance" }} camera={{ fov: 36, near: 0.1, far: 80, position: [-7, 2, 6] }}>
      <Contents {...props} dpr={dpr} zoom={zoom} />
    </ThreeCanvas>
  );
};
