// SFX for "Sand Song" (a new palette: tone + sand). Every sound has a visible cause:
//  - the plate's tone: a soft sung note at each figure's frequency (the sound that moves the sand), swelling in
//    as the sand leaps; it stops at toneOff
//  - sand: a dry granular hiss + tiny crackles that follow how many grains are hopping right now
//  - the grand final figure: a soft low bloom; ending: the last grains trickle, then silence
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { SSTORY } from "../src/scenes/sand/chladni";
import { addWrapped, Biquad, reverb, SR, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";

export function generateSandAudio(reel: Reel): string {
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const out = stereo(total);
  const r = rng(reel.seed, "sand-sfx");
  const M = SSTORY.modes;

  // the plate's tone
  M.forEach((md, k) => {
    const start = Math.max(0, md.t), end = k + 1 < M.length ? M[k + 1].t : SSTORY.toneOff;
    const len = end - start + 0.25;
    addWrapped(out, start, len, 0.5, (t) => {
      const env = Math.min(1, t / 0.25) * Math.min(1, (len - t) / 0.25);
      const vib = 1 + 0.003 * Math.sin(2 * Math.PI * 5 * t);
      const f = md.freq * vib;
      const v = Math.sin(2 * Math.PI * f * t) + 0.3 * Math.sin(2 * Math.PI * 2 * f * t) + 0.12 * Math.sin(2 * Math.PI * 3 * f * t);
      return v * env * 0.07 * (k === M.length - 1 ? 1.3 : 1);
    });
  });

  // sand: hiss + crackle, amount = grains in the air (from each figure's hop window)
  const activity = (t: number) => {
    let a = 0;
    for (const md of M) {
      const d = t - md.t;
      if (d > 0 && d < 1.3) a += Math.sin(Math.PI * Math.min(1, d / 1.3)) * (0.5 + md.hop);
      if (d >= 1.3 && t < SSTORY.toneOff) a += 0.05;
    }
    return Math.min(1.2, a);
  };
  const hl = new Biquad().set("bp", 5200, 0.6), hr = new Biquad().set("bp", 5600, 0.6);
  for (let i = 0; i < out[0].length; i++) {
    const t = i / SR, a = activity(t);
    out[0][i] += hl.run(r() * 2 - 1) * a * 0.12;
    out[1][i] += hr.run(r() * 2 - 1) * a * 0.12;
    if (r() < a * 0.0035) {
      const g = 0.05 + 0.1 * r(), side = r();
      out[0][i] += g * (1 - side); out[1][i] += g * side;
    }
  }

  // the grand figure: low bloom
  const G = M[M.length - 1].t;
  addWrapped(out, G, 2.5, 0.5, (t) => Math.sin(2 * Math.PI * 65 * t) * Math.min(1, t / 0.08) * Math.exp(-t * 1.3) * 0.35);
  // ending: last trickle
  for (let k = 0; k < 24; k++) {
    const t0 = SSTORY.toneOff + Math.pow(r(), 0.7) * 1.8, g = 0.06 * (1 - (t0 - SSTORY.toneOff) / 2);
    const bp = new Biquad().set("bp", 4000 + r() * 3000, 1.5);
    addWrapped(out, t0, 0.03, r(), (t) => bp.run(r() * 2 - 1) * Math.exp(-t * 200) * g * 3);
  }

  reverb(out, { room: 0.7, damp: 0.5, wet: 0.18, preDelayMs: 10, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.05);
  console.log(`wrote assets/${rel} (plate tones, sand hiss/crackle, grand bloom, trickle)`);
  return rel;
}
