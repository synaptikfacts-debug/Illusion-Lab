// "Ferrofluid Labyrinth": the labyrinth pattern real ferrofluid forms when squeezed thin between two glass plates in a
// magnetic field (Hele-Shaw labyrinthine instability). Generated with Gray-Scott reaction-diffusion in its "maze"
// regime (same stripe physics: constant channel width, branching, dead ends), confined to a round drop.
import { rng } from "../../core/seed";

export const MAZE = { w: 540, h: 960, seed: 10303, feed: 0.029, kill: 0.057, steps: 7000, dropR: 2.2 };

/** Runs the simulation; returns the B field (0..~0.5; fluid where B is high), row-major w x h. */
export function simulateMaze(): Float32Array {
  const { w, h, feed, kill, steps, dropR } = MAZE;
  const r = rng(MAZE.seed, "maze");
  let A = new Float32Array(w * h).fill(1), B = new Float32Array(w * h);
  let A2 = new Float32Array(w * h), B2 = new Float32Array(w * h);
  const inside = new Uint8Array(w * h);
  for (let j = 0; j < h; j++)
    for (let i = 0; i < w; i++) {
      const x = (i - w / 2) / (w / 2), y = ((j - h / 2) / (w / 2));
      const th = Math.atan2(y, x), rr = Math.hypot(x, y);
      const edge = dropR * (1 + 0.04 * Math.sin(5 * th + 1.1) + 0.025 * Math.sin(9 * th));
      if (rr < edge) inside[j * w + i] = 1;
    }
  for (let s = 0; s < 260; s++) {
    const ci = Math.floor(r() * w), cj = Math.floor(r() * h);
    for (let dj = -2; dj <= 2; dj++)
      for (let di = -2; di <= 2; di++) {
        const i = ci + di, j = cj + dj;
        if (i >= 0 && j >= 0 && i < w && j < h && inside[j * w + i]) { A[j * w + i] = 0.5; B[j * w + i] = 0.25; }
      }
  }
  for (let it = 0; it < steps; it++) {
    for (let j = 1; j < h - 1; j++)
      for (let i = 1; i < w - 1; i++) {
        const k = j * w + i;
        if (!inside[k]) { A2[k] = 1; B2[k] = 0; continue; }
        const lapA = 0.2 * (A[k - 1] + A[k + 1] + A[k - w] + A[k + w]) + 0.05 * (A[k - w - 1] + A[k - w + 1] + A[k + w - 1] + A[k + w + 1]) - A[k];
        const lapB = 0.2 * (B[k - 1] + B[k + 1] + B[k - w] + B[k + w]) + 0.05 * (B[k - w - 1] + B[k - w + 1] + B[k + w - 1] + B[k + w + 1]) - B[k];
        const abb = A[k] * B[k] * B[k];
        A2[k] = A[k] + lapA - abb + feed * (1 - A[k]);
        B2[k] = B[k] + 0.5 * lapB + abb - (kill + feed) * B[k];
      }
    [A, A2] = [A2, A];
    [B, B2] = [B2, B];
  }
  return B;
}

/**
 * Growth mode (the animation): one round drop in the middle bursts into a labyrinth whose front spreads outward over
 * the whole cell, like real ferrofluid between glass plates when the field comes on. Calls onSnap(step, B) every
 * `every` steps (B is reused: copy it if you keep it).
 */
export function simulateGrowth(steps: number, every: number, onSnap: (step: number, B: Float32Array) => void, dropR0 = 0.11) {
  const { w, h, feed, kill } = MAZE;
  const r = rng(MAZE.seed, "growth");
  let A = new Float32Array(w * h).fill(1), B = new Float32Array(w * h);
  let A2 = new Float32Array(w * h).fill(1), B2 = new Float32Array(w * h);
  for (let j = 0; j < h; j++)
    for (let i = 0; i < w; i++) {
      const x = (i - w / 2) / (w / 2), y = (j - h / 2) / (w / 2);
      const th = Math.atan2(y, x); // irregular edge (no symmetric petals)
      if (Math.hypot(x, y) < dropR0 * (1 + 0.05 * Math.sin(3 * th + 1.3) + 0.035 * Math.sin(7 * th + 0.4) + 0.025 * Math.sin(11 * th + 2.2))) {
        const k = j * w + i;
        A[k] = 0.5 + 0.04 * (r() - 0.5);
        B[k] = 0.25 + 0.04 * (r() - 0.5);
      }
    }
  onSnap(0, B);
  for (let it = 1; it <= steps; it++) {
    for (let j = 1; j < h - 1; j++)
      for (let i = 1; i < w - 1; i++) {
        const k = j * w + i;
        const lapA = 0.2 * (A[k - 1] + A[k + 1] + A[k - w] + A[k + w]) + 0.05 * (A[k - w - 1] + A[k - w + 1] + A[k + w - 1] + A[k + w + 1]) - A[k];
        const lapB = 0.2 * (B[k - 1] + B[k + 1] + B[k - w] + B[k + w]) + 0.05 * (B[k - w - 1] + B[k - w + 1] + B[k + w - 1] + B[k + w + 1]) - B[k];
        const abb = A[k] * B[k] * B[k];
        A2[k] = A[k] + lapA - abb + feed * (1 - A[k]);
        B2[k] = B[k] + 0.5 * lapB + abb - (kill + feed) * B[k];
      }
    [A, A2] = [A2, A];
    [B, B2] = [B2, B];
    if (it % every === 0) onSnap(it, B);
  }
}
