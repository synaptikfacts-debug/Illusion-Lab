// SFX for "Ink and Water": calm and simple (owner's preference). One soft water "plip" when each drop lands (a
// resonant bubble: a short sine that glides up, like a real drop), a very quiet deep-water ambience following the
// motion, and a slow airy swirl while the vortex turns. Then silence.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { energy, ISTORY, vortexAt } from "../src/scenes/ink/ink";
import { addWrapped, Biquad, reverb, SR, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";

export function generateInkAudio(reel: Reel): string {
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const out = stereo(total);
  const r = rng(reel.seed, "ink-sfx");
  const T0 = Number((reel.illusion.props as { t0?: number }).t0 ?? 0); // story time at the first frame
  // deep water ambience: low-passed noise, level follows the motion
  const lpL = new Biquad(), lpR = new Biquad();
  lpL.set("lp", 260, 0.6); lpR.set("lp", 260, 0.6);
  let e = 0;
  for (let i = 0; i < out[0].length; i++) {
    const t = i / SR;
    e += (energy(t + T0) - e) * 0.0003;
    out[0][i] += lpL.run(r() * 2 - 1) * e * 0.05;
    out[1][i] += lpR.run(r() * 2 - 1) * e * 0.05;
  }
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
  // the whirlpools: a slow airy swirl that follows the vortex strength (already turning at the first frame)
  const bp = new Biquad();
  addWrapped(out, 0, total - 0.05, 0.5, (t, k) => {
    const s = vortexAt(t + T0) * Math.min(1, t / 0.4);
    if (k % 64 === 0) bp.set("bp", 380 + 500 * s, 1.8);
    return bp.run(r() * 2 - 1) * s * 0.08 * (0.85 + 0.15 * Math.sin(2 * Math.PI * 0.4 * t));
  });
  reverb(out, { room: 0.86, damp: 0.5, wet: 0.28, preDelayMs: 18, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (water ambience, ${ISTORY.drops.length} drop plips, vortex swirl)`);
  return rel;
}
