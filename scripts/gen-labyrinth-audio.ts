// Sound effects for "Ferrofluid Labyrinth" - CALM (owner, Nov 11: the first mix was "ridiculous annoying"; wants calm
// and satisfying). Few sounds, all soft, each on a moment you can see: no drums, no rumble, no plucks, no cymbals.
// Salamander felt piano (CC BY 3.0, credited in the captions), heavily softened ("felt" low-pass), plus one triangle.
//  - the rewind: one soft reversed piano note swelling into the drop as it forms (2.2 s)
//  - the drop rests: one soft high felt tap
//  - the burst (3.2 s): a soft two-note felt tap
//  - the maze spreads: a few gentle felt taps, spaced wider as it fills (not one per finger)
//  - the magnet cuts out: one soft reversed note into the retraction
//  - the drop settles (28.6 s): a low felt note + a faint triangle; then silence
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { LSTORY } from "../src/scenes/labyrinth/story";
import { reverb, SR, stereo, type Stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { piano, play, unpitched } from "./lib/sampler";

type Voice = ReturnType<typeof unpitched>;
const reversed = (v: Voice): Voice => ({ ...v, sample: v.sample.map((ch) => Float32Array.from(ch).reverse()) as Stereo });
const CS_MAJ_PENT = [73, 75, 77, 80, 82, 85, 87]; // C#5 major pentatonic: nothing can clash

export function generateLabyrinthAudio(reel: Reel): string {
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const out = stereo(total);
  const r = rng(reel.seed, "labyrinth-calm-sfx");
  const S = LSTORY;
  const tap = (m: number, at: number, g: number, pan = 0.5) => play(out, piano(m, true), at, g, pan, 0.5, 1.6, 0.9); // soft felt tap

  // the rewind: a soft reversed note swelling into the drop
  const rv = reversed(piano(80, true));
  const rl = Math.min(rv.sample[0].length / SR, 1.1);
  play(out, rv, S.rewind[1] - rl, 0.1, 0.5, rl, 0.05, 0.85);
  tap(85, S.rewind[1] + 0.05, 0.12, 0.52);

  // the burst
  tap(73, S.burst, 0.13, 0.46);
  tap(80, S.burst + 0.12, 0.09, 0.56);

  // the maze spreads: a few gentle taps, further apart as it fills
  let t = S.burst + 1.4, gap = 1.2;
  while (t < S.filled) {
    tap(CS_MAJ_PENT[Math.floor(r() * CS_MAJ_PENT.length)], t, 0.06 + 0.02 * r(), 0.3 + 0.4 * r());
    t += gap;
    gap *= 1.18;
  }

  // the spiral winds: a very soft tap every few seconds as it turns
  for (let w = S.wind[0] + 1.5; w < S.retract[0] - 1; w += 3.2) tap(CS_MAJ_PENT[Math.floor(r() * CS_MAJ_PENT.length)] + 12, w, 0.045, 0.35 + 0.3 * r());

  // the magnet cuts out: one soft reversed note into the retraction
  const rr = reversed(piano(73, true));
  const rrl = Math.min(rr.sample[0].length / SR, 1.4);
  play(out, rr, S.retract[0] - rrl + 0.2, 0.09, 0.5, rrl, 0.05, 0.85);

  // the drop settles
  play(out, piano(49, true), S.retract[1], 0.09, 0.48, 1.5, 2.2, 0.85);
  play(out, unpitched("triangle", 1), S.retract[1] + 0.08, 0.04, 0.55, undefined, 1.8, 0.4);

  reverb(out, { room: 0.9, damp: 0.5, wet: 0.36, preDelayMs: 24, loop: false });
  const f0 = Math.round(S.fade[0] * SR), f1 = Math.round(S.fade[1] * SR);
  for (let k = f0; k < out[0].length; k++) {
    const g = k >= f1 ? 0 : 1 - (k - f0) / (f1 - f0);
    out[0][k] *= g;
    out[1][k] *= g;
  }
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (calm: soft felt taps on the visible moments only)`);
  return rel;
}
