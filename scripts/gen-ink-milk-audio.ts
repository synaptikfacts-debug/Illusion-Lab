// 0028 v3 "Black ink fired into milk" (3D) - sound from the shots in scripts/blender/ink_milk.py (events.json).
// Calm and creamy (owner, Nov 17: the old sounds were "horrible and unpleasant"): every shot = one soft, muted thock (the
// 0011 Singing Pins recipe, pitched 110-200 Hz with warm upper partials so it is heard on a phone speaker; bigger shot =
// deeper) and, a moment later, a quiet low "bloop" as the ink cap rolls over; close shots are thinned so it never
// clatters; the climax blast gets a soft sub swell; the last small drop gets one gentle note; silence into the fade.
// Usage: npx tsx scripts/gen-ink-milk-audio.ts <eventsDir> <seconds> <out.wav>
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { addWrapped, reverb, SR, stereo, writeWav } from "./lib/dsp";

const [dir, secArg, outPath] = process.argv.slice(2);
const DUR = Number(secArg);
const E = JSON.parse(readFileSync(join(dir, "events.json"), "utf8")) as { shots: { t: number; x: number; r: number; spd: number }[] };
const out = stereo(DUR);
let seed = 28;
const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 2 ** 32);

function thock(at: number, f: number, amp: number, pan: number, decay = 9, len = 1.4) {
  let lp = 0;
  addWrapped(out, at, len, pan, (t) => {
    const ph = 2 * Math.PI * f * t * (1 - 0.3 * t);
    const body = Math.sin(ph) * Math.exp(-t * decay) + 0.25 * Math.sin(1.5 * ph) * Math.exp(-t * decay * 1.8)
      + 0.4 * Math.sin(2 * ph) * Math.exp(-t * decay * 2.2) + 0.18 * Math.sin(3 * ph) * Math.exp(-t * decay * 3);
    lp += ((rnd() * 2 - 1) - lp) * 0.06;
    return Math.min(1, t / 0.004) * (body + lp * Math.exp(-t * 110) * 0.9) * amp;
  });
}
function bloop(at: number, f0: number, amp: number, pan: number) {
  let ph = 0;
  addWrapped(out, at, 0.7, pan, (t) => {
    const f = f0 * (1.35 - 0.35 * (1 - Math.exp(-t * 6)));       // a soft downward glide (the cap rolling over)
    ph += (2 * Math.PI * f) / SR;
    return (Math.sin(ph) + 0.3 * Math.sin(2 * ph)) * Math.exp(-t * 5) * Math.min(1, t / 0.02) * amp;
  });
}
function sub(at: number, f: number, amp: number, len: number) {
  addWrapped(out, at, len, 0.5, (t) => Math.sin(2 * Math.PI * f * t) * Math.min(1, t / 0.4) * Math.exp(-t * 1.2) * amp);
}

const shots = [...E.shots].sort((a, b) => a.t - b.t);
const lastT = shots[shots.length - 1].t;
let last = -9;
shots.forEach((s, i) => {
  const at = Math.max(0.02, s.t + 0.04);               // the pre-roll hook shot sounds on frame 0
  if (at >= DUR - 0.3) return;
  const pan = 0.5 + 0.35 * s.x;
  const big = Math.min(1, s.r / 0.14);
  if (i === shots.length - 1 && s.t === lastT && s.r < 0.06) {   // the last small drop: one gentle note into the calm
    thock(at, 196, 0.22, pan, 6, 2.0); bloop(at + 0.5, 330, 0.06, pan); return;
  }
  if (at - last < 0.3) { bloop(at + 0.4, 240 + 60 * rnd(), 0.05, pan); return; }  // close shots: just a bloop, no clatter
  last = at;
  thock(at, 175 - 65 * big + 8 * rnd(), 0.32 + 0.14 * big, pan);
  bloop(at + 0.45 + 0.15 * rnd(), 210 + 70 * rnd() - 50 * big, 0.07, pan);
  if (s.r >= 0.13) sub(at, 55, 0.18, 2.6);               // the giant blast: a soft swell underneath
});
reverb(out, { room: 0.82, damp: 0.55, wet: 0.3, preDelayMs: 20, loop: false });
const f0 = Math.round((DUR - 1.6) * SR), f1 = Math.round((DUR - 0.1) * SR);
for (let i = f0; i < out[0].length; i++) { const g = i >= f1 ? 0 : (1 - (i - f0) / (f1 - f0)) ** 1.5; out[0][i] *= g; out[1][i] *= g; }
writeWav(outPath, out, 1.0);
console.log(`wrote ${outPath}`);
