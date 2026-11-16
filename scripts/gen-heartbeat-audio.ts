// SFX for 0019 "This liquid has a heartbeat" - creamy, muted, liquid. Every sound has a visible cause
// (src/scenes/ferroMusic/heartbeat.ts):
//  the drop lands: a deep wet "plunk" + a muffled splash | each heartbeat: a soft lub-dub thock + a tiny wet sizzle
//  as the spikes jump | tower rising: a low creamy swell | each drip / rain drop landing: a soft liquid "plip"
//  (pitch by size) | the collapse: the deepest thock + a wide muffled splash | end: a last soft beat, then silence
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { beats, HB, landings } from "../src/scenes/ferroMusic/heartbeat";
import { addWrapped, reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";

export function generateHeartbeatAudio(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "heartbeat-sfx");
  const att = (t: number, a: number) => Math.min(1, t / a);
  const thock = (at: number, f: number, amp: number, pan = 0.5, decay = 30, len = 0.4, bend = 0.6) => {
    let lp = 0;
    addWrapped(out, Math.max(0, at), len, pan, (t) => {
      const body = Math.sin(2 * Math.PI * f * t * (1 - bend * t)) * Math.exp(-t * decay) + 0.22 * Math.sin(2 * Math.PI * f * 1.5 * t) * Math.exp(-t * decay * 1.8);
      lp += ((r() * 2 - 1) - lp) * 0.06;
      return att(t, 0.005) * (body + lp * Math.exp(-t * 120) * 0.5) * amp;
    });
  };
  const splash = (at: number, len: number, amp: number, pan = 0.5) => {
    let lp = 0;
    addWrapped(out, Math.max(0, at), len, pan, (t) => {
      lp += ((r() * 2 - 1) - lp) * 0.07;
      return lp * Math.exp(-t * (4 / len)) * att(t, 0.004) * amp;
    });
  };
  const plip = (at: number, size: number, pan: number, amp: number) => addWrapped(out, at, 0.2, pan, (t) => {
    const f = (520 - 60000 * size) * (1 + 1.4 * Math.exp(-t * 45));
    return Math.sin(2 * Math.PI * f * t) * Math.exp(-t * 28) * att(t, 0.003) * amp;
  });

  // the drop lands
  thock(HB.impact, 70, 0.34, 0.5, 9, 0.9, 0.5);
  splash(HB.impact, 0.5, 0.09);
  // heartbeats
  for (const b of beats()) {
    thock(b.t, 58, 0.24 * b.g, 0.5, 9, 0.7, 0.3);
    thock(b.t + 0.22, 64, 0.14 * b.g, 0.5, 11, 0.6, 0.3);
    splash(b.t + 0.02, 0.18, 0.025 * b.g, 0.5);
  }
  // the tower rising: a low creamy swell
  addWrapped(out, HB.tower[0], HB.tower[1] - HB.tower[0] + 1.5, 0.5, (t) => {
    const k = Math.min(1, t / (HB.tower[1] - HB.tower[0]));
    return (Math.sin(2 * Math.PI * (55 + 30 * k) * t) + 0.3 * Math.sin(2 * Math.PI * (110 + 60 * k) * t)) * k ** 1.5 * Math.exp(-Math.max(0, t - (HB.tower[1] - HB.tower[0])) * 2) * 0.05;
  });
  // the collapse: the deepest thock + a wide splash
  thock(HB.collapse, 52, 0.36, 0.5, 6, 1.2, 0.4);
  splash(HB.collapse, 0.9, 0.11);
  // every drop that lands (splash droplets, drips, the rain)
  for (const l of landings()) plip(l.t, l.r, 0.5 + Math.max(-0.4, Math.min(0.4, l.x * 6)), 0.05 + 6 * l.r);

  reverb(out, { room: 0.55, damp: 0.65, wet: 0.14, preDelayMs: 10, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (heartbeat liquid: plunk, beats, drips, rain)`);
  return rel;
}
