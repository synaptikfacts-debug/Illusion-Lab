// Score for 0021 "The Break" (director's cut) - YouTube only (TikTok/Instagram get the sounds only). Calm, wide,
// F major, real samples: a held breath before the hit, a wide chord on the impact, a slow-motion string swell, harp as
// the debris flies in, a piano answer on the planet hits, the strings opening up as the ring forms, resolving on F as
// it settles. VSCO-2 (CC0), Salamander piano (CC BY 3.0, credited by the render).
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import TL from "../src/scenes/cosmos/timeline.json";
import { reverb, SR, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, piano, play } from "./lib/sampler";

export function generateCosmosMusic(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "break-music-v1");
  const O = (inst: string, m: number, at: number, g: number, dur: number, pan = 0.5, rel = 1.4) => play(out, orch(inst, m, true), Math.max(0, at), g, pan, dur, rel, 0.7);
  const P = (m: number, at: number, g: number, dur: number, pan = 0.5) => play(out, piano(m, true), Math.max(0, at + (r() - 0.5) * 0.01), g, pan, dur, 2.0, 0.85);
  const harp = (notes: number[], at: number, step: number, g: number) => notes.forEach((m, i) => O("harp", m, at + i * step, g, 1.6, 0.3 + 0.4 * (i / notes.length)));
  const F = 41; // F2

  O("violins", F + 36, 0, 0.025, TL.impact + 0.05, 0.6, 0.2);                       // the held breath
  [F, F + 12, F + 19, F + 24, F + 28].forEach((m, i) => P(m, TL.impact + i * 0.03, 0.065, 2.4, 0.3 + 0.1 * i));
  O("glockenspiel", F + 43, TL.impact + 0.02, 0.025, 1.2, 0.6);
  O("celli", F + 12, TL.slowmo[0], 0.045, TL.slowmo[1] - TL.slowmo[0] + 0.6, 0.42, 1.0);  // slow-motion swell
  O("violas", F + 24, TL.slowmo[0] + 0.3, 0.035, TL.slowmo[1] - TL.slowmo[0] + 0.3, 0.58, 1.0);
  harp([F + 19, F + 24, F + 28, F + 31, F + 36, F + 40], TL.flyIn[0], 0.11, 0.05);     // the fly-in
  [F + 26, F + 29, F + 33].forEach((m, i) => P(m, TL.planetHits[0] + i * 0.35, 0.05, 1.6, 0.4 + 0.1 * i));
  O("basses", F + 5, TL.planetHits[0], 0.045, TL.streams[1] - TL.planetHits[0], 0.5, 1.0);
  O("celli", F + 17, TL.streams[0], 0.04, TL.ring[0] - TL.streams[0] + 0.4, 0.42, 1.0);
  O("violins", F + 36, TL.streams[0] + 0.3, 0.03, TL.ring[0] - TL.streams[0], 0.65, 0.8);
  O("basses", F + 7, TL.ring[0], 0.045, TL.hit2 - TL.ring[0], 0.5, 1.0);                // the first ring, held on C
  O("violins", F + 36, TL.hit2 - 0.6, 0.03, 0.65, 0.62, 0.2);                           // held breath before hit 2
  [F + 2, F + 14, F + 21, F + 26].forEach((m, i) => P(m, TL.hit2 + i * 0.04, 0.065, 2.4, 0.3 + 0.12 * i));  // D minor on hit 2
  O("glockenspiel", F + 45, TL.hit2 + 0.03, 0.022, 1.2, 0.55);
  O("celli", F + 14, TL.shatter[0], 0.045, TL.reform[0] - TL.shatter[0] + 0.4, 0.42, 1.0);     // slow-motion shatter
  harp([F + 26, F + 29, F + 33, F + 36, F + 38, F + 41], TL.reform[0], 0.16, 0.045);    // the ring re-forms
  O("violas", F + 21, TL.reform[0], 0.035, TL.reform[1] - TL.reform[0], 0.58, 1.0);
  [F + 12, F + 19, F + 24, F + 28].forEach((m, i) => P(m, TL.ring[0] + 0.05 + i * 0.08, 0.05, 2.6, 0.3 + 0.1 * i));
  [F + 12, F + 19, F + 24, F + 28, F + 31].forEach((m, i) => P(m, TL.reform[1] + 0.05 + i * 0.08, 0.05, 3.0, 0.3 + 0.1 * i));  // the tilted ring holds
  O("basses", F + 3, TL.reform[1] - 0.5, 0.04, TL.moon[0] - TL.reform[1] + 1.0, 0.5, 1.2);   // Bb under the calm ring

  // act 3 - the moon: a slow low swell in D minor as it drifts in and tears the ring, harp falling as the stream peels off
  O("celli", F + 2, TL.moon[0], 0.045, TL.moon[1] - TL.moon[0], 0.42, 1.6);
  O("basses", F - 3, TL.moon[0] + 0.5, 0.04, TL.moon[1] - TL.moon[0] - 0.5, 0.5, 1.6);
  O("violas", F + 21, TL.moon[0] + 2.0, 0.03, TL.moon[1] - TL.moon[0] - 2.0, 0.58, 1.4);
  harp([F + 38, F + 33, F + 29, F + 26, F + 21, F + 17], TL.moon[0] + 3.5, 0.2, 0.04);
  [F + 14, F + 21, F + 26].forEach((m, i) => P(m, TL.moon[1] - 1.5 + i * 0.12, 0.045, 2.6, 0.35 + 0.15 * i));

  // act 4 - the meteors: each strike gets a held breath, a soft low piano chord and one glockenspiel spark, climbing
  const metChords = [[F + 2, F + 14, F + 21], [F + 5, F + 17, F + 24], [F + 7, F + 19, F + 26], [F + 10, F + 22, F + 29]];
  TL.meteors.forEach((h, k) => {
    O("violins", F + 36 + k * 2, h - 0.5, 0.022, 0.55, 0.62, 0.2);
    metChords[k].forEach((m, i) => P(m, h + i * 0.04, 0.06, 2.2, 0.3 + 0.15 * i));
    O("glockenspiel", F + 43 + k * 2, h + 0.03, 0.02, 1.0, 0.45 + 0.1 * k);
  });
  O("celli", F + 5, TL.meteors[0] - 0.5, 0.04, TL.rain[0] - TL.meteors[0] + 0.5, 0.42, 1.2);

  // act 5 - the rain: strings rise as everything falls in, a wide chord on the bounce, harp and strings open as two rings form
  O("violas", F + 24, TL.rain[0], 0.035, TL.rain[1] - TL.rain[0], 0.58, 0.8);
  O("violins", F + 31, TL.rain[0] + 1.5, 0.03, TL.rain[1] - TL.rain[0] - 1.4, 0.65, 0.6);
  O("violins", F + 36, TL.bounce - 0.6, 0.025, 0.6, 0.62, 0.2);                              // breath before the bounce
  [F, F + 12, F + 19, F + 24, F + 28].forEach((m, i) => P(m, TL.bounce + i * 0.03, 0.07, 3.0, 0.3 + 0.1 * i));
  O("glockenspiel", F + 48, TL.bounce + 0.02, 0.025, 1.4, 0.6);
  harp([F + 24, F + 28, F + 31, F + 36, F + 40, F + 43], TL.double[0] + 0.3, 0.16, 0.045);
  harp([F + 26, F + 29, F + 33, F + 38, F + 41, F + 45], TL.double[0] + 3.2, 0.16, 0.04);
  O("violas", F + 21, TL.double[0], 0.035, TL.double[1] - TL.double[0], 0.58, 1.4);
  O("celli", F + 10, TL.double[0], 0.04, TL.double[1] - TL.double[0], 0.42, 1.4);              // Bb ... -> resolves
  O("basses", F + 7, TL.double[0] + 2.0, 0.04, TL.settle[0] - TL.double[0] - 1.5, 0.5, 1.4);   // C, the dominant

  // ending: resolves on F as the two rings settle, the camera pulls back, one last high note rings into the fade
  O("basses", F, TL.settle[0] - 0.5, 0.05, TL.fade[1] - TL.settle[0] + 0.5, 0.5, 1.8);
  O("celli", F + 12, TL.settle[0] - 0.5, 0.045, TL.fade[1] - TL.settle[0] + 0.5, 0.42, 1.8);
  [F + 12, F + 19, F + 24, F + 28, F + 31].forEach((m, i) => P(m, TL.settle[0] + 0.05 + i * 0.1, 0.055, 3.4, 0.3 + 0.1 * i));
  harp([F + 24, F + 28, F + 31, F + 36, F + 40, F + 43], TL.settle[0] + 1.2, 0.18, 0.04);
  P(F + 36, TL.settle[0] + 4.0, 0.04, 2.4, 0.55);
  P(F + 40, TL.fade[0] - 0.4, 0.035, 2.6, 0.6);

  reverb(out, { room: 0.9, damp: 0.45, wet: 0.3, preDelayMs: 24, loop: false });
  const f0 = Math.round(TL.fade[0] * SR), f1 = Math.round(TL.fade[1] * SR);
  for (let k = f0; k < out[0].length; k++) { const g = k >= f1 ? 0 : (1 - (k - f0) / (f1 - f0)) ** 1.5; out[0][k] *= g; out[1][k] *= g; }
  const rel = `generated/${reel.id}-music.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (the break score, F major)`);
  return rel;
}
