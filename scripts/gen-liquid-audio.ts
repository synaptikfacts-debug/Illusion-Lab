// Sound effects for "Liquid Obsidian" (a water palette, different from the wood/glass reels). Every sound has a
// visible cause in waves.ts:
//  drops: a water "plink" (fast rising sine chirp, like a real drop) + a low "plop" sized by the drop + a soft splash
//  rain: the same drops, accelerating; the star: a singing-bowl hum that swells and pulses with the pattern;
//  vortex: a swirling, panning whoosh that deepens; collapse: deep bloop + splash + the giant ring's rush; calm; silence.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { controls, drops, LSTORY } from "../src/scenes/liquid/waves";
import { timeline } from "../src/core/timing";
import { addWrapped, Biquad, reverb, SR, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";

export function generateLiquidAudio(reel: Reel): string {
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const out = stereo(total);
  const r = rng(reel.seed, "liquid-sfx");
  const S = LSTORY;

  const drop = (at: number, a: number, pan: number) => {
    if (at < 0) {
      // the hook drop already landed: only its tail (bloop) on frame 0
      at = 0;
    }
    const f0 = 900 + r() * 700, f1 = f0 * (1.9 + r() * 0.6);
    addWrapped(out, at, 0.12, pan, (t) => {
      const f = f0 + (f1 - f0) * Math.min(1, t / 0.025);
      return Math.sin(2 * Math.PI * f * t) * Math.exp(-t * 45) * Math.min(1, t / 0.002) * 0.35 * (0.5 + 0.5 * a);
    });
    const ph = 80 + 60 * (1 - a);
    addWrapped(out, at, 0.45, 0.5, (t) => Math.sin(2 * Math.PI * (ph + 90 * Math.exp(-t * 18)) * t) * Math.exp(-t * 8) * Math.min(1, t / 0.004) * 0.45 * a);
    const bp = new Biquad().set("bp", 2400, 0.8);
    addWrapped(out, at + 0.01, 0.35, pan, (t) => bp.run(r() * 2 - 1) * Math.exp(-t * 12) * 0.18 * a);
    // a few small droplets falling back
    for (let k = 0; k < Math.round(2 + 4 * a); k++) {
      const t0 = at + 0.18 + r() * 0.45, f = 1800 + r() * 1600;
      addWrapped(out, t0, 0.05, Math.min(1, Math.max(0, pan + (r() - 0.5) * 0.4)), (t) => Math.sin(2 * Math.PI * f * (1 + t * 8) * t) * Math.exp(-t * 90) * 0.08 * a);
    }
  };
  for (const d of drops(reel.seed)) if (d.a > 0 && d.t < total) drop(d.t, d.a, 0.5 + 0.18 * d.x);

  // singing-bowl hum for the standing-wave star (pulses with the pattern)
  const freqs = [174.6, 349.2 * 1.003, 523.5 * 0.998, 698.4];
  addWrapped(out, S.stand[0], S.stand[1] - S.stand[0] + 1.5, 0.5, (t) => {
    const k = controls(S.stand[0] + t);
    let v = 0;
    freqs.forEach((f, i) => (v += Math.sin(2 * Math.PI * f * t + i) * [1, 0.5, 0.25, 0.15][i]));
    return v * k.stand * k.pulse * 0.07;
  });

  // vortex: swirling whoosh, panning round, deepening
  {
    const bp = new Biquad();
    const len = S.collapse - S.vortex[0] + 0.3, s0 = Math.round(S.vortex[0] * SR);
    for (let i = 0; i < len * SR; i++) {
      const t = S.vortex[0] + i / SR;
      const k = controls(t).vort;
      if (i % 64 === 0) bp.set("bp", 1400 - 900 * k + 300 * Math.sin(t * 5), 1.2);
      const v = bp.run(r() * 2 - 1) * k * 0.55;
      const pan = 0.5 + 0.4 * Math.sin(t * 5);
      out[0][s0 + i] += v * (1 - pan);
      out[1][s0 + i] += v * pan;
    }
  }
  // collapse: deep bloop + rushing ring
  addWrapped(out, S.collapse, 1.6, 0.5, (t) => Math.sin(2 * Math.PI * (45 + 70 * Math.exp(-t * 6)) * t) * Math.exp(-t * 2.4) * Math.min(1, t / 0.01) * 0.75);
  {
    const bp = new Biquad();
    addWrapped(out, S.collapse + 0.1, 2.4, 0.5, (t, i) => {
      if (i % 64 === 0) bp.set("bp", 500 + 2500 * Math.exp(-t * 1.2), 0.9);
      return bp.run(r() * 2 - 1) * Math.exp(-t * 1.3) * Math.min(1, t * 6) * 0.3;
    });
  }

  reverb(out, { room: 0.9, damp: 0.35, wet: 0.32, preDelayMs: 24, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.05);
  console.log(`wrote assets/${rel} (water palette: drops, rain, bowl hum, vortex, collapse)`);
  return rel;
}
