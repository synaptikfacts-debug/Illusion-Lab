// Score for 0024 "This core is unlocking" - v2 (owner, Nov 16: the calm piano/harp score "is not the right music for this
// video"). Cinematic tech score, real orchestra only (VSCO-2, CC0), C minor: a driving celli/basses ostinato that speeds up
// with the dials, a low brass hit + timpani on every lock (the line climbs the scale), a big hit on the unlock, a timpani
// roll into the ignition, full brass chord + strings on the core, horns over the ostinato in the payoff, the ostinato
// slows as the bands come home and the final click lands on a low C hit; held strings ring into the fade.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { CORE, coreEvents, IGNITE as IGN_TAU, realAt, REWIND } from "../src/scenes/core/core";
import { reverb, SR, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, play, unpitched } from "./lib/sampler";

export function generateCoreMusic(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "core-music-v2");
  const R = realAt;
  const IGN = R(IGN_TAU), FIN = R(17.2), OPEN = R(7.0), IN0 = R(8.3), HOME0 = R(14.0);
  const O = (inst: string, m: number, at: number, g: number, dur: number, pan = 0.5, rel = 0.6, soft = true) =>
    at >= 0 && at < CORE.duration && play(out, orch(inst, m, soft), at, g, pan, dur, rel, 0.7);
  const drum = (at: number, g: number) => play(out, unpitched("bassdrum", 0), at, g, 0.5, 2.0, 1.0, 0.6);
  const hit = (at: number, g: number, chord = [36, 43, 48]) => {
    drum(at, 0.32 * g);
    O("timpani", 36, at, 0.32 * g, 2.2, 0.5, 1.4, false);
    O("tuba", chord[0], at, 0.14 * g, 1.6, 0.5, 0.8, false);
    O("trombone", chord[1], at, 0.12 * g, 1.6, 0.4, 0.8, false);
    O("horn", chord[2], at, 0.1 * g, 1.6, 0.6, 0.8, false);
  };
  // the ostinato: celli + basses 8ths on a C minor figure, step = seconds per note
  const ost = (from: number, to: number, step: (t: number) => number, g: number, fig = [36, 36, 43, 36, 39, 36, 43, 41]) => {
    for (let t = from, i = 0; t < to; t += step(t), i++) {
      const acc = i % 4 === 0 ? 1.25 : 1;
      O("celli", fig[i % fig.length] + 12, t, 0.06 * g * acc, step(t) * 0.8, 0.42, 0.12);
      O("basses", fig[i % fig.length], t, 0.05 * g * acc, step(t) * 0.8, 0.5, 0.12);
    }
  };
  // HOOK: the eruption at 0.3 s - full hit; the rewind: strings sweep down
  hit(0.3, 1.2, [36, 43, 51]);
  O("violins", 79, 0.3, 0.035, 0.5, 0.64, 0.4, false);
  for (let k = 0; k < 8; k++) O("violins", 79 - k * 2, REWIND[0] + 0.1 * k, 0.02, 0.2, 0.64, 0.15);
  // CRYPTEX: ostinato that speeds up as the dials go faster
  ost(REWIND[1], OPEN, (t) => 0.3 - 0.11 * Math.min(1, (t - 1.6) / 5), 1);
  O("violas", 60, R(3.0), 0.02, OPEN - R(3.0), 0.58, 0.8);
  const SC = [48, 50, 51, 53, 55, 56, 58, 60, 62, 63, 65, 67, 68, 70];
  let n = 0, home = 0;
  for (const e of coreEvents()) {
    if (e.kind === "lock") {
      const m = SC[Math.min(SC.length - 1, n++)];
      drum(e.t, 0.12);
      O("timpani", 36 + (n % 2 ? 0 : 7), e.t, 0.14, 1.2, 0.5, 0.9, false);
      O("horn", m, e.t, 0.07, 0.9, 0.55, 0.5, false);
      O("trombone", m - 12, e.t, 0.05, 0.9, 0.45, 0.5, false);
    }
    if (e.kind === "home") { O("celliPizz", SC[Math.max(0, 9 - home++)] - 12, e.t, 0.09, 0.8, 0.45 + 0.1 * r()); drum(e.t, 0.06); }
  }
  // seam pulse + UNLOCK: a swell and a big hit
  O("violins", 67, R(6.0), 0.03, OPEN - R(6.0), 0.64, 0.3);
  hit(OPEN, 1.0);
  // inner cryptex: ostinato again, higher and faster, violins join
  ost(OPEN + 0.4, IGN - 0.1, () => 0.16, 0.9, [43, 43, 48, 43, 51, 43, 48, 46]);
  for (let t = IN0, i = 0; t < IGN - 0.2; t += 0.16, i++) O("violins", [67, 70, 72, 70][i % 4], t, 0.018 + 0.012 * ((t - IN0) / (IGN - IN0)), 0.14, 0.64, 0.08);
  O("timpaniRoll", 36, IGN - 1.4, 0.24, 1.4, 0.5, 0.1);
  // IGNITION (slow motion): the full orchestra on C minor
  hit(IGN, 1.4, [36, 43, 48]);
  O("trumpet", 67, IGN + 0.05, 0.08, 3.0, 0.5, 1.0, false);
  O("horn", 63, IGN + 0.05, 0.1, 3.0, 0.6, 1.0, false);
  O("trombone", 55, IGN + 0.05, 0.1, 3.0, 0.4, 1.0, false);
  for (const [m, p] of [[48, 0.42], [55, 0.5], [60, 0.58], [63, 0.64], [72, 0.7]] as [number, number][]) O(m < 58 ? "celli" : "violins", m, IGN, 0.04, R(14.0) - IGN, p, 1.2);
  // PAYOFF: ostinato under a horn line
  ost(IGN + 1.2, HOME0, () => 0.15, 1.0);
  [[60, 0], [63, 0.6], [67, 1.2], [65, 1.8], [63, 2.4], [62, 3.0]].forEach(([m, d]) => O("horn", m, IGN + 1.4 + d, 0.08, 0.7, 0.6, 0.4, false));
  // HOMECOMING: the ostinato slows down
  ost(HOME0, FIN - 0.1, (t) => 0.18 + 0.2 * Math.min(1, (t - HOME0) / (FIN - HOME0)), 0.8);
  // FINAL click: a low C hit, then held strings ring into the fade
  hit(FIN, 1.1, [24, 36, 48]);
  for (const [m, p] of [[36, 0.42], [48, 0.5], [55, 0.58], [63, 0.64]] as [number, number][]) O(m < 50 ? "celli" : "violas", m, FIN + 0.1, 0.045, CORE.fade[1] - FIN, p, 1.5);
  reverb(out, { room: 0.85, damp: 0.5, wet: 0.24, preDelayMs: 18, loop: false });
  const f0 = Math.round(CORE.fade[0] * SR), f1 = Math.round(CORE.fade[1] * SR);
  for (let k = f0; k < out[0].length; k++) { const g = k >= f1 ? 0 : (1 - (k - f0) / (f1 - f0)) ** 1.5; out[0][k] *= g; out[1][k] *= g; }
  const rel = `generated/${reel.id}-music.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (core score v2, cinematic C minor)`);
  return rel;
}
