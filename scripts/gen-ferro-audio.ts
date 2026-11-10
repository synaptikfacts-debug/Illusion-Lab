// SFX for "Ferrofluid Bloom": calm and simple (owner's preference). A soft, deep magnetic hum whose level follows the
// field energy (felt more than heard), one soft rounded "pop" each time a magnet pulse lifts a ring of spikes, a gentle
// rising shimmer as the bloom opens, and a slow sigh as the magnet switches off and the spikes melt. Then silence.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { energy, FSTORY } from "../src/scenes/ferro/ferro";
import { addWrapped, Biquad, reverb, SR, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";

export function generateFerroAudio(reel: Reel): string {
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const out = stereo(total);
  const r = rng(reel.seed, "ferro-sfx");
  const S = FSTORY;
  // deep hum (two slightly detuned low sines + a soft octave), following the field energy
  let e = 0;
  for (let i = 0; i < out[0].length; i++) {
    const t = i / SR;
    e += (energy(t) - e) * 0.0004;
    const v = (Math.sin(2 * Math.PI * 55 * t) + Math.sin(2 * Math.PI * 55.4 * t) * 0.8 + 0.3 * Math.sin(2 * Math.PI * 110.3 * t)) * e * 0.09;
    out[0][i] += v;
    out[1][i] += v * 0.96;
  }
  // a soft pop for every magnet pulse
  const pop = (at: number, f: number, g: number, pan: number) =>
    addWrapped(out, at, 0.25, pan, (t) => Math.sin(2 * Math.PI * f * (1 + 1.5 * t) * t) * Math.exp(-t * 18) * Math.min(1, t / 0.006) * g);
  for (const p of S.pulses) if (p >= 0) pop(p + 0.15, 180 + r() * 30, 0.35, 0.5);
  pop(0.05, 190, 0.3, 0.5); // the hook
  // the bloom: a slow airy shimmer rising in
  const bp = new Biquad();
  addWrapped(out, S.bloom[0], S.bloom[1] - S.bloom[0] + 2.5, 0.5, (t, k) => {
    const x = t / (S.bloom[1] - S.bloom[0] + 2.5);
    if (k % 64 === 0) bp.set("bp", 2500 + 2000 * x, 1.5);
    return bp.run(r() * 2 - 1) * Math.sin(Math.PI * x) * 0.05;
  });
  // the crown: one deeper pop
  pop(S.crown[0] + 0.4, 120, 0.4, 0.5);
  // the melt: a slow sigh
  const lp = new Biquad();
  addWrapped(out, S.off, 3.2, 0.5, (t, k) => {
    if (k % 64 === 0) lp.set("lp", 1600 - 1200 * (t / 3.2), 0.7);
    return lp.run(r() * 2 - 1) * Math.sin(Math.PI * Math.min(1, t / 3.2)) * 0.14;
  });
  reverb(out, { room: 0.88, damp: 0.45, wet: 0.3, preDelayMs: 20, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (hum, ${S.pulses.length} pulse pops, bloom shimmer, melt sigh)`);
  return rel;
}
