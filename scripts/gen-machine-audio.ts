// 0027 "This machine runs on liquid" - SFX from events.json (scripts/blender/liquid_machine.py), creamy and muted:
// hook: a wet rising swell, a deep thock as the column is pulled up; passes: a soft thock + short wet "shh" each (thinned
// when the hub is fast so every one still reads); ring: a low rotating whoosh that rises; stop: a felted clack; gather: a
// slow wet slide; lift: the last soft thock as the bulb relaxes; a quiet hum under it all, silence + fade at the end.
// Usage: npx tsx scripts/gen-machine-audio.ts <dir> <sec> <out.wav>
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { addWrapped, Biquad, reverb, SR, stereo, writeWav } from "./lib/dsp";

const [dir, secArg, outPath] = process.argv.slice(2);
const DUR = Number(secArg);
const E = JSON.parse(readFileSync(join(dir, "events.json"), "utf8")) as {
  events: { t: number; kind: string }[]; hook: number; ring?: number; stop?: number; gather?: number; lift?: number;
};
const out = stereo(DUR);
let seed = 0x27;
const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 2 ** 32);
function thock(at: number, f: number, amp: number, decay = 14, len = 0.8, puff = 0.5) {
  if (at < 0 || at > DUR) return;
  let lp = 0;
  addWrapped(out, at, len, 0.5, (t) => {
    const body = Math.sin(2 * Math.PI * f * t * (1 - 0.35 * t)) * Math.exp(-t * decay);
    lp += (rnd() * 2 - 1 - lp) * 0.05;
    return Math.min(1, t / 0.004) * (body + lp * Math.exp(-t * 70) * puff) * amp;
  });
}
function wet(at: number, len: number, amp: number, f0: number, f1: number) {
  const lp = new Biquad();
  addWrapped(out, at, len, 0.5, (t) => {
    const u = t / len;
    return lp.set("lp", f0 + (f1 - f0) * u, 0.9).run(rnd() * 2 - 1) * Math.sin(Math.PI * Math.min(1, u)) ** 2 * amp;
  });
}
wet(0, E.hook + 0.1, 0.12, 300, 1600);
thock(E.hook, 48, 1.0, 8, 1.6, 0.8);
wet(E.hook, 0.9, 0.18, 1400, 250);
const ringT = E.ring ?? 99, stopT = E.stop ?? (E as unknown as { settle?: number }).settle ?? 99;
const X0 = E as unknown as { crown?: number[] };
let last = -1;
for (const e of E.events) {
  if (e.t < E.hook + 0.15 || e.t > ringT + 0.4 || (X0.crown ?? []).some((c) => Math.abs(c - e.t) < 0.05)) continue;
  if (e.t - last < 0.16) continue;                 // fast hub: keep each thock readable
  last = e.t;
  const k = Math.min(1, e.t / ringT);
  thock(e.t, 66 + 22 * k + 6 * rnd(), 0.38, 16, 0.6, 0.4);
  wet(e.t - 0.05, 0.4, 0.07, 500, 1800);
}
if (E.ring !== undefined) {                          // the spinning ring: a rotating low whoosh, rising
  const bp = new Biquad();
  const len = stopT - ringT + 0.6;
  addWrapped(out, ringT, len, 0.5, (t) => {
    const u = Math.min(1, t / len);
    const env = Math.sin(Math.PI * Math.min(1, u * 1.05)) ** 1.5;
    return bp.set("bp", 260 + 520 * u + 120 * Math.sin(t * 14), 1.6).run(rnd() * 2 - 1) * env * 0.16;
  });
}
if (E.stop !== undefined) thock(E.stop, 82, 0.55, 20, 0.6, 0.6);
const X = E as unknown as { crown?: number[]; settle?: number };
for (const tc of X.crown ?? []) { thock(tc, 46, 0.85, 8, 1.6, 0.7); wet(tc - 0.3, 1.2, 0.16, 400, 1500); }
if (X.settle !== undefined) { thock(X.settle, 62, 0.45, 12, 0.9, 0.4); wet(X.settle, 1.0, 0.1, 1200, 300); }
if (E.gather !== undefined) wet(E.gather, 2.6, 0.14, 900, 220);
if (E.lift !== undefined) thock(E.lift + 0.9, 56, 0.55, 9, 1.4, 0.4);
addWrapped(out, 0, DUR, 0.5, (t) => {
  const f = 55 + 18 * Math.min(1, t / stopT);
  const g = t < stopT ? 1 : Math.max(0, 1 - (t - stopT) / 1.5);
  return (Math.sin(2 * Math.PI * f * t) + 0.3 * Math.sin(4 * Math.PI * f * t)) * 0.025 * Math.min(1, t / 0.3) * g;
});
reverb(out, { room: 0.6, damp: 0.5, wet: 0.2, preDelayMs: 14, loop: false });
const f0 = Math.round((DUR - 1.4) * SR), f1 = Math.round((DUR - 0.05) * SR);
for (let i = f0; i < out[0].length; i++) { const g = i >= f1 ? 0 : (1 - (i - f0) / (f1 - f0)) ** 1.5; out[0][i] *= g; out[1][i] *= g; }
writeWav(outPath, out, 1.0);
console.log(`wrote ${outPath}`);
