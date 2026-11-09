// CPU mirror of the sculpture SDF in scene.frag.glsl (keep in sync) - used to place particles on the surface.
import { rng } from "../../core/seed";

export type Sat = [number, number, number, number]; // orbit radius, speed, phase, size

export function satellites(seed: number): Sat[] {
  const r = rng(seed, "sats");
  return Array.from({ length: 6 }, () => [
    0.62 + r() * 0.3,
    (0.35 + r() * 0.5) * (r() < 0.5 ? -1 : 1),
    r() * Math.PI * 2,
    0.15 + r() * 0.14,
  ]);
}

const smin = (a: number, b: number, k: number) => {
  const h = Math.min(1, Math.max(0, 0.5 + (0.5 * (b - a)) / k));
  return b * (1 - h) + a * h - k * h * (1 - h);
};

export function map(x: number, y: number, z: number, t: number, sats: Sat[]): number {
  let d = Math.hypot(x, y, z) - 0.62 * (1 + 0.05 * Math.sin(t * 1.7));
  d += 0.03 * Math.sin(x * 6 + t * 1.4) * Math.sin(y * 5 - t * 1.2) * Math.sin(z * 6 + t);
  for (const [or, sp, ph, sz] of sats) {
    const a = ph + t * sp;
    const sx = Math.cos(a) * or, sy = Math.sin(a * 0.83 + ph) * or * 0.75, sz2 = Math.sin(a) * or * 0.6;
    d = smin(d, Math.hypot(x - sx, y - sy, z - sz2) - sz, 0.32);
  }
  return d;
}

/** n points on the surface at time t (random points pulled onto the zero level set). xyz interleaved. */
export function sampleSurface(n: number, t: number, sats: Sat[], seed: number): Float32Array {
  const out = new Float32Array(n * 3), r = rng(seed, "surface", t.toFixed(3)), e = 0.002;
  for (let i = 0; i < n; i++) {
    const u = r() * 2 - 1, th = r() * Math.PI * 2, s = Math.sqrt(1 - u * u), rad = 0.3 + r() * 1.3;
    let x = s * Math.cos(th) * rad, y = u * rad, z = s * Math.sin(th) * rad;
    for (let k = 0; k < 7; k++) {
      const d = map(x, y, z, t, sats);
      const gx = map(x + e, y, z, t, sats) - d, gy = map(x, y + e, z, t, sats) - d, gz = map(x, y, z + e, t, sats) - d;
      const gl = Math.hypot(gx, gy, gz) || 1;
      x -= (gx / gl) * d; y -= (gy / gl) * d; z -= (gz / gl) * d;
    }
    out[i * 3] = x; out[i * 3 + 1] = y; out[i * 3 + 2] = z;
  }
  return out;
}
