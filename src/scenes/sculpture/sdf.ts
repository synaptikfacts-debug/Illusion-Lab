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

/** n points on a 3D heart (Taubin heart surface). Rays from the centre, bisected to the surface: no creases. */
export function sampleHeart(n: number, seed: number): Float32Array {
  const out = new Float32Array(n * 3), r = rng(seed, 'heart'), S = 0.72;
  const f = (x: number, y: number, z: number) => {
    const a = x * x + 2.25 * y * y + z * z - 1;
    return a * a * a - x * x * z * z * z - 0.1125 * y * y * z * z * z;
  };
  for (let i = 0; i < n; i++) {
    const u = r() * 2 - 1, th = r() * Math.PI * 2, sq = Math.sqrt(1 - u * u);
    const dx = sq * Math.cos(th), dy = sq * Math.sin(th) * 0.75, dz = u;
    let lo = 0, hi = 0.02;
    while (hi < 2.5 && f(dx * hi, dy * hi, dz * hi) < 0) { lo = hi; hi += 0.02; }
    for (let k = 0; k < 24; k++) {
      const m = (lo + hi) / 2;
      if (f(dx * m, dy * m, dz * m) < 0) lo = m; else hi = m;
    }
    const m = (lo + hi) / 2;
    out[i * 3] = dx * m * S; out[i * 3 + 1] = dz * m * S + 0.05; out[i * 3 + 2] = dy * m * S;
  }
  return out;
}
