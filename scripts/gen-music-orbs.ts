// Score for "Orb Waves": calm felt piano + soft strings (the owner liked 0004's), in D major. Gentle broken chords
// while the waves fold, the harmony opens up toward the in-phase climax, a full chord on the unified hit, then a
// slow resolve as the orbs come to rest; silence at the end.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { OP, SYNC_AT } from "../src/scenes/orbs/orbs";
import { reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, piano, play } from "./lib/sampler";

export function generateOrbMusic(reel: Reel): string {
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const out = stereo(total);
  const r = rng(reel.seed, "orb-music");
  const P = (m: number, at: number, g: number, pan = 0.5, dur = 1.2, rel = 1.2) => play(out, piano(m), at + (r() - 0.5) * 0.012, g, pan, dur, rel, 0.55);
  const prog: [number, number[]][] = [[38, [62, 66, 69, 73]], [47, [59, 62, 66, 71]], [43, [59, 62, 67, 71]], [45, [61, 64, 69, 73]]];
  const bar = (OP.L / OP.base) * 2; // two bounce periods per bar: the music breathes with the orbs
  for (let t0 = 0, b = 0; t0 < SYNC_AT - bar * 0.5; t0 += bar, b++) {
    const [bass, ch] = prog[b % 4];
    const lift = Math.min(1, t0 / SYNC_AT);
    P(bass, t0, 0.28, 0.42, bar, 1.0);
    for (let k = 0; k < 6; k++) P(ch[[0, 1, 2, 3, 2, 1][k]] + (k >= 3 ? 12 : 0) + (lift > 0.6 && k === 3 ? 12 : 0), t0 + k * (bar / 6), 0.11 + 0.05 * lift, 0.35 + 0.3 * (k / 5), bar / 3, 0.8);
    play(out, orch("celli", bass + 12), t0, 0.06 + 0.04 * lift, 0.4, bar, 0.6, 0.5);
  }
  play(out, orch("violas", 66), SYNC_AT - 6, 0.06, 0.6, 6, 0.3, 0.5);
  play(out, orch("violins", 74, true), SYNC_AT - 4, 0.05, 0.7, 4, 0.3, 0.5);
  // the unified hit
  for (const m of [26, 38]) P(m, SYNC_AT, 0.36, 0.45, 2.0, 1.6);
  for (const m of [62, 66, 69, 74, 78]) P(m, SYNC_AT + 0.02, 0.17, 0.55, 2.0, 1.6);
  play(out, orch("celli", 38), SYNC_AT, 0.1, 0.4, 3.0, 1.5, 0.5);
  // resolve as they settle
  const E = OP.settle[0] + 1.2, ring = total - E - 0.2;
  P(43, E, 0.24, 0.45, 1.2, 0.8);
  [62, 67, 71].forEach((m, i) => P(m, E + i * 0.3, 0.11, 0.5, 1.0, 0.8));
  for (const m of [38, 50]) P(m, E + 1.3, 0.26, 0.45, ring * 0.5, ring * 0.5);
  for (const m of [66, 69, 74]) P(m, E + 1.33, 0.12, 0.55, ring * 0.5, ring * 0.5);
  reverb(out, { room: 0.86, damp: 0.42, wet: 0.32, preDelayMs: 20, loop: false });
  const rel = `generated/${reel.id}-music.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (piano/strings, unified hit at ${SYNC_AT.toFixed(2)} s)`);
  return rel;
}
