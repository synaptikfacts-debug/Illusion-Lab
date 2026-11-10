import { useFrame, useThree } from "@react-three/fiber";
import { ThreeCanvas } from "@remotion/three";
import React, { useMemo } from "react";
import { useVideoConfig } from "remotion";
import * as THREE from "three";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { OutputPass } from "three/examples/jsm/postprocessing/OutputPass.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { ShaderPass } from "three/examples/jsm/postprocessing/ShaderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { camAt, INK_GLSL, ISTORY } from "./ink";

const VERT = /* glsl */ `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`;
const FRAG = /* glsl */ `${INK_GLSL}
varying vec2 vUv;
void main() { gl_FragColor = vec4(shade(vUv), 1.0); }`;

const POST = {
  uniforms: { tDiffuse: { value: null }, uFade: { value: 1 }, uSeed: { value: 0 } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `uniform sampler2D tDiffuse; uniform float uFade, uSeed; varying vec2 vUv;
    void main(){ vec4 c = texture2D(tDiffuse, vUv); vec2 d = (vUv - 0.5) * vec2(1.0, 1.25);
    c.rgb *= 1.0 - 0.35 * smoothstep(0.35, 0.95, length(d));
    float e = smoothstep(0.0, 1.0, uFade * 1.6 - length(d) * 0.9);
    c.rgb *= mix(uFade * uFade, 1.0, e * uFade);
    // fine film grain: no banding in the dark water, crisp HD texture
    float g = fract(sin(dot(gl_FragCoord.xy + uSeed, vec2(12.9898, 78.233))) * 43758.5453);
    c.rgb += (g - 0.5) * 0.012; gl_FragColor = c; }`,
};

const Contents: React.FC<{ t: number; dpr: number }> = ({ t, dpr }) => {
  const { gl, scene, camera, size } = useThree();
  const mats = useMemo(() => {
    scene.background = new THREE.Color("#010205");
    gl.toneMapping = THREE.ACESFilmicToneMapping;
    gl.toneMappingExposure = 1.0;
    const mat = new THREE.ShaderMaterial({
      vertexShader: VERT,
      fragmentShader: FRAG,
      depthTest: false,
      uniforms: {
        uT: { value: 0 },
        uDrop: { value: ISTORY.drops.map((d) => new THREE.Vector4(d[0], d[1], d[2], d[3])) },
        uCol: { value: ISTORY.drops.map((d) => new THREE.Vector3(...(ISTORY.colours[d[4]] as [number, number, number]))) },
        uVortT: { value: [...ISTORY.vortex] },
        uView: { value: new THREE.Vector2(1, 1) },
        uZoom: { value: 1 },
        uAng: { value: 0 },
      },
    });
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), mat);
    mesh.frustumCulled = false;
    return { mat, mesh };
  }, [gl, scene]);

  const composer = useMemo(() => {
    const w = size.width, h = size.height;
    const c = new EffectComposer(gl);
    c.setPixelRatio(dpr);
    c.setSize(w, h);
    c.addPass(new RenderPass(scene, camera));
    c.addPass(new UnrealBloomPass(new THREE.Vector2(w * dpr, h * dpr), 0.12, 0.3, 0.75));
    c.addPass(new OutputPass());
    const post = new ShaderPass(POST);
    c.addPass(post);
    return { c, post };
  }, [gl, scene, camera, size.width, size.height, dpr]);

  const u = mats.mat.uniforms;
  const cam = camAt(t);
  u.uT.value = t;
  u.uZoom.value = cam.zoom;
  u.uAng.value = cam.ang;
  u.uView.value.set(size.width / size.height, 1.0);
  const fx = Math.min(1, Math.max(0, (t - ISTORY.fade[0]) / (ISTORY.fade[1] - ISTORY.fade[0])));
  composer.post.uniforms.uFade.value = 1 - fx * fx * (3 - 2 * fx);
  composer.post.uniforms.uSeed.value = (t * 37.0) % 100;
  useFrame(() => composer.c.render(), 1);
  return <primitive object={mats.mesh} />;
};

export const InkScene: React.FC<{ t: number; dpr?: number }> = ({ dpr = 2, ...props }) => {
  const { width, height } = useVideoConfig();
  return (
    <ThreeCanvas width={width} height={height} dpr={dpr} gl={{ antialias: false, preserveDrawingBuffer: true, powerPreference: "high-performance" }} camera={{ position: [0, 0, 1] }}>
      <Contents {...props} dpr={dpr} />
    </ThreeCanvas>
  );
};
