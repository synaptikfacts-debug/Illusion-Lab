// 0026 "This chip is waking up" - SFX from the same events as the picture (out/<dir>/events.json, written by
// scripts/blender/chip_anim.py). Creamy, muted: a low thock with a felted puff when a wave of pulses lands in the chip,
// a soft electric swish riding each racing pulse (filtered noise, no clicks), muted rising blips as the buses boot, a
// warm low swell as the far board answers. Usage: npx tsx scripts/gen-chip-audio.ts <eventsDir> <seconds> <out.wav>
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { addWrapped, Biquad, reverb, SR, stereo, writeWav } from "./lib/dsp";

const [dir, secArg, outPath] = process.argv.slice(2);
const DUR = Number(secArg);
const EV: { t: number; kind: string; inward: boolean; len: number; x: number; y: number }[] = JSON.parse(readFileSync(join(dir, "events.json"), "utf8"));
const out = stereo(DUR);
let seed = 0x5eed26;
const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 2 ** 32);
const pan = (x: number) => Math.max(0.15, Math.min(0.85, 0.5 + x * 0.06));
const SPEED = 2.6;

const thock = (at: number, f: number, amp: number, p = 0.5, decay = 18, len = 0.6, puff = 0.5) => {
  if (at < 0 || at > DUR) return;
  let lp = 0;
  addWrapped(out, at, len, p, (t) => {
    const body = Math.sin(2 * Math.PI * f * t * (1 - 0.4 * t)) * Math.exp(-t * decay) + 0.2 * Math.sin(2 * Math.PI * f * 1.5 * t) * Math.exp(-t * decay * 1.8);
    lp += (rnd() * 2 - 1 - lp) * 0.05;
    return Math.min(1, t / 0.004) * (body + lp * Math.exp(-t * 90) * puff) * amp;
  });
};
// a soft electric swish: band-passed noise whose centre rises as the pulse approaches, ends as it lands
const swish = (t0: number, t1: number, amp: number, p: number) => {
  const bp = new Biquad();
  const len = t1 - t0;
  if (len <= 0) return;
  addWrapped(out, Math.max(0, t0), len + 0.05, p, (t) => {
    const u = Math.min(1, t / len);
    return bp.set("bp", 500 + 2600 * u * u, 3.5).run(rnd() * 2 - 1) * u ** 1.5 * Math.min(1, (len + 0.05 - t) / 0.05) * amp;
  });
};
const blip = (at: number, f: number, amp: number, p: number) =>
  addWrapped(out, at, 0.12, p, (t) => Math.sin(2 * Math.PI * f * t) * Math.exp(-t * 38) * Math.min(1, t / 0.003) * amp);
const swell = (at: number, len: number, f: number, amp: number) =>
  addWrapped(out, at, len, 0.5, (t) => {
    const e = Math.sin(Math.PI * Math.min(1, t / len)) ** 2;
    return (Math.sin(2 * Math.PI * f * t) + 0.5 * Math.sin(2 * Math.PI * f * 1.5 * t) + 0.3 * Math.sin(2 * Math.PI * f * 2 * t + 1)) * e * amp;
  });

// v3 hook: a low hot hum while the chip hovers over the glowing pads, a big thock as it seats, the burst swishes out
const seat = EV.find((e) => e.kind === "seat")?.t ?? 0.45;
addWrapped(out, 0, seat + 0.05, 0.5, (t) => (Math.sin(2 * Math.PI * 70 * t) + 0.4 * Math.sin(2 * Math.PI * 140 * t)) * 0.05 * Math.min(1, t / 0.05) * (t < seat ? 1 : Math.max(0, 1 - (t - seat) / 0.05)));
thock(seat, 50, 1.0, 0.5, 8, 1.6, 0.8);
const burst = EV.filter((e) => e.kind === "burst").sort((a, b) => a.t - b.t);
burst.forEach((e, i) => { if (i % 4 === 0) swish(e.t, e.t + 0.45, 0.06, pan(e.x)); });
const ring = EV.filter((e) => e.kind === "ring").sort((a, b) => a.t - b.t);
ring.forEach((e, i) => { if (i % 6 === 0) blip(e.t, 300 + 420 * (i / ring.length), 0.05, pan(e.x)); });
swell(1.0, 2.6, 92, 0.05);
// the chip answers each wave out of the other side: a lighter, higher thock
const replies = new Map<string, typeof EV>();
for (const e of EV.filter((e) => e.kind.startsWith("reply"))) replies.set(e.kind, [...(replies.get(e.kind) ?? []), e]);
[...replies.values()].forEach((w, i) => { const t = Math.min(...w.map((e) => e.t)); thock(t, 96 + 6 * i, 0.3, pan(w[0].x), 20, 0.5, 0.3); });
// waves: one thock per wave (pitch climbs), panned to the side it came from
const waves = new Map<string, typeof EV>();
for (const e of EV.filter((e) => e.kind.startsWith("wave"))) waves.set(e.kind, [...(waves.get(e.kind) ?? []), e]);
[...waves.values()].forEach((w, i) => {
  const t = w.reduce((a, e) => a + e.t, 0) / w.length;
  const x = w.reduce((a, e) => a + e.x, 0) / w.length;
  thock(t, 62 + 7 * i, 0.55, pan(x), 14, 0.8, 0.5);
  for (const e of w) swish(t - 0.6, e.t, 0.025, pan(e.x));
});
// boot: muted blips rising as bus after bus fires outward
const boot = EV.filter((e) => e.kind === "boot").sort((a, b) => a.t - b.t);
boot.forEach((e, i) => { if (i % 3 === 0) blip(e.t, 330 + 260 * (i / boot.length), 0.07, pan(e.x)); });
thock(3.2, 74, 0.5, 0.5, 12, 0.8, 0.4);
// the far board answers: a warm low swell
swell(4.0, 3.2, 98, 0.05);

reverb(out, { room: 0.6, damp: 0.55, wet: 0.18, preDelayMs: 12, loop: false });
writeWav(outPath, out, 1.0);
console.log(`wrote ${outPath}`);
