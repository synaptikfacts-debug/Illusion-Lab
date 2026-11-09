// Deterministic randomness. Never use Math.random() in a reel: renders must be reproducible.

/** 32-bit string hash (FNV-1a). */
export function hash(...parts: (string | number)[]): number {
  let h = 0x811c9dc5;
  for (const ch of parts.join("|")) {
    h ^= ch.charCodeAt(0);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

/** mulberry32: fast seeded PRNG returning floats in [0, 1). */
export function rng(seed: number, ...keys: (string | number)[]): () => number {
  let a = (keys.length ? hash(seed, ...keys) : seed) >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** One stable random number for (seed, keys). */
export const rand = (seed: number, ...keys: (string | number)[]) => rng(seed, ...keys)();
