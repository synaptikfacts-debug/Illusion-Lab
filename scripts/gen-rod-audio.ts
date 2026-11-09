// Sound effects for "The Eye" (rodStory), built from the SAME simulation as the picture so every sound has a
// visible cause (owner, Nov 10: "sounds are cheap and not related to the reel"). No music, no melody: this mix is
// used on every platform; YouTube adds the music on top.
//  - clacks: every rod that finishes a fast move clicks (real woodblock/claves recordings, VSCO-2 CC0), panned to
//    where the rod is, louder for harder moves, grouped in 6 ms bins so 20k events stay clean
//  - accents: the first pop, each drop that starts a ripple, a cymbal swell + timpani roll building through the
//    spiral, timpani + bass drum on the SNAP, soft lid swishes on the blink and the close, the last rod's "tock"
//  - air: very quiet dark air that follows how fast the whole wall moves
// Writes assets/generated/<id>-sfx.wav.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { rodSchema } from "../src/illusions/rodStory/schema";
import { simulate, STORY } from "../src/scenes/rods/sim";
import { addWrapped, Biquad, reverb, SR, stereo, type Stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, play, unpitched } from "./lib/sampler";

/** Plays a sample with a linear gain ramp (g0 -> g1) by rendering it into a scratch buffer first. */
function playRamp(out: Stereo, voice: ReturnType<typeof unpitched>, at: number, g0: number, g1: number, sec: number, pan = 0.5, reverse = false) {
  const tmp = stereo(sec + 0.5);
  const v = reverse ? { ...voice, sample: voice.sample.map((ch) => Float32Array.from(ch).reverse()) as Stereo } : voice;
  play(tmp, v, 0, 1, pan, sec, 0.3);
  const n = Math.round(sec * SR), s0 = Math.round(at * SR), N = out[0].length;
  for (let i = 0; i < n; i++) {
    const g = g0 + (g1 - g0) * (i / n);
    const k = (((s0 + i) % N) + N) % N;
    out[0][k] += tmp[0][i] * g;
    out[1][k] += tmp[1][i] * g;
  }
}

export function generateRodAudio(reel: Reel): string {
  const params = rodSchema.parse(reel.illusion.props);
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const sim = simulate(tl.fps, params.grid, params.rows, params.spacing);
  const out = stereo(total);
  const r = rng(reel.seed, "rod-sfx");
  const L = sim.layout;

  // 1) clacks, binned
  const BIN = 0.006, ZONES = 5;
  const bins = new Map<number, number>();
  for (const c of sim.clacks) {
    const zone = Math.min(ZONES - 1, Math.floor(((L.u[c.i] + 1) / 2) * ZONES));
    const key = Math.floor(c.t / BIN) * ZONES + zone;
    bins.set(key, (bins.get(key) ?? 0) + c.e * c.e);
  }
  const voices = [unpitched("woodblock", 0), unpitched("woodblock", 1), unpitched("woodblock", 2), unpitched("woodblock", 3)];
  let n = 0;
  for (const [key, e] of bins) {
    const zone = key % ZONES, t = Math.floor(key / ZONES) * BIN + r() * BIN;
    const g = Math.min(0.32, 0.075 * Math.sqrt(e));
    if (g < 0.006) continue;
    const v = voices[Math.floor(r() * voices.length)];
    const rate = 1.25 + r() * 0.55; // small rods: higher and lighter than a full-size woodblock
    play(out, { ...v, rate }, t, g, 0.15 + (zone / (ZONES - 1)) * 0.7, undefined, 0.3, 0.45);
    n++;
  }

  // 2) accents
  play(out, unpitched("woodblock", 0), 0.0, 0.55, 0.5, undefined, 0.3, 0.2); // first pop (frame 0)
  for (const s of STORY.sources) play(out, { ...unpitched("woodblock", 1), rate: 0.85 + 0.1 * s.a }, s.t, 0.42 * s.a, 0.5 + 0.35 * s.u, undefined, 0.3, 0.3);
  // build through the spiral: reversed soft cymbal + real cymbal swell + timpani roll, all landing on the SNAP
  const [s0, s1] = STORY.spiral;
  const swell = unpitched("cymbal", 2);
  const swellLen = Math.min(swell.sample[0].length / SR, s1 - s0);
  playRamp(out, swell, s1 - swellLen, 0.15, 0.55, swellLen, 0.5);
  const rev = unpitched("cymbal", 3);
  const revLen = Math.min(rev.sample[0].length / SR, 2.2);
  playRamp(out, rev, s1 - revLen, 0.05, 0.4, revLen, 0.5, true);
  playRamp(out, orch("timpaniRoll", 45), s0 + 0.5, 0.0, 0.5, s1 - s0 - 0.5, 0.5);
  // SNAP
  play(out, orch("timpani", 41), STORY.snap, 0.75, 0.5, undefined, 0.4);
  play(out, unpitched("bassdrum", 2), STORY.snap, 0.55, 0.5, undefined, 0.4);
  play(out, unpitched("cymbal", 3), STORY.snap + 0.02, 0.22, 0.5, undefined, 0.6);
  // lids: soft swishes (filtered noise shaped like the lid movement)
  const swish = (at: number, dur: number, g: number, f0: number, f1: number) => {
    const bp = new Biquad();
    addWrapped(out, at, dur, 0.5, (t, i) => {
      const x = t / dur;
      if (i % 64 === 0) bp.set("bp", f0 + (f1 - f0) * x, 1.1);
      return bp.run(r() * 2 - 1) * Math.sin(Math.PI * x) ** 2 * g;
    });
  };
  const [b0, b1] = STORY.blink;
  swish(b0, (b1 - b0) / 2, 0.2, 2400, 900);
  swish((b0 + b1) / 2, (b1 - b0) / 2, 0.14, 900, 2000);
  swish(STORY.close[0], STORY.close[1] - STORY.close[0], 0.16, 2000, 500);
  // THE END: the last rod
  play(out, { ...unpitched("woodblock", 0), rate: 0.72 }, STORY.lastLand + 0.12, 0.7, 0.5, undefined, 0.3, 0.15);
  play(out, orch("timpani", 41), STORY.lastLand + 0.12, 0.3, 0.5, undefined, 0.5);

  // 3) air
  const [Lc, Rc] = out;
  const bl = new Biquad(), br = new Biquad();
  let e = 0;
  const maxS = Math.max(...sim.speed);
  for (let i = 0; i < Lc.length; i++) {
    const f = Math.min(sim.frames - 1, Math.floor((i / SR) * tl.fps));
    e += (sim.speed[f] / maxS - e) * 0.0005;
    if (i % 128 === 0) { bl.set("lp", 300 + 900 * e, 0.6); br.set("lp", 320 + 950 * e, 0.6); }
    Lc[i] += bl.run(r() * 2 - 1) * e * 0.18;
    Rc[i] += br.run(r() * 2 - 1) * e * 0.18;
  }

  reverb(out, { room: 0.8, damp: 0.45, wet: 0.2, preDelayMs: 12 });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.05);
  console.log(`wrote assets/${rel} (${sim.clacks.length} rod clacks -> ${n} sounds, accents, air)`);
  return rel;
}
