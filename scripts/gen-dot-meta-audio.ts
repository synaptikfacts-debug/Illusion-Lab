// 0030 "Dot Metamorphosis" v2 - sound from the simulation's own events (scripts/blender/dot_meta.py -> events.json).
// Two files (CLAUDE.md "two videos per reel"):
//  <out>-sfx.wav    sounds only (TikTok / Instagram / Facebook / X): creamy muted thocks (the 0011 recipe: low sine with a
//                   slight pitch drop + a felted low-passed puff) and soft, low-passed glass taps - every sound has a
//                   visible cause: the dark-glass sphere's approach and impact, every bead it knocks away, the beads
//                   coming home, a bloom for every new shape, three thocks as the three spheres form, the grains landing
//                   in the hourglass, the dust scattering; silence after the ending.
//  <out>-music.wav  the YouTube score: calm felt piano (Salamander, CC BY 3.0 - credit in the caption), VSCO-2 strings,
//                   harp, pizzicato and a little glockenspiel (CC0), E major, written to the story beats and resolving
//                   on the last chord while the body turns to dust.
// Usage: npx tsx scripts/gen-dot-meta-audio.ts <eventsDir> <seconds> <outPrefix>
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { addWrapped, Biquad, reverb, SR, stereo, writeWav, type Stereo } from "./lib/dsp";
import { orch, piano, play } from "./lib/sampler";

const [dir, secArg, outPrefix] = process.argv.slice(2);
const DUR = Number(secArg);
interface Ev { impact: number; ret0: number; land: number; hits: [number, number][]; bursts: { t: number; s: number }[];
  shapes: number[]; wave: [number, number]; split: number; grains: number[]; dust: number }
const E = JSON.parse(readFileSync(join(dir, "events.json"), "utf8")) as Ev;
let seed = 30;
const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 2 ** 32);

// ---------------------------------------------------------------- SFX
const sfx = stereo(DUR);
function tap(out: Stereo, at: number, f: number, amp: number, pan: number, decay = 18) {
  let ph = 0; const lp = new Biquad().set("lp", 1600, 0.6);
  addWrapped(out, at, 0.5, pan, (t) => { ph += 2 * Math.PI * f * (1 - 0.15 * t) / SR; return lp.run(Math.sin(ph)) * Math.exp(-t * decay) * Math.min(1, t / 0.004) * amp; });
}
function thock(out: Stereo, at: number, f: number, amp: number, len = 1.0, decay = 11, pan = 0.5) {
  // the 0011 Singing Pins thock: a sine body with a slight pitch drop + a soft fifth above + a felted, low-passed puff;
  // pitched 110-200 Hz so it is heard on a phone speaker (a quiet sub layer is added separately where it helps)
  let lp = 0;
  addWrapped(out, at, len, pan, (t) => {
    const ph = 2 * Math.PI * f * t * (1 - 0.3 * t);
    const body = Math.sin(ph) * Math.exp(-t * decay) + 0.25 * Math.sin(1.5 * ph) * Math.exp(-t * decay * 1.8)
      + 0.4 * Math.sin(2 * ph) * Math.exp(-t * decay * 2.2) + 0.18 * Math.sin(3 * ph) * Math.exp(-t * decay * 3);  // warm upper partials: audible on a phone
    lp += ((rnd() * 2 - 1) - lp) * 0.06;
    return Math.min(1, t / 0.004) * (body + lp * Math.exp(-t * 110) * 0.9) * amp;
  });
}
function sub(out: Stereo, at: number, f: number, amp: number, len = 1.6, decay = 4) {
  addWrapped(out, at, len, 0.5, (t) => Math.min(1, t / 0.008) * Math.sin(2 * Math.PI * f * t * (1 - 0.2 * t)) * Math.exp(-t * decay) * amp);
}
function swell(out: Stereo, t0: number, t1: number, freqs: number[], peak: number, rise: number, tail = 0.15) {
  freqs.forEach((f0, k) => {
    let ph = 0;
    addWrapped(out, t0, t1 - t0 + tail + 0.05, 0.5, (t) => {
      const u = Math.min(1, t / (t1 - t0)); ph += 2 * Math.PI * f0 * (1 + rise * u * u) / SR;
      return Math.sin(ph) * u * u * (t > t1 - t0 ? Math.max(0, 1 - (t - (t1 - t0)) / tail) : 1) * peak / (k + 1);
    });
  });
}

