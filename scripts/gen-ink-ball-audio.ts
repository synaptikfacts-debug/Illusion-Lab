// 0028 v4 "glass ball hits an ink drop in milk" - the sound (owner, Nov 20: the thocks were "not pleasant - I want
// something nicer that suits a video like this"). Every sound still comes from an event in the simulation
// (events.json from scripts/milk_ink_v2.py, MI_OPEN=ball):
//   - the ball flying in: a soft airy whoosh that rises into the hit;
//   - the impact: a glass "ting" (real triangle + glockenspiel, VSCO-2 CC0), a deep underwater plunge and a rush of
//     bubbles;
//   - the little ink jets popping in the cloud: soft bubbles, tuned to a D major pentatonic so they sound like music;
//   - every story drop: water only (owner: "I hear bells - keep just the first 3 seconds' sounds") - a "plip" and a
//     softer "bloop"; big drops add the deep plunge, the climax a rush of bubbles; silence into the fade.
// Usage: npx tsx scripts/gen-ink-ball-audio.ts <eventsDir> <seconds> <out.wav>
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { addWrapped, Biquad, midiHz, reverb, SR, stereo, writeWav } from "./lib/dsp";
import { orch, play, unpitched } from "./lib/sampler";

interface Shot { t: number; x: number; r: number; spd: number }

const ARGS_FROM = 2;
const [dir, secArg, outPath] = process.argv.slice(ARGS_FROM);
const DUR = Number(secArg);
const E = JSON.parse(readFileSync(join(dir, "events.json"), "utf8")) as { shots: Shot[] };
const out = stereo(DUR);

const LCG_A = 1664525;
const LCG_C = 1013904223;
const UINT32 = 4294967296;
let seed = 2830;
const rnd = (): number => ((seed = (seed * LCG_A + LCG_C) >>> 0) / UINT32);

// D major pentatonic, D4..D6: always consonant, bright and calm
const OCTAVE = 12;
const D4 = 62;
const MAJ2 = 2;
const MAJ3 = 4;
const P5 = 7;
const MAJ6 = 9;
const PENTA = [0, MAJ2, MAJ3, P5, MAJ6];
const SCALE_OCTAVES = 2;
const SCALE = [...Array.from({ length: SCALE_OCTAVES }, (_, o) => PENTA.map((iv) => D4 + o * OCTAVE + iv)).flat(), D4 + SCALE_OCTAVES * OCTAVE];
const HARMONIC_2 = 2;
const TWO_PI = HARMONIC_2 * Math.PI;
const U_MAX = 0.999;
const MIN_AT = 0.02;
const CENTER = 0.5;
const PAN_SPREAD = 0.32;
const X_RANGE = 2.4;

// event kinds (classified from the simulation's event fields)
const IMPACT_R = 0.19;
const POP_R = 0.04;
const POP_SPD = 0.7;
const SAME = 1e-6;
const BIG_K = 1.5;
const CLIMAX_K = 1.9;

// the whoosh of the ball flying in
const WHOOSH_LEN = 0.42;
const WHOOSH_F0 = 380;
const WHOOSH_F1 = 2600;
const WHOOSH_Q = 1.1;
const WHOOSH_GAIN = 0.2;
const WHOOSH_SHAPE = 2.2;
const RETUNE_EVERY = 32;
const NOISE_SPAN = 2;

// the impact
const TING_GAIN = 0.55;
const GLOCK_HI = 91;
const GLOCK_HI2 = 98;
const GLOCK_GAIN = 0.32;
const GLOCK_GAIN2 = 0.14;
const PLUNGE_F0 = 330;
const PLUNGE_F1 = 105;
const PLUNGE_GLIDE = 7;
const PLUNGE_DECAY = 3.6;
const PLUNGE_LEN = 1.4;
const PLUNGE_GAIN = 0.5;
const PLUNGE_H2 = 0.35;
const RUSH_N = 16;
const RUSH_SPAN = 1.1;
const RUSH_F_LO = 420;
const RUSH_F_HI = 1500;
const RUSH_AMP = 0.11;

// one bubble / water-drop "plip": a sine whose pitch rises fast as the air pocket closes
const BUB_RISE = 0.7;
const BUB_RISE_T = 0.045;
const BUB_DECAY = 38;
const BUB_LEN = 0.35;
const BUB_ATTACK = 0.002;
const CLICK_LEN = 0.004;
const CLICK_GAIN = 0.25;

// drops
const PLIP_OCT = 1;
const PLIP_GAIN = 0.16;
const BLOOP_DELAY = 0.07;
const BLOOP_GAIN = 0.09;
const CLOSE_GAP = 0.25;
const CLOSE_DAMP = 0.55;
const BIG_BLOOP_GAIN = 0.24;
const CLIMAX_BUBBLES = 10;
const POP_GAIN = 0.075;
const POP_OCT = 1;
const LAST_LIFT = 1.2;
const LAST_PLUNGE_GAIN = 0.16;

const REV_ROOM = 0.86;
const REV_DAMP = 0.45;
const REV_WET = 0.32;
const REV_PRE_MS = 24;
const REVERB = { room: REV_ROOM, damp: REV_DAMP, wet: REV_WET, preDelayMs: REV_PRE_MS, loop: false };
const FADE_LEN = 1.6;
const FADE_GAP = 0.1;
const FADE_POW = 1.5;
const TAIL_GUARD = 0.3;

const panOf = (x: number): number => CENTER + PAN_SPREAD * (x / (X_RANGE / NOISE_SPAN));
const noteOf = (x: number, k: number): number => {
  const u = Math.min(U_MAX, Math.max(0, x / X_RANGE + CENTER));
  return SCALE[(Math.floor(u * SCALE.length) + k) % SCALE.length];
};

