// SFX for "Orb Waves": a glassy tock for every orb bounce, from the same physics as the picture (orbs.ts impacts).
// Pitch follows the ring (centre orbs higher), pan follows x, level follows the bounce amplitude, so the in-phase
// climax is one big unified hit and the settle fades into silence. Binned per 5 ms and 5 zones.
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
  const r = rng(reel.seed, "orb-sfx");
  const bins = new Map<string, { t: number; e: number; n: number; pitch: number; pan: number }>();
  for (const o of orbLayout(reel.seed)) {
    const zone = Math.min(4, Math.floor(((o.x / OP.discRadius) + 1) / 2 * 5));
    for (const im of impacts(o)) {
      const key = `${Math.floor(im.t / 0.005)}|${zone}`;
      const b = bins.get(key) ?? { t: im.t, e: 0, n: 0, pitch: 0, pan: 0.15 + zone * 0.175 };
      b.e += im.e; b.n++; b.pitch += o.r01;
      bins.set(key, b);
    }
  }
  for (const b of bins.values()) {
    const ring = b.pitch / b.n, e = b.e / b.n;
    const f = 1900 + 1700 * (1 - ring) + r() * 250;
    const g = Math.min(0.24, 0.035 * Math.sqrt(b.n)) * (0.25 + 0.75 * e);
    if (g < 0.003) continue;
    addWrapped(out, b.t + r() * 0.003, 0.06, b.pan, (t) =>
      (Math.sin(2 * Math.PI * f * t) + 0.3 * Math.sin(2 * Math.PI * f * 2.7 * t) * Math.exp(-t * 200)) * Math.exp(-t * 95) * Math.min(1, t * 5000) * g);
  }
  // the in-phase climax: a soft low thump under the unified hit
  addWrapped(out, SYNC_AT - 0.02, 0.8, 0.5, (t) => Math.sin(2 * Math.PI * (60 + 40 * Math.exp(-t * 10)) * t) * Math.exp(-t * 5) * Math.min(1, t * 400) * 0.4);
  reverb(out, { room: 0.8, damp: 0.4, wet: 0.22, preDelayMs: 12, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.05);
  console.log(`wrote assets/${rel} (${bins.size} bounce sounds, climax at ${SYNC_AT.toFixed(2)} s)`);
  return rel;
}
