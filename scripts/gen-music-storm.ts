// Score for 0023 v2 "This liquid became a storm": dark, cinematic, D minor - low strings and a timpani pulse, a hit
// on each spike event, a rising ostinato under the vortex, horns into the tornado, a held chord on the collapse that
// rings into the fade. VSCO-2 (CC0) + Salamander piano (CC BY 3.0, credited by the render).
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { STORM } from "../src/scenes/ferroMusic/storm";
import { reverb, SR, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, piano, play, unpitched } from "./lib/sampler";

export function generateStormMusic(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "storm-music");
  const O = (inst: string, m: number, at: number, g: number, dur: number, pan = 0.5, rel = 1.0) => play(out, orch(inst, m, true), Math.max(0, at), g, pan, dur, rel, 0.7);
  const P = (m: number, at: number, g: number, dur: number, pan = 0.5) => play(out, piano(m, true), Math.max(0, at + (r() - 0.5) * 0.01), g, pan, dur, 1.8, 0.8);
  const hit = (at: number, g: number) => { play(out, unpitched("bassdrum", 0), at, 0.3 * g, 0.5, 2, 1.2, 0.6); O("timpani", 38, at, 0.28 * g, 2, 0.5, 1.5); P(26, at, 0.2 * g, 3, 0.45); P(38, at + 0.01, 0.14 * g, 3, 0.5); };
  // hook + rewind: a dark held chord, a hit on the crest
  O("basses", 38, 0, 0.07, 1.8, 0.5, 0.6);
  O("celli", 50, 0, 0.05, 1.8, 0.42, 0.6);
  hit(0.5, 1);
  // the bass hit and the fronts
  for (const [t, g] of [[2.2, 0.9], [3.6, 0.6], [5.2, 0.6]] as [number, number][]) hit(t, g);
  O("celli", 50, 2.2, 0.045, 4.8, 0.42, 0.8);
  O("violas", 57, 2.4, 0.03, 4.6, 0.58, 0.8);
  // the vortex: a cello ostinato that speeds up
  for (let t = 7.0, gap = 0.5, i = 0; t < STORM.collapse - 0.2; t += gap, gap = Math.max(0.17, gap * 0.95), i++) O("celli", [38, 50, 45, 50][i % 4], t, 0.07, gap * 0.9, 0.42, 0.25);
  O("basses", 38, 7.0, 0.06, STORM.collapse - 7.0, 0.5, 0.5);
  // the tornado: violins climb, horns swell, a timpani roll into the collapse
  [62, 64, 65, 67, 69, 70].forEach((m, i) => O("violins", m + 12, 11.0 + i * 0.5, 0.03 + i * 0.006, 0.55, 0.64, 0.3));
  O("horn", 50, 11.6, 0.06, 2.4, 0.4, 0.3);
  O("horn", 57, 11.8, 0.06, 2.2, 0.6, 0.3);
  O("timpaniRoll", 38, STORM.collapse - 1.2, 0.18, 1.2, 0.5, 0.1);
  // the collapse: a big hit and a D minor chord that rings out
  hit(STORM.collapse, 1.2);
  [50, 57, 62, 65, 69].forEach((m, i) => P(m, STORM.collapse + 0.04 + i * 0.05, 0.065, 4, 0.35 + 0.07 * i));
  O("celli", 38, STORM.collapse, 0.06, STORM.fade[1] - STORM.collapse, 0.42, 1.5);
  O("violins", 74, STORM.collapse + 0.2, 0.025, STORM.fade[1] - STORM.collapse - 0.2, 0.64, 1.5);
  reverb(out, { room: 0.9, damp: 0.4, wet: 0.28, preDelayMs: 22, loop: false });
  const f0 = Math.round(STORM.fade[0] * SR), f1 = Math.round(STORM.fade[1] * SR);
  for (let k = f0; k < out[0].length; k++) { const g = k >= f1 ? 0 : (1 - (k - f0) / (f1 - f0)) ** 1.5; out[0][k] *= g; out[1][k] *= g; }
  const rel = `generated/${reel.id}-music.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (storm score, D minor)`);
  return rel;
}
