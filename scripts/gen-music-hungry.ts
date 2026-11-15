// Score for 0018 "This liquid is hungry": playful-but-cinematic (not childish), D minor, real samples.
// Pizzicato celli step in time with each hunt, a soft piano note answers every gulp (rising as it grows), strings
// swell into the big bead, the chain of beads plays a quickening pizzicato run, a full chord blooms on the crown,
// and the twins end on a quiet D major. VSCO-2 (CC0), Salamander piano (CC BY 3.0, credited by the render).
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { BEADS, COLD, HUNGRY, REAL_DURATION, REWIND, sToR } from "../src/scenes/ferroMusic/hungry";
import { reverb, SR, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, piano, play, unpitched } from "./lib/sampler";

export function generateHungryMusic(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "hungry-music");
  const O = (inst: string, m: number, at: number, g: number, dur: number, pan = 0.5, rel = 1.0) => play(out, orch(inst, m, true), Math.max(0, sToR(at)), g, pan, dur / 1.45, rel, 0.7);
  const P = (m: number, at: number, g: number, dur: number, pan = 0.5) => play(out, piano(m, true), Math.max(0, sToR(at) + (r() - 0.5) * 0.01), g, pan, dur, 1.6, 0.8);
  // a low bed that breathes
  const bed: [number, number, number][] = [[0, 8.4, 38], [8.4, 11.4, 34], [11.4, 15, 41], [15, 18.4, 45], [18.4, 24.4, 38]];
  for (const [a, b, m] of bed) { O("basses", m, a, 0.06, b - a + 0.2, 0.5, 0.8); O("violas", m + 19, a + 0.1, 0.025, b - a, 0.58, 0.8); }
  // pizzicato steps while it hunts (sneaking)
  for (let t = 0.2, i = 0; t < 8.2; t += 0.5, i++) O("celliPizz", [50, 53, 57, 53][i % 4], t, 0.06, 0.3, 0.42, 0.3);
  // a soft piano note on every gulp, rising as it grows
  const notes = [62, 65, 69, 72, 74, 69, 72, 74, 77, 81, 84];
  BEADS.forEach((b, i) => P(notes[i], b.eat + 0.02, b.big ? 0.09 : 0.06, 1.2, 0.35 + 0.05 * i));
  // the big bead: strings swell, a low hit
  O("celli", 50, 8.8, 0.06, 2.0, 0.42, 0.5);
  O("violins", 74, 9.2, 0.035, 1.6, 0.64, 0.4);
  play(out, unpitched("bassdrum", 0), sToR(10.6), 0.22, 0.5, 1.6, 1.0, 0.6);
  // the cold open: a deep hit on the harpoon and a held dark chord under the rewind
  play(out, unpitched("bassdrum", 0), 0.42, 0.3, 0.5, 1.6, 1.0, 0.6);
  play(out, orch("basses", 38, true), 0, 0.08, 0.5, COLD + REWIND, 0.4, 0.7);
  play(out, orch("celli", 50, true), 0, 0.06, 0.42, COLD + REWIND, 0.4, 0.7);
  // the early bristles: a low string stab each
  for (const at of [2.0, 6.3]) { play(out, orch("celli", 38, true), at, 0.08, 0.42, 0.9, 0.5, 0.7); play(out, orch("basses", 26, true), at, 0.07, 0.5, 0.9, 0.5, 0.7); }
  // the chain: quickening pizzicato
  for (let t = 11.6, gap = 0.36, i = 0; t < 14.6; t += gap, gap = Math.max(0.16, gap * 0.9), i++) O("violinsPizz", [62, 65, 69, 74][i % 4] + 12, t, 0.05, 0.25, 0.6, 0.3);
  // full: strings rise, a chord blooms on the crown
  [62, 64, 65, 67, 69].forEach((m, i) => O("violins", m + 12, 15 + i * 0.5, 0.03 + i * 0.005, 0.55, 0.64, 0.3));
  O("timpaniRoll", 38, 16.0, 0.12, 1.4, 0.5, 0.1);
  [38, 50, 57, 62, 65].forEach((m, i) => P(m, HUNGRY.crown[0] + 1.6 + i * 0.05, 0.07, 2.2, 0.35 + 0.07 * i));
  // the twins: a quiet D major, one last note into the fade
  [50, 54, 57, 62].forEach((m, i) => P(m, HUNGRY.split[1] + 0.1 + i * 0.12, 0.05, 2.6, 0.4 + 0.07 * i));
  O("celli", 50, HUNGRY.split[1], 0.04, 4.5, 0.42, 1.5);
  P(78, 21.9, 0.04, 2.0, 0.55);
  reverb(out, { room: 0.85, damp: 0.45, wet: 0.26, preDelayMs: 18, loop: false });
  const f0 = Math.round(sToR(HUNGRY.fade[0]) * SR), f1 = Math.round(Math.min(REAL_DURATION, sToR(HUNGRY.fade[1])) * SR);
  for (let k = f0; k < out[0].length; k++) { const g = k >= f1 ? 0 : (1 - (k - f0) / (f1 - f0)) ** 1.5; out[0][k] *= g; out[1][k] *= g; }
  const rel = `generated/${reel.id}-music.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (hungry liquid score, D minor)`);
  return rel;
}
