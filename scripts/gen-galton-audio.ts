// SFX for "Marble Cascade": every pin hit is a tiny glassy click, every landing a small clack on the stack
// (pitch rises as the stack grows), the gold marble rings like a bell. Built from the same simulation as the picture.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { buildMarbles, events, GB } from "../src/scenes/galton/galton";
import { addWrapped, Biquad, reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, play } from "./lib/sampler";

export function generateGaltonAudio(reel: Reel): string {
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const out = stereo(total);
  const r = rng(reel.seed, "galton-sfx");
  const { pins, lands } = events(buildMarbles(reel.seed));
  const W = (GB.rows + 1) * GB.s;
  const bin = <T extends { t: number; x: number }>(list: T[], dt: number) => {
    const m = new Map<string, { t: number; n: number; x: number; item: T }>();
    for (const e of list) {
      if (e.t < 0 || e.t > total) continue;
      const key = `${Math.floor(e.t / dt)}|${Math.floor((e.x / W + 0.5) * 6)}`;
      const b = m.get(key) ?? { t: e.t, n: 0, x: e.x, item: e };
      b.n++;
      m.set(key, b);
    }
    return [...m.values()];
  };
  for (const b of bin(pins, 0.004)) {
    const f = 3800 + r() * 2600, g = Math.min(0.16, 0.05 * Math.sqrt(b.n));
    addWrapped(out, b.t, 0.03, 0.5 + 0.42 * (b.x / (W / 2)), (t) => Math.sin(2 * Math.PI * f * t) * Math.exp(-t * 260) * Math.min(1, t * 6000) * g);
  }
  for (const b of bin(lands.filter((l) => !l.gold), 0.006)) {
    const lv = b.item.level;
    const f = 1700 + lv * 14 + r() * 300, g = Math.min(0.2, 0.07 * Math.sqrt(b.n));
    const bp = new Biquad().set("bp", f * 1.4, 2);
    addWrapped(out, b.t, 0.05, 0.5 + 0.42 * (b.x / (W / 2)), (t) => (Math.sin(2 * Math.PI * f * t) * 0.7 + bp.run(r() * 2 - 1) * 0.6) * Math.exp(-t * 120) * g);
  }
  const gold = lands.find((l) => l.gold)!;
  play(out, orch("glockenspiel", 96), gold.t, 0.35, 0.5, undefined, 1.5, 0.2);
  play(out, orch("glockenspiel", 103), gold.t + 0.02, 0.2, 0.5, undefined, 1.5, 0.2);
  reverb(out, { room: 0.78, damp: 0.4, wet: 0.2, preDelayMs: 10, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.05);
  console.log(`wrote assets/${rel} (${pins.length} pin hits, ${lands.length} landings, gold bell)`);
  return rel;
}
