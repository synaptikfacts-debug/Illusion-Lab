// Score for 0024 "This core is unlocking": calm, precise, F# minor. The cryptex PLAYS the melody - every dial that clacks
// into place sounds the next note of a rising F# minor line on felt piano (outer shell low, inner shell an octave up);
// harp arpeggios carry the gyroscope, strings swell into the ignition, the bands landing walk the line back down and the
// last clack resolves on a held F# minor (add9) that rings into the fade. VSCO-2 (CC0) + Salamander piano (CC BY 3.0).
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { CORE, coreEvents, IGNITE as IGN_TAU, realAt, REWIND } from "../src/scenes/core/core";
import { reverb, SR, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, piano, play } from "./lib/sampler";

export function generateCoreMusic(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "core-music");
  const O = (inst: string, m: number, at: number, g: number, dur: number, pan = 0.5, rel = 1.0) => play(out, orch(inst, m, true), Math.max(0, at), g, pan, dur, rel, 0.7);
  const P = (m: number, at: number, g: number, dur: number, pan = 0.5) => play(out, piano(m, true), Math.max(0, at + (r() - 0.5) * 0.008), g, pan, dur, 1.8, 0.8);
  // F# natural minor, rising
  const IGNITE = realAt(IGN_TAU), R = realAt;
  const SC = [54, 56, 57, 59, 61, 62, 64, 66, 68, 69, 71, 73, 74, 76];
  // hook: the open core - a held F#m(add9) on harp + strings; the rewind pulls a reversed-sounding harp gliss down
  [54, 61, 66, 68, 73].forEach((m, i) => O("harp", m, 0.02 + i * 0.05, 0.06, 1.0, 0.35 + 0.07 * i));
  O("violins", 73, 0, 0.02, 0.8, 0.62, 0.4);
  for (let k = 0; k < 8; k++) O("harp", SC[12 - k], REWIND[0] + 0.1 * k, 0.03, 0.4, 0.7 - 0.05 * k, 0.3);
  // a low bed under the cryptex
  O("celli", 42, REWIND[1], 0.04, 5.5, 0.42, 1.0);
  O("basses", 30, REWIND[1], 0.03, 5.5, 0.5, 1.0);
  let lockN = 0, homeN = 0;
  for (const e of coreEvents()) {
    if (e.kind === "lock") {
      const m = SC[Math.min(SC.length - 1, lockN++)] - (e.shell === 0 ? 0 : 0);
      P(m, e.t, 0.07, 1.6, 0.4 + 0.2 * r());
      if (e.shell === 1) O("glockenspiel", m + 12, e.t + 0.02, 0.012, 0.8, 0.6);
    }
    if (e.kind === "seam") { [54, 61, 66].forEach((m, i) => O("violas", m, e.t - 0.2 + 0.04 * i, 0.03, 1.6, 0.4 + 0.1 * i, 0.8)); }
    if (e.kind === "home") { P(SC[Math.max(0, 11 - homeN++)], e.t, 0.055, 1.4, 0.45 + 0.1 * r()); }
  }
  // the unlock + inner cryptex: strings breathe
  O("celli", 47, 7.0, 0.04, R(11) - 7.0, 0.42, 1.0);
  O("violas", 59, 7.2, 0.025, 3.8, 0.58, 1.0);
  // ignition: a swell into a full chord
  O("violins", 73, IGNITE - 1.0, 0.025, 1.2, 0.64, 0.4);
  [30, 42, 54, 61, 66, 68, 73].forEach((m, i) => P(m, IGNITE + 0.02 + i * 0.04, 0.06, 3.2, 0.3 + 0.06 * i));
  O("celli", 42, IGNITE, 0.05, 3.2, 0.42, 1.2);
  O("violins", 78, IGNITE + 0.2, 0.02, 3.0, 0.64, 1.2);
  // gyroscope: harp arpeggios circling the core
  const arp = [54, 61, 66, 68, 73, 68, 66, 61];
  for (let t = IGNITE + 0.4, i = 0; t < R(14.1); t += 0.2, i++) O("harp", arp[i % 8] + (i % 16 >= 8 ? 12 : 0), t, 0.032, 0.6, 0.3 + 0.4 * ((i * 3) % 8) / 7);
  // homecoming: a low bed while the bands land
  O("celli", 42, R(14.0), 0.04, R(17.4) - R(14.0), 0.42, 0.8);
  // the final clack resolves the line
  const fin = R(17.2);
  [30, 42, 54, 56, 61, 66].forEach((m, i) => P(m, fin + 0.02 + i * 0.05, 0.065, 3.6, 0.35 + 0.06 * i));
  O("celli", 42, fin, 0.05, CORE.fade[1] - fin, 0.42, 1.4);
  O("violins", 68, fin + 0.2, 0.018, CORE.fade[1] - fin - 0.2, 0.64, 1.4);
  reverb(out, { room: 0.88, damp: 0.45, wet: 0.3, preDelayMs: 20, loop: false });
  const f0 = Math.round(CORE.fade[0] * SR), f1 = Math.round(CORE.fade[1] * SR);
  for (let k = f0; k < out[0].length; k++) { const g = k >= f1 ? 0 : (1 - (k - f0) / (f1 - f0)) ** 1.5; out[0][k] *= g; out[1][k] *= g; }
  const rel = `generated/${reel.id}-music.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (core score, F# minor)`);
  return rel;
}
