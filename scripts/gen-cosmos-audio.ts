// SFX for 0021 "The Break" (director's cut) - CREAMY, MUTED THOCKS (owner, Nov 15 2026), every one from the physics
// simulation's own collision log (src/scenes/cosmos/break_events.json, written by scripts/blender/cosmos_break.py):
//  impact = the cue ball smashing the cluster (deep thock + a felted burst) | click = bead hits bead (small, higher
//  thock, softer as they come) | planet = bead bounces off the gas giant (lower, rounder thock). A soft rising swell
//  under the fly-in, two last slow thocks as the ring settles, then silence into the fade.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import EV from "../src/scenes/cosmos/break_events.json";
import TL from "../src/scenes/cosmos/timeline.json";
import { addWrapped, reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";

export function generateCosmosAudio(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "break-thocks-v1");
  const thock = (at: number, f: number, amp: number, pan = 0.5, decay = 38, len = 0.25, puffAmt = 0.5) => {
    if (at < 0 || at > TL.duration) return;
    let lp = 0;
    addWrapped(out, at, len, pan, (t) => {
      const body = Math.sin(2 * Math.PI * f * t * (1 - 0.6 * t)) * Math.exp(-t * decay)
        + 0.25 * Math.sin(2 * Math.PI * f * 1.5 * t) * Math.exp(-t * decay * 1.8);
      lp += ((r() * 2 - 1) - lp) * 0.06;
      return Math.min(1, t / 0.004) * (body + lp * Math.exp(-t * 160) * puffAmt) * amp;
    });
  };
  // the fly-in: a muffled swell rising into the planet hits (no hiss)
  {
    let lp = 0;
    const [a, b] = [TL.flyIn[0] - 0.3, TL.planetHits[0]];
    addWrapped(out, a, b - a, 0.5, (t) => {
      const x = t / (b - a);
      lp += ((r() * 2 - 1) - lp) * (0.015 + 0.05 * x);
      return lp * x ** 2.2 * 0.16 + Math.sin(2 * Math.PI * (50 + 40 * x) * t) * x ** 3 * 0.04;
    });
  }
  // the collision log
  let lastClick = -1;
  for (const e of EV.events) {
    const s = e.s;
    if (e.kind === "impact") {
      thock(e.t, 56, 0.5, 0.5, 6, 1.2, 1.0);
      thock(e.t + 0.004, 112, 0.18, 0.5, 13, 0.6, 0.35);
      for (let i = 0; i < 14; i++) thock(e.t + 0.02 + r() * 0.35, 180 + 160 * r(), 0.05 * (1 - i / 18), r(), 44);
    } else if (e.kind === "click") {
      if (e.t - lastClick < 0.045) continue;
      lastClick = e.t;
      thock(e.t, 230 + 140 * r(), 0.025 + 0.045 * s, 0.2 + 0.6 * r(), 46, 0.2, 0.4);
    } else {
      thock(e.t, 120 + 70 * r(), 0.03 + 0.06 * s, 0.25 + 0.5 * r(), 26, 0.35, 0.6);
    }
  }
  // the ring settles: two last slow thocks, then silence
  thock(TL.settle[0] + 0.2, 104, 0.08, 0.45, 16, 0.7, 0.55);
  thock(TL.settle[0] + 1.0, 92, 0.055, 0.55, 16, 0.8, 0.55);
  reverb(out, { room: 0.62, damp: 0.65, wet: 0.17, preDelayMs: 12, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (the break: ${EV.events.length} collision thocks)`);
  return rel;
}
