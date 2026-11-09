import { useThree } from "@react-three/fiber";
import { ThreeCanvas } from "@remotion/three";
import React, { useMemo } from "react";
import { useVideoConfig } from "remotion";
import * as THREE from "three";
import { Reflector } from "three/examples/jsm/objects/Reflector.js";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { layout, orbState, type BounceParams } from "./physics";

export interface BounceLook {
  background: string;
  plate: string;
  /** Orb colours from the centre of the disc to the edge. */
  gradient: string[];
}

const tmpM = new THREE.Matrix4(), tmpQ = new THREE.Quaternion(), tmpP = new THREE.Vector3(), tmpS = new THREE.Vector3();

function gradientAt(stops: THREE.Color[], x: number): THREE.Color {
  const f = Math.min(0.9999, Math.max(0, x)) * (stops.length - 1), i = Math.floor(f);
  return stops[i].clone().lerp(stops[i + 1], f - i);
}

const Contents: React.FC<{ t: number; seed: number; params: BounceParams; look: BounceLook; sway: number }> = ({
  t,
  seed,
  params,
  look,
  sway,
}) => {
  const { gl, scene, camera, size } = useThree();
  const key = JSON.stringify(params);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const orbs = useMemo(() => layout(params, seed), [key, seed]);

  // environment for glossy reflections (deterministic, built once)
  useMemo(() => {
    const pmrem = new THREE.PMREMGenerator(gl);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    scene.background = new THREE.Color(look.background);
    pmrem.dispose();
  }, [gl, scene, look.background]);

  const mesh = useMemo(() => {
    const geo = new THREE.SphereGeometry(1, 20, 14);
    const mat = new THREE.MeshPhysicalMaterial({ roughness: 0.18, metalness: 0.15, clearcoat: 1, clearcoatRoughness: 0.08, envMapIntensity: 1.1 });
    const m = new THREE.InstancedMesh(geo, mat, orbs.length);
    m.castShadow = true;
    m.frustumCulled = false;
    const stops = look.gradient.map((c) => new THREE.Color(c));
    orbs.forEach((o, i) => m.setColorAt(i, gradientAt(stops, o.r01)));
    m.instanceColor!.needsUpdate = true;
    return m;
  }, [orbs, look.gradient]);

  const mirror = useMemo(() => {
    const R = params.discRadius + 0.25;
    const r = new Reflector(new THREE.CircleGeometry(R, 128), {
      textureWidth: Math.round(size.width),
      textureHeight: Math.round(size.width),
      color: new THREE.Color("#8a8f99"),
    });
    r.rotation.x = -Math.PI / 2;
    r.position.y = 0.001;
    return r;
  }, [params.discRadius, size.width]);

  // orbs: bounce + squash on impact
  orbs.forEach((o, i) => {
    const { y, toImpact } = orbState(o, params, t);
    const squash = 0.28 * Math.exp(-((toImpact / 0.03) ** 2));
    tmpP.set(o.x, y + o.size * (1 - squash), o.z);
    tmpS.set(o.size * (1 + squash * 0.5), o.size * (1 - squash), o.size * (1 + squash * 0.5));
    tmpM.compose(tmpP, tmpQ, tmpS);
    mesh.setMatrixAt(i, tmpM);
  });
  mesh.instanceMatrix.needsUpdate = true;

  // camera: elevated three-quarter view with a slow sway that returns to the start at the loop point
  const ang = sway;
  const D = 24, el = (26 * Math.PI) / 180;
  camera.position.set(Math.sin(ang) * Math.cos(el) * D, Math.sin(el) * D + 0.4, Math.cos(ang) * Math.cos(el) * D);
  camera.lookAt(0, 0.75, 0);

  const R = params.discRadius + 0.25;
  return (
    <>
      <hemisphereLight args={["#cfd8ff", "#0a0a12", 0.6]} />
      <directionalLight
        position={[-4, 12, 6]}
        intensity={2.2}
        castShadow
        shadow-mapSize={[2048, 2048]}
        shadow-camera-left={-5}
        shadow-camera-right={5}
        shadow-camera-top={5}
        shadow-camera-bottom={-5}
        shadow-bias={-0.0004}
      />
      <pointLight position={[5, 4, -3]} intensity={30} color={look.gradient[look.gradient.length - 1]} />
      <primitive object={mesh} />
      <primitive object={mirror} />
      {/* milky glass top over the mirror: soft reflection + shadows */}
      <mesh rotation-x={-Math.PI / 2} position-y={0.003} receiveShadow>
        <circleGeometry args={[R, 128]} />
        <meshStandardMaterial color={look.plate} transparent opacity={0.78} roughness={0.35} metalness={0} />
      </mesh>
      <mesh position-y={-0.11} receiveShadow castShadow>
        <cylinderGeometry args={[R, R * 0.98, 0.22, 128]} />
        <meshPhysicalMaterial color={look.plate} roughness={0.25} clearcoat={1} />
      </mesh>
    </>
  );
};

export const BounceScene: React.FC<{ t: number; seed: number; params: BounceParams; look: BounceLook; sway: number }> = (props) => {
  const { width, height } = useVideoConfig();
  return (
    <ThreeCanvas
      width={width}
      height={height}
      shadows
      gl={{ antialias: true, preserveDrawingBuffer: true }}
      camera={{ fov: 28, near: 0.5, far: 100, position: [0, 10, 22] }}
    >
      <Contents {...props} />
    </ThreeCanvas>
  );
};
