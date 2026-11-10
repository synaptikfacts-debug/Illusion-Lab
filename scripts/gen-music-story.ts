// YouTube-only music for "The Eye" (rodStory): calm, real instruments, written to the story so it has an ENDING.
// Salamander felt piano (CC BY 3.0, credited in the description), VSCO-2 strings + harp (CC0). Key of F.
//  0-7 s     one soft high piano note on every drop that starts a ripple, a low cello note underneath
//  7-11      strings swell, a rising piano arpeggio speeds up into the snap
//  10.3-11   harp glissando -> 11.0 full Fmaj9 on the SNAP
//  11-17.9   gentle broken chords while the eye lives (high note when the pupil widens)
//  17.9-21.8 the eye closes: Bbmaj9 -> C7sus4 -> final F chord exactly on the last rod, then it rings out
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { STORY } from "../src/scenes/rods/sim";
import { reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, piano, play } from "./lib/sampler";

export function generateStoryMusic(reel: Reel): string {
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const out = stereo(total);
  const r = rng(reel.seed, "story-music");
  const h = () => (r() - 0.5) * 0.016;
  const P = (m: number, at: number, g: number, pan = 0.5, dur = 1.2, rel = 1.2, tone = 0.55) =>
    play(out, piano(m), at + h(), g, pan, dur, rel, tone);

  // 0-7: a note per drop
  const drops = [77, 81, 84, 86, 79, 81, 89];
  P(84, 0.0, 0.2, 0.5, 0.8, 1.2, 0.4); // the stare
  for (const m of [29, 41]) P(m, STORY.explode, 0.4, 0.45, 1.6, 1.4, 0.45); // the shatter
  [96, 93, 89, 84, 81, 77, 72, 69, 65, 60].forEach((m, i) => play(out, orch("harp", m), STORY.explode + i * 0.06, 0.18, 0.75 - i * 0.05));
  STORY.sources.forEach((s, i) => P(drops[i % drops.length], s.t, 0.3, 0.5 + 0.3 * s.u, 1.8, 1.6));
  play(out, orch("celli", 41), 1.0, 0.1, 0.4, 6.0, 1.2, 0.5);
  play(out, orch("violas", 57), 3.5, 0.07, 0.6, 3.6, 1.0, 0.5);

  // 7-11: strings swell + accelerating rising arpeggio
  const [s0, s1] = STORY.spiral;
  play(out, orch("celli", 38), s0, 0.12, 0.4, 1.6, 0.5, 0.45);
  play(out, orch("celli", 46), s0 + 1.6, 0.14, 0.4, 1.5, 0.5, 0.45);
  play(out, orch("celli", 48), s0 + 3.1, 0.17, 0.4, 0.9, 0.3, 0.45);
  play(out, orch("violas", 62), s0 + 0.4, 0.08, 0.65, 3.5, 0.3, 0.45);
  play(out, orch("violins", 69, true), s0 + 1.8, 0.06, 0.7, 2.2, 0.2, 0.45);
  const arp = [62, 65, 69, 72, 74, 77, 70, 74, 77, 81, 84, 72, 77, 79, 82, 84, 89, 91];
  let t = s0 + 0.2, gap = 0.42;
  for (let i = 0; t < s1 - 0.35; i++) {
    P(arp[i % arp.length], t, 0.16 + 0.12 * ((t - s0) / (s1 - s0)), 0.3 + 0.4 * ((i * 0.37) % 1), 0.4, 0.6, 0.6);
    t += gap;
    gap = Math.max(0.11, gap * 0.93);
  }
  const scale = [53, 55, 57, 58, 60, 62, 64, 65, 67, 69, 70, 72, 74, 76, 77, 79, 81, 82, 84, 86];
  scale.forEach((m, i) => play(out, orch("harp", m), STORY.snap - 0.7 + (i / scale.length) * 0.7, 0.22, 0.25 + (i / scale.length) * 0.5));

  // 11: SNAP chord
  const S = STORY.snap;
  for (const m of [29, 41]) P(m, S, 0.45, 0.45, 2.0, 1.8, 0.4);
  for (const m of [57, 60, 64, 67, 69]) P(m, S, 0.24, 0.55, 2.0, 1.8, 0.5);
  P(84, S, 0.2, 0.6, 2.0, 2.0, 0.4);
  play(out, orch("celli", 41), S, 0.14, 0.4, 4.0, 1.5, 0.45);
  play(out, orch("violas", 60), S, 0.09, 0.6, 4.0, 1.5, 0.45);
  play(out, orch("violins", 72, true), S + 0.1, 0.07, 0.7, 3.6, 1.5, 0.45);

  // 11-17.9: the eye lives
  const chords: [number, number[], number][] = [
    [S + 2.0, [41, 53, 57, 60, 64], 2.0],
    [S + 4.0, [45, 52, 55, 60, 64], 2.0],
    [S + 6.0, [38, 50, 53, 57, 64], 1.9],
  ];
  for (const [at, notes, len] of chords) {
    P(notes[0], at, 0.32, 0.42, len, 1.2, 0.5);
    const rh = notes.slice(1);
    [0, 1, 2, 3, 2, 1].forEach((k, j) => P(rh[k % rh.length] + 12, at + j * (len / 6), 0.15 + r() * 0.05, 0.35 + r() * 0.3, len / 3, 0.9, 0.6));
    play(out, orch("celli", notes[0] + 12), at, 0.08, 0.4, len, 0.8, 0.5);
  }
  P(84, STORY.dilate[0] + 0.2, 0.2, 0.62, 1.4, 1.4, 0.45);

  // 17.9-21.8: closing -> resolve on the last rod
  const C0 = STORY.close[0], END = STORY.lastLand;
  P(34, C0, 0.3, 0.42, 2.2, 1.0, 0.5);
  [58, 62, 65, 69, 72].forEach((m, j) => P(m, C0 + j * 0.38, 0.15, 0.4 + j * 0.06, 1.2, 0.9, 0.6));
  play(out, orch("celli", 46), C0, 0.1, 0.4, 2.3, 0.8, 0.5);
  P(36, C0 + 2.3, 0.28, 0.42, END - C0 - 2.3, 0.4, 0.5);
  [60, 65, 67, 70].forEach((m, j) => P(m, C0 + 2.3 + j * 0.42, 0.13, 0.45 + j * 0.05, 0.9, 0.6, 0.6));
  play(out, orch("violas", 58), C0 + 2.3, 0.07, 0.6, END - C0 - 2.3, 0.4, 0.5);
  const ring = total - END - 0.2;
  for (const m of [29, 41]) P(m, END, 0.3, 0.45, ring * 0.5, ring * 0.5, 0.5);
  for (const m of [60, 65, 69, 72]) P(m, END + 0.05, 0.15, 0.55, ring * 0.5, ring * 0.5, 0.6);
  P(89, STORY.ember[0] + 1.1, 0.12, 0.6, 1.4, ring * 0.5, 0.5); // a last high note as the ember fades

  reverb(out, { room: 0.86, damp: 0.42, wet: 0.34, preDelayMs: 20, loop: false });
  const rel = `generated/${reel.id}-music.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (story score, final chord at ${END.toFixed(2)} s)`);
  return rel;
}
