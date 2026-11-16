// Score for 0023 "Mercury learned to dance" (HANDOFF: harp + glockenspiel rising with each pattern). B major, airy.
// A low string bed, a harp figure that climbs one step per pattern (ring -> spiral -> star -> orbit), a glockenspiel
// sparkle on every merge, a swell into the final merge and a held chord that rings into the fade.
// VSCO-2 (CC0) + Salamander piano (CC BY 3.0, credited by the render).
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import EV from "../src/scenes/mercury/events.json";
import { reverb, SR, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, piano, play } from "./lib/sampler";

export function generateMercuryMusic(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "mercury-music");
  const O = (inst: string, m: number, at: number, g: number, dur: number, pan = 0.5, rel = 1.2) => play(out, orch(inst, m, true), Math.max(0, at), g, pan, dur, rel, 0.7);
  const P = (m: number, at: number, g: number, dur: number, pan = 0.5) => play(out, piano(m, true), Math.max(0, at + (r() - 0.5) * 0.01), g, pan, dur, 1.8, 0.8);
  // cold open: a bright held chord
  [59, 63, 66, 71].forEach((m, i) => O("harp", m, 0.02 + i * 0.04, 0.08, 1.4, 0.35 + 0.1 * i));
  // the drum: a low bed
  O("celli", 47, EV.rewind[1], 0.04, EV.ring[0] - EV.rewind[1], 0.42, 1.0);
  O("violas", 59, EV.rewind[1] + 0.3, 0.025, EV.ring[0] - EV.rewind[1], 0.58, 1.0);
  // the patterns: a harp figure that climbs one step per pattern
  const figs: [number[], number, number][] = [
    [[59, 63, 66, 71], EV.ring[0], EV.ring[1]],
    [[61, 66, 70, 73], EV.spiral[0], EV.spiral[1]],
    [[63, 68, 71, 75], EV.star[0], EV.star[1]],
    [[66, 71, 75, 78], EV.orbit[0], EV.orbit[1]],
  ];
  figs.forEach(([notes, a, b], k) => {
    const step = k === 3 ? 0.22 : 0.3;
    for (let t = a, i = 0; t < b - 0.1; t += step, i++) O("harp", notes[i % 4] + (i % 8 >= 4 ? 12 : 0), t, 0.055 + 0.008 * k, 1.0, 0.3 + 0.4 * ((i * 3) % 7) / 6);
    O("celli", notes[0] - 12, a, 0.04, b - a, 0.42, 0.8);
    O("violins", notes[3] + 12, a + 0.3, 0.012 + 0.006 * k, b - a - 0.3, 0.64, 0.8);
  });
  // a glockenspiel sparkle on every merge
  for (const m of EV.merges) O("glockenspiel", [83, 87, 90, 95, 99][Math.min(4, m.level - 1)], m.t + 0.03, 0.02, 1.0, 0.6);
  // the final merge: a full chord that rings into the fade
  [47, 59, 63, 66, 71, 75].forEach((m, i) => P(m, EV.splash + 0.03 + i * 0.05, 0.065, 3.4, 0.35 + 0.06 * i));
  O("celli", 47, EV.splash, 0.05, EV.fade[1] - EV.splash, 0.42, 1.5);
  O("violins", 78, EV.splash + 0.2, 0.02, EV.fade[1] - EV.splash - 0.2, 0.64, 1.5);
  P(83, EV.settle[0] + 1.6, 0.035, 2.2, 0.55);
  reverb(out, { room: 0.9, damp: 0.4, wet: 0.3, preDelayMs: 22, loop: false });
  const f0 = Math.round(EV.fade[0] * SR), f1 = Math.round(EV.fade[1] * SR);
  for (let k = f0; k < out[0].length; k++) { const g = k >= f1 ? 0 : (1 - (k - f0) / (f1 - f0)) ** 1.5; out[0][k] *= g; out[1][k] *= g; }
  const rel = `generated/${reel.id}-music.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (mercury score, harp + glockenspiel, B major)`);
  return rel;
}