function bubble(at: number, f0: number, amp: number, pan: number, withClick = false): void {
  let ph = 0;
  addWrapped(out, at, BUB_LEN, pan, (t) => {
    const f = f0 * (1 + BUB_RISE * Math.min(1, t / BUB_RISE_T));
    ph += (TWO_PI * f) / SR;
    const click = withClick && t < CLICK_LEN ? (rnd() * NOISE_SPAN - 1) * CLICK_GAIN * (1 - t / CLICK_LEN) : 0;
    return (Math.sin(ph) * Math.exp(-t * BUB_DECAY) * Math.min(1, t / BUB_ATTACK) + click) * amp;
  });
}

function plunge(at: number, gain: number): void {
  let ph = 0;
  addWrapped(out, at, PLUNGE_LEN, CENTER, (t) => {
    const f = PLUNGE_F1 + (PLUNGE_F0 - PLUNGE_F1) * Math.exp(-t * PLUNGE_GLIDE);
    ph += (TWO_PI * f) / SR;
    return (Math.sin(ph) + PLUNGE_H2 * Math.sin(HARMONIC_2 * ph)) * Math.exp(-t * PLUNGE_DECAY) * Math.min(1, t / BUB_ATTACK * BUB_RISE) * gain;
  });
}

function whoosh(end: number): void {
  const bp = new Biquad();
  const start = Math.max(0, end - WHOOSH_LEN);
  const len = end - start;
  addWrapped(out, start, len, CENTER - PAN_SPREAD / NOISE_SPAN, (t, i) => {
    const x = t / len;
    if (i % RETUNE_EVERY === 0) bp.set("bp", WHOOSH_F0 + (WHOOSH_F1 - WHOOSH_F0) * x * x, WHOOSH_Q);
    return bp.run(rnd() * NOISE_SPAN - 1) * Math.pow(x, WHOOSH_SHAPE) * WHOOSH_GAIN;
  });
}

function impact(at: number): void {
  play(out, unpitched("triangle", 0), at, TING_GAIN, CENTER);
  play(out, orch("glockenspiel", GLOCK_HI), at, GLOCK_GAIN, CENTER);
  play(out, orch("glockenspiel", GLOCK_HI2), at + BUB_RISE_T, GLOCK_GAIN2, CENTER);
  plunge(at, PLUNGE_GAIN);
  Array.from({ length: RUSH_N }, (_, j) => j).forEach(() => {
    bubble(at + rnd() * RUSH_SPAN, RUSH_F_LO + (RUSH_F_HI - RUSH_F_LO) * rnd(), RUSH_AMP * (CENTER + rnd()), CENTER + (rnd() - CENTER) * PAN_SPREAD * NOISE_SPAN);
  });
}

const shots = [...E.shots].sort((a, b) => a.t - b.t);
const drops = shots.filter((s) => s.r < IMPACT_R && !(Math.abs(s.r - POP_R) < SAME && Math.abs(s.spd - POP_SPD) < SAME));
const lastDrop = drops[drops.length - 1];
let lastAt = -9;
let popK = 0;
let dropK = 0;

shots.forEach((s) => {
  const at = Math.max(MIN_AT, s.t);
  if (at >= DUR - TAIL_GUARD) return;
  const pan = panOf(s.x);
  if (s.r >= IMPACT_R) { whoosh(at); impact(at); return; }
  if (Math.abs(s.r - POP_R) < SAME && Math.abs(s.spd - POP_SPD) < SAME) {          // a little ink jet: a soft bubble
    popK += 1;
    bubble(at, midiHz(noteOf(s.x, popK) + POP_OCT * OCTAVE), POP_GAIN, pan);
    return;
  }
  // owner, Nov 20: "I hear some bells - keep just the sounds of the first 3 seconds": every story drop is water only -
  // a "plip" as it enters, a softer "bloop" a moment later as its air pocket closes; big drops add the deep plunge,
  // the climax a rush of bubbles. No harp, no glockenspiel.
  dropK += 1;
  const note = noteOf(s.x, dropK);
  const damp = at - lastAt < CLOSE_GAP ? CLOSE_DAMP : 1;
  lastAt = at;
  const k = s.spd;
  const isLast = s === lastDrop;
  bubble(at, midiHz(note + PLIP_OCT * OCTAVE), PLIP_GAIN * damp * (isLast ? LAST_LIFT : 1), pan, true);
  bubble(at + BLOOP_DELAY, midiHz(note - OCTAVE), BLOOP_GAIN * damp, pan);
  if (k >= BIG_K || isLast) plunge(at, isLast ? LAST_PLUNGE_GAIN : BIG_BLOOP_GAIN);
  if (k >= CLIMAX_K) {
    Array.from({ length: CLIMAX_BUBBLES }, (_, j) => j).forEach(() => {
      bubble(at + rnd() * RUSH_SPAN, RUSH_F_LO + (RUSH_F_HI - RUSH_F_LO) * rnd(), RUSH_AMP * (CENTER + rnd()), CENTER + (rnd() - CENTER) * PAN_SPREAD * NOISE_SPAN);
    });
  }
});

reverb(out, REVERB);
const f0 = Math.round((DUR - FADE_LEN) * SR), f1 = Math.round((DUR - FADE_GAP) * SR);
out[0].forEach((_, i) => {
  if (i < f0) return;
  const g = i >= f1 ? 0 : (1 - (i - f0) / (f1 - f0)) ** FADE_POW;
  out[0][i] *= g; out[1][i] *= g;
});
writeWav(outPath, out, 1.0);
console.log(`wrote ${outPath} (${drops.length} drops, ${popK} bubbles)`);
