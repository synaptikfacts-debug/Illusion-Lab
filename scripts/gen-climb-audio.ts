// SFX for 0022 "This liquid climbs on its own" - creamy, muted THOCKS tied to what the liquid visibly does (the same
// beat map as scripts/blender/ferro_climb.py: real = story + 2.0 after the cold open + rewind):
//  open = the halo flares its spikes (deep thock + a felted puff) | rewind = a soft swoosh falling in pitch |
//  wake = little thocks as spikes rise across the pool | climb = a thock each time the front grips a new turn of the
//  spiral, soft ticks in between | slip = a muffled slide + a catch thock | bloom = a swell into the halo opening |
//  drain = falling thocks as it lets go turn by turn | settle = one last drip, then silence into the fade.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import TL from "../src/scenes/climb/timeline.json";
import { addWrapped, reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";

const sm = (a: number, b: number, x: number) => {
  const k = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return k * k * (3 - 2 * k);
};

/** real time at which the climbing front reaches fraction f of the spiral (inverts the smoothstep in the scene) */
function climbTime(f: number): number {
  let lo = 1.5;
  let hi = 10.5;
  for (let i = 0; i < 40; i++) {
    const m = (lo + hi) / 2;
    if (sm(1.5, 10.5, m) < f) lo = m;
    else hi = m;
  }
  return (lo + hi) / 2 + 2.0;
}

export function generateClimbAudio(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "climb-thocks-v1");
  const thock = (at: number, f: number, amp: number, pan = 0.5, decay = 30, len = 0.35, puffAmt = 0.5) => {
    if (at < 0 || at > TL.duration) return;
    let lp = 0;
    addWrapped(out, at, len, pan, (t) => {
      const body = Math.sin(2 * Math.PI * f * t * (1 - 0.5 * t)) * Math.exp(-t * decay)
        + 0.22 * Math.sin(2 * Math.PI * f * 1.5 * t) * Math.exp(-t * decay * 1.8);
      lp += ((r() * 2 - 1) - lp) * 0.05;
      return Math.min(1, t / 0.005) * (body + lp * Math.exp(-t * 140) * puffAmt) * amp;
    });
  };
  const swell = (a: number, b: number, amp: number, f0: number, f1: number, down = false) => {
    let lp = 0;
    addWrapped(out, a, b - a, 0.5, (t) => {
      const x = t / (b - a);
      const e = down ? (1 - x) ** 1.5 * Math.min(1, t / 0.05) : x ** 2;
      lp += ((r() * 2 - 1) - lp) * (down ? 0.06 - 0.045 * x : 0.012 + 0.03 * x);
      return lp * e * amp + Math.sin(2 * Math.PI * (f0 + (f1 - f0) * x) * t) * e * amp * 0.25;
    });
  };
  // cold open: the halo flares
  thock(0.04, 52, 0.42, 0.5, 5, 1.3, 1.0);
  thock(0.05, 104, 0.15, 0.5, 12, 0.7, 0.3);
  for (let i = 0; i < 10; i++) thock(0.06 + i * 0.045, 190 + 90 * r(), 0.045, 0.2 + 0.6 * r(), 40);
  // the rewind: a soft swoosh falling in pitch
  swell(TL.rewind[0], TL.rewind[1], 0.14, 220, 60, true);
  // the pool wakes: spikes rising across it
  for (let i = 0; i < 9; i++) thock(TL.wake[0] + 0.1 + i * 0.15 + r() * 0.05, 210 + 120 * r(), 0.03 + 0.02 * (i / 9), 0.25 + 0.5 * r(), 44, 0.25, 0.35);
  // the climb: a thock on every new turn, soft ticks at each third of a turn, climbing in pitch
  const steps = Math.floor(TL.turns * 3);
  for (let k = 1; k <= steps; k++) {
    const t = climbTime(k / (TL.turns * 3));
    const turn = k % 3 === 0;
    const up = k / steps;
    thock(t, turn ? 96 + 30 * up : 170 + 80 * up, turn ? 0.13 : 0.045, 0.35 + 0.3 * r(), turn ? 18 : 38, turn ? 0.7 : 0.3, 0.55);
  }
  // the slip and the catch
  swell(TL.slip[0], TL.slip[0] + 0.5, 0.09, 140, 80, true);
  thock(TL.slip[1], 84, 0.15, 0.5, 14, 0.8, 0.6);
  // the halo blooms
  swell(TL.bloom[0] - 0.6, TL.bloom[1], 0.12, 60, 120);
  thock(TL.bloom[1], 70, 0.2, 0.5, 9, 1.1, 0.8);
  for (let i = 0; i < 6; i++) thock(TL.bloom[1] + 0.25 + i * 0.12, 260 - 15 * i, 0.03, 0.2 + 0.12 * i, 40);
  // the drain: it lets go turn by turn, falling
  for (let i = 0; i < 5; i++) thock(TL.drain[0] + 0.3 + i * 0.62, 140 - 14 * i, 0.08 - 0.01 * i, 0.4 + 0.05 * i, 20, 0.6, 0.5);
  // one last drip as the pool goes smooth, then silence
  thock(TL.settle + 0.2, 180, 0.05, 0.55, 26, 0.6, 0.3);
  reverb(out, { room: 0.7, damp: 0.6, wet: 0.2, preDelayMs: 14, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (the climb: grips, slip, bloom, drain)`);
  return rel;
}
