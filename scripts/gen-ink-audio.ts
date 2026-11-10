// SFX for "Ink and Water": calm and simple (owner's preference). One soft water "plip" when each drop lands (a
// resonant bubble: a short sine that glides up, like a real drop), a very quiet deep-water ambience following the
// motion, and a slow airy swirl while the vortex turns. Then silence. Nov 10: ambience + swirl removed ("sounds like an ocean");
// now only drop plips + a few quiet bubbles in the whirlpools, mixed quieter.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { ISTORY, vortexAt } from "../src/scenes/ink/ink";
import { addWrapped, reverb, SR, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";

export function generateInkAudio(reel: Reel): string {
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const out = stereo(total);
  const r = rng(reel.seed, "ink-sfx");
  const T0 = Number((reel.illusion.props as { t0?: number }).t0 ?? 0); // story time at the first frame
  // a water plip per drop: resonant bubble gliding up in pitch
  const plip = (at: number, f: number, g: number, pan: number) => {
    let ph = 0;
    addWrapped(out, at, 0.3, pan, (t) => {
      const fr = f * (1 + 0.9 * Math.min(1, t / 0.05));
      ph += (2 * Math.PI * fr) / SR;
      return Math.sin(ph) * Math.exp(-t * 26) * Math.min(1, t / 0.003) * g;
    });
  };
  for (const d of ISTORY.drops) {
    if (d[2] - T0 < 0.4) continue; // only drops that land during the reel (never a cluster at the start)
    const size = d[3];
    plip(d[2] - T0, 520 + (0.3 - size) * 1800 + r() * 60, 0.22, 0.5 + d[0] * 0.8);
  }
  // the whirlpools: a few tiny, quiet bubbles rising now and then while the water turns (no noise beds: owner, Nov 10)
  let lastB = -1;
  for (let t = 0.6; t < total - 3; t += 0.35 + r() * 0.9) {
    const s = vortexAt(t + T0);
    if (s < 0.25 || t - lastB < 0.5) continue;
    plip(t, 900 + r() * 700, 0.05 + 0.05 * s, 0.25 + 0.5 * r());
    lastB = t;
  }
  reverb(out, { room: 0.86, damp: 0.5, wet: 0.28, preDelayMs: 18, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (drop plips + soft whirlpool bubbles)`);
  return rel;
}
