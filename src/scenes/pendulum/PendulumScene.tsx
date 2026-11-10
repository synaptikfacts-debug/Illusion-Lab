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
import { angleAt, PD, pivotX, pivotY, SYNC_AT } from "./pendulum";

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
    return { bobs, threads };
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

  const [cx, cy, cz, lx, ly] = camAt(t);
  camera.position.set(lx + (cx - lx) * zoom, ly + (cy - ly) * zoom, cz * zoom);
  camera.lookAt(lx, ly, 0);
  camera.updateMatrixWorld();
  const b = composer.bokeh.uniforms as Record<string, THREE.IUniform>;
  b.focus.value = camera.position.distanceTo(new THREE.Vector3(lx, ly, 0));
  b.aperture.value = 0.0024 / Math.max(1, b.focus.value * 0.6);
  const fx = Math.min(1, Math.max(0, (t - PD.fade[0]) / (PD.fade[1] - PD.fade[0])));
  composer.post.uniforms.uFade.value = 1 - fx * fx * (3 - 2 * fx);
  useFrame(() => composer.c.render(), 1);

  const len = PD.cols * PD.spacing + 0.5;
  return (
    <>
      <hemisphereLight args={["#c9d2ff", "#0b0b10", 0.25]} />
      <directionalLight position={[-3, 8, 5]} intensity={2.0} color="#fff1e0" castShadow shadow-mapSize={[2048, 2048]} shadow-camera-left={-6} shadow-camera-right={6} shadow-camera-top={6} shadow-camera-bottom={-6} />
      <pointLight position={[6, 1, -4]} intensity={10} color="#5f8cff" />
      <primitive object={parts.threads} />
      <primitive object={parts.bobs} />
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
