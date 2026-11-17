// 0026 "This motherboard builds itself" - SFX from the same events as the picture (events.json from
// scripts/blender/mobo_anim.py). Creamy and muted, every sound has a visible cause:
//   chip: a low hot hum while it falls onto the glowing pads, a deep thock + felted puff when it seats
//   tiny parts: soft low "tk" ticks as they snap in (thinned to a readable zipper), chokes: heavy felted thuds,
//   silver caps: a rounder tock, ICs: a light tock; POWER: a warm rising swell + soft electric swishes on the pulses;
//   climax: two swells with a thock; the last pulse into the chip: a final soft thock, then silence and the fade.
// Usage: npx tsx scripts/gen-mobo-audio.ts <eventsDir> <out.wav>
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { addWrapped, Biquad, reverb, stereo, writeWav } from "./lib/dsp";

const [dir, outPath] = process.argv.slice(2);
const DUR = 21;
const E = JSON.parse(readFileSync(join(dir, "events.json"), "utf8")) as {
  drops: { t: number; kind: string; x: number; y: number }[];
  signals: { t: number; kind: string; inward: boolean; len: number; x: number }[];
  seat: number; power: number;
};
const out = stereo(DUR);
let seed = 0x0b0a26;
const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 2 ** 32);
const pan = (x: number) => Math.max(0.15, Math.min(0.85, 0.5 + x * 0.05));
const SPEED = 2.6;

function thock(at: number, f: number, amp: number, p = 0.5, decay = 18, len = 0.6, puff = 0.5) {
  if (at < 0 || at > DUR) return;
  let lp = 0;
  addWrapped(out, at, len, p, (t) => {
    const body = Math.sin(2 * Math.PI * f * t * (1 - 0.4 * t)) * Math.exp(-t * decay) + 0.2 * Math.sin(2 * Math.PI * f * 1.5 * t) * Math.exp(-t * decay * 1.8);
    lp += (rnd() * 2 - 1 - lp) * 0.05;
    return Math.min(1, t / 0.004) * (body + lp * Math.exp(-t * 90) * puff) * amp;
  });
}
function swish(t0: number, t1: number, amp: number, p: number) {
  const bp = new Biquad();
  const len = t1 - t0;
  if (len <= 0) return;
  addWrapped(out, Math.max(0, t0), len + 0.05, p, (t) => {
    const u = Math.min(1, t / len);
    return bp.set("bp", 500 + 2400 * u * u, 3.5).run(rnd() * 2 - 1) * u ** 1.5 * Math.min(1, (len + 0.05 - t) / 0.05) * amp;
  });
}
function swell(at: number, len: number, f: number, amp: number) {
  addWrapped(out, at, len, 0.5, (t) => {
    const e = Math.sin(Math.PI * Math.min(1, t / len)) ** 2;
    return (Math.sin(2 * Math.PI * f * t) + 0.5 * Math.sin(2 * Math.PI * f * 1.5 * t) + 0.3 * Math.sin(2 * Math.PI * f * 2 * t + 1)) * e * amp;
  });
}

// chip: hot hum while falling, the seat
addWrapped(out, 0, E.seat + 0.05, 0.5, (t) => (Math.sin(2 * Math.PI * 70 * t) + 0.4 * Math.sin(2 * Math.PI * 140 * t)) * 0.06 * Math.min(1, t / 0.04) * (t < E.seat ? 1 : Math.max(0, 1 - (t - E.seat) / 0.05)));
thock(E.seat, 48, 1.0, 0.5, 8, 1.6, 0.8);
// the parts as they land
let lastTick = -1;
for (const d of [...E.drops].sort((a, b) => a.t - b.t)) {
  if (d.kind === "smd") {
    if (d.t - lastTick < 0.035) continue;                  // thin the zipper so each tick still reads
    lastTick = d.t;
    thock(d.t, 380 + 120 * rnd(), 0.05, pan(d.x), 60, 0.12, 0.3);
  } else if (d.kind === "choke") thock(d.t, 46 + 6 * rnd(), 0.6, pan(d.x), 11, 0.9, 0.6);
  else if (d.kind === "cap") thock(d.t, 105 + 15 * rnd(), 0.3, pan(d.x), 16, 0.6, 0.35);
  else if (d.kind === "ic") thock(d.t, 160 + 30 * rnd(), 0.16, pan(d.x), 24, 0.4, 0.3);
  else if (d.kind === "slot") thock(d.t, 70, 0.3, pan(d.x), 12, 0.8, 0.4);
}
// power on
swell(E.power - 0.2, 2.4, 82, 0.06);
thock(E.power, 58, 0.55, 0.5, 10, 1.0, 0.5);
const sig = E.signals;
const groups = new Map<string, typeof sig>();
for (const s of sig) groups.set(s.kind, [...(groups.get(s.kind) ?? []), s]);
for (const [kind, g] of groups) {
  const t = Math.min(...g.map((s) => s.t));
  if (kind.startsWith("wave")) { thock(t, 92 + 4 * Number(kind.slice(4)), 0.28, pan(g[0].x), 18, 0.5, 0.3); swish(t - 0.5, t, 0.04, pan(g[0].x)); }
  if (kind.startsWith("reply")) swish(t, t + 0.4, 0.035, pan(g[0].x));
  if (kind === "climax0" || kind === "climax1") { swell(t - 0.3, 1.6, 98, 0.07); thock(t, 54, 0.6, 0.5, 9, 1.2, 0.5); }
}
for (let i = 0; i < 6; i++) swish(E.power + i * 0.06, E.power + 0.5 + i * 0.06, 0.03, 0.2 + 0.12 * i);
const last = sig.find((s) => s.kind === "last");
if (last) { swish(last.t - Math.min(last.len, 3) / SPEED, last.t, 0.12, 0.5); thock(last.t, 60, 0.5, 0.5, 9, 1.4, 0.5); }

reverb(out, { room: 0.62, damp: 0.55, wet: 0.17, preDelayMs: 12, loop: false });
const f0 = Math.round(19.3 * 48000), f1 = Math.round(20.95 * 48000);
for (let k = f0; k < out[0].length; k++) { const g = k >= f1 ? 0 : (1 - (k - f0) / (f1 - f0)) ** 1.5; out[0][k] *= g; out[1][k] *= g; }
writeWav(outPath, out, 1.0);
console.log(`wrote ${outPath}`);
