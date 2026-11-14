// SFX for 0016 "Urchin Heart": every sound has a visible cause (src/scenes/urchin/timeline.json), all synthesized
// here (original audio). The track loops: nothing rings across the cut except what also starts at frame 0.
//  - the twitch: a soft wet poke against the jelly skin + a low thump
//  - heartbeats: a deep, round lub-dub inside the gel (muffled - it is INSIDE the jelly)
//  - crawl: a soft gel squelch on every beat while it rolls
//  - urchin: a creaking, glassy stretch as the spikes press the skin out
//  - split: a long wet stretch, then a tiny pop when the neck lets go; merge: a heavy wet slap + sub drop
//  - breach: a crisp, glassy "tsk" for every spike piercing the skin, a soft suck as the gel heals around them
//  - settle: a final jelly wobble
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import TL from "../src/scenes/urchin/timeline.json";
import { addWrapped, reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";

export function generateUrchinAudio(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "urchin-sfx");
  const thump = (at: number, g: number, f0 = 58, pan = 0.5) => addWrapped(out, at, 0.5, pan, (t) => {
    const f = f0 * (1 - 0.3 * Math.min(1, t / 0.12));
    return (Math.sin(2 * Math.PI * f * t) + 0.2 * Math.sin(4 * Math.PI * f * t) * Math.exp(-t * 30)) * Math.min(1, t / 0.012) * Math.exp(-t * 10) * g;
  });
  const wet = (at: number, len: number, g: number, f0: number, f1: number, pan = 0.5) => {
    let lp = 0;
    addWrapped(out, at, len + 0.1, pan, (t) => {
      lp += ((r() * 2 - 1) - lp) * 0.12;
      const k = Math.min(1, t / len);
      const f = f0 + (f1 - f0) * k;
      return (Math.sin(2 * Math.PI * f * t) * 0.5 + lp * 0.55) * Math.min(1, t / 0.01) * (t < len ? 1 - 0.3 * k : Math.exp(-(t - len) * 30)) * Math.exp(-t * (2.5 / len)) * g;
    });
  };
  const tsk = (at: number, g: number, pan: number, f: number) => {
    let hp = 0, prev = 0;
    addWrapped(out, at, 0.2, pan, (t) => {
      const x = r() * 2 - 1;
      hp = 0.85 * (hp + x - prev); prev = x; // bright, glassy
      return (hp * 0.5 + Math.sin(2 * Math.PI * f * t) * 0.6) * Math.exp(-t * 45) * Math.min(1, t / 0.002) * g;
    });
  };
  const creak = (at: number, len: number, g: number) => addWrapped(out, at, len, 0.5, (t) => {
    const f = 140 + 60 * Math.sin(t * 3) + 30 * t;
    const grain = 0.5 + 0.5 * Math.sin(2 * Math.PI * 23 * t + 3 * Math.sin(2 * Math.PI * 7 * t)); // a soft, rubbery creak
    return Math.sin(2 * Math.PI * f * t) * grain * Math.min(1, t / 0.4) * Math.max(0, 1 - t / len) * g;
  });
  const drop = (at: number, g: number) => addWrapped(out, at, 1.8, 0.5, (t) => Math.sin(2 * Math.PI * 55 * (1 - 0.4 * Math.min(1, t / 0.8)) * t) * Math.exp(-t * 2.6) * Math.min(1, t / 0.006) * g);

  // twitch
  wet(TL.twitch, 0.25, 0.09, 320, 140, 0.35);
  thump(TL.twitch + 0.02, 0.22, 62, 0.4);
  // heartbeats (lub-dub)
  for (const b of TL.beats) { thump(b, 0.28); thump(b + 0.22, 0.16, 68); }
  // crawl squelches
  for (const b of TL.beats.filter((x) => x >= TL.crawl[0] && x <= TL.crawl[1])) wet(b + 0.08, 0.3, 0.05, 220, 120, 0.6);
  // urchin
  creak(TL.urchin[0] + 0.2, TL.urchin[1] - TL.urchin[0] - 0.6, 0.035);
  for (let k = 0; k < 6; k++) wet(TL.urchin[0] + 0.3 + k * 0.22, 0.18, 0.035, 500 + 60 * k, 260, 0.3 + 0.08 * k);
  // split: a long stretch and the neck letting go, then the merge slam
  wet(TL.split[0] + 0.3, 1.6, 0.06, 120, 260, 0.5);
  tsk(TL.split[0] + 1.75, 0.05, 0.5, 900);
  wet(TL.merge - 0.12, 0.35, 0.13, 180, 70);
  drop(TL.merge, 0.32);
  // breach: one glassy pierce per spike wave, a soft suck as the gel heals
  for (let k = 0; k < 9; k++) tsk(TL.breach[0] + 0.5 + k * 0.07, 0.055, 0.2 + 0.07 * k, 1500 + 120 * (k % 4));
  wet(TL.breach[1] - 0.9, 0.7, 0.07, 400, 120);
  // settle
  wet(TL.settle[0] + 0.1, 0.4, 0.04, 260, 160);

  reverb(out, { room: 0.5, damp: 0.6, wet: 0.12, preDelayMs: 8, loop: true });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (urchin heart sfx)`);
  return rel;
}
