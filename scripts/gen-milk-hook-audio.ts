// 0028 v4 cold-open hook for the sound (owner, Nov 20: "a prettier, more interesting opening"; the cold open + tape rewind
// is the channel's proven hook - 0018 got ~1.2k views in a day): the story SFX (written in story time) are laid onto the
// real timeline = [cold open: story FROM .. FROM+COLD] [rewind: back to 0 in REW s, fast, muffled + a falling whoosh]
// [the story from 0]. The picture is cut the same way in ffmpeg (see the 0028 v4 build notes).
// Usage: npx tsx scripts/gen-milk-hook-audio.ts <story.wav> <from> <cold> <rew> <storySec> <out.wav>
import { spawnSync } from "node:child_process";
import { Biquad, SR, stereo, writeWav } from "./lib/dsp";

const CHANNELS = 2;
const BYTES_PER_SAMPLE = 4;
const MAX_BUFFER = 1024 * 1024 * 1024;   // 1 GiB of decoded audio
const FILTER_EVERY = 32;              // retune the filters every N samples
const REWIND_LP_HZ = 1400;
const FILTER_Q = 0.7;
const REWIND_GAIN = 0.5;
const REWIND_EDGE = 8;                // 1/8 of the rewind fades in and out
const SWEEP_TOP_HZ = 3200;
const SWEEP_FALL = 0.12;
const SWEEP_FLOOR_HZ = 300;
const SWEEP_Q = 2.0;
const SWEEP_SHAPE = 1.5;
const SWEEP_GAIN = 0.55;
const LCG_A = 1664525;
const LCG_C = 1013904223;
const UINT32 = 4294967296;               // 2^32
const WAV_DRIVE = 1.0;

const ARGS_FROM = 2;                     // argv[0] = node, argv[1] = script
const NOISE_SPAN = 2;                    // uniform 0..1 -> -1..1
const [inPath, fromA, coldA, rewA, storyA, outPath] = process.argv.slice(ARGS_FROM);
const FROM = Number(fromA), COLD = Number(coldA), REW = Number(rewA), STORY = Number(storyA);
const raw = spawnSync("ffmpeg", ["-v", "error", "-i", inPath, "-f", "f32le", "-ac", String(CHANNELS), "-ar", String(SR), "-"], { maxBuffer: MAX_BUFFER }).stdout as Buffer;
const inter = new Float32Array(raw.buffer, raw.byteOffset, raw.length / BYTES_PER_SAMPLE);
const n = inter.length / CHANNELS;
const src = [0, 1].map((c) => Float32Array.from({ length: n }, (_, i) => inter[CHANNELS * i + c])) as [Float32Array, Float32Array];

/** story time for a real time: cold open, then the rewind back to 0, then the story */
function tauAt(t: number): number {
  if (t < COLD) return FROM + t;
  if (t < COLD + REW) return (FROM + COLD) * (1 - (t - COLD) / REW);
  return t - COLD - REW;
}

const out = stereo(COLD + REW + STORY);
const lp = [new Biquad(), new Biquad()];
out[0].forEach((_, i) => {
  const t = i / SR;
  const pos = tauAt(t) * SR, k = Math.floor(pos), fr = pos - k;
  if (k < 0 || k + 1 >= n) return;
  const x = (t - COLD) / REW;
  const inRewind = x > 0 && x < 1;
  if (inRewind && i % FILTER_EVERY === 0) lp.forEach((b) => b.set("lp", REWIND_LP_HZ, FILTER_Q));
  const g = REWIND_GAIN * Math.min(1, x * REWIND_EDGE, (1 - x) * REWIND_EDGE);
  [0, 1].forEach((c) => {
    const s = src[c][k] * (1 - fr) + src[c][k + 1] * fr;
    out[c][i] = inRewind ? lp[c].run(s) * g : s;        // the rewind: backwards, darker, softer, a dip at both ends
  });
});

let seed = 2804;
const rnd = () => ((seed = (seed * LCG_A + LCG_C) >>> 0) / UINT32);
const bp = new Biquad();
const s0 = Math.round(COLD * SR), N = Math.round(REW * SR);
Array.from({ length: N }, (_, i) => i).forEach((i) => {   // a tape-rewind whoosh: band noise falling in pitch
  const x = i / N;
  if (i % FILTER_EVERY === 0) bp.set("bp", SWEEP_TOP_HZ * Math.pow(SWEEP_FALL, x) + SWEEP_FLOOR_HZ, SWEEP_Q);
  const v = bp.run(rnd() * NOISE_SPAN - 1) * Math.sin(Math.PI * x) ** SWEEP_SHAPE * SWEEP_GAIN;
  out[0][s0 + i] += v; out[1][s0 + i] += v;
});
writeWav(outPath, out, WAV_DRIVE);
console.log(`wrote ${outPath} (${(COLD + REW + STORY).toFixed(2)} s)`);
