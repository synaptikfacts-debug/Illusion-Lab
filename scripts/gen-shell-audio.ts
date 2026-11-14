// SFX for 0017 "Obsidian Heart" v4 - a TAPPING sound world (owner: "maybe tapping"): real woodblock samples (VSCO-2,
// CC0) pitched per plate, glassy crystal tinks, soft low pulses. Every sound has a visible cause
// (src/scenes/shell/timeline.json, real time). No noise beds.
//  peel: one tap per plate as it pops, faster and faster | blast: a burst of taps + a deep knock
//  orbit: a soft patter of plates | grow: crystals cracking out - dense glassy ticks rising in pitch
//  pulses: a warm low pulse + a chime per light wave | retract: ticks falling | slam: a spiral of taps + knock
//  ending: one last soft pulse, then silence
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import TL from "../src/scenes/shell/timeline.json";
import { addWrapped, reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { play, unpitched } from "./lib/sampler";

export function generateShellAudio(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "shell-taps-v4");
  const tap = (at: number, g: number, rate: number, pan: number) => {
    if (at < 0) return;
    play(out, { ...unpitched("woodblock", Math.floor(r() * 4)), rate }, at, g, pan, 0.25, 0.08, 0.6);
  };
  const tink = (at: number, g: number, f: number, pan: number) => addWrapped(out, at, 0.4, pan, (t) =>
    (Math.sin(2 * Math.PI * f * t) + 0.35 * Math.sin(2 * Math.PI * f * 2.76 * t) * Math.exp(-t * 30)) * Math.exp(-t * 12) * Math.min(1, t / 0.002) * g);
  const knock = (at: number, g: number) => {
    play(out, { ...unpitched("woodblock", 0), rate: 0.42 }, at, g, 0.5, 0.5, 0.15, 0.4);
    addWrapped(out, at, 0.7, 0.5, (t) => Math.sin(2 * Math.PI * 58 * (1 - 0.3 * Math.min(1, t / 0.2)) * t) * Math.exp(-t * 6) * Math.min(1, t / 0.004) * g * 0.7);
  };
  const pulse = (at: number, g: number) => addWrapped(out, at, 0.9, 0.5, (t) =>
    (Math.sin(2 * Math.PI * 55 * t) + 0.3 * Math.sin(2 * Math.PI * 110 * t)) * Math.sin(Math.PI * Math.min(1, t / 0.9)) ** 2 * g);

  // peel: one tap per popping plate, accelerating like the picture (tp = p0 + (p1-p0) * x^0.55)
  const n = 70;
  for (let i = 0; i < n; i++) {
    const x = i / n;
    tap(TL.peel[0] + (TL.peel[1] - TL.peel[0]) * x ** 0.55, 0.06 + 0.03 * x, 0.9 + 0.9 * r(), 0.2 + 0.6 * r());
  }
  // blast
  for (let i = 0; i < 26; i++) tap(TL.blast[0] + r() * 0.3, 0.06, 0.8 + r(), r());
  knock(TL.blast[0], 0.3);
  // orbit: a gentle patter while the plates circle
  for (let t = TL.blast[1]; t < TL.grow[0]; t += 0.14 + 0.12 * r()) tap(t, 0.03, 1.1 + 0.6 * r(), 0.5 + 0.4 * Math.sin(t * 4));
  // crystals grow out: dense glassy ticks rising in pitch
  for (let i = 0; i < 90; i++) {
    const x = i / 90;
    tink(TL.grow[0] + (TL.grow[1] - TL.grow[0]) * x + (r() - 0.5) * 0.03, 0.025, 1400 + 1800 * x + 300 * r(), r());
  }
  // light pulses: a warm low pulse and a chime each
  TL.pulses.forEach((p, i) => { pulse(p - 0.05, 0.12); tink(p + 0.05, 0.06, [1760, 2093, 2637][i], 0.5); });
  // retract: ticks falling
  for (let i = 0; i < 50; i++) {
    const x = i / 50;
    tink(TL.retract[0] + (TL.retract[1] - TL.retract[0]) * x, 0.02, 2600 - 1400 * x, r());
  }
  // slam: a spiral of taps rising, then a deep knock
  for (let i = 0; i < 64; i++) {
    const x = i / 64;
    tap(TL.slam[0] + (TL.slam[1] - TL.slam[0]) * (0.6 + 0.25 * x) / 1.25, 0.075, 0.8 + 1.1 * x, 0.2 + 0.6 * x);
  }
  knock(TL.slam[1] - 0.15, 0.32);
  // ending
  pulse(TL.last - 0.05, 0.08);

  reverb(out, { room: 0.55, damp: 0.55, wet: 0.15, preDelayMs: 8, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (obsidian heart v4 taps)`);
  return rel;
}
