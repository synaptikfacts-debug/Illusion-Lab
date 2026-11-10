// Score for "Marble Cascade": calm felt piano (the owner liked 0004's score) with soft strings, in A major.
// Broken chords under the cascade, a held breath when the stream stops, a rising arpeggio as the gold marble
// zig-zags down, the final chord exactly on its landing, then silence.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { buildMarbles, GB } from "../src/scenes/galton/galton";
import { reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, piano, play } from "./lib/sampler";

export function generateGaltonMusic(reel: Reel): string {
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const out = stereo(total);
  const r = rng(reel.seed, "galton-music");
  const gold = buildMarbles(reel.seed).find((m) => m.gold)!;
  const P = (m: number, at: number, g: number, pan = 0.5, dur = 1.2, rel = 1.2) => play(out, piano(m), at + (r() - 0.5) * 0.012, g, pan, dur, rel, 0.55);
  const prog: [number, number[]][] = [[45, [64, 69, 73, 76]], [42, [61, 66, 69, 73]], [38, [62, 66, 69, 74]], [40, [64, 68, 71, 76]]];
  const bar = 2.4, end = GB.emit[1] + 1.2;
  for (let t0 = 0, b = 0; t0 < end; t0 += bar, b++) {
    const [bass, ch] = prog[b % 4];
    P(bass, t0, 0.3, 0.42, bar, 1.0);
    for (let k = 0; k < 8; k++) P(ch[[0, 1, 2, 3, 2, 1, 2, 3][k]] + (k > 3 ? 12 : 0), t0 + k * (bar / 8), 0.12 + (k % 2 ? 0 : 0.04), 0.35 + 0.3 * (k / 7), bar / 4, 0.8);
    play(out, orch("celli", bass + 12), t0, 0.07, 0.4, bar, 0.6, 0.5);
  }
  P(40, end, 0.24, 0.45, 2.0, 1.0);
  [64, 68, 71].forEach((m, i) => P(m, end + i * 0.25, 0.12, 0.5, 1.6, 1.0));
  play(out, orch("violas", 64), end, 0.06, 0.6, gold.t0 - end + 0.5, 0.6, 0.5);
  for (let k = 0; k < GB.rows; k++) P([69, 73, 76, 81][k % 4] + 12 * Math.floor(k / 4), gold.t0 + 0.32 + k * GB.step, 0.1 + 0.01 * k, 0.4 + 0.2 * (k % 2), 0.3, 0.6);
  const ring = total - gold.land - 0.2;
  for (const m of [33, 45]) P(m, gold.land, 0.34, 0.45, ring * 0.5, ring * 0.5);
  for (const m of [61, 64, 69, 73, 76]) P(m, gold.land + 0.03, 0.15, 0.55, ring * 0.5, ring * 0.5);
  play(out, orch("celli", 45), gold.land, 0.08, 0.4, ring * 0.5, ring * 0.4, 0.5);
  reverb(out, { room: 0.86, damp: 0.42, wet: 0.32, preDelayMs: 20, loop: false });
  const rel = `generated/${reel.id}-music.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (piano/strings, final chord at ${gold.land.toFixed(2)} s)`);
  return rel;
}
