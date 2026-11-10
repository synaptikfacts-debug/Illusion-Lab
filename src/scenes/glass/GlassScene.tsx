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
import { makeParticlePoints, type ParticleData } from "../../gl/particleShader";
import { CUBE, cubeAt, GSTORY, regionColour, type GlassCube } from "./glassSim";

/** Camera keys [t, px, py, pz, lx, ly, lz]: close on the staring face, pull back into the storm, orbit the
 *  tornado, settle on the face, 3/4 views to show the relief, push in on the wink, rise with the drifting cubes. */
const CAM: number[][] = [
  [0.0, 0, 0.45, 8.9, 0, 0.35, 0],
  [0.6, 0, 0.45, 8.3, 0, 0.35, 0],
  [1.9, 0, 0.6, 12.0, 0, 0.3, 0],
  [5.0, 4.6, 1.4, 9.8, 0, 0.2, 0],
  [8.6, -4.8, 1.8, 9.4, 0, 0.3, 0],
  [12.2, 0, 0.6, 11.4, 0, 0.3, 0],
  [13.6, 0, 0.4, 11.2, 0, 0.25, 0],
  [16.0, 3.0, 0.7, 10.4, 0, 0.25, 0],
  [18.4, -3.0, 0.7, 10.2, 0, 0.25, 0],
  [19.4, 0.5, 0.8, 8.8, 0.35, 0.55, 0],
  [20.8, 0, 0.3, 11.0, 0, 0.2, 0],
  [23.2, 0, 0.3, 11.4, 0, 0.2, 0],
  [25.0, 0, 0.8, 11.2, 0, 0.6, 0],
  [27.6, 0, 2.2, 12.8, 0, 2.0, 0],
  [30.5, 0, 3.4, 14.0, 0, 3.4, 0],
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
  uniforms: { tDiffuse: { value: null }, uFade: { value: 0 }, uWhite: { value: new THREE.Vector3(1.0, 0.97, 0.94) } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `uniform sampler2D tDiffuse; uniform float uFade; uniform vec3 uWhite; varying vec2 vUv;
    void main(){ vec4 c = texture2D(tDiffuse, vUv); vec2 d = (vUv - 0.5) * vec2(1.0, 1.25);
    c.rgb *= 1.0 - 0.18 * smoothstep(0.35, 0.9, length(d)); // soft, light vignette
    // fade into the light: from the top down, like the cubes rising into the sky
    float k = smoothstep(0.0, 1.0, uFade * 1.5 - (1.0 - vUv.y) * 0.5);
    c.rgb = mix(c.rgb, uWhite, k); gl_FragColor = c; }`,
};

function skyTexture() {
  const c = document.createElement("canvas");
  c.width = 4; c.height = 1024;
  const g = c.getContext("2d")!;
  const grad = g.createLinearGradient(0, 0, 0, 1024);
  grad.addColorStop(0, "#9fc7ff");
  grad.addColorStop(0.38, "#c9b6f2");
  grad.addColorStop(0.68, "#ffc6c2");
  grad.addColorStop(1, "#ffe4c6");
  g.fillStyle = grad;
  g.fillRect(0, 0, 4, 1024);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

const M = new THREE.Matrix4(), Q = new THREE.Quaternion(), P = new THREE.Vector3(), S = new THREE.Vector3(), A = new THREE.Vector3(), C = new THREE.Color();

const Contents: React.FC<{ cubes: GlassCube[]; t: number; dpr: number; zoom: number; glowBoost: number; parts: ParticleData }> = ({ cubes, t, dpr, zoom, glowBoost, parts }) => {
  const { gl, scene, camera, size } = useThree();

  useMemo(() => {
    const pmrem = new THREE.PMREMGenerator(gl);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.02).texture;
    scene.environmentIntensity = 0.5;
    scene.background = skyTexture();
    pmrem.dispose();
    gl.toneMapping = THREE.ACESFilmicToneMapping;
    gl.toneMappingExposure = 0.82;
  }, [gl, scene]);

  const meshes = useMemo(() => {
    const geo = new THREE.BoxGeometry(CUBE * 0.84, CUBE * 0.84, CUBE * 0.84); // gaps: the sky shines through
    const glass = new THREE.MeshPhysicalMaterial({
      color: "#ffffff",
      roughness: 0.1,
      metalness: 0,
      transmission: 0.92,
      thickness: 0.6,
      ior: 1.45,
      iridescence: 0.6,
      iridescenceIOR: 1.5,
      clearcoat: 0.35,
      clearcoatRoughness: 0.12,
      attenuationColor: new THREE.Color("#ffd9e8"),
      attenuationDistance: 1.2,
    });
    const box = new THREE.InstancedMesh(geo, glass, cubes.length);
    box.castShadow = true;
    box.receiveShadow = true;
    box.frustumCulled = false;
    cubes.forEach((c, i) => {
      const [r, g, b] = regionColour(c);
      const j = 0.88 + 0.12 * Math.abs(Math.sin(i * 12.9898) * 43758.5453 % 1); // each cube a slightly different glass
      box.setColorAt(i, C.setRGB(r * j, g * j, b * (0.94 + 0.06 * j), THREE.SRGBColorSpace));
    });
    box.instanceColor!.needsUpdate = true;
    const glowGeo = new THREE.BoxGeometry(CUBE * 0.9, CUBE * 0.9, CUBE * 0.9);
    const glow = new THREE.InstancedMesh(glowGeo, new THREE.MeshBasicMaterial({ blending: THREE.AdditiveBlending, transparent: true, depthWrite: false, toneMapped: false }), cubes.length);
    glow.frustumCulled = false;
    glow.setColorAt(0, C.setRGB(0, 0, 0));
    return { box, glow };
  }, [cubes]);

  const composer = useMemo(() => {
    const w = size.width, h = size.height;
    const c = new EffectComposer(gl);
    c.setPixelRatio(dpr);
    c.setSize(w, h);
    c.addPass(new RenderPass(scene, camera));
    const bokeh = new BokehPass(scene, camera, { focus: 9, aperture: 0.001, maxblur: 0.01 });
    c.addPass(bokeh);
    c.addPass(new UnrealBloomPass(new THREE.Vector2(w * dpr, h * dpr), 0.22, 0.5, 1.6));
    c.addPass(new OutputPass());
    const post = new ShaderPass(POST);
    c.addPass(post);
    return { c, bokeh, post };
  }, [gl, scene, camera, size.width, size.height, dpr]);

  const points = useMemo(() => makeParticlePoints(parts, (size.height * dpr) / (2 * Math.tan((16 * Math.PI) / 180)), -1000), [parts, size.height, dpr]);
  (points.material as THREE.ShaderMaterial).uniforms.uT.value = t;

  const ia = new THREE.Color("#4f7dff"), ib = new THREE.Color("#9fd0ff"), lip = new THREE.Color("#ff6f95");
  cubes.forEach((c, i) => {
    const s = cubeAt(c, t);
    A.set(c.ax[0], c.ax[1], c.ax[2]);
    Q.setFromAxisAngle(A, s.qa + 0.09 * (((i * 7.31) % 1) - 0.5)); // tiny resting tilt: each cube catches the light
    M.compose(P.set(s.x, s.y, s.z), Q, S.setScalar(Math.max(0.0001, s.scale)));
    meshes.box.setMatrixAt(i, M);
    meshes.glow.setMatrixAt(i, M);
    const g = s.g * glowBoost;
    if (c.v < -0.4) C.copy(lip).multiplyScalar(g * g * 0.9);
    else C.copy(ia).lerp(ib, s.hue).multiplyScalar(g * g * 1.25);
    meshes.glow.setColorAt(i, C);
  });
  meshes.box.instanceMatrix.needsUpdate = true;
  meshes.glow.instanceMatrix.needsUpdate = true;
  meshes.glow.instanceColor!.needsUpdate = true;

  const [cx, cy, cz, lx, ly, lz] = camAt(t);
  camera.position.set(lx + (cx - lx) * zoom, ly + (cy - ly) * zoom, lz + (cz - lz) * zoom);
  camera.lookAt(lx, ly, lz);
  camera.updateMatrixWorld();
  const focus = camera.position.distanceTo(new THREE.Vector3(lx, ly, lz));
  const u = composer.bokeh.uniforms as Record<string, THREE.IUniform>;
  u.focus.value = focus;
  u.aperture.value = 0.0022 / Math.max(1, focus * 0.6);
  const fx = Math.min(1, Math.max(0, (t - GSTORY.fade[0]) / (GSTORY.fade[1] - GSTORY.fade[0])));
  composer.post.uniforms.uFade.value = fx * fx * (3 - 2 * fx);

  useFrame(() => composer.c.render(), 1);

  return (
    <>
      <hemisphereLight args={["#ffe9f0", "#b9a2f0", 0.18]} />
      <directionalLight
        position={[-7, 3.5, 5]}
        intensity={3.0}
        color="#fff0e2"
        castShadow
        shadow-mapSize={[4096, 4096]}
        shadow-camera-left={-5}
        shadow-camera-right={5}
        shadow-camera-top={6}
        shadow-camera-bottom={-6}
        shadow-camera-near={1}
        shadow-camera-far={30}
        shadow-bias={-0.0004}
        shadow-radius={5}
      />
      <directionalLight position={[5, -2, 4]} intensity={0.8} color="#c9d8ff" />
      <primitive object={meshes.box} />
      <primitive object={meshes.glow} />
      <primitive object={points} />
    </>
  );
};

export const GlassScene: React.FC<{ cubes: GlassCube[]; t: number; parts: ParticleData; dpr?: number; zoom?: number; glowBoost?: number }> = ({
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
      camera={{ fov: 32, near: 0.1, far: 80, position: [0, 0.5, 9] }}
    >
      <Contents {...props} dpr={dpr} zoom={zoom} glowBoost={glowBoost} />
    </ThreeCanvas>
  );
};
