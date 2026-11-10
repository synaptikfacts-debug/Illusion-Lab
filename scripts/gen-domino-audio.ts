// Sound effects for "The Butterfly Domino", from the same simulation as the picture (every sound has a visible cause).
//  - hook: a soft triangle shimmer on the glowing butterfly
//  - rewind: every domino springing up = reversed clicks + a reversed cymbal breath
//  - fuse: each lane domino is a single crisp click (you can count them), plus a soft fuse crackle on the spark
//  - bloom: thousands of landings binned into a dense, panned ceramic rattle; a soft timpani as it bursts
//  - wings: a soft air whoosh on every beat + the light rattle of wing dominoes dropping back
//  - ending: one last triangle as the body glow goes out, then silence
// Real recordings (VSCO-2 CC0 woodblock/claves, cymbal, timpani, triangle). Writes assets/generated/<id>-sfx.wav.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { dominoSchema } from "../src/illusions/dominoStory/schema";
import { DSTORY, simulateDominoes } from "../src/scenes/dominoes/sim";
import { addWrapped, Biquad, reverb, SR, stereo, type Stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, play, unpitched } from "./lib/sampler";

type Voice = ReturnType<typeof unpitched>;
const reversed = (v: Voice): Voice => ({ ...v, sample: v.sample.map((ch) => Float32Array.from(ch).reverse()) as Stereo });

function playRamp(out: Stereo, voice: Voice, at: number, g0: number, g1: number, sec: number, pan = 0.5) {
  const tmp = stereo(sec + 0.5);
  play(tmp, voice, 0, 1, pan, sec, 0.3);
  const n = Math.round(sec * SR), s0 = Math.round(at * SR), N = out[0].length;
  for (let i = 0; i < n; i++) {
    const g = g0 + (g1 - g0) * (i / n), k = s0 + i;
    if (k < 0 || k >= N) continue;
    out[0][k] += tmp[0][i] * g;
    out[1][k] += tmp[1][i] * g;
  }
}

export function generateDominoAudio(reel: Reel): string {
  const p = dominoSchema.parse(reel.illusion.props);
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const sim = simulateDominoes(tl.fps, p.cols, p.rows, p.spacing);
  const L = sim.layout;
  const out = stereo(total);
  const r = rng(reel.seed, "domino-sfx");
  const clicks = [unpitched("woodblock", 2), unpitched("woodblock", 3), unpitched("woodblock", 1)];
  const panOf = (i: number) => 0.5 + 0.42 * L.u[i];
  const swish = (at: number, dur: number, g: number, f0: number, f1: number, pan = 0.5) => {
    const bp = new Biquad();
    addWrapped(out, at, dur, pan, (t, i) => {
      const x = t / dur;
      if (i % 64 === 0) bp.set("bp", f0 + (f1 - f0) * x, 0.9);
      return bp.run(r() * 2 - 1) * Math.sin(Math.PI * x) ** 2 * g;
    });
  };

  // hook shimmer
  play(out, unpitched("triangle", 0), 0.0, 0.3, 0.55, undefined, 0.5, 0.2);

  // rewind: reversed cymbal breath + reversed clicks binned
  const cym = unpitched("cymbal", 4);
  const cLen = Math.min(cym.sample[0].length / SR, DSTORY.rewind[1] - DSTORY.rewind[0] + 0.2);
  playRamp(out, reversed(cym), DSTORY.rewind[1] + 0.1 - cLen, 0.1, 0.45, cLen);
  const bins = new Map<string, { t: number; e: number; pan: number; k: number; lane: boolean }>();
  let laneHits = 0;
  for (const h of sim.hits) {
    if (L.lane[h.i] && h.k === 0) {
      // the fuse: one clear click per domino, slightly brighter as it runs
      const step = Math.round((h.t - DSTORY.lane.start) / DSTORY.lane.step);
      play(out, { ...clicks[step % 2], rate: 1.7 + step * 0.008 }, h.t, 0.36, panOf(h.i) + (r() - 0.5) * 0.1, undefined, 0.2, 0.25);
      laneHits++;
      continue;
    }
    const zone = Math.min(4, Math.floor(((L.u[h.i] + 1) / 2) * 5));
    const key = `${h.k}|${Math.floor(h.t / 0.005)}|${zone}`;
    const b = bins.get(key) ?? { t: h.t, e: 0, pan: 0.15 + zone * 0.175, k: h.k, lane: false };
    b.e += h.e * h.e;
    bins.set(key, b);
  }
  let n = 0;
  for (const b of bins.values()) {
    const g = Math.min(0.3, (b.k === 1 ? 0.035 : b.k === 2 ? 0.04 : 0.06) * Math.sqrt(b.e));
    if (g < 0.005) continue;
    const v = clicks[Math.floor(r() * clicks.length)];
    const rate = (b.k === 2 ? 1.5 : 1.85) + r() * 0.5;
    play(out, b.k === 1 ? { ...reversed(v), rate } : { ...v, rate }, b.t + (r() - 0.5) * 0.004, g, b.pan, undefined, 0.2, 0.35);
    n++;
  }

  // fuse crackle following the spark
  const fz = new Biquad().set("bp", 3800, 1.4);
  const fuseLen = DSTORY.bloom.start - DSTORY.lane.start;
  addWrapped(out, DSTORY.lane.start, fuseLen, 0.5, (t) => {
    const x = r();
    return (x > 0.985 ? (r() * 2 - 1) * 2.2 : 0) * 0.05 + fz.run(r() * 2 - 1) * 0.02 * Math.min(1, t * 3) * Math.min(1, (fuseLen - t) * 4);
  });

  // bloom: reversed cymbal leading in + soft timpani on the burst + a long rising air
  const rev = reversed(unpitched("cymbal", 3));
  const rLen = Math.min(rev.sample[0].length / SR, 1.6);
  playRamp(out, rev, DSTORY.bloom.start - rLen, 0.05, 0.35, rLen);
  play(out, orch("timpani", 50), DSTORY.bloom.start, 0.45, 0.5, undefined, 0.5);
  swish(DSTORY.bloom.start, 6.5, 0.05, 300, 1400);

  // wings
  DSTORY.beats.forEach((b, j) => {
    const len = DSTORY.beatLen[j];
    swish(b, len, j === 3 ? 0.2 : 0.15, 500, 1600, 0.4);
    swish(b + 0.05, len, j === 3 ? 0.16 : 0.12, 600, 1800, 0.6);
  });

  // ending: last chime as the body glow goes out
  play(out, { ...unpitched("triangle", 1), rate: 0.94 }, DSTORY.fadeGlow[1] + 0.3, 0.2, 0.5, undefined, 0.5, 0.3);

  reverb(out, { room: 0.82, damp: 0.42, wet: 0.22, preDelayMs: 14, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.05);
  console.log(`wrote assets/${rel} (${laneHits} fuse clicks, ${n} rattle sounds from ${sim.hits.length} domino hits)`);
  return rel;
}
