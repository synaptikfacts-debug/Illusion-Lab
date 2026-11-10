// "Pendulum Helix": a pendulum-wave sculpture in a dark studio (owner's pick, Nov 10).
// 5 tiers x 30 glossy spheres on fine threads. In every tier the pendulum k completes (N0 + k) swings per cycle T,
// so the tier moves through snakes, twisting helices and zig-zags and realigns at T. Alternate tiers run in reverse
// order (the fast end at the other side) and swing mirrored, so the layers cross like a double helix.
// The video starts a little into the cycle (already a smooth snake), all spheres line up at the sync moment, then
// the swing dies down and they hang still. Closed-form in time, shared with the sound.

export const PD = {
  tiers: 4,
  cols: 36,
  spacing: 0.22, // along x
  tierGap: 1.45, // vertical distance between tiers
  L: 1.0, // thread length
  bob: 0.09, // sphere radius
  T: 325, // realign cycle (s)
  N0: 146, // swings per cycle of the slowest pendulum (0.45 - 0.56 Hz: calm)
  theta: 0.42, // swing amplitude (rad)
  start: 0.917, // a clean sine wave on every row (about 5 waves), stretching into one wave, then the line // video starts just past the two-row pattern, then 3 rows, 4, one long wave, the line
  duration: 30,
  decay: [27.4, 29.4] as [number, number],
  fade: [28.4, 30.0] as [number, number],
};
export const SYNC_AT = PD.T * (1 - PD.start); // 27 s

const sm = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};
export const ampAt = (v: number) => PD.theta * (1 - sm(PD.decay[0], PD.decay[1], v));

/** Swings per cycle for column k of tier j (alternate tiers reversed). */
export const swingsOf = (j: number, k: number) => PD.N0 + (j % 2 === 0 ? k : PD.cols - 1 - k);

/** Pendulum angle at video time v. */
export function angleAt(j: number, k: number, v: number) {
  const p = v + PD.start * PD.T;
  const sgn = j % 2 === 0 ? 1 : -1;
  return sgn * ampAt(v) * Math.cos((2 * Math.PI * swingsOf(j, k) * p) / PD.T);
}

export const pivotX = (k: number) => (k - (PD.cols - 1) / 2) * PD.spacing;
export const pivotY = (j: number) => ((PD.tiers - 1) / 2 - j) * PD.tierGap + PD.L * 0.5;

/** Centre crossings (sound): when a sphere passes the bottom of its swing, with its current energy. */
export function crossings(j: number) {
  const out: { t: number; k: number; e: number }[] = [];
  for (let k = 0; k < PD.cols; k++) {
    const n = swingsOf(j, k);
    const p0 = PD.start * PD.T;
    // cos(2 pi n p / T) = 0  ->  p = T (m + 0.5) / (2n)
    for (let m = 0; ; m++) {
      const v = (PD.T * (m + 0.5)) / (2 * n) - p0;
      if (v > PD.decay[1]) break;
      if (v >= 0) out.push({ t: v, k, e: ampAt(v) / PD.theta });
    }
  }
  return out.sort((a, b) => a.t - b.t);
}
