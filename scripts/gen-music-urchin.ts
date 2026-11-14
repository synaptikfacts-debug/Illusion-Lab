// Score for 0016 "Urchin Heart": original, cinematic and tactile. E minor, tempo locked to the heartbeat.
// Low celli + basses breathe with the heart, a harp and a glockenspiel note mark every transformation, the strings and
// a timpani roll rise into the BREACH (the payoff, 23.4 s), a chord lands on it, and the score resolves to E major as
// the sphere settles - then thins to a single soft note so the loop back to frame 0 is seamless.
// Real samples: VSCO-2 (CC0) and the Salamander piano (CC BY 3.0, credited by the render).
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import TL from "../src/scenes/urchin/timeline.json";
import { reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, piano, play, unpitched } from "./lib/sampler";

export function generateUrchinMusic(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "urchin-music");
  const O = (inst: string, m: number, at: number, g: number, dur: number, pan = 0.5, rel = 1.2) => play(out, orch(inst, m, true), Math.max(0, at), g, pan, dur, rel, 0.7);
  const P = (m: number, at: number, g: number, dur: number, pan = 0.5) => play(out, piano(m, true), Math.max(0, at + (r() - 0.5) * 0.01), g, pan, dur, 1.8, 0.8);

  // a heartbeat bass pulse under everything (E)
  const pulseAt = [0.4, ...TL.beats];
  for (const b of pulseAt) O("basses", 40, b, 0.06, 0.6, 0.5, 0.6);
  // E minor bed that breathes, with a harp note on every transformation
  const bed: [number, number, number[]][] = [[0, 6, [52, 55, 59]], [6, 10, [48, 52, 55]], [10, 15, [45, 48, 52]], [15, 19, [47, 50, 54]], [19, 22.6, [48, 52, 55]], [22.6, 23.4, [47, 51, 54]]];
  for (const [a, b, ch] of bed) {
    O("celli", ch[0], a, 0.05, b - a + 0.2, 0.42, 0.8);
    O("violas", ch[2], a + 0.1, 0.03, b - a + 0.1, 0.58, 0.8);
  }
  for (const [t, m] of [[TL.twitch, 76], [TL.crawl[0], 71], [TL.urchin[0], 74], [TL.split[0], 79], [TL.merge, 83]] as [number, number][]) {
    O("harp", m - 12, t, 0.09, 1.8, 0.4);
    O("glockenspiel", m + 12, t + 0.02, 0.025, 1.5, 0.62);
  }
  // the rise into the breach: violins climb, a timpani roll
  [64, 66, 67, 69, 71, 72].forEach((m, i) => O("violins", m + 12, TL.merge - 3.2 + i * 0.55, 0.03 + i * 0.006, 0.6, 0.64, 0.3));
  O("timpaniRoll", 40, TL.breach[0] - 1.2, 0.18, 1.2, 0.5, 0.1);
  // the breach: a chord lands (E minor add9), piano + strings + a soft bass drum
  play(out, unpitched("bassdrum", 0), TL.breach[0], 0.32, 0.5, 2.0, 1.2, 0.6);
  O("timpani", 40, TL.breach[0], 0.3, 2.0, 0.5, 1.5);
  [52, 59, 64, 66, 67, 71].forEach((m, i) => P(m, TL.breach[0] + 0.04 + i * 0.05, 0.06, 3, 0.35 + 0.06 * i));
  O("celli", 40, TL.breach[0], 0.07, 3.4, 0.42, 1.5);
  O("violins", 71, TL.breach[0] + 0.1, 0.04, 3.2, 0.66, 1.5);
  // resolve to E major as it settles, then thin out to one soft note that also opens the reel (seamless loop)
  [56, 59, 64, 68].forEach((m, i) => P(m, TL.breach[1] + 0.1 + i * 0.12, 0.05, 2.5, 0.4 + 0.07 * i));
  O("celli", 52, TL.breach[1], 0.05, TL.duration - TL.breach[1] - 0.3, 0.42, 1.2);
  P(76, TL.settle[1] - 1.6, 0.035, 1.4, 0.6);

  reverb(out, { room: 0.88, damp: 0.45, wet: 0.28, preDelayMs: 20, loop: true });
  const rel = `generated/${reel.id}-music.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (urchin heart score, E minor -> E major)`);
  return rel;
}
