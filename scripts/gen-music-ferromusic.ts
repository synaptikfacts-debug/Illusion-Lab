// Score for "Ferrofluid vs Music" v4 (owner, Nov 11: v3 music "too childish - must attract everyone").
// Cinematic and dark, like a trailer or a nature documentary: D minor, a driving cello/bass ostinato, low piano octaves
// on the hits, slow string and horn swells, timpani rolls into each climax, a deep hit on the snap, the merge and the
// tower, which lands on D MAJOR (the release), then rings out. Real samples only: VSCO-2 orchestra (CC0) and the
// Salamander piano (CC BY 3.0, credited). Every cue follows src/scenes/ferroMusic/score.ts.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { FM_EVENTS as FM } from "../src/scenes/ferroMusic/creature";
import { reverb, SR, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, piano, play, unpitched } from "./lib/sampler";

export function generateFerroMusic(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "ferromusic-v4");
  const hum = () => (r() - 0.5) * 0.012;
  const O = (inst: string, m: number, at: number, g: number, dur: number, pan = 0.5, rel = 1.4) => play(out, orch(inst, m, true), Math.max(0, at), g, pan, dur, rel, 0.7);
  const P = (m: number, at: number, g: number, dur: number, pan = 0.5, hard = false) => play(out, piano(m, !hard), Math.max(0, at + hum()), g, pan, dur, 2.0, 0.8);
  const hit = (at: number, g: number) => {
    play(out, unpitched("bassdrum", 0), at, 0.5 * g, 0.5, 2.5, 1.5, 0.6);
    O("timpani", 38, at, 0.35 * g, 2.5, 0.5, 2);
    P(26, at, 0.32 * g, 4, 0.45, true);
    P(38, at + 0.01, 0.22 * g, 4, 0.5, true);
  };
  const E = 0.25; // eighth note (120 bpm)
  const ostinato = (a: number, b: number, g: number, notes = [38, 50, 45, 50]) => {
    for (let t = a, i = 0; t < b - 0.05; t += E, i++) {
      O("celli", notes[i % notes.length], t + hum(), g * (i % 2 ? 0.75 : 1), E * 0.9, 0.42, 0.25);
      if (i % 4 === 0) O("basses", 38, t, g * 0.8, E * 3.6, 0.5, 0.4);
    }
  };

  // 0-2.5 HOOK: driving ostinato, high violins straining upward, a timpani roll into the snap
  ostinato(0, FM.snap, 0.11);
  O("violins", 81, 0, 0.045, FM.snap, 0.62, 0.15);
  O("violas", 69, 0, 0.04, FM.snap, 0.56, 0.15);
  O("timpaniRoll", 45, 0.9, 0.16, FM.snap - 0.9, 0.5, 0.1);
  // 2.6 REACH: the strings cut, one soft deep hit
  hit(FM.snap, 0.45); // v7: it notices something - a soft hit, not a crash

  // 3-10 the walker: mysterious - long low strings, a slow piano figure in D minor
  const prog: [number, number[]][] = [[38, [50, 53, 57]], [34, [50, 53, 58]], [41, [48, 53, 57]], [36, [48, 52, 55]]];
  for (let i = 0; i < 4; i++) {
    const t = 3.2 + i * 1.7, [root, tones] = prog[i];
    O("basses", root, t, 0.07, 1.8, 0.48, 1.2);
    O("celli", tones[0], t + 0.05, 0.06, 1.8, 0.42, 1.2);
    O("violas", tones[2], t + 0.1, 0.04, 1.8, 0.58, 1.2);
    P(root + 12, t, 0.09, 1.8, 0.45);
    P(tones[1] + 12, t + 0.6, 0.06, 1.2, 0.55);
    P(tones[2] + 12, t + 1.1, 0.05, 1.0, 0.6);
  }
  // 10 it splits in two: a soft horn
  O("horn", 57, FM.second, 0.08, 2.5, 0.6, 1.5);

  // 10-16 the pair circles in: the ostinato returns and builds; strings thicken; roll into the merge
  ostinato(10, FM.merge, 0.085);
  O("violas", 62, 12, 0.04, 4, 0.58, 0.3);
  O("violins", 74, 14, 0.04, 2, 0.64, 0.2);
  O("timpaniRoll", 45, 14.6, 0.14, 1.4, 0.5, 0.1);
  hit(FM.merge, 0.6);

  // 15.6-19.6 the dance and the rain: a gentle, glowing interlude - harp-like piano arpeggios over warm strings
  const dch: [number, number[]][] = [[38, [62, 65, 69, 74]], [43, [62, 67, 70, 74]]];
  for (let i = 0; i < 4; i++) {
    const t0 = FM.dance[0] + i * 1.0, [root, tones] = dch[i % 2];
    O("celli", root + 12, t0, 0.05, 1.05, 0.42, 1.0);
    tones.forEach((m, j) => P(m + 12, t0 + j * 0.2, 0.045, 1.0, 0.35 + 0.1 * j));
  }
  O("violas", 69, FM.dance[0], 0.035, FM.dance[1] - FM.dance[0], 0.58, 1.2);
  // 19.6-26.2 three lobes: the ostinato returns in three voices (one per lobe), horns call, roll into the slam
  O("horn", 57, FM.split3, 0.08, 2.5, 0.6, 1.5);
  ostinato(FM.split3 + 0.5, FM.merge2, 0.085, [38, 50, 45, 53]);
  O("violas", 62, FM.split3 + 2, 0.04, 4, 0.58, 0.3);
  O("violins", 74, FM.merge2 - 2, 0.045, 2, 0.64, 0.2);
  O("timpaniRoll", 45, FM.merge2 - 1.4, 0.16, 1.4, 0.5, 0.1);
  hit(FM.merge2, 0.8);

  // 16-22 the second spin: full ostinato, a rising violin line, horns swell, roll into the tower
  ostinato(FM.spin2[0] + 0.3, FM.tower, 0.12, [38, 50, 46, 50]);
  [74, 76, 77, 79, 81, 82].forEach((m, i) => O("violins", m, FM.spin2[0] + 0.5 + i * 0.9, 0.05 + i * 0.006, 0.95, 0.64, 0.3));
  O("horn", 50, FM.tower - 3, 0.06, 3, 0.4, 0.3);
  O("horn", 57, FM.tower - 2.8, 0.06, 2.8, 0.6, 0.3);
  O("timpaniRoll", 45, FM.tower - 1.6, 0.2, 1.6, 0.5, 0.1);

  // 22 THE TOWER: a deep hit and the release on D MAJOR, held and ringing out
  hit(FM.tower, 1.15);
  const ring = FM.fade[1] - FM.tower;
  O("basses", 38, FM.tower, 0.09, ring * 0.7, 0.48, 3);
  O("celli", 50, FM.tower, 0.08, ring * 0.7, 0.42, 3);
  O("violas", 57, FM.tower + 0.05, 0.06, ring * 0.65, 0.58, 3);
  O("violins", 66, FM.tower + 0.1, 0.05, ring * 0.6, 0.64, 3);
  O("violins", 74, FM.tower + 0.15, 0.04, ring * 0.55, 0.7, 3);
  O("horn", 50, FM.tower, 0.08, 3.5, 0.4, 2);
  O("horn", 54, FM.tower + 0.05, 0.07, 3.5, 0.6, 2);
  [62, 66, 69, 74].forEach((m, i) => P(m, FM.tower + 0.06 + i * 0.07, 0.07, 4, 0.4 + 0.07 * i));
  // the melt: one high, quiet piano line settling, the last note rings into the fade
  [81, 78, 74].forEach((m, i) => P(m, FM.melt[0] + 0.4 + i * 1.1, 0.05, 2.5, 0.55));
  P(62, FM.melt[1] - 0.2, 0.05, 3, 0.5);

  reverb(out, { room: 0.9, damp: 0.4, wet: 0.3, preDelayMs: 24, loop: false });
  const f0 = Math.round(FM.fade[0] * SR), f1 = Math.round(FM.fade[1] * SR);
  for (let k = f0; k < out[0].length; k++) {
    const g = k >= f1 ? 0 : (1 - (k - f0) / (f1 - f0)) ** 1.5;
    out[0][k] *= g;
    out[1][k] *= g;
  }
  const rel = `generated/${reel.id}-music.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (cinematic score, D minor -> D major)`);
  return rel;
}
