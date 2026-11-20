// 0028 "Black ink fired into milk" - soft SFX (owner, Nov 17: "the sounds are horrible and unpleasant"). No noise, no
// whooshes: each shot = a creamy, muted thock (low sine with a slight pitch drop + a felted, low-passed puff) and a quiet
// liquid "bloop" (a soft sine glide) a moment later as the ink sinks in; close shots are thinned so it never clatters;
// gentle room reverb; the last drop gets a single soft plip, then silence into the fade.
// Usage: npx tsx scripts/gen-milk-cosmos-audio.ts <eventsDir> <seconds> <out.wav>
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { addWrapped, Biquad, reverb, SR, stereo, writeWav } from "./lib/dsp";

const [dir, secArg, outPath] = process.argv.slice(2);
const DUR = Number(secArg);
const E = JSON.parse(readFileSync(join(dir, "events.json"), "utf8")) as { shots: { t: number; x: number; k: number }[] };
const out = stereo(DUR);
let seed = 11;
const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 2 ** 32);

// the story clock of milk_cosmos.py (real time -> story time), to place sounds on the slowed picture
const ss = (a: number, b: number, t: number) => { const k = Math.min(1, Math.max(0, (t - a) / (b - a))); return k * k * (3 - 2 * k); };
const rate = (t: number) => 0.6 - 0.28 * ss(4.6, 5.8, t);
const realOf: number[] = [];
{ let tau = 0; for (let t = 0; t < DUR; t += 1 / 600) { while (realOf.length <= Math.floor(tau * 100)) realOf.push(t); tau += rate(t) / 600; } }
const real = (tau: number) => realOf[Math.max(0, Math.min(realOf.length - 1, Math.round(tau * 100)))] ?? DUR;

function thock(at: number, f: number, amp: number, pan: number) {
  const lp = new Biquad().set("lp", 900, 0.7);
  addWrapped(out, at, 0.9, pan, (t) => {
    const body = Math.sin(2 * Math.PI * f * t * (1 - 0.25 * t)) * Math.exp(-t * 11);
    const puff = lp.run(rnd() * 2 - 1) * Math.exp(-t * 70) * 0.35;
    return Math.min(1, t / 0.006) * (body + puff) * amp;
  });
}
function bloop(at: number, f0: number, amp: number, pan: number) {
  let ph = 0;
  addWrapped(out, at, 0.45, pan, (t) => {
    const f = f0 * (1 + 0.6 * (1 - Math.exp(-t * 18)));
    ph += (2 * Math.PI * f) / SR;
    return Math.sin(ph) * Math.exp(-t * 9) * Math.min(1, t / 0.01) * amp;
  });
}

let last = -9;
const shots = [...E.shots].sort((a, b) => a.t - b.t);
shots.forEach((s, i) => {
  const at = Math.max(0.02, real(Math.max(0, s.t + 0.05)));
  if (at - last < 0.32 && i !== shots.length - 1) return;   // thin close shots: never a clatter
  last = at;
  const pan = 0.25 + 0.5 * s.x;
  const k = Math.min(1.5, s.k);
  if (i === shots.length - 1) { bloop(at, 420, 0.12, 0.5); return; }   // the last drop: one soft plip
  thock(at, 58 + 10 * rnd(), 0.32 * k, pan);
  bloop(at + 0.12, 160 + 60 * rnd(), 0.05 * k, pan);
});
reverb(out, { room: 0.8, damp: 0.6, wet: 0.3, preDelayMs: 18, loop: false });
const f0 = Math.round((DUR - 1.8) * SR), f1 = Math.round((DUR - 0.1) * SR);
for (let i = f0; i < out[0].length; i++) { const g = i >= f1 ? 0 : (1 - (i - f0) / (f1 - f0)) ** 1.5; out[0][i] *= g; out[1][i] *= g; }
writeWav(outPath, out, 1.0);
console.log(`wrote ${outPath}`);
