// SFX for "Orb Waves" - owner's pick from four options (Nov 10): C "soft taps". One simple calm sound, no music:
// muted, low fingertip taps on felt when each ring of orbs lands, sparse (one per ring per 0.2 s), panned where it
// lands, level following the bounce amplitude (fades out as the orbs settle). The in-phase climax is a soft
// cluster of taps. Same physics as the picture.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { impacts, OP, orbLayout, SYNC_AT } from "../src/scenes/orbs/orbs";
import { addWrapped, Biquad, reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";

export function generateOrbAudio(reel: Reel): string {
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const out = stereo(total);
  const r = rng(reel.seed, "orb-taps");
  const R = 8;
  const tap = (at: number, f: number, g: number, pan: number) => {
    const lp = new Biquad().set("lp", 900, 0.7);
    addWrapped(out, at, 0.09, pan, (t) => (Math.sin(2 * Math.PI * f * t) * 0.8 + lp.run(r() * 2 - 1) * 0.5) * Math.exp(-t * 45) * Math.min(1, t / 0.003) * g);
  };
  const bins = new Map<string, { t: number; n: number; e: number; ring: number; x: number }>();
  for (const o of orbLayout(reel.seed)) {
    const ring = Math.min(R - 1, Math.floor((1 - o.r01) * R));
    for (const im of impacts(o)) {
      const key = `${ring}|${Math.floor(im.t / 0.04)}`;
      const b = bins.get(key) ?? { t: im.t, n: 0, e: 0, ring, x: 0 };
      b.n++; b.e += im.e; b.x += o.x;
      bins.set(key, b);
    }
  }
  const last = new Array(R).fill(-1);
  let n = 0;
  for (const b of [...bins.values()].sort((a, c) => a.t - c.t)) {
    if (b.t - last[b.ring] < 0.2) continue;
    const e = b.e / b.n;
    if (e < 0.04) continue;
    last[b.ring] = b.t;
    tap(b.t, 180 + b.ring * 18, 0.22 * (0.2 + 0.8 * e), 0.5 + 0.35 * (b.x / b.n / OP.discRadius));
    n++;
  }
  // climax: a soft cluster of taps across the disc
  for (let k = 0; k < 6; k++) tap(SYNC_AT + k * 0.018 + r() * 0.01, 170 + r() * 120, 0.2, 0.2 + k * 0.12);
  reverb(out, { room: 0.6, damp: 0.6, wet: 0.12, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (${n} soft taps, climax cluster at ${SYNC_AT.toFixed(2)} s)`);
  return rel;
}
