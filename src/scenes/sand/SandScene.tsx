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
import { GRAIN_COLOURS, grainAt, PH, PW, SSTORY, type Sand } from "./chladni";

/** Camera [t, px, py, pz, lx, ly, lz]: low macro in the leaping grains (hook), rise to top-down for each figure,
 *  sweeping 3/4 passes during the fast run, high and still for the grand figure, rise into the light. */
const CAM: number[][] = [
  [0.0, 1.2, 1.25, 3.0, 0, 0.12, 0.3],
  [1.6, 0.8, 2.4, 4.6, 0, 0, 0.2],
  [2.8, 0, 9.6, 1.4, 0, 0, 0.1],
  [5.6, 0.4, 9.2, 1.8, 0, 0, 0.1],
  [8.4, -0.4, 9.4, 1.6, 0, 0, 0.1],
  [11.0, 1.8, 3.2, 4.4, 0, 0, 0.6],
  [13.6, -1.6, 4.0, 4.8, 0, 0, 0],
  [15.4, 0, 9.8, 1.4, 0, 0, 0.1],
  [17.8, 1.4, 2.8, 4.0, 0.3, 0, 0.6],
  [19.4, 0, 10.4, 1.2, 0, 0, 0.1],
  [23.5, 0, 11.0, 1.2, 0, 0, 0.1],
  [28.0, 0, 13.6, 1.0, 0, 0, 0.1],
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
  uniforms: { tDiffuse: { value: null }, uFade: { value: 0 } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `uniform sampler2D tDiffuse; uniform float uFade; varying vec2 vUv;
    void main(){ vec4 c = texture2D(tDiffuse, vUv); vec2 d = (vUv - 0.5) * vec2(1.0, 1.25);
    c.rgb *= 1.0 - 0.3 * smoothstep(0.3, 0.9, length(d));
    c.rgb = mix(c.rgb, vec3(1.0, 0.95, 0.88), smoothstep(0.0, 1.0, uFade)); gl_FragColor = c; }`,
};

const M = new THREE.Matrix4(), Q = new THREE.Quaternion(), P = new THREE.Vector3(), S = new THREE.Vector3(), C = new THREE.Color();
const R = 0.0105;

const Contents: React.FC<{ sand: Sand; t: number; dpr: number; zoom: number }> = ({ sand, t, dpr, zoom }) => {
  const { gl, scene, camera, size } = useThree();

  useMemo(() => {
    const pmrem = new THREE.PMREMGenerator(gl);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.03).texture;
    scene.environmentIntensity = 0.35;
    scene.background = new THREE.Color("#e9d8c2");
    scene.fog = new THREE.Fog("#e9d8c2", 14, 34);
    pmrem.dispose();
    gl.toneMapping = THREE.ACESFilmicToneMapping;
    gl.toneMappingExposure = 1.0;
  }, [gl, scene]);

  const grains = useMemo(() => {
    const g = new THREE.IcosahedronGeometry(R, 1);
    const m = new THREE.InstancedMesh(g, new THREE.MeshStandardMaterial({ roughness: 0.75, metalness: 0.05 }), sand.count);
    m.castShadow = true;
    m.receiveShadow = true;
    m.frustumCulled = false;
    for (let i = 0; i < sand.count; i++) {
      const [r, gg, b] = GRAIN_COLOURS[sand.colour[i]];
      const j = (0.85 + 0.15 * sand.seed[i]) * [0.7, 1.05, 0.62, 0.95][sand.colour[i]]; // near-equal brightness, contrast in hue
      m.setColorAt(i, C.setRGB(r * j, gg * j, b * j, THREE.SRGBColorSpace));
    }
    m.instanceColor!.needsUpdate = true;
    return m;
  }, [sand]);

  const composer = useMemo(() => {
    const w = size.width, h = size.height;
    const c = new EffectComposer(gl);
    c.setPixelRatio(dpr);
    c.setSize(w, h);
    c.addPass(new RenderPass(scene, camera));
    const bokeh = new BokehPass(scene, camera, { focus: 5, aperture: 0.002, maxblur: 0.01 });
    c.addPass(bokeh);
    c.addPass(new OutputPass());
    const post = new ShaderPass(POST);
    c.addPass(post);
    return { c, bokeh, post };
  }, [gl, scene, camera, size.width, size.height, dpr]);

  for (let i = 0; i < sand.count; i++) {
    const [x, y, h] = grainAt(sand, i, t);
    const sc = sand.size[i];
    M.compose(P.set(x, R * sc + h, y), Q, S.setScalar(sc));
    grains.setMatrixAt(i, M);
  }
  grains.instanceMatrix.needsUpdate = true;

  const [cx, cy, cz, lx, ly, lz] = camAt(t);
  camera.position.set(lx + (cx - lx) * zoom, ly + (cy - ly) * zoom, lz + (cz - lz) * zoom);
  camera.lookAt(lx, ly, lz);
  camera.updateMatrixWorld();
  const focus = camera.position.distanceTo(new THREE.Vector3(lx, ly, lz));
  const b = composer.bokeh.uniforms as Record<string, THREE.IUniform>;
  b.focus.value = focus;
  b.aperture.value = 0.004 / Math.max(1, focus * 0.6);
  const fx = Math.min(1, Math.max(0, (t - SSTORY.fade[0]) / (SSTORY.fade[1] - SSTORY.fade[0])));
  composer.post.uniforms.uFade.value = fx * fx * (3 - 2 * fx);

  useFrame(() => composer.c.render(), 1);

  return (
    <>
      <hemisphereLight args={["#fff3e2", "#8a7aa8", 1.1]} />
      <directionalLight
        position={[-6, 4.2, 3.5]}
        intensity={1.5}
        color="#ffe2bd"
        castShadow
        shadow-mapSize={[4096, 4096]}
        shadow-camera-left={-4.5}
        shadow-camera-right={4.5}
        shadow-camera-top={4.5}
        shadow-camera-bottom={-4.5}
        shadow-camera-near={1}
        shadow-camera-far={25}
        shadow-bias={-0.0002}
        shadow-radius={2}
      />
      <directionalLight position={[4, 3, -5]} intensity={0.6} color="#9fc6ff" />
      <primitive object={grains} />
      {/* deep navy enamel plate on a brass rim */}
      <mesh position={[0, -0.04, 0]} receiveShadow>
        <boxGeometry args={[PW, 0.08, PH]} />
        <meshPhysicalMaterial color="#6a5f8f" roughness={0.45} metalness={0.1} clearcoat={0.6} clearcoatRoughness={0.3} />
      </mesh>
      {[0, 1, 2, 3].map((k) => {
        const along = k < 2, s = k % 2 ? 1 : -1;
        return (
          <mesh key={k} position={along ? [0, 0.0, s * (PH / 2 + 0.05)] : [s * (PW / 2 + 0.05), 0.0, 0]} castShadow receiveShadow>
            <boxGeometry args={along ? [PW + 0.2, 0.1, 0.1] : [0.1, 0.1, PH]} />
            <meshStandardMaterial color="#c79a52" roughness={0.3} metalness={0.9} />
          </mesh>
        );
      })}
      <mesh rotation-x={-Math.PI / 2} position-y={-0.09} receiveShadow>
        <planeGeometry args={[80, 80]} />
        <meshStandardMaterial color="#e3cfb5" roughness={0.9} />
      </mesh>
    </>
  );
};

export const SandScene: React.FC<{ sand: Sand; t: number; dpr?: number; zoom?: number }> = ({ dpr = 2, zoom = 1, ...props }) => {
  const { width, height } = useVideoConfig();
  return (
    <ThreeCanvas width={width} height={height} dpr={dpr} shadows="soft" gl={{ antialias: true, preserveDrawingBuffer: true, powerPreference: "high-performance" }} camera={{ fov: 34, near: 0.05, far: 80, position: [0, 6, 4] }}>
      <Contents {...props} dpr={dpr} zoom={zoom} />
    </ThreeCanvas>
  );
};
