// Score for "Sand Song": a new instrument palette (no piano, no harp/marimba lead): flute, clarinet, pizzicato
// strings, soft celli (VSCO-2, CC0). G major, light and warm, follows the figures:
//  each new figure = a pizzicato chord + a flute phrase; the fast run (13.6-19.4) = rising pizzicato steps;
//  the grand figure = full chord with flute high note; 24+ the tone stops -> clarinet + flute resolve, silence.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { SSTORY } from "../src/scenes/sand/chladni";
import { reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, play } from "./lib/sampler";

export function generateSandMusic(reel: Reel): string {
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const out = stereo(total);
  const r = rng(reel.seed, "sand-music");
  const M = SSTORY.modes;
  const pz = (m: number, at: number, g: number, pan = 0.5) => play(out, orch(m < 55 ? "celliPizz" : "violinsPizz", m), at, g, pan);
  const fl = (m: number, at: number, dur: number, g: number, pan = 0.55) => play(out, orch("flute", m), at, g, pan, dur, 0.5, 0.3);
  const cl = (m: number, at: number, dur: number, g: number, pan = 0.45) => play(out, orch("clarinet", m), at, g, pan, dur, 0.6, 0.3);

  const chords = [[43, 59, 62, 67], [40, 59, 64, 67], [36, 60, 64, 67], [38, 57, 62, 66], [43, 59, 62, 71], [40, 59, 64, 71], [36, 60, 67, 72], [38, 62, 66, 74], [45, 64, 69, 73], [43, 67, 71, 74]];
  const phrases = [[74, 76, 79], [76, 74, 71], [72, 76, 79], [74, 78, 81], [79, 76, 74]];
  M.forEach((md, k) => {
    const t0 = Math.max(0.02, md.t + 0.15), ch = chords[k % chords.length];
    ch.forEach((m, j) => pz(m, t0 + j * 0.06, j === 0 ? 0.32 : 0.2, 0.3 + j * 0.13));
    if (k < 5) phrases[k].forEach((m, j) => fl(m, t0 + 0.5 + j * 0.42, 0.38, 0.13 + (j === 2 ? 0.04 : 0)));
  });
  // the fast run: rising pizzicato steps between figures
  for (let k = 5; k < M.length - 1; k++) {
    const a = M[k].t, b = M[k + 1].t, ch = chords[k];
    for (let i = 0, t = a + 0.5; t < b - 0.1; i++, t += 0.18) pz(ch[1 + (i % 3)] + 12 * Math.floor(i / 3), t, 0.12, 0.35 + 0.3 * ((i % 3) / 2));
  }
  play(out, orch("celli", 43), 0.3, 0.08, 0.4, 11, 1.5, 0.45);
  play(out, orch("celli", 38), M[5].t, 0.1, 0.4, M[9].t - M[5].t, 0.5, 0.45);
  // the grand figure
  const G = M[M.length - 1].t;
  [31, 43, 55, 59, 62, 67, 71, 74].forEach((m, j) => pz(m, G + j * 0.04, j < 2 ? 0.34 : 0.18, 0.3 + j * 0.06));
  fl(86, G + 0.4, 2.4, 0.15);
  play(out, orch("celli", 43), G, 0.11, 0.4, 4.0, 1.5, 0.45);
  play(out, orch("violas", 59), G + 0.3, 0.07, 0.6, 3.6, 1.5, 0.45);
  // ending: the tone stops -> clarinet + flute resolve
  const E = SSTORY.toneOff;
  cl(55, E + 0.1, 2.6, 0.13);
  cl(59, E + 0.9, 1.9, 0.1);
  fl(79, E + 1.4, 1.8, 0.11);
  fl(74, E + 2.4, 1.6, 0.09);
  pz(43, E + 2.0, 0.22, 0.45);
  void r;

  reverb(out, { room: 0.84, damp: 0.4, wet: 0.3, preDelayMs: 18, loop: false });
  const rel = `generated/${reel.id}-music.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (flute/clarinet/pizzicato score)`);
  return rel;
}
