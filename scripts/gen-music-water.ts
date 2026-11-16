// Score for 0020 "This water falls upward": new sound palette (not the ferrofluid reels' strings + piano pulse):
// harp arpeggios and glassy glockenspiel over soft high strings, in E major/C# minor - airy, weightless, wondering.
// A rising harp line follows the climbing water, a held chord blooms on the ceiling hit, a soft descending line under the
// rain, and it settles on E major into the fade. VSCO-2 (CC0), Salamander piano (CC BY 3.0, credited by the render).
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import EV from "../src/scenes/water/events.json";
import { reverb, SR, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, piano, play } from "./lib/sampler";

export function generateWaterMusic(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "water-music");
  const O = (inst: string, m: number, at: number, g: number, dur: number, pan = 0.5, rel = 1.2) => play(out, orch(inst, m, true), Math.max(0, at), g, pan, dur, rel, 0.7);
  const P = (m: number, at: number, g: number, dur: number, pan = 0.5) => play(out, piano(m, true), Math.max(0, at + (r() - 0.5) * 0.01), g, pan, dur, 1.8, 0.8);
  // cold open: a bright chord on the hit
  [64, 68, 71, 76].forEach((m, i) => O("harp", m, EV.coldHit + i * 0.04, 0.09, 1.5, 0.35 + 0.1 * i));
  O("violins", 83, EV.coldHit, 0.02, 0.8, 0.6, 0.6);
  // the rise: a climbing harp arpeggio, soft high strings
  const arp = [52, 56, 59, 64, 68, 71, 76, 80, 83, 88];
  const [a, b] = EV.rise;
  for (let i = 0; i < 26; i++) O("harp", arp[i % arp.length] + (i >= arp.length ? 0 : 0), a + (b - a) * (i / 26), 0.06 + 0.002 * i, 1.2, 0.3 + 0.4 * ((i * 3) % 7) / 6);
  O("violins", 76, a, 0.02, b - a, 0.64, 1.0);
  O("violas", 68, a + 0.5, 0.025, b - a - 0.5, 0.56, 1.0);
  O("celli", 52, a, 0.035, b - a, 0.42, 1.0);
  // the braid: a glassy shimmer
  for (let i = 0; i < 6; i++) O("glockenspiel", [88, 92, 95, 91, 88, 95][i], EV.braid[0] + i * 0.35, 0.018, 1.0, 0.3 + 0.08 * i);
  // the hit: a held chord blooms
  [52, 59, 64, 68, 71, 76].forEach((m, i) => P(m, EV.hit + 0.03 + i * 0.05, 0.06, 3.0, 0.35 + 0.06 * i));
  O("celli", 49, EV.hit, 0.05, 3, 0.42, 1.5);
  // the rain: a soft descending harp line
  [83, 80, 76, 73, 71, 68, 64].forEach((m, i) => O("harp", m, EV.hit + 1.5 + i * 0.45, 0.05, 1.4, 0.4 + 0.05 * i));
  // the refill and the settle: E major into the fade
  [52, 56, 59, 64].forEach((m, i) => P(m, EV.refill[1] - 0.3 + i * 0.14, 0.05, 3.0, 0.4 + 0.07 * i));
  O("celli", 40, EV.refill[1] - 0.3, 0.04, EV.fade[1] - EV.refill[1] + 0.3, 0.42, 1.5);
  reverb(out, { room: 0.9, damp: 0.4, wet: 0.3, preDelayMs: 22, loop: false });
  const f0 = Math.round(EV.fade[0] * SR), f1 = Math.round(EV.fade[1] * SR);
  for (let k = f0; k < out[0].length; k++) { const g = k >= f1 ? 0 : (1 - (k - f0) / (f1 - f0)) ** 1.5; out[0][k] *= g; out[1][k] *= g; }
  const rel = `generated/${reel.id}-music.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (water score, harp + strings, E major)`);
  return rel;
}
