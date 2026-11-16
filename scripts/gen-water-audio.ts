// SFX for 0020 "This water falls upward" - soft, creamy WATER sounds, every one tied to a visible event
// (src/scenes/water/events.json, written by scripts/blender/water_up.py in real time):
//  cold-open splash on the ceiling: a deep wet thock + a soft muffled splash | rewind: a reversed, sucking swell
//  bulge: a low bubbling gulp | rise: a gentle, rising trickle (filtered, no hiss) | braid: a soft twisting swirl
//  the hit: the deepest wet thock + a splash | each drop that lands: a soft liquid "plip" (in the glass) or a tiny tap
//  (on the stone) | refill: a creamy pouring gurgle | end: silence
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import EV from "../src/scenes/water/events.json";
import { addWrapped, reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";

export function generateWaterAudio(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "water-sfx");
  const att = (t: number, a: number) => Math.min(1, t / a);
  const thock = (at: number, f: number, amp: number, decay = 12, len = 0.8, bend = 0.5) => {
    let lp = 0;
    addWrapped(out, Math.max(0, at), len, 0.5, (t) => {
      const body = Math.sin(2 * Math.PI * f * t * (1 - bend * t)) * Math.exp(-t * decay);
      lp += ((r() * 2 - 1) - lp) * 0.06;
      return att(t, 0.005) * (body + lp * Math.exp(-t * 90) * 0.5) * amp;
    });
  };
  const splash = (at: number, len: number, amp: number) => {
    let lp = 0;
    addWrapped(out, Math.max(0, at), len, 0.5, (t) => { lp += ((r() * 2 - 1) - lp) * 0.08; return lp * Math.exp(-t * (4 / len)) * att(t, 0.004) * amp; });
  };
  const bubbles = (from: number, to: number, n: number, amp: number, f0: number, f1: number) => {
    for (let i = 0; i < n; i++) {
      const x = i / n, at = from + (to - from) * x + (r() - 0.5) * 0.05;
      const f = f0 + (f1 - f0) * x + 80 * r();
      addWrapped(out, at, 0.12, 0.3 + 0.4 * r(), (t) => Math.sin(2 * Math.PI * f * (1 + 2.2 * t) * t) * Math.exp(-t * 35) * att(t, 0.004) * amp);
    }
  };
  const plip = (at: number, size: number, pan: number, amp: number) => addWrapped(out, at, 0.22, pan, (t) => {
    const f = (620 - 70000 * size) * (1 + 1.3 * Math.exp(-t * 40));
    return Math.sin(2 * Math.PI * f * t) * Math.exp(-t * 26) * att(t, 0.003) * amp;
  });

  // cold open: the rope hits the ceiling
  thock(EV.coldHit, 60, 0.32, 6, 1.0, 0.4);
  splash(EV.coldHit, 0.6, 0.08);
  // rewind: a reversed sucking swell
  let lp = 0;
  const [r0, r1] = EV.rewind;
  addWrapped(out, r0 - 0.05, r1 - r0 + 0.1, 0.5, (t) => {
    const k = Math.min(1, t / (r1 - r0 + 0.1));
    lp += ((r() * 2 - 1) - lp) * (0.02 + 0.08 * k);
    return lp * k ** 2 * 0.14 + Math.sin(2 * Math.PI * (70 + 240 * k * k) * t) * k ** 2.5 * 0.04;
  });
  // bulge: a low bubbling gulp
  bubbles(EV.bulge[0], EV.bulge[1], 10, 0.05, 180, 320);
  thock(EV.bulge[1], 110, 0.14, 18, 0.5, 0.6);
  // the rise: a gentle trickle of tiny bubbles climbing in pitch
  bubbles(EV.rise[0], EV.rise[1], 70, 0.022, 300, 900);
  // the braid twisting: a soft swirl
  bubbles(EV.braid[0], EV.braid[1], 30, 0.03, 500, 700);
  // the hit
  thock(EV.hit, 55, 0.36, 5, 1.2, 0.4);
  splash(EV.hit, 0.9, 0.1);
  // every drop that lands
  for (const l of EV.landings) {
    if (l.inGlass) plip(l.t, l.r, 0.5 + Math.max(-0.35, Math.min(0.35, l.x * 6)), 0.06 + 8 * l.r);
    else plip(l.t, l.r * 0.5, 0.5 + Math.max(-0.4, Math.min(0.4, l.x * 4)), 0.03);
  }
  // refill: a creamy pouring gurgle
  bubbles(EV.refill[0], EV.refill[1], 40, 0.03, 220, 160);

  reverb(out, { room: 0.6, damp: 0.6, wet: 0.16, preDelayMs: 12, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (water falls upward sfx, ${EV.landings.length} drops)`);
  return rel;
}
