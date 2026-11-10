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
import { ringAt, RP } from "./rings";

/** Camera [t, radius, height, lookY]: close inside the spiral staircase (hook), drift out and up, level with the
 *  rings for the sync moment, slow pull-back as they settle flat. The camera also orbits slowly the whole time. */
const CAM: number[][] = [
  [0, 7.4, 2.6, 0.1],
  [4, 8.6, 3.8, 0],
  [10, 9.8, 5.0, 0],
  [16, 9.6, 3.0, 0],
  [RP.syncAt - 1, 8.2, 1.6, 0],
  [RP.syncAt + 1.5, 8.4, 2.0, 0],
  [RP.decay[1], 8.6, 4.2, 0],
  [RP.duration, 9.6, 5.6, 0],
];

function camAt(t: number) {
  let j = 0;
  while (j < CAM.length - 2 && t > CAM[j + 1][0]) j++;
  const a = CAM[j], b = CAM[j + 1];
  const x = Math.min(1, Math.max(0, (t - a[0]) / (b[0] - a[0])));
  const s = x * x * (3 - 2 * x);
  return [a[1] + (b[1] - a[1]) * s, a[2] + (b[2] - a[2]) * s, a[3] + (b[3] - a[3]) * s];
}

const POST = {
  uniforms: { tDiffuse: { value: null }, uFade: { value: 1 } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `uniform sampler2D tDiffuse; uniform float uFade; varying vec2 vUv;
    void main(){ vec4 c = texture2D(tDiffuse, vUv); vec2 d = (vUv - 0.5) * vec2(1.0, 1.25);
    c.rgb *= 1.0 - 0.38 * smoothstep(0.3, 0.9, length(d));
    float e = smoothstep(0.0, 1.0, uFade * 1.6 - length(d) * 0.9);
    c.rgb *= mix(uFade * uFade, 1.0, e * uFade); gl_FragColor = c; }`,
};

const M = new THREE.Matrix4(), Q = new THREE.Quaternion(), E = new THREE.Euler(), P = new THREE.Vector3(), S = new THREE.Vector3(1, 1, 1);

const Contents: React.FC<{ t: number; dpr: number; zoom: number }> = ({ t, dpr, zoom }) => {
  const { gl, scene, camera, size } = useThree();

  useMemo(() => {
    const pmrem = new THREE.PMREMGenerator(gl);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.03).texture;
    scene.environmentIntensity = 0.75;
    // deep emerald void, darker below
    const c = document.createElement("canvas");
    c.width = 4; c.height = 512;
    const g = c.getContext("2d")!;
    const gr = g.createLinearGradient(0, 0, 0, 512);
    gr.addColorStop(0, "#1a5f4a"); gr.addColorStop(0.5, "#11463a"); gr.addColorStop(1, "#092b22");
    g.fillStyle = gr; g.fillRect(0, 0, 4, 512);
    const tex = new THREE.CanvasTexture(c);
    tex.colorSpace = THREE.SRGBColorSpace;
    scene.background = tex;
    scene.fog = new THREE.Fog("#11463a", 13, 28);
    pmrem.dispose();
    gl.toneMapping = THREE.ACESFilmicToneMapping;
    gl.toneMappingExposure = 0.88;
  }, [gl, scene]);

  const rings = useMemo(() => {
    // one instanced torus scaled per ring (tube thins slightly outward)
    const mesh = new THREE.InstancedMesh(
      new THREE.TorusGeometry(1, RP.tube, 26, 220),
      new THREE.MeshPhysicalMaterial({ color: "#f0c050", metalness: 1, roughness: 0.3, clearcoat: 0.4, clearcoatRoughness: 0.25 }),
      RP.count,
    );
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.frustumCulled = false;
    const col = new THREE.Color();
    for (let i = 0; i < RP.count; i++) {
      // warm gold at the centre drifting to rose gold at the rim
      const k = i / (RP.count - 1);
      mesh.setColorAt(i, col.setRGB(0.96, 0.78 - 0.18 * k, 0.33 + 0.12 * k, THREE.SRGBColorSpace));
    }
    mesh.instanceColor!.needsUpdate = true;
    return mesh;
  }, []);

  const composer = useMemo(() => {
    const w = size.width, h = size.height;
    const c = new EffectComposer(gl);
    c.setPixelRatio(dpr);
    c.setSize(w, h);
    c.addPass(new RenderPass(scene, camera));
    const bokeh = new BokehPass(scene, camera, { focus: 7, aperture: 0.001, maxblur: 0.008 });
    c.addPass(bokeh);
    c.addPass(new UnrealBloomPass(new THREE.Vector2(w * dpr, h * dpr), 0.07, 0.4, 1.8));
    c.addPass(new OutputPass());
    const post = new ShaderPass(POST);
    c.addPass(post);
    return { c, bokeh, post };
  }, [gl, scene, camera, size.width, size.height, dpr]);

  for (let i = 0; i < RP.count; i++) {
    const { tilt, axis, radius } = ringAt(i, t);
    E.set(Math.cos(axis) * tilt, axis * 0.08, Math.sin(axis) * tilt, "XYZ");
    Q.setFromEuler(E);
    // torus lies in the XY plane: rotate flat first, then the swing tilt
    const flat = new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI / 2, 0, 0));
    Q.multiply(flat);
    M.compose(P.set(0, 0, 0), Q, S.set(radius, radius, 1));
    rings.setMatrixAt(i, M);
  }
  rings.instanceMatrix.needsUpdate = true;

  const [rad, ht, ly] = camAt(t);
  const ang = 0.9 + 0.14 * t; // slow continuous orbit
  camera.position.set(Math.sin(ang) * rad * zoom, ht * zoom, Math.cos(ang) * rad * zoom);
  camera.lookAt(0, ly, 0);
  camera.updateMatrixWorld();
  const b = composer.bokeh.uniforms as Record<string, THREE.IUniform>;
  b.focus.value = camera.position.length();
  b.aperture.value = 0.0026 / Math.max(1, b.focus.value * 0.6);
  const fx = Math.min(1, Math.max(0, (t - RP.fade[0]) / (RP.fade[1] - RP.fade[0])));
  composer.post.uniforms.uFade.value = 1 - fx * fx * (3 - 2 * fx);
  useFrame(() => composer.c.render(), 1);

  return (
    <>
      <hemisphereLight args={["#ffe9c4", "#14523f", 0.5]} />
      <directionalLight
        position={[-6, 7, 4]}
        intensity={1.6}
        color="#fff0d2"
        castShadow
        shadow-mapSize={[4096, 4096]}
        shadow-camera-left={-5}
        shadow-camera-right={5}
        shadow-camera-top={5}
        shadow-camera-bottom={-5}
        shadow-bias={-0.0004}
        shadow-radius={3}
      />
      <pointLight position={[5, -2, -4]} intensity={10} color="#2fae8f" />
      <pointLight position={[-5, 3, -3]} intensity={7} color="#ffb766" />
      <primitive object={rings} />
      {/* a small polished gold sphere at the heart of the sculpture */}
      <mesh castShadow>
        <sphereGeometry args={[0.16, 32, 24]} />
        <meshPhysicalMaterial color="#f5c75a" metalness={1} roughness={0.1} clearcoat={1} />
      </mesh>
    </>
  );
};

export const RingScene: React.FC<{ t: number; dpr?: number; zoom?: number }> = ({ dpr = 2, zoom = 1, ...props }) => {
  const { width, height } = useVideoConfig();
  return (
    <ThreeCanvas width={width} height={height} dpr={dpr} shadows="soft" gl={{ antialias: true, preserveDrawingBuffer: true, powerPreference: "high-performance" }} camera={{ fov: 34, near: 0.1, far: 80, position: [0, 3, 8] }}>
      <Contents {...props} dpr={dpr} zoom={zoom} />
    </ThreeCanvas>
  );
};
