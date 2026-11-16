// Score for 0022 "This liquid climbs on its own" - YouTube only. Calm, D major (0021 was F), real samples: a wide
// chord on the opening flare, a breath through the rewind, a harp + felt piano line that climbs one step for every turn
// the liquid grips, a suspended chord on the slip, an open chord + glockenspiel when the halo blooms, a falling harp as
// it drains, resolving on D as the pool goes smooth. VSCO-2 (CC0), Salamander piano (CC BY 3.0, credited by the render).
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import TL from "../src/scenes/climb/timeline.json";
import { reverb, SR, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, piano, play } from "./lib/sampler";

export function generateClimbMusic(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "climb-music-v1");
  const O = (inst: string, m: number, at: number, g: number, dur: number, pan = 0.5, rel = 1.4) => play(out, orch(inst, m, true), Math.max(0, at), g, pan, dur, rel, 0.7);
  const P = (m: number, at: number, g: number, dur: number, pan = 0.5) => play(out, piano(m, true), Math.max(0, at + (r() - 0.5) * 0.01), g, pan, dur, 2.0, 0.85);
  const harp = (notes: number[], at: number, step: number, g: number) => notes.forEach((m, i) => O("harp", m, at + i * step, g, 1.6, 0.3 + 0.4 * (i / notes.length)));
  const D = 38; // D2

  [D, D + 12, D + 19, D + 24, D + 28].forEach((m, i) => P(m, 0.04 + i * 0.03, 0.065, 1.4, 0.3 + 0.1 * i)); // the flare
  O("glockenspiel", D + 43, 0.05, 0.022, 0.9, 0.6);
  O("violins", D + 36, TL.rewind[0], 0.02, TL.rewind[1] - TL.rewind[0], 0.6, 0.4); // a held breath
  O("celli", D + 12, TL.wake[0], 0.04, TL.climb[1] - TL.wake[0], 0.42, 1.2); // the floor under the climb
  O("basses", D, TL.wake[0] + 0.5, 0.035, TL.slip[0] - TL.wake[0], 0.5, 1.2);
  // one step up the D major scale for every turn it grips (harp + piano), the strings thicken as it rises
  const scale = [D + 24, D + 26, D + 28, D + 31, D + 33, D + 36];
  const grips = [4.6, 6.0, 7.3, 8.6, 10.0, 11.6];
  grips.forEach((t, k) => {
    O("harp", scale[k], t, 0.05, 1.8, 0.35 + 0.06 * k);
    P(scale[k] - 12, t + 0.02, 0.04, 1.8, 0.45);
  });
  O("violas", D + 21, 6.5, 0.03, TL.slip[0] - 6.5, 0.58, 1.0);
  // the slip: a suspended chord, then the push
  [D + 7, D + 19, D + 24, D + 26].forEach((m, i) => P(m, TL.slip[0] + i * 0.05, 0.045, 1.6, 0.35 + 0.1 * i));
  O("basses", D + 7, TL.slip[0], 0.04, TL.bloom[0] - TL.slip[0] + 0.3, 0.5, 1.0); // A, the dominant
  O("violins", D + 31, TL.slip[1], 0.028, TL.bloom[1] - TL.slip[1], 0.64, 0.6);
  // the halo blooms: open D chord + glockenspiel + a harp run up
  [D, D + 12, D + 19, D + 24, D + 28, D + 31].forEach((m, i) => P(m, TL.bloom[1] + i * 0.035, 0.07, 3.2, 0.3 + 0.08 * i));
  O("glockenspiel", D + 48, TL.bloom[1] + 0.03, 0.024, 1.4, 0.6);
  harp([D + 24, D + 28, D + 31, D + 36, D + 40, D + 43], TL.bloom[1] + 0.2, 0.12, 0.045);
  O("violas", D + 24, TL.bloom[1], 0.032, TL.drain[0] - TL.bloom[1] + 0.5, 0.58, 1.2);
  // the drain: a falling harp, celli on G, resolving to D as the pool goes smooth
  harp([D + 43, D + 40, D + 36, D + 31, D + 28, D + 24], TL.drain[0] + 0.2, 0.42, 0.04);
  O("celli", D + 17, TL.drain[0], 0.04, TL.settle - TL.drain[0] + 0.2, 0.42, 1.2);
  O("basses", D, TL.settle - 0.3, 0.05, TL.fade[1] - TL.settle + 0.3, 0.5, 1.8);
  O("celli", D + 12, TL.settle - 0.3, 0.045, TL.fade[1] - TL.settle + 0.3, 0.42, 1.8);
  [D + 12, D + 19, D + 24, D + 28, D + 31].forEach((m, i) => P(m, TL.settle + 0.05 + i * 0.1, 0.055, 2.8, 0.3 + 0.1 * i));
  P(D + 40, TL.settle + 1.2, 0.035, 2.2, 0.6);

  reverb(out, { room: 0.9, damp: 0.45, wet: 0.3, preDelayMs: 24, loop: false });
  const f0 = Math.round(TL.fade[0] * SR);
  const f1 = Math.round(TL.fade[1] * SR);
  for (let k = f0; k < out[0].length; k++) {
    const g = k >= f1 ? 0 : (1 - (k - f0) / (f1 - f0)) ** 1.5;
    out[0][k] *= g;
    out[1][k] *= g;
  }
  const rel = `generated/${reel.id}-music.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (the climb score, D major)`);
  return rel;
}