// the opening: approach -> impact -> knocked beads -> the beads come home
swell(sfx, 0, E.impact, [147, 220], 0.04, 0.4);
thock(sfx, E.impact, 98, 0.55, 1.8, 6); thock(sfx, E.impact + 0.004, 196, 0.18, 0.8, 12); sub(sfx, E.impact, 49, 0.3, 2.2, 3.2);
for (let i = 0; i < 6; i++) tap(sfx, E.impact + 0.01 * i, 1300 + 500 * rnd(), 0.07, 0.3 + 0.4 * rnd(), 9);
for (const [t, n] of E.hits) {
  const k = Math.min(4, Math.ceil(n / 25));
  for (let i = 0; i < k; i++) tap(sfx, t + 0.05 * rnd(), 450 + 450 * rnd(), 0.06, 0.15 + 0.7 * rnd(), 10);
}
swell(sfx, E.ret0, E.land, [330, 495, 660], 0.045, 0.5);
for (let i = 0; i < 50; i++) tap(sfx, E.land - 0.6 + 0.6 * Math.sqrt(rnd()), 900 + 800 * rnd(), 0.028, 0.2 + 0.6 * rnd());
thock(sfx, E.land, 131, 0.4); sub(sfx, E.land, 65, 0.15);
// every new shape is a light wave crossing the body: a soft chime as the ring sets off, a shimmer of taps that rises in
// pitch as it travels (nodes re-forming behind it), and a thock when the new shape closes - a different pitch per shape
const SHAPE_HZ = [147, 131, 165, 123, 175, 110, 147];
const [WAVE, FLIP] = E.wave;
E.shapes.slice(1).forEach((ts, i) => {
  tap(sfx, ts, 990, 0.05, 0.5, 4);
  for (let k = 0; k < 34; k++) { const u = rnd(); tap(sfx, ts + 0.15 + WAVE * u, 700 + 900 * u + 200 * rnd(), 0.022, 0.2 + 0.6 * rnd(), 16); }
  thock(sfx, ts + WAVE + FLIP * 0.75, SHAPE_HZ[i % SHAPE_HZ.length], 0.4);
});
// the split: sparkles while the beads travel, one thock per sphere as it closes
for (let k = 0; k < 40; k++) tap(sfx, E.split + 0.2 + 1.5 * rnd(), 1500 + 1200 * rnd(), 0.016, 0.15 + 0.7 * rnd(), 22);
[0.0, 0.35, 0.7].forEach((d, i) => thock(sfx, E.split + 1.2 + d, [175, 147, 131][i], 0.34, 1.0, 11, [0.5, 0.25, 0.75][i]));
// the hourglass: every few grains landing on the pile = a soft low tap (sand patter, thinned so it never clatters)
E.grains.forEach((t, i) => { if (i % 5 === 0) tap(sfx, t, 420 + 300 * rnd(), 0.024, 0.4 + 0.2 * rnd(), 26); });
// the disc flattening and turning: a soft rising swell; the calm body: a warm settle thock
const discT = E.shapes[6], blobT = E.shapes[7];
swell(sfx, discT, discT + 1.8, [196, 294], 0.04, 0.25, 0.8);
thock(sfx, blobT + 1.7, 110, 0.38, 1.4, 8); sub(sfx, blobT + 1.7, 55, 0.15);
// a soft hum that breathes with the body, from the landing until the dust
addWrapped(sfx, E.land, E.dust + 2.5 - E.land, 0.5, (t) => {
  const fade = Math.min(1, t / 0.8) * Math.max(0, Math.min(1, (E.dust + 2.5 - E.land - t) / 2.0));
  return (Math.sin(2 * Math.PI * 82 * t) + 0.5 * Math.sin(2 * Math.PI * 164 * t) + 0.25 * Math.sin(2 * Math.PI * 246 * t)) * 0.016 * (1 + 0.3 * Math.sin(t * 2.2)) * fade;
});
// the ending: the dust scatters (falling soft taps), one last gentle note rings out, then silence
for (let k = 0; k < 70; k++) {
  const u = rnd();
  tap(sfx, E.dust + 0.3 + 2.6 * u, 1500 - 700 * u + 300 * rnd(), 0.022 * (1 - 0.7 * u), 0.2 + 0.7 * rnd(), 14);
}
tap(sfx, E.dust + 2.4, 660, 0.05, 0.5, 2.2);
reverb(sfx, { room: 0.85, damp: 0.5, wet: 0.34, preDelayMs: 22, loop: false });

