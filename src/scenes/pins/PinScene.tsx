import { useThree } from "@react-three/fiber";
import { ThreeCanvas } from "@remotion/three";
import React, { useMemo } from "react";
import { useVideoConfig } from "remotion";
import * as THREE from "three";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { Reflector } from "three/examples/jsm/objects/Reflector.js";
import { clockW, height, layout, type PinParams } from "./physics";

export interface PinLook {
  background: string;
  /** Glowing tip colours from low to high. */
  tips: string[];
  shaft: string;
}

const M = new THREE.Matrix4(), Q = new THREE.Quaternion(), P = new THREE.Vector3(), S = new THREE.Vector3(), C = new THREE.Color();

function gradient(stops: THREE.Color[], x: number, out: THREE.Color) {
  const f = Math.min(0.9999, Math.max(0, x)) * (stops.length - 1), i = Math.floor(f);
  return out.copy(stops[i]).lerp(stops[i + 1], f - i);
}

const Contents: React.FC<{ t: number; params: PinParams; look: PinLook; sway: number }> = ({ t, params, look, sway }) => {
  const { gl, scene, camera, size } = useThree();
  const key = JSON.stringify(params);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const pins = useMemo(() => layout(params), [key]);
  const stops = useMemo(() => look.tips.map((c) => new THREE.Color(c)), [look.tips]);

  useMemo(() => {
    const pmrem = new THREE.PMREMGenerator(gl);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    // soft vertical glow behind the wall instead of flat black
    const c = document.createElement("canvas");
    c.width = 4; c.height = 512;
    const g = c.getContext("2d")!;
    const grad = g.createLinearGradient(0, 0, 0, 512);
    grad.addColorStop(0, look.background);
    grad.addColorStop(0.42, look.tips[1] + "38");
    grad.addColorStop(0.6, look.tips[0] + "30");
    grad.addColorStop(1, look.background);
    g.fillStyle = look.background; g.fillRect(0, 0, 4, 512);
    g.fillStyle = grad; g.fillRect(0, 0, 4, 512);
    const tex = new THREE.CanvasTexture(c);
    tex.colorSpace = THREE.SRGBColorSpace;
    scene.background = tex;
    pmrem.dispose();
  }, [gl, scene, look.background]);

  const R = params.spacing * 0.32;
  const { shafts, tips } = useMemo(() => {
    const shaftGeo = new THREE.CylinderGeometry(R * 0.72, R * 0.72, 1, 10, 1);
    shaftGeo.translate(0, 0.5, 0); // origin at the base
    const shafts = new THREE.InstancedMesh(
      shaftGeo,
      new THREE.MeshPhysicalMaterial({ color: look.shaft, metalness: 0.9, roughness: 0.28, clearcoat: 0.6 }),
      pins.length,
    );
    const tips = new THREE.InstancedMesh(new THREE.SphereGeometry(R, 16, 10), new THREE.MeshBasicMaterial({ toneMapped: false }), pins.length);
    for (const m of [shafts, tips]) m.frustumCulled = false;
    shafts.castShadow = true;
    tips.setColorAt(0, C.set("#ffffff"));
    return { shafts, tips };
  }, [pins.length, R, look.shaft]);

  const mirror = useMemo(() => {
    const w = params.grid * params.spacing + 0.6;
    const m = new Reflector(new THREE.PlaneGeometry(w, w), {
      textureWidth: Math.round(size.width),
      textureHeight: Math.round(size.width),
      color: new THREE.Color("#3a3f52"),
    });
    m.rotation.x = -Math.PI / 2;
    return m;
  }, [params.grid, params.spacing, size.width]);

  pins.forEach((pin, i) => {
    const h = height(pin, params, t);
    const hh = 0.04 + h;
    M.compose(P.set(pin.x, 0, pin.z), Q, S.set(1, hh, 1));
    shafts.setMatrixAt(i, M);
    M.compose(P.set(pin.x, hh, pin.z), Q, S.set(1, 1, 1));
    tips.setMatrixAt(i, M);
    tips.setColorAt(i, gradient(stops, h / params.maxHeight, C));
  });
  shafts.instanceMatrix.needsUpdate = true;
  tips.instanceMatrix.needsUpdate = true;
  tips.instanceColor!.needsUpdate = true;

  // camera tilts over the top as the picture forms (w -> 1 mid-loop), sways gently; loops exactly
  const w = clockW(t, params.loopSec);
  const el = ((30 + 34 * w * w * w) * Math.PI) / 180;
  // wall seen corner-on (45 deg): a diamond that fills the tall frame
  const yaw = Math.PI / 4 + sway;
  const D = 28;
  camera.position.set(Math.sin(yaw) * Math.cos(el) * D, Math.sin(el) * D, Math.cos(yaw) * Math.cos(el) * D);
  camera.lookAt(0, 0.35 * (1 - w), 0);

  const half = (params.grid * params.spacing) / 2 + 0.3;
  return (
    <>
      <hemisphereLight args={["#b9c6ff", "#05050a", 0.5]} />
      <directionalLight position={[-5, 10, 4]} intensity={1.6} />
      <pointLight position={[half + 1, 2.5, -half]} intensity={40} color={look.tips[look.tips.length - 2]} />
      <pointLight position={[-half - 1, 2, half * 0.3]} intensity={30} color={look.tips[0]} />
      <primitive object={mirror} />
      <primitive object={shafts} />
      <primitive object={tips} />
    </>
  );
};

export const PinScene: React.FC<{ t: number; params: PinParams; look: PinLook; sway: number }> = (props) => {
  const { width, height: h } = useVideoConfig();
  return (
    <ThreeCanvas width={width} height={h} gl={{ antialias: true, preserveDrawingBuffer: true }} camera={{ fov: 30, near: 0.5, far: 100, position: [0, 10, 18] }}>
      <Contents {...props} />
    </ThreeCanvas>
  );
};
