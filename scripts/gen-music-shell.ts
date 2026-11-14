// Score for 0017 "Obsidian Heart" v4: original, dark and cinematic, C# minor, under the tapping SFX.
// Tension under the peel, a hit on the blast, a wide string chord while the crystals grow, a chime-like piano line on
// the light pulses, a timpani roll into the slam and a chord on it, then one note rings into the fade.
// Real samples: VSCO-2 (CC0), Salamander piano (CC BY 3.0, credited by the render).
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import TL from "../src/scenes/shell/timeline.json";
import { reverb, SR, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, piano, play, unpitched } from "./lib/sampler";

export function generateShellMusic(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "shell-music-v4");
  const O = (inst: string, m: number, at: number, g: number, dur: number, pan = 0.5, rel = 1.2) => play(out, orch(inst, m, true), Math.max(0, at), g, pan, dur, rel, 0.7);
  const P = (m: number, at: number, g: number, dur: number, pan = 0.5) => play(out, piano(m, true), Math.max(0, at + (r() - 0.5) * 0.01), g, pan, dur, 1.8, 0.8);
  // tension under the peel: low C# and a rising violin line
  O("basses", 37, 0, 0.07, TL.blast[0] + 0.2, 0.5, 0.4);
  O("celli", 49, 0, 0.05, TL.blast[0], 0.42, 0.4);
  [61, 62, 64, 66].forEach((m, i) => O("violins", m + 12, 0.4 + i * 0.6, 0.025 + i * 0.006, 0.65, 0.64, 0.2));
  // blast hit
  play(out, unpitched("bassdrum", 0), TL.blast[0], 0.3, 0.5, 2, 1.2, 0.6);
  O("timpani", 37, TL.blast[0], 0.3, 2, 0.5, 1.5);
  [49, 56, 61, 64].forEach((m, i) => P(m, TL.blast[0] + 0.03 + i * 0.04, 0.07, 2.4, 0.35 + 0.08 * i));
  // orbit + grow: a wide chord, strings swell as the crystals grow
  O("celli", 45, TL.blast[1], 0.05, TL.grow[0] - TL.blast[1] + 0.2, 0.42, 1.0);
  O("violas", 56, TL.blast[1] + 0.1, 0.035, TL.grow[0] - TL.blast[1], 0.58, 1.0);
  O("celli", 49, TL.grow[0], 0.06, TL.retract[1] - TL.grow[0], 0.42, 1.0);
  O("violas", 56, TL.grow[0] + 0.1, 0.045, TL.retract[1] - TL.grow[0], 0.58, 1.0);
  O("violins", 68, TL.grow[0] + 0.4, 0.035, TL.retract[0] - TL.grow[0], 0.66, 1.0);
  O("harp", 61, TL.grow[0], 0.08, 2, 0.4);
  // the light pulses: a chime-like piano line
  TL.pulses.forEach((p, i) => { P([73, 76, 80][i], p, 0.06, 1.4, 0.4 + 0.1 * i); O("glockenspiel", [85, 88, 92][i], p + 0.02, 0.02, 1.2, 0.6); });
  // roll into the slam, chord on it
  O("timpaniRoll", 37, TL.slam[0] + 0.2, 0.15, TL.slam[1] - TL.slam[0] - 0.3, 0.5, 0.1);
  play(out, unpitched("bassdrum", 0), TL.slam[1] - 0.15, 0.3, 0.5, 2, 1.2, 0.6);
  [37, 49, 56, 61, 64].forEach((m, i) => P(m, TL.slam[1] - 0.12 + i * 0.05, 0.07, 2.6, 0.35 + 0.07 * i));
  // the ending: one note rings into the fade
  O("celli", 37, TL.slam[1], 0.05, TL.fade[1] - TL.slam[1], 0.42, 1.5);
  P(68, TL.last, 0.045, 1.8, 0.55);
  reverb(out, { room: 0.88, damp: 0.45, wet: 0.26, preDelayMs: 20, loop: false });
  const f0 = Math.round(TL.fade[0] * SR), f1 = Math.round(TL.fade[1] * SR);
  for (let k = f0; k < out[0].length; k++) { const g = k >= f1 ? 0 : (1 - (k - f0) / (f1 - f0)) ** 1.5; out[0][k] *= g; out[1][k] *= g; }
  const rel = `generated/${reel.id}-music.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (obsidian heart v4 score, C# minor)`);
  return rel;
}
