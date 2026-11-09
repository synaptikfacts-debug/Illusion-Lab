import { ThreeCanvas } from "@remotion/three";
import React, { useMemo } from "react";
import { useVideoConfig } from "remotion";
import * as THREE from "three";

const VERT = /* glsl */ `
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = vec4(position.xy, 0.0, 1.0);
}`;

export type UniformValue = number | THREE.Vector2 | THREE.Vector3 | THREE.Vector4 | THREE.Texture | null;

/**
 * Full-frame fragment shader on the GPU. Pass uniforms as plain values; they are updated every frame.
 * `uRes` (pixels) and `uAspect` (w/h) are always provided. Colours: use `rgb()` so they stay sRGB (no colour management).
 */
export const ShaderPlane: React.FC<{ frag: string; uniforms: Record<string, UniformValue> }> = ({ frag, uniforms }) => {
  const { width, height } = useVideoConfig();
  const material = useMemo(
    () =>
      new THREE.ShaderMaterial({
        vertexShader: VERT,
        fragmentShader: frag,
        uniforms: { uRes: { value: new THREE.Vector2(width, height) }, uAspect: { value: width / height } },
        depthTest: false,
        depthWrite: false,
      }),
    [frag, width, height],
  );
  for (const [k, v] of Object.entries(uniforms)) {
    if (material.uniforms[k]) material.uniforms[k].value = v;
    else material.uniforms[k] = { value: v };
  }
  return (
    <ThreeCanvas width={width} height={height} linear flat gl={{ antialias: false, preserveDrawingBuffer: true }}>
      <mesh frustumCulled={false} material={material}>
        <planeGeometry args={[2, 2]} />
      </mesh>
    </ThreeCanvas>
  );
};

/** "#rrggbb" -> sRGB vec3 (0..1), bypassing three's colour management. */
export function rgb(hex: string): THREE.Vector3 {
  const n = parseInt(hex.slice(1), 16);
  return new THREE.Vector3(((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255);
}

export const vec2 = (x: number, y: number) => new THREE.Vector2(x, y);
