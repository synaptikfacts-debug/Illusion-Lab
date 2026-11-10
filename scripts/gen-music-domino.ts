// Story score for "The Butterfly Domino" (every platform). D major, real instruments: Salamander felt piano (CC BY 3.0),
// VSCO-2 pizzicato strings, harp, glockenspiel, violas/celli/violins (CC0).
//  0       glockenspiel + harp shimmer on the glowing butterfly
//  0.6-1.6 falling harp run as every domino springs back up
//  2.2-5   the fuse: a pizzicato note on every 2nd domino, climbing the scale (you can count along)
//  5       the burst: Dmaj9 + strings; 5-11.5 flowing piano over D - Bm - G - A while the butterfly appears
//  11.5    full reveal: G -> D with glockenspiel sparkle
//  13-19.5 wing beats: a harp sweep up and a soft chord on every beat (last one slow)
//  19.5-   ending: Em9 -> Asus -> final D as the glow goes out, last glockenspiel note, silence
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { DSTORY } from "../src/scenes/dominoes/sim";
import { simulateDominoes } from "../src/scenes/dominoes/sim";
import { dominoSchema } from "../src/illusions/dominoStory/schema";
import { reverb, stereo, writeWav } from "./lib/dsp";
import { warpToReal } from "./lib/domino-time";
import { ASSETS } from "./lib/paths";
import { orch, piano, play } from "./lib/sampler";

const D_MAJOR = [0, 2, 4, 5, 7, 9, 11];
const deg = (root: number, d: number) => root + 12 * Math.floor(d / 7) + D_MAJOR[((d % 7) + 7) % 7];

