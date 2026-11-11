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
import { camShow, heightAt, layoutShow, SHOW, tipsAt } from "./show";

const M = new THREE.Matrix4(), Q = new THREE.Quaternion(), P = new THREE.Vector3(), Sc = new THREE.Vector3();
const CA = new THREE.Color(), CB = new THREE.Color(), C = new THREE.Color();
const cache = new Map<string, THREE.Color>();
const col = (h: string) => { let c = cache.get(h); if (!c) { c = new THREE.Color(h); cache.set(h, c); } return c; };

function grad(stops: string[], x: number, out: THREE.Color) {
  const f = Math.min(0.9999, Math.max(0, x)) * (stops.length - 1), i = Math.floor(f);
  return out.copy(col(stops[i])).lerp(col(stops[i + 1]), f - i);
}

const POST = {
  uniforms: { tDiffuse: { value: null }, uFade: { value: 1 }, uSeed: { value: 0 } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `uniform sampler2D tDiffuse; uniform float uFade, uSeed; varying vec2 vUv;
    void main(){ vec4 c = texture2D(tDiffuse, vUv); vec2 d = (vUv - 0.5) * vec2(1.0, 1.25);
    c.rgb *= 1.0 - 0.38 * smoothstep(0.32, 0.95, length(d));
    float e = smoothstep(0.0, 1.0, uFade * 1.6 - length(d) * 0.9);
    c.rgb *= mix(uFade * uFade, 1.0, e * uFade);
    float g = fract(sin(dot(gl_FragCoord.xy + uSeed, vec2(12.9898, 78.233))) * 43758.5453);
    c.rgb += (g - 0.5) * 0.01; gl_FragColor = c; }`,
};

const Contents: React.FC<{ t: number; dpr: number }> = ({ t, dpr }) => {
  const { gl, scene, camera, size } = useThree();
  const pins = useMemo(() => layoutShow(), []);
  const R = SHOW.spacing * 0.33;

  useMemo(() => {
    const pmrem = new THREE.PMREMGenerator(gl);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    pmrem.dispose();
    gl.toneMapping = THREE.ACESFilmicToneMapping;
    gl.toneMappingExposure = 1.0;
    // deep violet studio with a soft horizontal glow band behind the wall
    const c = document.createElement("canvas");
    c.width = 4; c.height = 512;
    const g = c.getContext("2d")!;
    const gr = g.createLinearGradient(0, 0, 0, 512);
    gr.addColorStop(0, "#020208");
    gr.addColorStop(0.36, "#1a0f3d");
    gr.addColorStop(0.5, "#2a1660");
    gr.addColorStop(0.64, "#120b30");
    gr.addColorStop(1, "#020208");
    g.fillStyle = gr; g.fillRect(0, 0, 4, 512);
    const tex = new THREE.CanvasTexture(c);
    tex.colorSpace = THREE.SRGBColorSpace;
    scene.background = tex;
  }, [gl, scene]);

  const { shafts, tips } = useMemo(() => {
    const sg = new THREE.CylinderGeometry(R * 0.7, R * 0.7, 1, 12, 1);
    sg.translate(0, 0.5, 0);
    const shafts = new THREE.InstancedMesh(sg, new THREE.MeshPhysicalMaterial({ color: "#4a4f68", metalness: 0.88, roughness: 0.34, clearcoat: 0.3, clearcoatRoughness: 0.4 }), pins.length);
    const tips = new THREE.InstancedMesh(new THREE.SphereGeometry(R, 20, 14), new THREE.MeshBasicMaterial({ toneMapped: false }), pins.length);
    for (const m of [shafts, tips]) m.frustumCulled = false;
    tips.setColorAt(0, C.set("#ffffff"));
    return { shafts, tips };
  }, [pins.length, R]);

  const mirror = useMemo(() => {
    const w = SHOW.grid * SHOW.spacing + 0.5;
    const m = new Reflector(new THREE.PlaneGeometry(w, w), {
      textureWidth: Math.round(size.width * dpr),
      textureHeight: Math.round(size.width * dpr),
      color: new THREE.Color("#4a4f66"),
    });
    m.rotation.x = -Math.PI / 2;
    return m;
  }, [size.width, dpr]);

  const composer = useMemo(() => {
    const w = size.width, h = size.height;
    const c = new EffectComposer(gl);
    c.setPixelRatio(dpr);
    c.setSize(w, h);
    c.addPass(new RenderPass(scene, camera));
    const bokeh = new BokehPass(scene, camera, { focus: 28, aperture: 0.00012, maxblur: 0.006 });
    c.addPass(bokeh);
    c.addPass(new UnrealBloomPass(new THREE.Vector2(w * dpr, h * dpr), 0.32, 0.35, 0.82));
    c.addPass(new OutputPass());
    const post = new ShaderPass(POST);
    c.addPass(post);
    return { c, bokeh, post };
  }, [gl, scene, camera, size.width, size.height, dpr]);

  // pins
  const tp = tipsAt(t);
  pins.forEach((pin, i) => {
    const h = heightAt(pin, t);
    const hh = 0.03 + h;
    M.compose(P.set(pin.x, 0, pin.z), Q, Sc.set(1, hh, 1));
    shafts.setMatrixAt(i, M);
    M.compose(P.set(pin.x, hh, pin.z), Q, Sc.set(1, 1, 1));
    tips.setMatrixAt(i, M);
    const x = h / SHOW.maxHeight;
    grad(tp.a, x, CA);
    grad(tp.b, x, CB);
    tips.setColorAt(i, C.copy(CA).lerp(CB, tp.mix).multiplyScalar(0.5 + 0.45 * x));
  });
  shafts.instanceMatrix.needsUpdate = true;
  tips.instanceMatrix.needsUpdate = true;
  tips.instanceColor!.needsUpdate = true;

  // camera: corner-on, tilts over the top as each picture forms, a slow drift over the minute; ends high and wide
  const cam = camShow(t);
  const D = cam.D;
  camera.position.set(...cam.pos);
  camera.lookAt(...cam.look);
  camera.updateMatrixWorld();

  const b = composer.bokeh.uniforms as Record<string, THREE.IUniform>;
  b.focus.value = D;
  const fx = Math.min(1, Math.max(0, (t - SHOW.fade[0]) / (SHOW.fade[1] - SHOW.fade[0])));
  composer.post.uniforms.uFade.value = 1 - fx * fx * (3 - 2 * fx);
  composer.post.uniforms.uSeed.value = (t * 37) % 100;
  useFrame(() => composer.c.render(), 1);

  const half = (SHOW.grid * SHOW.spacing) / 2 + 0.3;
  const cTop = col(tp.a[2]), cLow = col(tp.a[1]);
  return (
    <>
      <hemisphereLight args={["#b9c6ff", "#05050a", 0.45]} />
      <directionalLight position={[-5, 10, 4]} intensity={0.8} />
      <pointLight position={[half + 1, 2.5, -half]} intensity={45} color={cTop} />
      <pointLight position={[-half - 1, 2, half * 0.3]} intensity={32} color={cLow} />
      <primitive object={mirror} />
      <primitive object={shafts} />
      <primitive object={tips} />
    </>
  );
};

export const PinShowScene: React.FC<{ t: number; dpr?: number }> = ({ dpr = 2, ...props }) => {
  const { width, height } = useVideoConfig();
  return (
    <ThreeCanvas width={width} height={height} dpr={dpr} gl={{ antialias: true, preserveDrawingBuffer: true, powerPreference: "high-performance" }} camera={{ fov: 30, near: 0.5, far: 100, position: [0, 10, 18] }}>
      <Contents {...props} dpr={dpr} />
    </ThreeCanvas>
  );
};
