// Score for "Ferrofluid Labyrinth" - CALM (owner, Nov 11: wants calm and satisfying). Slow sustained strings and a few
// spacious felt-piano chords in C# major (no minor tension, no quickening ostinato), resolving as the drop settles.
// Salamander felt piano (CC BY 3.0, credited in the captions), VSCO-2 violas/celli/violins (CC0), soft samples only.
//  0-2.2       a single high note, then quiet through the rewind
//  2.2-14      long string chords (C#maj7 -> F#maj9 -> A#m7 -> G#sus) with one soft piano chord on each change
//  14-26       the same, an octave of violins added very softly as the spiral winds
//  26-28.6     the strings thin out to one sustained note
//  28.6-31     resolve on C# major, ring out through the fade, then silence
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { LSTORY } from "../src/scenes/labyrinth/story";
import { reverb, SR, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, piano, play } from "./lib/sampler";

export function generateLabyrinthMusic(reel: Reel): string {
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const out = stereo(total);
  const r = rng(reel.seed, "labyrinth-calm-music");
  const S = LSTORY;
  const P = (m: number, at: number, g: number, pan = 0.5, dur = 2.5, rel = 2.0) => play(out, piano(m, true), at + (r() - 0.5) * 0.02, g, pan, dur, rel, 0.8);
  const Str = (inst: string, m: number, at: number, g: number, dur: number, pan = 0.5) => play(out, orch(inst, m, true), at, g, pan, dur, 1.6, 0.7);

  P(85, 0.05, 0.08, 0.55, 1.0, 1.2);

  // long chords, one soft piano chord on each change
  const prog: [number, number[]][] = [
    [37, [61, 65, 68, 72]], // C#maj7
    [42, [61, 66, 70, 73]], // F#maj9-ish
    [46, [61, 65, 70, 73]], // A#m7
    [44, [61, 66, 68, 71]], // G#sus
  ];
  const bar = 4.0;
  let t = S.rewind[1] + 0.2, i = 0;
  while (t < S.retract[0] - 0.5) {
    const [root, tones] = prog[i % prog.length];
    const len = Math.min(bar, S.retract[0] - t);
    Str("celli", root + 12, t, 0.05, len, 0.42);
    Str("violas", tones[1], t + 0.1, 0.035, len, 0.58);
    if (t > S.wind[0]) Str("violins", tones[3] + 12, t + 0.3, 0.02, len, 0.66);
    P(root, t, 0.1, 0.45, len * 0.8, 1.6);
    tones.forEach((m, j) => P(m + 12, t + 0.35 + j * 0.28, 0.05, 0.4 + 0.07 * j, 1.6, 1.6));
    t += bar;
    i++;
  }
  // the magnet cuts out: one sustained note
  Str("violas", 68, S.retract[0] - 0.3, 0.035, S.retract[1] - S.retract[0] + 0.6, 0.55);

  // resolve on C# major and ring out
  const D = S.retract[1];
  const ring = S.fade[1] - D;
  P(37, D, 0.12, 0.45, ring * 0.7, ring * 0.3);
  [61, 65, 68, 73].forEach((m, j) => P(m, D + 0.08 + j * 0.12, 0.06, 0.45 + 0.05 * j, ring * 0.7, ring * 0.3));
  Str("celli", 49, D, 0.04, ring * 0.8, 0.42);

  reverb(out, { room: 0.9, damp: 0.45, wet: 0.38, preDelayMs: 24, loop: false });
  const f0 = Math.round(S.fade[0] * SR), f1 = Math.round(S.fade[1] * SR);
  for (let k = f0; k < out[0].length; k++) {
    const g = k >= f1 ? 0 : (1 - (k - f0) / (f1 - f0)) ** 1.5;
    out[0][k] *= g;
    out[1][k] *= g;
  }
  const rel = `generated/${reel.id}-music.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (calm score, C# major)`);
  return rel;
}