export function generateDominoMusic(reel: Reel): string {
  const p = dominoSchema.parse(reel.illusion.props);
  const tl = timeline(reel);
  simulateDominoes(tl.fps, p.cols, p.rows, p.spacing); // sets DSTORY.bloom.start
  const total = tl.total / tl.fps;
  const out = stereo(DSTORY.duration); // story time, warped to the video timeline at the end
  const r = rng(reel.seed, "domino-music");
  const h = () => (r() - 0.5) * 0.014;
  const P = (m: number, at: number, g: number, pan = 0.5, dur = 1.2, rel = 1.2, tone = 0.55) => play(out, piano(m), at + h(), g, pan, dur, rel, tone);
  const S = DSTORY, B = S.bloom.start;

  // 0: shimmer
  [86, 90, 93].forEach((m, i) => play(out, orch("glockenspiel", m + 12 > 108 ? m : m + 12), 0.02 + i * 0.07, 0.16, 0.4 + i * 0.1));
  [62, 66, 69, 74].forEach((m, i) => play(out, orch("harp", m), 0.0 + i * 0.03, 0.18, 0.45 + i * 0.05));
  P(50, 0.0, 0.25, 0.45, 0.6, 1.0, 0.5);
  // rewind: falling harp
  for (let i = 0; i < 14; i++) play(out, orch("harp", deg(62, 14 - i)), S.rewind[0] + i * ((S.rewind[1] - S.rewind[0]) / 14), 0.17, 0.7 - i * 0.03);
  play(out, orch("celli", 50), S.rewind[1], 0.1, 0.4, S.lane.start - S.rewind[1] + 0.4, 0.5, 0.45);
  // fuse: pizzicato climbing on every 2nd domino
  const steps = Math.round((B - 0.12 - S.lane.start) / S.lane.step);
  for (let k = 0; k <= steps; k += 2) {
    const d = Math.floor(k / 4);
    play(out, orch("violinsPizz", deg(62, d)), S.lane.start + k * S.lane.step, 0.2 + 0.1 * (k / steps), 0.45 + (k % 4 ? 0.1 : -0.1));
  }
  play(out, orch("celliPizz", 38), S.lane.start, 0.2, 0.4);
  play(out, orch("celliPizz", 45), S.lane.start + (B - S.lane.start) / 2, 0.2, 0.4);

  // burst + flowing piano
  for (const m of [26, 38]) P(m, B, 0.42, 0.45, 2.2, 1.6, 0.4);
  for (const m of [62, 66, 69, 73, 76]) P(m, B, 0.2, 0.55, 2.0, 1.6, 0.5);
  play(out, orch("celli", 38), B, 0.13, 0.4, 6.2, 1.2, 0.45);
  play(out, orch("violas", 62), B + 0.3, 0.09, 0.6, 6.0, 1.2, 0.45);
  play(out, orch("violins", 74, true), B + 2.5, 0.06, 0.7, 4.0, 1.2, 0.45);
  const prog: [number, number[]][] = [[50, [62, 66, 69, 73]], [47, [59, 62, 66, 69]], [43, [59, 62, 67, 71]], [45, [61, 64, 69, 73]]];
  const seg = (13.0 - B) / prog.length;
  prog.forEach(([bass, ch], j) => {
    const t0 = B + j * seg;
    P(bass - 12, t0, 0.3, 0.42, seg, 1.0, 0.5);
    const arp = [...ch, ch[2] + 12, ch[1] + 12, ch[3], ch[1]];
    for (let k = 0; k * 0.2 < seg; k++) P(arp[k % arp.length] + 12, t0 + k * 0.2, 0.12 + 0.05 * (k % 2 ? 0 : 1), 0.35 + r() * 0.3, 0.35, 0.6, 0.6);
  });
  // full reveal
  P(43, 13.0, 0.3, 0.45, 1.0, 0.8, 0.5);
  for (const m of [26, 38]) P(m, 13.9, 0.36, 0.45, 1.6, 1.4, 0.45);
  for (const m of [62, 66, 69, 74, 78]) P(m, 13.9, 0.17, 0.55, 1.6, 1.4, 0.5);
  [93, 98, 102, 105].forEach((m, i) => play(out, orch("glockenspiel", m), 13.9 + i * 0.09, 0.13, 0.4 + i * 0.1));

  // wing beats
  const beatCh = [[62, 66, 69, 74], [59, 62, 66, 71], [55, 59, 62, 67], [57, 61, 64, 69], [52, 55, 59, 64], [57, 62, 64, 69]];
  S.beats.forEach((b, j) => {
    const len = S.beatLen[j], ch = beatCh[j];
    for (let i = 0; i < 10; i++) play(out, orch("harp", deg(62, i + j)), b + i * (len * 0.45) / 10, 0.14, 0.3 + i * 0.04);
    ch.forEach((m) => P(m, b + len * 0.45, 0.14, 0.5, len, 0.9, 0.55));
    P(ch[0] - 24, b + len * 0.45, 0.24, 0.45, len, 0.9, 0.5);
    play(out, orch("glockenspiel", Math.min(108, ch[3] + 24)), b + len * 0.5, 0.11, 0.6);
  });
  play(out, orch("violas", 59), S.beats[0], 0.08, 0.6, S.beats[S.beats.length - 1] - S.beats[0] + 1.5, 1.2, 0.45);
  play(out, orch("violins", 74, true), S.beats[2], 0.05, 0.7, S.beats[5] - S.beats[2] + 1.5, 1.2, 0.45);

  // ending
  const E = S.fadeGlow[0];
  P(40, E, 0.28, 0.45, 1.4, 1.0, 0.5); // Em9
  [59, 62, 66, 71].forEach((m, i) => P(m, E + i * 0.35, 0.13, 0.45 + i * 0.05, 1.0, 0.8, 0.6));
  P(45, E + 1.5, 0.26, 0.45, 1.2, 0.6, 0.5); // Asus
  [62, 64, 69, 74].forEach((m, i) => P(m, E + 1.5 + i * 0.3, 0.12, 0.5, 0.9, 0.6, 0.6));
  const END = S.fadeGlow[1] - 0.2;
  const ring = total - END - 0.2;
  for (const m of [26, 38]) P(m, END, 0.3, 0.45, ring * 0.5, ring * 0.5, 0.5);
  for (const m of [62, 66, 69, 74]) P(m, END + 0.05, 0.14, 0.55, ring * 0.5, ring * 0.5, 0.6);
  play(out, orch("celli", 38), END, 0.08, 0.4, ring * 0.45, ring * 0.4, 0.5);
  play(out, orch("glockenspiel", 98), END + 1.4, 0.1, 0.6);

  reverb(out, { room: 0.86, damp: 0.42, wet: 0.34, preDelayMs: 20, loop: false });
  const rel = `generated/${reel.id}-music.wav`;
  writeWav(join(ASSETS, rel), warpToReal(out, total), 1.0);
  console.log(`wrote assets/${rel} (domino story score, burst at ${B.toFixed(2)} s, final chord at ${END.toFixed(2)} s)`);
  return rel;
}
