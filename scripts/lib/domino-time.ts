// Maps an audio buffer written in STORY time (tau) onto the real video timeline (src/scenes/dominoes/sim.ts HOOK):
// the hook plays the burst, the rewind plays it backwards fast like a tape (filtered, softened), then the story.
import { HOOK, tauAt } from "../../src/scenes/dominoes/sim";
import { Biquad, SR, stereo, type Stereo } from "./dsp";

export function warpToReal(src: Stereo, realSec: number): Stereo {
  const out = stereo(realSec);
  const n = src[0].length;
  const a = HOOK.to - HOOK.from;
  const lpL = new Biquad(), lpR = new Biquad();
  for (let i = 0; i < out[0].length; i++) {
    const t = i / SR;
    const pos = tauAt(t) * SR;
    const k = Math.floor(pos), f = pos - k;
    if (k < 0 || k + 1 >= n) continue;
    let l = src[0][k] * (1 - f) + src[0][k + 1] * f, r = src[1][k] * (1 - f) + src[1][k + 1] * f;
    const x = (t - a) / HOOK.rewindLen;
    if (x > 0 && x < 1) {
      // the rewind: fast backwards playback, darker and softer, with a short dip at both ends
      if (i % 32 === 0) { lpL.set("lp", 1600, 0.7); lpR.set("lp", 1600, 0.7); }
      const g = 0.55 * Math.min(1, x * 8, (1 - x) * 8);
      l = lpL.run(l) * g;
      r = lpR.run(r) * g;
    }
    out[0][i] = l;
    out[1][i] = r;
  }
  return out;
}

/** A tape-rewind sweep on the real timeline (falling pitch whoosh) to sell the rewind. */
export function addRewindSweep(out: Stereo, seedRand: () => number) {
  const a = HOOK.to - HOOK.from, len = HOOK.rewindLen;
  const bp = new Biquad();
  const s0 = Math.round(a * SR), N = Math.round(len * SR);
  for (let i = 0; i < N; i++) {
    const x = i / N;
    if (i % 32 === 0) bp.set("bp", 3500 * Math.pow(0.15, x) + 250, 2.0);
    const env = Math.sin(Math.PI * x) ** 1.5;
    const v = bp.run(seedRand() * 2 - 1) * env * 0.5;
    out[0][s0 + i] += v;
    out[1][s0 + i] += v;
  }
}
