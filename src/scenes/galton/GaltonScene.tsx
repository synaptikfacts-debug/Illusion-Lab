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
import { BINS, binX, floorY, GB, marbleAt, type Marble } from "./galton";

/** Camera [t, px, py, pz, lx, ly, lz]: close on the pins with marbles streaming through (hook), pull back to the
 *  whole board, slow drift down with the growing curve, follow the gold marble, ease back, fade. */
const CAM: number[][] = [
  [0.0, 1.0, 1.6, 6.2, 0, 1.4, 0],
  [2.0, 0.6, 1.0, 9.0, 0, 0.6, 0],
  [5.0, 0, -0.2, 16.0, 0, -0.5, 0],
  [12.0, 0.6, -0.5, 15.4, 0, -0.7, 0],
  [17.5, -0.5, -0.7, 15.6, 0, -0.7, 0],
  [19.4, 0, 2.6, 5.2, 0, 2.3, 0],
  [21.0, 0, 0.0, 5.0, 0, -0.4, 0],
  [22.6, 0, -0.6, 10.0, 0, -1.0, 0],
  [27.0, 0, -0.5, 16.6, 0, -0.7, 0],
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
  uniforms: { tDiffuse: { value: null }, uFade: { value: 1 } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `uniform sampler2D tDiffuse; uniform float uFade; varying vec2 vUv;
    void main(){ vec4 c = texture2D(tDiffuse, vUv); vec2 d = (vUv - 0.5) * vec2(1.0, 1.25);
    c.rgb *= 1.0 - 0.35 * smoothstep(0.3, 0.9, length(d));
    float e = smoothstep(0.0, 1.0, uFade * 1.6 - length(d) * 0.9);
    c.rgb *= mix(uFade * uFade, 1.0, e * uFade); gl_FragColor = c; }`,
};

const M = new THREE.Matrix4(), Q = new THREE.Quaternion(), P = new THREE.Vector3(), S = new THREE.Vector3(), C = new THREE.Color();

/** Candy rainbow by release time. */
function candy(h: number, out: THREE.Color) {
  return out.setHSL(0.95 - h * 0.6, 0.85, 0.55, THREE.SRGBColorSpace);
}

const Contents: React.FC<{ marbles: Marble[]; t: number; dpr: number; zoom: number }> = ({ marbles, t, dpr, zoom }) => {
  const { gl, scene, camera, size } = useThree();

  useMemo(() => {
    const pmrem = new THREE.PMREMGenerator(gl);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.02).texture;
    scene.environmentIntensity = 0.7;
    scene.background = new THREE.Color("#050507");
    pmrem.dispose();
    gl.toneMapping = THREE.ACESFilmicToneMapping;
    gl.toneMappingExposure = 1.0;
  }, [gl, scene]);

  const parts = useMemo(() => {
    const ball = new THREE.InstancedMesh(
      new THREE.SphereGeometry(GB.r, 24, 16),
      new THREE.MeshPhysicalMaterial({ roughness: 0.08, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.03 }),
      marbles.length,
    );
    ball.castShadow = true;
    ball.frustumCulled = false;
    marbles.forEach((m, i) => ball.setColorAt(i, m.gold ? C.set("#000000") : candy(m.hue, C)));
    // the gold marble: its own metallic gold mesh with a soft glow
    const gold = new THREE.Mesh(
      new THREE.SphereGeometry(GB.r * 1.2, 32, 24),
      new THREE.MeshPhysicalMaterial({ color: "#ffcf4a", metalness: 1, roughness: 0.12, clearcoat: 1, emissive: "#ff9d1a", emissiveIntensity: 0.6 }),
    );
    ball.instanceColor!.needsUpdate = true;
    // chrome pins
    const pinCount = (GB.rows * (GB.rows + 1)) / 2;
    const pins = new THREE.InstancedMesh(
      new THREE.CylinderGeometry(0.022, 0.022, 0.16, 20).rotateX(Math.PI / 2),
      new THREE.MeshStandardMaterial({ color: "#e8ecf2", metalness: 1, roughness: 0.15 }),
      pinCount,
    );
    let n = 0;
    for (let k = 0; k < GB.rows; k++)
      for (let j = 0; j <= k; j++) {
        M.compose(P.set((j - k / 2) * GB.s, GB.topY - k * GB.dy, 0.04), Q, S.set(1, 1, 1));
        pins.setMatrixAt(n++, M);
      }
    pins.castShadow = true;
    return { ball, pins, gold };
  }, [marbles]);

  const composer = useMemo(() => {
    const w = size.width, h = size.height;
    const c = new EffectComposer(gl);
    c.setPixelRatio(dpr);
    c.setSize(w, h);
    c.addPass(new RenderPass(scene, camera));
    const bokeh = new BokehPass(scene, camera, { focus: 10, aperture: 0.001, maxblur: 0.008 });
    c.addPass(bokeh);
    c.addPass(new UnrealBloomPass(new THREE.Vector2(w * dpr, h * dpr), 0.18, 0.35, 1.5));
    c.addPass(new OutputPass());
    const post = new ShaderPass(POST);
    c.addPass(post);
    return { c, bokeh, post };
  }, [gl, scene, camera, size.width, size.height, dpr]);

  marbles.forEach((m, i) => {
    const p = marbleAt(m, t);
    if (!p) M.compose(P.set(0, 99, 0), Q, S.setScalar(0.0001));
    else M.compose(P.set(p[0], p[1], 0.04), Q, S.setScalar(m.gold ? 0.0001 : 1));
    parts.ball.setMatrixAt(i, M);
  });
  parts.ball.instanceMatrix.needsUpdate = true;
  const gm = marbles[marbles.length - 1], gp = marbleAt(gm, t);
  parts.gold.visible = !!gp;
  if (gp) parts.gold.position.set(gp[0], gp[1], 0.04);

  const [cx, cy, cz, lx, ly, lz] = camAt(t);
  camera.position.set(lx + (cx - lx) * zoom, ly + (cy - ly) * zoom, lz + (cz - lz) * zoom);
  camera.lookAt(lx, ly, lz);
  camera.updateMatrixWorld();
  const focus = camera.position.distanceTo(new THREE.Vector3(lx, ly, lz));
  const b = composer.bokeh.uniforms as Record<string, THREE.IUniform>;
  b.focus.value = focus;
  b.aperture.value = 0.0035 / Math.max(1, focus * 0.6);
  const fx = Math.min(1, Math.max(0, (t - GB.fade[0]) / (GB.fade[1] - GB.fade[0])));
  composer.post.uniforms.uFade.value = 1 - fx * fx * (3 - 2 * fx);
  useFrame(() => composer.c.render(), 1);

  const fy = floorY(), top = GB.topY - GB.rows * GB.dy - 0.15, w = BINS * GB.s;
  return (
    <>
      <hemisphereLight args={["#ffffff", "#202030", 0.35]} />
      <directionalLight position={[-3, 6, 7]} intensity={2.2} castShadow shadow-mapSize={[4096, 4096]} shadow-camera-left={-5} shadow-camera-right={5} shadow-camera-top={6} shadow-camera-bottom={-6} shadow-bias={-0.0004} />
      <directionalLight position={[4, -2, 5]} intensity={0.6} color="#bcd4ff" />
      <primitive object={parts.ball} />
      <primitive object={parts.pins} />
      <primitive object={parts.gold} />
      {(() => { const gp = marbleAt(marbles[marbles.length - 1], t); return gp ? <pointLight position={[gp[0], gp[1], 0.3]} intensity={0.6} distance={1.2} color="#ffb340" /> : null; })()}
      {/* glossy black backboard */}
      <mesh position={[0, -0.3, -0.06]} receiveShadow>
        <boxGeometry args={[w + 0.5, 10.6, 0.06]} />
        <meshStandardMaterial color="#010102" roughness={0.7} metalness={0} envMapIntensity={0.05} />
      </mesh>
      {/* bin dividers + floor + funnel (chrome) */}
      {Array.from({ length: BINS + 1 }, (_, b) => (
        <mesh key={b} position={[binX(b) - GB.s / 2, (top + fy) / 2, 0.04]} castShadow>
          <boxGeometry args={[0.018, top - fy, 0.14]} />
          <meshStandardMaterial color="#d9dde4" metalness={1} roughness={0.2} />
        </mesh>
      ))}
      <mesh position={[0, fy - 0.03, 0.04]}>
        <boxGeometry args={[w + 0.1, 0.06, 0.16]} />
        <meshStandardMaterial color="#d9dde4" metalness={1} roughness={0.2} />
      </mesh>
      {[-1, 1].map((s) => (
        <mesh key={s} position={[s * 0.62, GB.topY + 0.75, 0.04]} rotation={[0, 0, s * 0.85]}>
          <boxGeometry args={[1.1, 0.04, 0.16]} />
          <meshStandardMaterial color="#d9dde4" metalness={1} roughness={0.2} />
        </mesh>
      ))}
    </>
  );
};

export const GaltonScene: React.FC<{ marbles: Marble[]; t: number; dpr?: number; zoom?: number }> = ({ dpr = 2, zoom = 1, ...props }) => {
  const { width, height } = useVideoConfig();
  return (
    <ThreeCanvas width={width} height={height} dpr={dpr} shadows="soft" gl={{ antialias: true, preserveDrawingBuffer: true, powerPreference: "high-performance" }} camera={{ fov: 34, near: 0.05, far: 80, position: [0, 0, 12] }}>
      <Contents {...props} dpr={dpr} zoom={zoom} />
    </ThreeCanvas>
  );
};
