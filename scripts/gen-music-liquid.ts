// Score for "Liquid Obsidian" (every platform). A new sound palette (no piano): harp, marimba, strings, glockenspiel
// (VSCO-2, CC0). E minor / Dorian, mysterious and liquid, written to the beats:
//  0     harp shimmer on the crater; 1-7 marimba droplet notes on every drop; 7-11 an accelerating marimba figure
//  with the rain; 11-16.6 slow string chords + harp arpeggio over the turning star; 15.6-22 strings deepen and swirl
//  into the vortex; 22 the collapse = low strings + harp sweep up; 23-30 a calm resolve on E major, last glockenspiel.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { drops, LSTORY } from "../src/scenes/liquid/waves";
import { reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, play } from "./lib/sampler";

const DOR = [0, 2, 3, 5, 7, 9, 10];
const deg = (root: number, d: number) => root + 12 * Math.floor(d / 7) + DOR[((d % 7) + 7) % 7];

export function generateLiquidMusic(reel: Reel): string {
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const out = stereo(total);
  const r = rng(reel.seed, "liquid-music");
  const S = LSTORY, E = 52;
  const harp = (m: number, at: number, g: number, pan = 0.5) => play(out, orch("harp", m), at, g, pan);
  const mar = (m: number, at: number, g: number, pan = 0.5) => play(out, orch("marimba", m), at, g, pan, undefined, 0.6, 0.4);

  // 0: harp shimmer
  [64, 67, 71, 74, 78, 83].forEach((m, i) => harp(m, i * 0.05, 0.16, 0.35 + i * 0.06));
  play(out, orch("celli", 40), 0, 0.1, 0.4, 7.0, 1.2, 0.5);
  // drops: a marimba note per drop (Dorian, wandering)
  const ds = drops(reel.seed).filter((d) => d.a > 0 && d.t > 0.5 && d.t < S.rain[0]);
  ds.forEach((d, i) => mar(deg(E + 12, [4, 2, 6, 5, 3, 7, 4][i % 7]), d.t, 0.22, 0.5 + 0.18 * d.x));
  play(out, orch("violas", 59), 3.0, 0.06, 0.6, 4.0, 1.2, 0.5);
  // rain: accelerating marimba figure
  let t = S.rain[0], gap = 0.32, k = 0;
  while (t < S.rain[1]) {
    mar(deg(E + 12, [0, 2, 4, 6, 4, 2][k % 6] + Math.floor(k / 6)), t, 0.14 + 0.06 * (k % 2), 0.35 + 0.3 * ((k * 0.37) % 1));
    t += gap; gap = Math.max(0.11, gap * 0.95); k++;
  }
  play(out, orch("celli", 45), S.rain[0], 0.1, 0.4, S.rain[1] - S.rain[0], 0.8, 0.5);
  // the star: slow chords + harp arpeggio
  const chords = [[40, 55, 59, 62, 66], [45, 57, 60, 64, 67], [43, 55, 59, 62, 66], [47, 54, 59, 62, 66]];
  const seg = (S.stand[1] - S.stand[0]) / chords.length;
  chords.forEach((ch, j) => {
    const t0 = S.stand[0] + j * seg;
    play(out, orch("celli", ch[0]), t0, 0.12, 0.4, seg, 0.6, 0.45);
    play(out, orch("violas", ch[2]), t0, 0.07, 0.6, seg, 0.6, 0.45);
    for (let i = 0; i * 0.23 < seg; i++) harp(ch[1 + (i % 4)] + 12, t0 + i * 0.23, 0.11, 0.3 + 0.4 * ((i % 4) / 3));
  });
  [88, 91, 95].forEach((m, i) => play(out, orch("glockenspiel", m), S.stand[0] + 1.6 + i * 0.4, 0.08, 0.5));
  // vortex: strings deepen and swirl
  play(out, orch("celli", 40), S.vortex[0], 0.14, 0.4, S.collapse - S.vortex[0], 0.3, 0.45);
  play(out, orch("violas", 55), S.vortex[0] + 1, 0.08, 0.6, S.collapse - S.vortex[0] - 1, 0.3, 0.45);
  play(out, orch("violins", 71, true), S.vortex[0] + 2.5, 0.05, 0.7, S.collapse - S.vortex[0] - 2.5, 0.3, 0.45);
  for (let i = 0, tt = S.vortex[0] + 2; tt < S.collapse - 0.2; i++, tt += 0.36 - 0.012 * i) mar(deg(E, 14 - (i % 7)), tt, 0.1, 0.5 + 0.35 * Math.sin(i));
  // collapse: low strings + harp sweep up
  play(out, orch("celli", 40), S.collapse, 0.18, 0.4, 2.5, 1.5, 0.45);
  for (let i = 0; i < 16; i++) harp(deg(E, i + 7), S.collapse + 0.05 + i * 0.045, 0.16, 0.3 + i * 0.03);
  // ending: calm resolve to E major, last glockenspiel, silence
  const R = S.collapse + 2.6;
  play(out, orch("celli", 40), R, 0.1, 0.4, 3.5, 2.0, 0.5);
  play(out, orch("violas", 56), R + 0.3, 0.07, 0.6, 3.2, 2.0, 0.5);
  [64, 68, 71, 76].forEach((m, i) => harp(m, R + i * 0.3, 0.13, 0.4 + i * 0.07));
  mar(76, S.lastDrop, 0.16, 0.6);
  play(out, orch("glockenspiel", 88), S.fade[0] + 0.4, 0.09, 0.55);

  reverb(out, { room: 0.9, damp: 0.35, wet: 0.38, preDelayMs: 24, loop: false });
  const rel = `generated/${reel.id}-music.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (harp/marimba/strings score, ${k} rain notes)`);
  return rel;
}
