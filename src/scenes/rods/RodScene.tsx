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
import type { RodSim } from "./sim";

export interface RodLook {
  rod: string;
  plate: string;
  background: string;
  glowA: string; // outer iris / energy
  glowB: string; // inner iris
  key: string;
  rim: string;
}

/** Camera keys: [t, px, py, pz, lx, ly, lz]. Start pose == end pose so the reel can loop after its ending. */
const CAM: number[][] = [
  [0.0, 0.35, 1.9, 1.7, 0, 0.3, 0],
  [1.4, 0.5, 2.9, 2.9, 0, 0.2, 0],
  [3.6, 0.0, 6.4, 7.2, 0, 0.0, 0],
  [7.0, -1.4, 9.4, 6.2, 0, 0.0, 0],
  [10.6, 0.0, 13.3, 3.0, 0, 0.0, -0.05],
  [12.5, 0.0, 13.7, 2.0, 0, 0.0, -0.45],
  [16.4, 0.0, 13.5, 2.0, 0, 0.0, -0.45],
  [17.4, 0.0, 10.6, 1.5, 0, 0.0, -0.4],
  [19.3, 0.0, 12.6, 2.0, 0, 0.0, -0.45],
  [21.0, 0.3, 4.2, 3.4, 0, 0.2, 0],
  [22.2, 0.35, 1.9, 1.7, 0, 0.3, 0],
  [23.0, 0.35, 1.9, 1.7, 0, 0.3, 0],
];

function camAt(t: number) {
  // Catmull-Rom through the keys, eased per segment
  let j = 0;
  while (j < CAM.length - 2 && t > CAM[j + 1][0]) j++;
  const k0 = CAM[Math.max(0, j - 1)], k1 = CAM[j], k2 = CAM[j + 1], k3 = CAM[Math.min(CAM.length - 1, j + 2)];
  const x = Math.min(1, Math.max(0, (t - k1[0]) / (k2[0] - k1[0])));
  const s = x * x * (3 - 2 * x);
  const out = new Array(6);
  for (let c = 1; c <= 6; c++) {
    const p0 = k0[c], p1 = k1[c], p2 = k2[c], p3 = k3[c];
    out[c - 1] = 0.5 * (2 * p1 + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s * s + (-p0 + 3 * p1 - 3 * p2 + p3) * s * s * s);
  }
  return out as [number, number, number, number, number, number];
}

