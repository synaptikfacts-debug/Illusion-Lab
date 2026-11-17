// SFX for 0024 "This core is unlocking" - creamy, muted, mechanical. Every sound has a visible cause
// (src/scenes/core/core.ts coreEvents):
//  hook: the open core hums | rewind: a reversed swell + the bands ratcheting shut, a slam at 1.6
//  spin: a felted dial whirr that slows into its notch | lock: a soft double thock (body + latch)
//  seam: a rising soft swell as the light runs up the seam | open: a deep slide per band | ignite: a warm deep bloom
//  orbit: a low rotating hum | home: a thock per landing band | final: the heaviest thock + latch, then silence
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { CORE, coreEvents, IGNITE, IN_LOCKS, IN_STARTS, OUT_LOCKS, OUT_STARTS, realAt, HOOK_OUT } from "../src/scenes/core/core";
import { FLARES } from "../src/scenes/core/fx";
import { addWrapped, reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";

export function generateCoreAudio(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "core-sfx");
  const att = (t: number, a: number) => Math.min(1, t / a);
  const thock = (at: number, f: number, amp: number, pan = 0.5, decay = 26, len = 0.45, puff = 0.5) => {
    if (at < 0 || at > CORE.duration) return;
    let lp = 0;
    addWrapped(out, at, len, pan, (t) => {
      const body = Math.sin(2 * Math.PI * f * t * (1 - 0.45 * t)) * Math.exp(-t * decay) + 0.22 * Math.sin(2 * Math.PI * f * 1.5 * t) * Math.exp(-t * decay * 1.8);
      lp += ((r() * 2 - 1) - lp) * 0.05;
      return att(t, 0.004) * (body + lp * Math.exp(-t * 110) * puff) * amp;
    });
  };
  const lock = (at: number, f: number, amp: number, pan: number) => { thock(at, f, amp, pan); thock(at + 0.028, f * 0.72, amp * 0.6, pan, 32, 0.3, 0.3); };
  // a felted dial whirr: low-passed noise pulsed at the detent rate, slowing to the notch (no bright ticks)
  const whirr = (from: number, to: number, amp: number, pan: number) => {
    let a = 0, b = 0, ph = 0;
    const len = to - from;
    addWrapped(out, from, len + 0.05, pan, (t) => {
      const u = Math.min(1, t / len);
      const rate = 26 * (1 - u) ** 2 + 2;
      ph += rate / 48000;
      a += ((r() * 2 - 1) - a) * 0.035;
      b += (a - b) * 0.035;
      const det = 0.45 + 0.55 * Math.max(0, Math.sin(2 * Math.PI * ph)) ** 6;
      const env = Math.min(1, t / 0.12) * (1 - u) ** 0.6;
      return (b * 3 + 0.25 * Math.sin(2 * Math.PI * (70 + 40 * (1 - u)) * t)) * det * env * amp;
    });
  };
  const boom = (at: number, amp: number, len = 2.0, f = 41) => addWrapped(out, at, len, 0.5, (t) =>
    (Math.sin(2 * Math.PI * f * (1 - 0.2 * Math.min(1, t / 0.7)) * t) + 0.3 * Math.sin(2 * Math.PI * f * 2 * t) * Math.exp(-t * 5)) * Math.exp(-t * 1.9) * att(t, 0.01) * amp);
  const swell = (from: number, len: number, f0: number, f1: number, amp: number, reverse = false) => addWrapped(out, from, len, 0.5, (t) => {
    const u = t / len;
    const k = reverse ? 1 - u : u;
    const env = reverse ? (1 - u) ** 0.5 * Math.min(1, t / 0.05) : u ** 1.6 * Math.exp(-Math.max(0, u - 0.9) * 30);
    const f = f0 + (f1 - f0) * k;
    return (Math.sin(2 * Math.PI * f * t) + 0.4 * Math.sin(2 * Math.PI * f * 1.5 * t)) * env * amp;
  });
  const hum = (from: number, len: number, amp: number, rot: (t: number) => number) => addWrapped(out, from, len, 0.5, (t) => {
    const env = Math.min(1, t / 0.8) * Math.min(1, (len - t) / 0.6);
    const s = rot(t);
    return (Math.sin(2 * Math.PI * 55 * t + 1.5 * Math.sin(s)) + 0.3 * Math.sin(2 * Math.PI * 82.5 * t)) * (0.7 + 0.3 * Math.sin(s * 2)) * env * amp;
  });
  const pan = (i: number, n: number) => 0.3 + 0.4 * (i / (n - 1));

  // v6 hook (option A): inside the sphere the mercury core hums; a rising air rush as the camera flies out through the
  // slit; the two hemispheres clack shut behind it at 1.72 s
  hum(0, HOOK_OUT, 0.06, (t) => 3 * t);
  swell(0.4, HOOK_OUT - 0.45, 120, 380, 0.05);
  thock(0.25, 52, 0.22, 0.5, 9, 1.0, 0.55); // the mercury surge in the hook
  lock(1.72, 78, 0.3, 0.5);
  boom(1.72, 0.16, 1.2);
  // dials
  OUT_STARTS.forEach((s, i) => whirr(s, OUT_LOCKS[i], 0.05, pan(i, 8)));
  IN_STARTS.forEach((s, i) => whirr(s, IN_LOCKS[i], 0.035, pan(i, 6)));
  for (const e of coreEvents()) {
    if (e.kind === "lock") lock(e.t, e.shell === 0 ? 92 + 5 * e.i : 120 + 6 * e.i, e.shell === 0 ? 0.24 : 0.17, e.shell === 0 ? pan(e.i, 8) : pan(e.i, 6));
    if (e.kind === "seam") swell(e.t - 0.35, 0.55, 180, 360, 0.06);
    if (e.kind === "open") thock(e.t + 0.15, 58 + 4 * e.i, 0.08, e.shell === 0 ? pan(e.i, 8) : 0.5, 6, 1.2, 0.2);
    if (e.kind === "ignite") { boom(e.t, 0.3, 2.6, 38); swell(e.t - 0.6, 0.65, 90, 180, 0.05); }
    if (e.kind === "home") thock(e.t, e.shell === 0 ? 86 + 4 * e.i : 112 + 5 * e.i, e.shell === 0 ? 0.2 : 0.14, e.shell === 0 ? pan(e.i, 8) : 0.5, 22, 0.5, 0.45);
    if (e.kind === "final") { lock(e.t, 64, 0.42, 0.5); boom(e.t, 0.22, 2.2, 36); }
  }
  // a soft felted puff (low-passed air) for the spark bursts - never a bright crackle
  const puff = (at: number, amp: number, dur = 0.5) => { let a = 0, b = 0; addWrapped(out, at, dur, 0.5, (t) => { a += ((r() * 2 - 1) - a) * 0.12; b += (a - b) * 0.12; return b * 2.2 * Math.exp(-t * 7) * att(t, 0.006) * amp; }); };
  for (const e of coreEvents()) {
    if (e.kind === "lock") puff(e.t, e.shell === 0 ? 0.1 : 0.07, 0.35);
    if (e.kind === "open" && e.i === 0) puff(e.t + 0.2, 0.16, 0.9);
    if (e.kind === "ignite") puff(e.t, 0.2, 1.2);
    if (e.kind === "final") puff(e.t, 0.12, 0.6);
  }
  // core pulses (v6: no cold-open eruption any more)
  for (const f of [FLARES[0], FLARES[2]]) { const t = realAt(f); if (t > 2) { boom(t, 0.16, 1.2, 46); puff(t, 0.1, 0.5); } }
  // the gyroscope hum while the bands orbit the core
  hum(realAt(IGNITE) - 0.5, realAt(15.2) - realAt(IGNITE) + 0.5, 0.045, (t) => 1.2 * t + 0.2 * t * t);

  // v8: the liquid-metal core ripples on every pulse - a soft, creamy liquid "bloop" (a low tone sliding up, felted)
  const bloop = (at: number, f: number, amp: number, pan: number) => {
    let lp = 0;
    addWrapped(out, at, 0.35, pan, (t) => {
      const ff = f * (1 + 0.9 * (1 - Math.exp(-t * 28)));
      const v = Math.sin(2 * Math.PI * ff * t) * Math.exp(-t * 14) * att(t, 0.006);
      lp += (v - lp) * 0.25;
      return lp * amp;
    });
  };
  FLARES.forEach((f, i) => { const t = realAt(f); if (t > 2) { bloop(t, 150 + 22 * (i % 3), 0.16, 0.42 + 0.16 * (i % 2)); bloop(t + 0.11, 210 + 15 * (i % 2), 0.08, 0.55); } });
  reverb(out, { room: 0.55, damp: 0.6, wet: 0.15, preDelayMs: 10, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (core sfx)`);
  return rel;
}
