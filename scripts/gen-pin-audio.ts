// Sound effects for a pinWall reel, computed from the same physics as the picture (owner rule: SFX on every
// version, no music/melody - the owner adds trending music on Instagram/TikTok):
//  - ticks: a tiny non-pitched metal tick each time a pin peaks (waves crossing the wall = rattling sweeps)
//  - motion: airy whoosh whose level and brightness follow how fast the whole wall is moving
//  - lock: soft cascade + low thump when the pins freeze into the picture
// Writes assets/generated/<id>-sfx.wav.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { pinSchema } from "../src/illusions/pinWall/schema";
import { height, layout, peakTimes } from "../src/scenes/pins/physics";
import { addWrapped, Biquad, SR, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";

export function generatePinAudio(reel: Reel): string {
  const params = pinSchema.parse(reel.illusion.props);
  const tl = timeline(reel);
  const L = params.loopSec || tl.total / tl.fps;
  const p = { ...params, loopSec: L };
  const pins = layout(p);
  const out = stereo(L);
  const r = rng(reel.seed, "pin-sfx");
  const offset = params.startAt * L; // pin time = video time + offset
  const vt = (pt: number) => (((pt - offset) % L) + L) % L;
  const span = params.grid * params.spacing;
  let ticks = 0;

  // 1) ticks
  pins.forEach((pin, i) => {
    if (i % params.voiceEvery !== 0) return;
    const pan = 0.5 + 0.45 * ((pin.x - pin.z) / span);
    const centre = 3500 + r() * 4000;
    for (const tp of peakTimes(pin, p)) {
      const bp = new Biquad().set("bp", centre, 2.2);
      const amp = 0.05 * (0.6 + 0.4 * r());
      addWrapped(out, vt(tp), 0.03, pan, (t) => bp.run(r() * 2 - 1) * Math.exp(-t * 220) * amp);
      ticks++;
    }
  });

  // 2) motion whoosh: mean pin speed sampled every 10 ms (subset of pins)
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
  for (let i = 0; i < Lc.length; i++) {
    const x = (i / SR) / step, k0 = Math.floor(x) % nS, k1 = (k0 + 1) % nS;
    const e = (speed[k0] * (1 - (x % 1)) + speed[k1] * (x % 1)) / maxS;
    if (i % 64 === 0) { bl.set("bp", 300 + 2200 * e, 0.8); br.set("bp", 340 + 2400 * e, 0.8); }
    Lc[i] += bl.run(r() * 2 - 1) * e * 0.35;
    Rc[i] += br.run(r() * 2 - 1) * e * 0.35;
  }

  // 3) lock: pins settle into the picture (pin time L/2)
  const lockAt = vt(L / 2) - 0.6;
  for (let k = 0; k < 40; k++) {
    const hp = new Biquad().set("hp", 2500 + r() * 3000, 0.9);
    const t = lockAt - 0.9 * Math.pow(1 - k / 40, 1.6);
    addWrapped(out, t, 0.04, 0.2 + r() * 0.6, (tt) => hp.run(r() * 2 - 1) * Math.exp(-tt * 160) * 0.22);
  }
  addWrapped(out, lockAt, 1.2, 0.5, (t) => Math.sin(2 * Math.PI * (42 + 30 * Math.exp(-t * 12)) * t) * Math.exp(-t * 3.5) * Math.min(1, t * 300) * 0.8);
  const air = new Biquad().set("hp", 5000, 0.7);
  addWrapped(out, lockAt, 2.5, 0.5, (t) => air.run(r() * 2 - 1) * Math.exp(-t * 1.6) * Math.min(1, t * 20) * 0.08);

  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.3);
  console.log(`wrote assets/${rel} (${ticks} ticks, motion whoosh, lock at ${lockAt.toFixed(2)} s)`);
  return rel;
}
