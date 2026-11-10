// SFX for "Orb Waves" (owner: one simple, calm sound - bubbles; no marimba, no music, no mix of many sounds).
// Each landing ring plays one soft bubble "bloop" (Minnaert-style: a sine whose pitch glides up as it fades),
// pitch from the ring (edge lower, centre higher), panned where it lands. Sparse: one bubble per ring per 0.16 s.
// The in-phase climax is a small cluster of bubbles; the settle fades to silence. Same physics as the picture.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { impacts, OP, orbLayout, SYNC_AT } from "../src/scenes/orbs/orbs";
import { addWrapped, reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";

export function generateOrbAudio(reel: Reel): string {
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const out = stereo(total);
  const r = rng(reel.seed, "orb-bubbles");
  const R = 8;
  const bubble = (at: number, f0: number, g: number, pan: number) =>
    addWrapped(out, at, 0.16, pan, (t) => {
      const f = f0 * (1 + 2.2 * t); // the bubble's pitch rises as it closes
      return Math.sin(2 * Math.PI * f * t) * Math.exp(-t * 34) * Math.min(1, t / 0.004) * g;
    });
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
    if (b.t - last[b.ring] < 0.16) continue;
    const e = b.e / b.n;
    const g = Math.min(0.32, 0.07 * Math.sqrt(b.n)) * (0.15 + 0.85 * e);
    if (g < 0.02) continue;
    last[b.ring] = b.t;
    bubble(b.t + r() * 0.01, 380 + b.ring * 70 + r() * 40, g, 0.5 + 0.35 * (b.x / b.n / OP.discRadius));
    n++;
  }
  // climax: a little cluster of bubbles
  for (let k = 0; k < 7; k++) bubble(SYNC_AT + k * 0.03 + r() * 0.02, 420 + r() * 500, 0.22, 0.2 + r() * 0.6);
  reverb(out, { room: 0.7, damp: 0.5, wet: 0.18, preDelayMs: 10, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (${n} soft bubbles, climax cluster at ${SYNC_AT.toFixed(2)} s)`);
  return rel;
}
