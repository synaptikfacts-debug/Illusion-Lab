// Score for 0019 "This liquid has a heartbeat": slow, warm, cinematic - F minor, real samples, tempo locked to the
// heartbeat. A low cello/bass pulse on every beat, a soft piano answer, strings rise with the tower, a chord blooms on
// the collapse, the rain gets a glockenspiel shimmer, and it settles on F major into the fade.
// VSCO-2 (CC0), Salamander piano (CC BY 3.0, credited by the render).
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { beats, HB } from "../src/scenes/ferroMusic/heartbeat";
import { reverb, SR, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, piano, play, unpitched } from "./lib/sampler";

export function generateHeartbeatMusic(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "heartbeat-music");
  const O = (inst: string, m: number, at: number, g: number, dur: number, pan = 0.5, rel = 1.0) => play(out, orch(inst, m, true), Math.max(0, at), g, pan, dur, rel, 0.7);
  const P = (m: number, at: number, g: number, dur: number, pan = 0.5) => play(out, piano(m, true), Math.max(0, at + (r() - 0.5) * 0.01), g, pan, dur, 1.6, 0.8);
  // the splash of the hook: a low hit and a dark chord
  play(out, unpitched("bassdrum", 0), HB.impact, 0.26, 0.5, 1.6, 1.0, 0.6);
  [41, 53, 56, 60].forEach((m, i) => P(m, HB.impact + 0.03 + i * 0.05, 0.06, 2.4, 0.35 + 0.08 * i));
  // a pulse on every heartbeat, a soft piano answer (F minor, rising as the beats speed up)
  const ans = [65, 68, 72, 70, 68, 72, 75, 77, 75, 80, 77, 84, 80, 84];
  beats().forEach((b, i) => {
    O("basses", 29, b.t, 0.07 * b.g, 0.5, 0.5, 0.4);
    O("celli", 41, b.t + 0.01, 0.05 * b.g, 0.45, 0.42, 0.4);
    if (i < ans.length) P(ans[i], b.t + 0.18, 0.045, 1.0, 0.4 + 0.04 * (i % 5));
  });
  // the tower: strings rise
  O("celli", 41, HB.tower[0], 0.05, HB.collapse - HB.tower[0], 0.42, 0.6);
  O("violas", 56, HB.tower[0] + 0.5, 0.035, HB.collapse - HB.tower[0] - 0.5, 0.58, 0.6);
  [65, 67, 68, 70, 72, 73].forEach((m, i) => O("violins", m + 12, HB.tower[0] + 1.5 + i * 0.6, 0.025 + i * 0.005, 0.7, 0.64, 0.3));
  O("timpaniRoll", 41, HB.collapse - 1.0, 0.13, 1.0, 0.5, 0.1);
  // the collapse: a chord blooms; the rain gets a soft shimmer
  play(out, unpitched("bassdrum", 0), HB.collapse, 0.3, 0.5, 2, 1.2, 0.6);
  [41, 53, 60, 65, 68, 72].forEach((m, i) => P(m, HB.collapse + 0.03 + i * 0.05, 0.065, 2.8, 0.35 + 0.06 * i));
  for (let i = 0; i < 8; i++) O("glockenspiel", [84, 87, 89, 91, 92, 89, 87, 84][i], HB.collapse + 0.5 + i * 0.22, 0.016, 0.8, 0.3 + 0.06 * i);
  // the settle: F major into the fade
  [53, 57, 60, 65].forEach((m, i) => P(m, 15.2 + i * 0.14, 0.05, 3.0, 0.4 + 0.06 * i));
  O("celli", 41, 15.2, 0.045, HB.fade[1] - 15.2, 0.42, 1.5);
  P(77, 16.7, 0.035, 2.2, 0.55);
  reverb(out, { room: 0.88, damp: 0.45, wet: 0.27, preDelayMs: 20, loop: false });
  const f0 = Math.round(HB.fade[0] * SR), f1 = Math.round(HB.fade[1] * SR);
  for (let k = f0; k < out[0].length; k++) { const g = k >= f1 ? 0 : (1 - (k - f0) / (f1 - f0)) ** 1.5; out[0][k] *= g; out[1][k] *= g; }
  const rel = `generated/${reel.id}-music.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (heartbeat score, F minor -> F major)`);
  return rel;
}
