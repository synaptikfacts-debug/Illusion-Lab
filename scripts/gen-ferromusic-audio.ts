// SFX for 0012 v7 "This liquid came alive": every sound has a visible cause (src/scenes/ferroMusic/creature.ts).
//  - a HEARTBEAT: a deep, soft lub-dub on every beat the picture shows (the split halves answer left and right)
//  - soft wet "shlick" sounds when it reaches out, when it splits and when the halves merge
//  - a deep sub drop on the merge and on the crown, an airy rising whoosh into the crown
//  - a gentle liquid settle in the long exhale
// No noise beds.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { beats, LIFE } from "../src/scenes/ferroMusic/creature";
import { addWrapped, reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";

export function generateFerroMusicAudio(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "ferroalive-sfx");
  // one heart sound: a low, rounded thump (pitch falls a little), no click
  const thump = (at: number, g: number, pan: number, f0: number) => {
    if (at < 0) return;
    addWrapped(out, at, 0.5, pan, (t) => {
      const f = f0 * (1 - 0.35 * Math.min(1, t / 0.12));
      const env = Math.min(1, t / 0.012) * Math.exp(-t * 11);
      return (Math.sin(2 * Math.PI * f * t) + 0.25 * Math.sin(2 * Math.PI * 2 * f * t) * Math.exp(-t * 30)) * env * g;
    });
  };
  let nb = 0;
  for (const b of beats()) {
    const pan = b.who === 1 ? 0.3 : b.who === 2 ? 0.7 : 0.5;
    thump(b.t, 0.3 * b.g, pan, 62);
    thump(b.t + 0.22, 0.18 * b.g, pan, 70);
    nb++;
  }
  const shlick = (at: number, g: number, pan = 0.5) => {
    let lp = 0;
    addWrapped(out, at, 0.55, pan, (t) => {
      lp += ((r() * 2 - 1) - lp) * 0.16;
      const f = 160 + 480 * Math.min(1, t / 0.14);
      return (Math.sin(2 * Math.PI * f * t) * 0.45 + lp * 0.6) * Math.exp(-t * 8) * Math.min(1, t / 0.012) * g;
    });
  };
  const drop = (at: number, g: number) => addWrapped(out, at, 2.2, 0.5, (t) => {
    const f = 60 * (1 - 0.45 * Math.min(1, t / 0.8));
    return Math.sin(2 * Math.PI * f * t) * Math.exp(-t * 2.2) * Math.min(1, t / 0.006) * g;
  });
  const whoosh = (at: number, len: number, g: number) => {
    let a = 0, b = 0;
    addWrapped(out, at, len + 0.3, 0.5, (t) => {
      const k = Math.min(1, t / len);
      const cut = 0.01 + 0.1 * k * k;
      a += ((r() * 2 - 1) - a) * cut;
      b += (a - b) * cut;
      return b * (t < len ? k ** 2.4 : Math.exp(-(t - len) * 25)) * g;
    });
  };
  shlick(LIFE.reach + 0.1, 0.08, 0.6);
  shlick(LIFE.split + 0.3, 0.08, 0.4);
  shlick(LIFE.split + 0.45, 0.07, 0.6);
  shlick(LIFE.merge - 0.08, 0.11);
  drop(LIFE.merge, 0.2);
  whoosh(LIFE.crown - 2.2, 2.2, 0.13);
  drop(LIFE.crown, 0.36);
  let lp = 0;
  addWrapped(out, LIFE.exhale[0] + 0.2, 3, 0.5, (t) => {
    lp += ((r() * 2 - 1) - lp) * 0.02;
    return lp * Math.exp(-t * 1.2) * (t / (t + 0.4)) * 0.07;
  });
  reverb(out, { room: 0.55, damp: 0.6, wet: 0.14, preDelayMs: 10, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (${nb} heartbeats, wet sounds, 2 deep drops)`);
  return rel;
}