// ---------------------------------------------------------------- SCORE (YouTube only)
const mus = stereo(DUR);
const hum = () => (rnd() - 0.5) * 0.014;
const P = (m: number, at: number, g: number, pan = 0.5, dur = 1.6, rel = 1.4, tone = 0.5) => play(mus, piano(m), at + hum(), g, pan, dur, rel, tone);
const S = (inst: string, m: number, at: number, g: number, dur: number, pan = 0.5, rel = 1.2) => play(mus, orch(inst, m), at, g, pan, dur, rel, 0.45);
// E major. chords as midi lists (low -> high)
const CH: Record<string, number[]> = {
  E: [40, 52, 56, 59, 63, 66], Cs: [37, 49, 56, 61, 64, 68], A: [33, 45, 52, 57, 61, 64], B: [35, 47, 54, 59, 63, 66],
  Gs: [32, 44, 51, 56, 59, 63], Fs: [30, 42, 49, 54, 57, 61], Bsus: [35, 47, 52, 59, 64, 66], Asus: [33, 45, 52, 57, 59, 64],
};
const broken = (name: string, at: number, g: number, step = 0.18) => CH[name].forEach((m, i) => P(m, at + i * step, g * (i ? 0.75 : 1), 0.3 + 0.08 * i, 2.4, 2.0));
// the stare, the impact (low E + B, a harp falling with the debris), a soft pad through the slow motion
P(76, 0.0, 0.16, 0.5, 0.9, 1.0, 0.4);
for (const m of [28, 40]) P(m, E.impact, 0.4, 0.45, 2.2, 1.8, 0.45);
[88, 83, 80, 76, 71, 68, 64, 59].forEach((m, i) => play(mus, orch("harp", m), E.impact + 0.05 + i * 0.07, 0.16, 0.3 + 0.06 * i, 1.4));
S("celli", 40, E.impact + 0.3, 0.09, E.land - E.impact, 0.45, 1.5);
S("violas", 59, E.impact + 0.6, 0.06, E.land - E.impact - 0.3, 0.6, 1.5);
// home: Emaj broken; then one chord per shape, a quiet melody note on top, strings underneath
broken("E", E.land, 0.2);
const prog = ["Cs", "A", "B", "Gs", "A", "Fs", "Bsus"];
const melody = [68, 69, 71, 75, 73, 69, 71];
E.shapes.slice(1).forEach((t, i) => {
  broken(prog[i], t + 0.55, 0.17, 0.2);
  P(melody[i] + 12, t + 1.4, 0.14, 0.62, 1.8, 2.0, 0.4);
  S("celli", CH[prog[i]][0] + 12, t + 0.4, 0.07, 3.0, 0.45, 1.6);
});
// split: a harp arpeggio up; hourglass: soft pizzicato with the falling grains; disc: a few glockenspiel stars
[64, 68, 71, 76, 80, 83, 88].forEach((m, i) => play(mus, orch("harp", m), E.split + 0.3 + i * 0.09, 0.14, 0.3 + 0.06 * i, 1.6));
const hg0 = E.grains[0] ?? E.shapes[5] + 0.8;
[64, 68, 71, 68, 64, 66, 71, 68].forEach((m, i) => play(mus, orch("celliPizz", m - 12), hg0 + i * 0.32, 0.12, 0.45, 0.6));
[88, 83, 85, 80].forEach((m, i) => play(mus, orch("glockenspiel", m), discT + 0.7 + i * 0.55, 0.05, 0.35 + 0.1 * i, 1.0));
// the ending: Asus -> Bsus -> E, the last chord lands as the dust starts and rings out to silence
broken("Asus", blobT + 0.5, 0.17, 0.22);
broken("Bsus", blobT + 1.9, 0.17, 0.22);
CH.E.forEach((m, i) => P(m, E.dust + 0.2 + i * 0.12, i ? 0.16 : 0.22, 0.3 + 0.08 * i, 3.2, 2.4, 0.4));
P(88, E.dust + 1.4, 0.1, 0.6, 2.0, 2.4, 0.35);
S("violins", 64, blobT + 0.4, 0.05, E.dust - blobT + 2.0, 0.55, 2.0);
S("celli", 40, E.dust + 0.2, 0.08, 2.4, 0.45, 2.0);
reverb(mus, { room: 0.88, damp: 0.45, wet: 0.36, preDelayMs: 26, loop: false });

// silence after the ending: both tracks fade to zero by the end of the picture fade
for (const out of [sfx, mus]) {
  const f0 = Math.round((DUR - 1.6) * SR), f1 = Math.round((DUR - 0.1) * SR);
  for (let i = f0; i < out[0].length; i++) { const g = i >= f1 ? 0 : (1 - (i - f0) / (f1 - f0)) ** 1.5; out[0][i] *= g; out[1][i] *= g; }
}
writeWav(`${outPrefix}-sfx.wav`, sfx, 1.0);
writeWav(`${outPrefix}-music.wav`, mus, 1.0);
console.log(`wrote ${outPrefix}-sfx.wav and ${outPrefix}-music.wav`);
