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
import { DSTORY, type DominoSim } from "./sim";

export interface DominoLook {
  body: string;
  plate: string;
  background: string;
  key: string;
  rim: string;
}

/** Camera keys [t, px, py, pz, lx, ly, lz]: top-down hook, low macro tracking of the lane, rise, top-down, ease away. */
const CAM: number[][] = [
  [0.0, 0, 12.6, 1.1, 0, 0, -0.15],
  [0.6, 0, 11.8, 1.0, 0, 0, -0.15],
  [1.6, 0.3, 6.8, 7.4, 0, 0, 1.2],
  [2.2, 0.62, 0.7, 5.35, 0.05, 0.04, 3.45],
  [5.0, 0.62, 0.82, 1.25, 0.05, 0.04, -0.4],
  [6.2, 0.6, 2.8, 2.9, 0, 0, -0.2],
  [8.4, -1.4, 7.6, 5.6, 0, 0, -0.2],
  [11.4, 0, 13.4, 1.6, 0, 0, -0.15],
  [13.2, 0, 13.4, 1.6, 0, 0, -0.15],
  [15.8, 0, 12.0, 1.4, 0, 0, -0.15],
  [19.0, 0, 13.2, 1.6, 0, 0, -0.15],
  [24.5, 0, 16.6, 2.4, 0, 0, -0.1],
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

const POST = {
  uniforms: { tDiffuse: { value: null }, uAmount: { value: 0.45 }, uFade: { value: 1 } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `uniform sampler2D tDiffuse; uniform float uAmount; uniform float uFade; varying vec2 vUv;
    void main(){ vec4 c = texture2D(tDiffuse, vUv); vec2 d = (vUv - 0.5) * vec2(1.0, 1.25);
    c.rgb *= 1.0 - uAmount * smoothstep(0.25, 0.85, length(d));
    float e = smoothstep(0.0, 1.0, uFade * 1.6 - length(d) * 0.9);
    c.rgb *= mix(uFade * uFade, 1.0, e * uFade); gl_FragColor = c; }`,
};

const M = new THREE.Matrix4(), M2 = new THREE.Matrix4(), M3 = new THREE.Matrix4(), C = new THREE.Color();
const W = 0.085, H = 0.095, D = 0.026;

const Contents: React.FC<{ sim: DominoSim; frame: number; t: number; look: DominoLook; dpr: number; zoom: number; glowBoost: number }> = ({
  sim,
  frame,
  t,
  look,
  dpr,
  zoom,
  glowBoost,
}) => {
  const { gl, scene, camera, size } = useThree();
  const L = sim.layout;

  useMemo(() => {
    const pmrem = new THREE.PMREMGenerator(gl);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.03).texture;
    scene.environmentIntensity = 0.3;
    scene.background = new THREE.Color(look.background);
    scene.fog = new THREE.Fog(look.background, 26, 46);
    pmrem.dispose();
    gl.toneMapping = THREE.ACESFilmicToneMapping;
    gl.toneMappingExposure = 1.0;
  }, [gl, scene, look.background]);

  const meshes = useMemo(() => {
    const bodyGeo = new THREE.BoxGeometry(W, H, D);
    bodyGeo.translate(0, H / 2, 0);
    // face plate on the back (-z) face: it ends up on top once the domino falls forward (+z)
    const faceGeo = new THREE.BoxGeometry(W * 0.9, H * 0.9, 0.003);
    faceGeo.translate(0, H / 2, -D / 2 - 0.0016);
    const glowGeo = new THREE.PlaneGeometry(W * 0.92, H * 0.92);
    glowGeo.rotateY(Math.PI);
    glowGeo.translate(0, H / 2, -D / 2 - 0.0035);
    const body = new THREE.InstancedMesh(
      bodyGeo,
      new THREE.MeshPhysicalMaterial({ color: look.body, roughness: 0.16, metalness: 0.1, clearcoat: 1, clearcoatRoughness: 0.06 }),
      L.count,
    );
    const face = new THREE.InstancedMesh(
      faceGeo,
      new THREE.MeshPhysicalMaterial({ color: "#ffffff", roughness: 0.28, metalness: 0.25, clearcoat: 0.8, iridescence: 0.5, iridescenceIOR: 1.6 }),
      L.count,
    );
    const glow = new THREE.InstancedMesh(
      glowGeo,
      new THREE.MeshBasicMaterial({ blending: THREE.AdditiveBlending, transparent: true, depthWrite: false, toneMapped: false, side: THREE.DoubleSide }),
      L.count,
    );
    for (const m of [body, face, glow]) m.frustumCulled = false;
    body.castShadow = true;
    body.receiveShadow = true;
    face.receiveShadow = true;
    for (let i = 0; i < L.count; i++) face.setColorAt(i, C.setRGB(L.colR[i], L.colG[i], L.colB[i], THREE.SRGBColorSpace));
    face.instanceColor!.needsUpdate = true;
    glow.setColorAt(0, C.setRGB(0, 0, 0));
    return { body, face, glow };
  }, [L, look.body]);

  const composer = useMemo(() => {
    const w = size.width, h = size.height;
    const c = new EffectComposer(gl);
    c.setPixelRatio(dpr);
    c.setSize(w, h);
    c.addPass(new RenderPass(scene, camera));
    const bokeh = new BokehPass(scene, camera, { focus: 8, aperture: 0.001, maxblur: 0.009 });
    c.addPass(bokeh);
    c.addPass(new UnrealBloomPass(new THREE.Vector2(w * dpr, h * dpr), 0.5, 0.45, 1.4));
    c.addPass(new OutputPass());
    const post = new ShaderPass(POST);
    c.addPass(post);
    return { c, bokeh, post };
  }, [gl, scene, camera, size.width, size.height, dpr]);

  const f = Math.min(sim.frames - 1, frame);
  for (let i = 0; i < L.count; i++) {
    const o = f * L.count + i;
    const th = sim.theta[o];
    const dx = L.dir[i * 2], dz = L.dir[i * 2 + 1];
    // world = T(pos) * Ry(yaw) * T(0,0,D/2) * Rx(theta) * T(0,0,-D/2)
    M.makeRotationY(Math.atan2(dx, dz)).setPosition(L.x[i], 0, L.z[i]);
    M2.makeTranslation(0, 0, D / 2);
    M.multiply(M2);
    M3.makeRotationX(th);
    M.multiply(M3);
    M2.makeTranslation(0, 0.0004 * (i % 7), -D / 2); // tiny height offsets stop overlapping faces flickering
    M.multiply(M2);
    meshes.body.setMatrixAt(i, M);
    meshes.face.setMatrixAt(i, M);
    meshes.glow.setMatrixAt(i, M);
    const g = sim.light[o] * glowBoost;
    C.setRGB(L.colR[i], L.colG[i], L.colB[i], THREE.SRGBColorSpace).multiplyScalar(g * 1.45);
    meshes.glow.setColorAt(i, C);
  }
  meshes.body.instanceMatrix.needsUpdate = true;
  meshes.face.instanceMatrix.needsUpdate = true;
  meshes.glow.instanceMatrix.needsUpdate = true;
  meshes.glow.instanceColor!.needsUpdate = true;

  const [cx, cy, cz, lx, ly, lz] = camAt(t);
  const px = lx + (cx - lx) * zoom, py = ly + (cy - ly) * zoom, pz = lz + (cz - lz) * zoom;
  camera.position.set(px, py, pz);
  camera.lookAt(lx, ly, lz);
  camera.updateMatrixWorld();
  const focus = Math.hypot(px - lx, py - ly, pz - lz);
  const u = composer.bokeh.uniforms as Record<string, THREE.IUniform>;
  u.focus.value = focus;
  u.aperture.value = 0.0028 / Math.max(1, focus * 0.7);
  const fx = Math.min(1, Math.max(0, (t - DSTORY.fade[0]) / (DSTORY.fade[1] - DSTORY.fade[0])));
  composer.post.uniforms.uFade.value = 1 - fx * fx * (3 - 2 * fx);

  useFrame(() => composer.c.render(), 1);

  const hx = (L.cols * L.spacing) / 2 + 0.1, hz = (L.rows * L.spacing) / 2 + 0.1;
  const laneIdx = L.lane.indexOf(1);
  const laneSteps = (t - DSTORY.lane.start) / DSTORY.lane.step;
  const sparkZ = hz - 0.1 - laneSteps * L.spacing;
  const sparkOn = t > DSTORY.lane.start && t < DSTORY.bloom.start + 0.6 ? Math.min(1, (t - DSTORY.lane.start) * 4) * Math.min(1, (DSTORY.bloom.start + 0.6 - t) * 3) : 0;
  return (
    <>
      <hemisphereLight args={["#9fb0e0", "#040406", 0.22]} />
      <directionalLight
        position={[-6, 3.6, -2.5]}
        intensity={2.6}
        color={look.key}
        castShadow
        shadow-mapSize={[4096, 4096]}
        shadow-camera-left={-4.6}
        shadow-camera-right={4.6}
        shadow-camera-top={4.6}
        shadow-camera-bottom={-4.6}
        shadow-camera-near={1}
        shadow-camera-far={20}
        shadow-bias={-0.0003}
        shadow-normalBias={0.015}
        shadow-radius={3}
      />
      <directionalLight position={[5, 4, 6]} intensity={0.55} color={look.rim} />
      {/* a warm spark that travels with the chain up the lane */}
      {sparkOn > 0 && <pointLight position={[L.x[laneIdx], 0.18, sparkZ]} intensity={0.9 * sparkOn} distance={1.6} decay={2} color="#ffb35c" />}
      <primitive object={meshes.body} />
      <primitive object={meshes.face} />
      <primitive object={meshes.glow} />
      <mesh position={[0, -0.06, 0]} receiveShadow>
        <boxGeometry args={[hx * 2, 0.12, hz * 2]} />
        <meshPhysicalMaterial color={look.plate} metalness={0.4} roughness={0.32} clearcoat={0.8} />
      </mesh>
      <mesh rotation-x={-Math.PI / 2} position-y={-0.13} receiveShadow>
        <planeGeometry args={[60, 60]} />
        <meshStandardMaterial color={look.background} roughness={0.6} metalness={0.1} />
      </mesh>
    </>
  );
};

export const DominoScene: React.FC<{ sim: DominoSim; frame: number; t: number; look: DominoLook; dpr?: number; zoom?: number; glowBoost?: number }> = ({
  dpr = 2,
  zoom = 1,
  glowBoost = 1,
  ...props
}) => {
  const { width, height } = useVideoConfig();
  return (
    <ThreeCanvas
      width={width}
      height={height}
      dpr={dpr}
      shadows="soft"
      gl={{ antialias: true, preserveDrawingBuffer: true, powerPreference: "high-performance" }}
      camera={{ fov: 32, near: 0.03, far: 60, position: [0, 6, 8] }}
    >
      <Contents {...props} dpr={dpr} zoom={zoom} glowBoost={glowBoost} />
    </ThreeCanvas>
  );
};
