// SFX for "Orb Waves" (owner: calm and satisfying, not loud clicks, not music only). Research: the satisfying norm
// for bouncing-ball reels is a soft musical note per bounce (the motion plays its own melody); wood + a little glass.
// So: each ring of orbs owns one note of the D major pentatonic (edge low, centre high), played on a real, soft
// marimba recording (VSCO-2, CC0) whenever that ring's orbs land. Folding waves = rippling arpeggios; the in-phase
// climax = one full chord. A very soft glockenspiel adds an occasional glass sparkle. Same physics as the picture.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { impacts, OP, orbLayout, SYNC_AT } from "../src/scenes/orbs/orbs";
import { reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, play } from "./lib/sampler";

const RING_NOTES = [62, 64, 66, 69, 71, 74, 76, 78]; // D pentatonic, edge (0) -> centre (7)

export function generateOrbAudio(reel: Reel): string {
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const out = stereo(total);
  const r = rng(reel.seed, "orb-sfx");
  const R = RING_NOTES.length;
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
  // one soft note per ring at most every 0.14 s (no machine-gun repeats)
  const lastByRing = new Array(R).fill(-1);
  const list = [...bins.values()].sort((a, b) => a.t - b.t);
  let notes = 0;
  for (const b of list) {
    if (b.t - lastByRing[b.ring] < 0.14) continue;
    const e = b.e / b.n;
    const g = Math.min(0.2, 0.04 * Math.sqrt(b.n)) * (0.15 + 0.85 * e);
    if (g < 0.01) continue;
    lastByRing[b.ring] = b.t;
    const pan = 0.5 + 0.35 * (b.x / b.n / OP.discRadius);
    play(out, orch("marimba", RING_NOTES[b.ring]), b.t + r() * 0.01, g, pan, undefined, 0.6, 0.5);
    if (b.ring >= 5 && r() < 0.18) play(out, orch("glockenspiel", RING_NOTES[b.ring] + 24), b.t + 0.01, g * 0.25, pan, undefined, 0.8, 0.4);
    notes++;
  }
  // the in-phase climax: a full soft chord
  [50, 62, 66, 69, 74, 78, 81].forEach((m, i) => play(out, orch("marimba", m), SYNC_AT + i * 0.012, 0.16, 0.3 + i * 0.06, undefined, 0.8, 0.45));
  play(out, orch("glockenspiel", 93), SYNC_AT + 0.05, 0.08, 0.6, undefined, 1.2, 0.4);
  reverb(out, { room: 0.86, damp: 0.45, wet: 0.3, preDelayMs: 18, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (${notes} soft marimba notes, climax chord at ${SYNC_AT.toFixed(2)} s)`);
  return rel;
}
