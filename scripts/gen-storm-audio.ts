// SFX for 0023 v2 "This liquid became a storm" - creamy, muted, heavy. Every sound has a visible cause
// (src/scenes/ferroMusic/storm.ts):
//  hook: the spike wall rushing at the lens (a deep rising rush + a heavy thock as it crests) | rewind: a reversed swell
//  bass hit: a deep boom + a ring of soft thocks as the spikes burst | fronts: a rolling wave of thocks sweeping across
//  vortex: a low rotating hum that rises with the spin | tornado: a deep swelling drone | collapse: the heaviest thock,
//  a wide splash and a cascade of droplet thocks as they land | aftershocks: two softer thocks | then silence
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { landings, STORM } from "../src/scenes/ferroMusic/storm";
import { addWrapped, reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";

export function generateStormAudio(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "storm-sfx");
  const att = (t: number, a: number) => Math.min(1, t / a);
  const thock = (at: number, f: number, amp: number, pan = 0.5, decay = 30, len = 0.4, puff = 0.5) => {
    if (at < 0 || at > STORM.duration) return;
    let lp = 0;
    addWrapped(out, at, len, pan, (t) => {
      const body = Math.sin(2 * Math.PI * f * t * (1 - 0.5 * t)) * Math.exp(-t * decay) + 0.25 * Math.sin(2 * Math.PI * f * 1.5 * t) * Math.exp(-t * decay * 1.8);
      lp += ((r() * 2 - 1) - lp) * 0.06;
      return att(t, 0.004) * (body + lp * Math.exp(-t * 120) * puff) * amp;
    });
  };
  const boom = (at: number, amp: number, len = 1.6) => addWrapped(out, at, len, 0.5, (t) =>
    (Math.sin(2 * Math.PI * 44 * (1 - 0.25 * Math.min(1, t / 0.6)) * t) + 0.35 * Math.sin(2 * Math.PI * 88 * t) * Math.exp(-t * 6)) * Math.exp(-t * 2.4) * att(t, 0.005) * amp);
  const rush = (from: number, to: number, amp: number, rising = true) => {
    let a = 0, b = 0;
    const len = to - from;
    addWrapped(out, from, len + 0.15, 0.5, (t) => {
      const k = Math.min(1, t / len);
      const cut = rising ? 0.01 + 0.08 * k * k : 0.09 - 0.07 * k;
      a += ((r() * 2 - 1) - a) * cut;
      b += (a - b) * cut;
      const env = t < len ? (rising ? k ** 1.8 : 1 - k) : Math.exp(-(t - len) * 25);
      return b * env * amp + Math.sin(2 * Math.PI * (50 + (rising ? 40 * k : 40 * (1 - k))) * t) * env * amp * 0.35;
    });
  };
  const sweep = (t0: number, dur: number, n: number, amp: number, l2r: boolean) => {
    for (let i = 0; i < n; i++) { const x = i / n; thock(t0 + dur * x, 150 + 70 * r(), amp * (0.6 + 0.4 * r()), l2r ? 0.1 + 0.8 * x : 0.9 - 0.8 * x, 28, 0.35, 0.4); }
  };

  // hook: the wall rushes in, crests on the lens; the rewind sucks it back
  rush(0, 0.5, 0.16, true);
  thock(0.5, 62, 0.36, 0.5, 7, 1.0, 0.9);
  boom(0.5, 0.3);
  rush(0.7, 1.6, 0.1, false);
  // the bass hit: the ring of spikes bursts out
  boom(2.2, 0.36);
  for (let i = 0; i < 12; i++) thock(2.22 + 0.04 * i, 190 + 60 * r(), 0.07, 0.15 + 0.7 * (i / 11), 30, 0.3);
  // the fronts rip across
  sweep(3.6, 1.6, 18, 0.09, true);
  boom(3.6, 0.2, 1.0);
  sweep(5.2, 1.6, 18, 0.09, false);
  boom(5.2, 0.2, 1.0);
  // vortex: a rotating low hum that speeds up
  addWrapped(out, 7.0, 7.1, 0.5, (t) => {
    const s = t + 7.0;
    const spin = 1.2 * (s - 7) + 0.42 * (s - 7) ** 2;
    const env = Math.min(1, t / 1.5) * (1 - Math.min(1, Math.max(0, (t - 6.8) / 0.3)));
    return (Math.sin(2 * Math.PI * 55 * t + 2 * Math.sin(spin)) + 0.3 * Math.sin(2 * Math.PI * 110 * t)) * (0.6 + 0.4 * Math.sin(spin * 3)) * env * 0.05;
  });
  // tornado: a deep swell rising into the collapse
  rush(11.0, 14.0, 0.12, true);
  // collapse: the heaviest thock, a wide splash, droplets landing
  thock(STORM.collapse, 52, 0.4, 0.5, 5, 1.4, 0.9);
  boom(STORM.collapse, 0.38, 2.0);
  let lp = 0;
  addWrapped(out, STORM.collapse, 0.9, 0.5, (t) => { lp += ((r() * 2 - 1) - lp) * 0.08; return lp * Math.exp(-t * 4.5) * att(t, 0.004) * 0.1; });
  for (const l of landings()) thock(l.t, 300 + 150 * r(), 0.04 + 6 * l.r, 0.5 + Math.max(-0.4, Math.min(0.4, l.x * 6)), 40, 0.2, 0.4);
  thock(STORM.collapse + 0.6, 70, 0.18, 0.5, 9, 0.8, 0.6);
  thock(STORM.collapse + 1.4, 80, 0.1, 0.5, 10, 0.7, 0.5);

  reverb(out, { room: 0.6, damp: 0.6, wet: 0.16, preDelayMs: 12, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (storm sfx)`);
  return rel;
}
