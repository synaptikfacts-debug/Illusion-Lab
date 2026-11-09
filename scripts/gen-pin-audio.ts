// Calm, satisfying sound effects for a pinWall reel, computed from the same physics as the picture.
// Owner rules: SFX on every version, no music or melody (Instagram/TikTok get the owner's trending track),
// calm and satisfying (Nov 9 feedback: not harsh, not "AI slop").
//  - taps: soft, rounded fingertip-on-wood taps when pins peak (random pitch, never a scale), thinning out as the
//    wall slows down
//  - air: dark, gentle air that follows how fast the wall is moving
//  - settle: soft woodblock "tok" and a warm low "whum" when the pins lock into the picture, then a calm exhale
// Everything sits in a light reverb. Writes assets/generated/<id>-sfx.wav.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { pinSchema } from "../src/illusions/pinWall/schema";
import { height, layout, peakTimes } from "../src/scenes/pins/physics";
import { addWrapped, Biquad, reverb, SR, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { play, unpitched } from "./lib/sampler";

export function generatePinAudio(reel: Reel): string {
  const params = pinSchema.parse(reel.illusion.props);
  const tl = timeline(reel);
  const L = params.loopSec || tl.total / tl.fps;
  const p = { ...params, loopSec: L };
  const pins = layout(p);
  const out = stereo(L);
  const r = rng(reel.seed, "pin-sfx-calm");
  const offset = params.startAt * L; // pin time = video time + offset
  const vt = (pt: number) => (((pt - offset) % L) + L) % L;
  const span = params.grid * params.spacing;
  let taps = 0;

  // 1) soft taps
  pins.forEach((pin, i) => {
    if (i % (params.voiceEvery * 3) !== 0) return;
    const pan = 0.5 + 0.4 * ((pin.x - pin.z) / span);
    const f = 420 + r() * 520; // wood/felt range, random so it never forms a melody
    const amp = 0.05 * (0.5 + 0.5 * pin.target);
    for (const tp of peakTimes(pin, p)) {
      const ff = f * (0.97 + r() * 0.06);
      addWrapped(out, vt(tp), 0.09, pan, (t) => {
        const env = Math.min(1, t / 0.0015) * Math.exp(-t * 48);
        return (Math.sin(2 * Math.PI * ff * t * (1 - 0.06 * t)) + 0.25 * Math.sin(2 * Math.PI * ff * 2.6 * t) * Math.exp(-t * 90)) * env * amp;
      });
      taps++;
    }
  });

  // 2) air: mean pin speed every 10 ms (subset), smoothed, drives a dark low-passed noise
  const step = 0.01, nS = Math.round(L / step);
  const speed = new Float32Array(nS);
  const sub = pins.filter((_, i) => i % 7 === 0);
  let maxS = 1e-9;
  for (let k = 0; k < nS; k++) {
    const pt = k * step + offset;
    let s = 0;
    for (const pin of sub) s += Math.abs(height(pin, p, pt + 0.005) - height(pin, p, pt - 0.005)) / 0.01;
    speed[k] = s / sub.length;
    maxS = Math.max(maxS, speed[k]);
  }
  const [Lc, Rc] = out;
  const bl = new Biquad(), br = new Biquad();
  let e = 0;
  for (let i = 0; i < Lc.length; i++) {
    const x = (i / SR) / step, k0 = Math.floor(x) % nS, k1 = (k0 + 1) % nS;
    const target = (speed[k0] * (1 - (x % 1)) + speed[k1] * (x % 1)) / maxS;
    e += (target - e) * 0.0004; // ~50 ms smoothing
    if (i % 128 === 0) { bl.set("lp", 260 + 700 * e, 0.6); br.set("lp", 280 + 760 * e, 0.6); }
    const g = 0.035 + Math.pow(e, 1.4) * 0.5; // soft room-tone floor: never dead silent
    Lc[i] += bl.run(r() * 2 - 1) * g;
    Rc[i] += br.run(r() * 2 - 1) * g;
  }

  // 3) settle into the picture (pin time L/2)
  const lockAt = vt(L / 2) - 0.5;
  play(out, unpitched("woodblock", 0), lockAt, 0.35, 0.5, 0.25, 0.4, 0.75);
  addWrapped(out, lockAt, 1.6, 0.5, (t) => Math.sin(2 * Math.PI * (52 + 14 * Math.exp(-t * 6)) * t) * Math.min(1, t / 0.04) * Math.exp(-t * 2.2) * 0.45);
  const exhale = new Biquad().set("lp", 1400, 0.6);
  addWrapped(out, lockAt + 0.1, 2.8, 0.5, (t) => exhale.run(r() * 2 - 1) * Math.min(1, t / 0.4) * Math.exp(-t * 1.3) * 0.12);

  reverb(out, { room: 0.78, damp: 0.5, wet: 0.22 });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.1);
  console.log(`wrote assets/${rel} (${taps} soft taps, motion air, settle at ${lockAt.toFixed(2)} s)`);
  return rel;
}