const VIGNETTE = {
  uniforms: { tDiffuse: { value: null }, uAmount: { value: 0.42 } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `uniform sampler2D tDiffuse; uniform float uAmount; varying vec2 vUv;
    void main(){ vec4 c = texture2D(tDiffuse, vUv); vec2 d = (vUv - 0.5) * vec2(1.0, 1.25);
    c.rgb *= 1.0 - uAmount * smoothstep(0.25, 0.85, length(d)); gl_FragColor = c; }`,
};

const M = new THREE.Matrix4(), Q = new THREE.Quaternion(), P = new THREE.Vector3(), S = new THREE.Vector3(), C = new THREE.Color();

const Contents: React.FC<{ sim: RodSim; frame: number; t: number; look: RodLook; dpr: number }> = ({ sim, frame, t, look, dpr }) => {
  const { gl, scene, camera, size } = useThree();
  const L = sim.layout;
  const R = L.spacing * 0.4;
  const H = 1.05;

  useMemo(() => {
    const pmrem = new THREE.PMREMGenerator(gl);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.03).texture;
    scene.environmentIntensity = 0.22;
    scene.background = new THREE.Color(look.background);
    scene.fog = new THREE.Fog(look.background, 24, 45);
    pmrem.dispose();
    gl.toneMapping = THREE.ACESFilmicToneMapping;
    gl.toneMappingExposure = 0.9;
  }, [gl, scene, look.background]);

  const meshes = useMemo(() => {
    const shaftGeo = new THREE.CylinderGeometry(R, R, 1, 24, 1, true);
    shaftGeo.translate(0, 0.5, 0);
    const capGeo = new THREE.SphereGeometry(R, 28, 14, 0, Math.PI * 2, 0, Math.PI / 2);
    capGeo.scale(1, 0.62, 1);
    const glowGeo = new THREE.SphereGeometry(R * 1.04, 20, 10, 0, Math.PI * 2, 0, Math.PI / 2);
    glowGeo.scale(1, 0.66, 1);
    const metal = new THREE.MeshPhysicalMaterial({ color: look.rod, metalness: 1, roughness: 0.32, clearcoat: 0.3, clearcoatRoughness: 0.2 });
    const capMat = new THREE.MeshPhysicalMaterial({ color: look.rod, metalness: 1, roughness: 0.12, clearcoat: 1, clearcoatRoughness: 0.05 });
    const glowMat = new THREE.MeshBasicMaterial({ blending: THREE.AdditiveBlending, transparent: true, depthWrite: false, toneMapped: false });
    const mk = (g: THREE.BufferGeometry, m: THREE.Material) => {
      const im = new THREE.InstancedMesh(g, m, sim.count);
      im.frustumCulled = false;
      im.castShadow = true;
      im.receiveShadow = true;
      return im;
    };
    const shafts = mk(shaftGeo, metal), caps = mk(capGeo, capMat), glows = mk(glowGeo, glowMat);
    glows.castShadow = false;
    glows.setColorAt(0, C.setRGB(0, 0, 0));
    return { shafts, caps, glows };
  }, [sim.count, R, look.rod]);

  const composer = useMemo(() => {
    const w = size.width, h = size.height;
    const c = new EffectComposer(gl);
    c.setPixelRatio(dpr);
    c.setSize(w, h);
    c.addPass(new RenderPass(scene, camera));
    const bokeh = new BokehPass(scene, camera, { focus: 8, aperture: 0.0012, maxblur: 0.006 });
    c.addPass(bokeh);
    c.addPass(new UnrealBloomPass(new THREE.Vector2(w * dpr, h * dpr), 0.55, 0.45, 1.6));
    c.addPass(new OutputPass());
    c.addPass(new ShaderPass(VIGNETTE));
    return { c, bokeh };
  }, [gl, scene, camera, size.width, size.height, dpr]);

  // per-frame state from the simulation
  const ga = new THREE.Color(look.glowA), gb = new THREE.Color(look.glowB);
  const f = Math.min(sim.frames - 1, frame);
  for (let i = 0; i < sim.count; i++) {
    const o = f * sim.count + i;
    const top = sim.height[o] * H;
    const x = L.x[i], z = L.z[i];
    M.compose(P.set(x, -0.2, z), Q, S.set(1, top + 0.2, 1));
    meshes.shafts.setMatrixAt(i, M);
    M.compose(P.set(x, top, z), Q, S.set(1, 1, 1));
    meshes.caps.setMatrixAt(i, M);
    meshes.glows.setMatrixAt(i, M);
    const g = sim.glow[o];
    C.copy(ga).lerp(gb, sim.hue[o]).multiplyScalar(g * g * 3.2);
    meshes.glows.setColorAt(i, C);
  }
  meshes.shafts.instanceMatrix.needsUpdate = true;
  meshes.caps.instanceMatrix.needsUpdate = true;
  meshes.glows.instanceMatrix.needsUpdate = true;
  meshes.glows.instanceColor!.needsUpdate = true;

  const [px, py, pz, lx, ly, lz] = camAt(t);
  camera.position.set(px, py, pz);
  camera.lookAt(lx, ly, lz);
  camera.updateMatrixWorld();
  const focus = Math.hypot(px - lx, py - ly, pz - lz);
  const u = composer.bokeh.uniforms as Record<string, THREE.IUniform>;
  u.focus.value = focus;
  // close shots get a shallow, macro-like depth of field; wide shots stay sharp
  u.aperture.value = 0.0022 / Math.max(1, focus * 0.6);
  u.maxblur.value = 0.009;

  useFrame(() => composer.c.render(), 1);

  const hx = (L.n * L.spacing) / 2 + 0.12, hz = (L.rows * L.spacing) / 2 + 0.12;
  return (
    <>
      <hemisphereLight args={["#9fb4d6", "#050608", 0.12]} />
      <directionalLight
        position={[-6.5, 3.4, -2.4]}
        intensity={3.0}
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
        shadow-normalBias={0.02}
        shadow-radius={4}
      />
      <directionalLight position={[5, 3, 6]} intensity={0.35} color={look.rim} />
      
      <primitive object={meshes.shafts} />
      <primitive object={meshes.caps} />
      <primitive object={meshes.glows} />
      {/* anodised plate with a chrome frame */}
      <mesh position={[0, -0.13, 0]} receiveShadow>
        <boxGeometry args={[hx * 2, 0.26, hz * 2]} />
        <meshPhysicalMaterial color={look.plate} metalness={0.7} roughness={0.38} clearcoat={0.5} />
      </mesh>
      {[0, 1, 2, 3].map((k) => {
        const along = k < 2;
        const s = k % 2 ? 1 : -1;
        return (
          <mesh key={k} position={along ? [0, 0.04, s * (hz + 0.06)] : [s * (hx + 0.06), 0.04, 0]} castShadow receiveShadow>
            <boxGeometry args={along ? [hx * 2 + 0.24, 0.1, 0.12] : [0.12, 0.1, hz * 2]} />
            <meshPhysicalMaterial color={look.rod} metalness={1} roughness={0.18} clearcoat={1} />
          </mesh>
        );
      })}
      <mesh rotation-x={-Math.PI / 2} position-y={-0.27} receiveShadow>
        <planeGeometry args={[60, 60]} />
        <meshStandardMaterial color={look.background} roughness={0.55} metalness={0.2} />
      </mesh>
    </>
  );
};

export const RodScene: React.FC<{ sim: RodSim; frame: number; t: number; look: RodLook; dpr?: number }> = ({ dpr = 2, ...props }) => {
  const { width, height } = useVideoConfig();
  return (
    <ThreeCanvas
      width={width}
      height={height}
      dpr={dpr}
      shadows="soft"
      gl={{ antialias: true, preserveDrawingBuffer: true, powerPreference: "high-performance" }}
      camera={{ fov: 32, near: 0.05, far: 60, position: [0, 4, 8] }}
    >
      <Contents {...props} dpr={dpr} />
    </ThreeCanvas>
  );
};
