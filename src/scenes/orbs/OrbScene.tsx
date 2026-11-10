import { useFrame, useThree } from "@react-three/fiber";
import { ThreeCanvas } from "@remotion/three";
import React, { useMemo } from "react";
import { useVideoConfig } from "remotion";
import * as THREE from "three";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { Reflector } from "three/examples/jsm/objects/Reflector.js";
import { BokehPass } from "three/examples/jsm/postprocessing/BokehPass.js";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { OutputPass } from "three/examples/jsm/postprocessing/OutputPass.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { ShaderPass } from "three/examples/jsm/postprocessing/ShaderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { OP, orbAt, SYNC_AT, type Orb } from "./orbs";

/** Our look: midnight studio, black-mirror plate with a gold rim, pearl -> peach -> coral -> magenta -> indigo orbs. */
const GRADIENT = ["#fff3e4", "#ffc39a", "#ff6f7d", "#d93fa8", "#6a43f2"];

/** Camera: slow continuous orbit (half a turn over the reel). Low and close in the hook, rising to a 3/4 view,
 *  high and centred for the in-phase climax, easing back for the settle. [t, radius, height, lookY] */
const CAM: number[][] = [
  [0, 8.4, 4.4, 0.3],
  [3, 8.2, 5.0, 0.3],
  [12, 9.0, 6.6, 0.2],
  [20, 8.8, 5.8, 0.3],
  [SYNC_AT - 1.2, 9.2, 5.6, 0.3],
  [SYNC_AT + 1.5, 9.4, 5.8, 0.3],
  [30, 11.5, 7.0, 0.2],
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

const M = new THREE.Matrix4(), Q = new THREE.Quaternion(), P = new THREE.Vector3(), S = new THREE.Vector3();

function gradientAt(stops: THREE.Color[], x: number) {
  const f = Math.min(0.9999, Math.max(0, x)) * (stops.length - 1), i = Math.floor(f);
  return stops[i].clone().lerp(stops[i + 1], f - i);
}

const Contents: React.FC<{ orbs: Orb[]; t: number; dpr: number; zoom: number }> = ({ orbs, t, dpr, zoom }) => {
  const { gl, scene, camera, size } = useThree();

  useMemo(() => {
    const pmrem = new THREE.PMREMGenerator(gl);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.03).texture;
    scene.environmentIntensity = 0.6;
    const c = document.createElement("canvas");
    c.width = 4; c.height = 512;
    const g = c.getContext("2d")!;
    const gr = g.createLinearGradient(0, 0, 0, 512);
    gr.addColorStop(0, "#020208"); gr.addColorStop(0.55, "#0d0b22"); gr.addColorStop(1, "#05040c");
    g.fillStyle = gr; g.fillRect(0, 0, 4, 512);
    const tex = new THREE.CanvasTexture(c);
    tex.colorSpace = THREE.SRGBColorSpace;
    scene.background = tex;
    pmrem.dispose();
    gl.toneMapping = THREE.ACESFilmicToneMapping;
    gl.toneMappingExposure = 1.0;
  }, [gl, scene]);

  const parts = useMemo(() => {
    const mesh = new THREE.InstancedMesh(
      new THREE.SphereGeometry(1, 24, 16),
      new THREE.MeshPhysicalMaterial({ roughness: 0.1, metalness: 0.05, clearcoat: 1, clearcoatRoughness: 0.04, iridescence: 0.35, iridescenceIOR: 1.4 }),
      orbs.length,
    );
    mesh.castShadow = true;
    mesh.frustumCulled = false;
    const stops = GRADIENT.map((c) => new THREE.Color(c));
    orbs.forEach((o, i) => mesh.setColorAt(i, gradientAt(stops, o.r01)));
    mesh.instanceColor!.needsUpdate = true;
    const R = OP.discRadius + 0.22;
    const mirror = new Reflector(new THREE.CircleGeometry(R, 160), { textureWidth: 1024, textureHeight: 1024, color: new THREE.Color("#22222c") });
    mirror.rotation.x = -Math.PI / 2;
    mirror.position.y = 0.001;
    return { mesh, mirror, R };
  }, [orbs]);

  const composer = useMemo(() => {
    const w = size.width, h = size.height;
    const c = new EffectComposer(gl);
    c.setPixelRatio(dpr);
    c.setSize(w, h);
    c.addPass(new RenderPass(scene, camera));
    const bokeh = new BokehPass(scene, camera, { focus: 8, aperture: 0.001, maxblur: 0.008 });
    c.addPass(bokeh);
    c.addPass(new UnrealBloomPass(new THREE.Vector2(w * dpr, h * dpr), 0.1, 0.35, 1.8));
    c.addPass(new OutputPass());
    const post = new ShaderPass(POST);
    c.addPass(post);
    return { c, bokeh, post };
  }, [gl, scene, camera, size.width, size.height, dpr]);

  orbs.forEach((o, i) => {
    const { y, squash } = orbAt(o, t);
    M.compose(P.set(o.x, y + o.size * (1 - squash), o.z), Q, S.set(o.size * (1 + squash * 0.5), o.size * (1 - squash), o.size * (1 + squash * 0.5)));
    parts.mesh.setMatrixAt(i, M);
  });
  parts.mesh.instanceMatrix.needsUpdate = true;

  const [rad, ht, ly] = camAt(t);
  const ang = 0.6 + (Math.PI * t) / OP.duration; // half a turn over the reel
  const rr = rad * zoom;
  camera.position.set(Math.sin(ang) * rr, ht * zoom, Math.cos(ang) * rr);
  camera.lookAt(0, ly, 0);
  camera.updateMatrixWorld();
  const b = composer.bokeh.uniforms as Record<string, THREE.IUniform>;
  b.focus.value = camera.position.distanceTo(new THREE.Vector3(0, ly, 0));
  b.aperture.value = 0.0028 / Math.max(1, b.focus.value * 0.6);
  const fx = Math.min(1, Math.max(0, (t - OP.fade[0]) / (OP.fade[1] - OP.fade[0])));
  composer.post.uniforms.uFade.value = 1 - fx * fx * (3 - 2 * fx);
  useFrame(() => composer.c.render(), 1);

  return (
    <>
      <hemisphereLight args={["#e9e6ff", "#120c1c", 0.35]} />
      <directionalLight position={[-5, 9, 4]} intensity={2.4} color="#fff2e6" castShadow shadow-mapSize={[4096, 4096]} shadow-camera-left={-4} shadow-camera-right={4} shadow-camera-top={4} shadow-camera-bottom={-4} shadow-bias={-0.0004} shadow-radius={3} />
      <pointLight position={[4, 3, -3]} intensity={25} color="#ff5fa8" />
      <pointLight position={[-4, 2.5, -2]} intensity={20} color="#6f5cff" />
      <primitive object={parts.mesh} />
      <primitive object={parts.mirror} />
      <mesh rotation-x={-Math.PI / 2} position-y={0.003} receiveShadow>
        <circleGeometry args={[parts.R, 160]} />
        <shadowMaterial opacity={0.55} />
      </mesh>
      {/* gold rim */}
      <mesh rotation-x={-Math.PI / 2} position-y={0.02}>
        <torusGeometry args={[parts.R, 0.05, 20, 200]} />
        <meshStandardMaterial color="#d8a94f" metalness={1} roughness={0.2} />
      </mesh>
      <mesh position-y={-0.16} receiveShadow>
        <cylinderGeometry args={[parts.R, parts.R * 0.97, 0.3, 160]} />
        <meshPhysicalMaterial color="#0b0b10" roughness={0.3} clearcoat={1} />
      </mesh>
    </>
  );
};

export const OrbScene: React.FC<{ orbs: Orb[]; t: number; dpr?: number; zoom?: number }> = ({ dpr = 2, zoom = 1, ...props }) => {
  const { width, height } = useVideoConfig();
  return (
    <ThreeCanvas width={width} height={height} dpr={dpr} shadows="soft" gl={{ antialias: true, preserveDrawingBuffer: true, powerPreference: "high-performance" }} camera={{ fov: 32, near: 0.1, far: 80, position: [0, 6, 9] }}>
      <Contents {...props} dpr={dpr} zoom={zoom} />
    </ThreeCanvas>
  );
};
