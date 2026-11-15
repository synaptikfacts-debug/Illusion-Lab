// SFX for 0018 "This liquid is hungry" v2 - creamy, muted sounds, timed to the REAL-time edit
// (src/scenes/ferroMusic/hungry.ts: cold open on the climax, a fast rewind, then the story at 1.45x; sToR maps story
// events to real time). Every sound has a visible cause:
//  cold open: a deep bristling crackle + a heavy wet THWACK as the spike-harpoon lunges at the lens
//  rewind: a reversed swell sucking everything back | each harpoon strike: a quick wet whip + a creamy GULP
//  pounce: a soft lift + a deep landing thock | rolling beads: a low roll | the big bead: wet squelches + the biggest
//  gulp | full: a racing, muted heartbeat | split: a long wet stretch + a soft pop | end: a last slow heartbeat
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { BEADS, BRISTLES, COLD, heartbeats, HUNGRY, REWIND, SPEED, sToR } from "../src/scenes/ferroMusic/hungry";
import { addWrapped, reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";

export function generateHungryAudio(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "hungry-sfx-v2");
  const att = (t: number, a: number) => Math.min(1, t / a);
  const thock = (at: number, f: number, amp: number, pan = 0.5, decay = 30, len = 0.35, bend = 0.6) => {
    let lp = 0;
    addWrapped(out, Math.max(0, at), len, pan, (t) => {
      const body = Math.sin(2 * Math.PI * f * t * (1 - bend * t)) * Math.exp(-t * decay) + 0.22 * Math.sin(2 * Math.PI * f * 1.5 * t) * Math.exp(-t * decay * 1.8);
      lp += ((r() * 2 - 1) - lp) * 0.06;
      return att(t, 0.005) * (body + lp * Math.exp(-t * 120) * 0.5) * amp;
    });
  };
  const slurp = (at: number, len: number, amp: number, pan = 0.5) => {
    let lp = 0;
    addWrapped(out, Math.max(0, at), len + 0.05, pan, (t) => {
      const k = Math.min(1, t / len);
      lp += ((r() * 2 - 1) - lp) * (0.05 + 0.05 * Math.sin(Math.PI * k));
      return (lp * 0.9 + 0.35 * Math.sin(2 * Math.PI * (260 - 140 * k) * t)) * Math.sin(Math.PI * k) ** 1.5 * amp;
    });
  };
  const whip = (at: number, amp: number, pan = 0.5) => {
    let lp = 0;
    addWrapped(out, Math.max(0, at), 0.18, pan, (t) => {
      const k = t / 0.18;
      lp += ((r() * 2 - 1) - lp) * (0.04 + 0.2 * k);
      return lp * Math.sin(Math.PI * k) * amp;
    });
  };
  const crackle = (from: number, to: number, n: number, amp: number) => {
    for (let i = 0; i < n; i++) {
      const at = from + (to - from) * r();
      let lp = 0, lp2 = 0;
      addWrapped(out, at, 0.04, r(), (t) => { lp += ((r() * 2 - 1) - lp) * 0.12; lp2 += (lp - lp2) * 0.12; return att(t, 0.002) * lp2 * Math.exp(-t * 140) * amp; });
    }
  };
  const heart = (at: number, g: number) => { thock(at, 58, 0.24 * g, 0.5, 9, 0.7, 0.3); thock(at + 0.22 / SPEED, 64, 0.14 * g, 0.5, 11, 0.6, 0.3); };

  // cold open: bristling crackle, the harpoon lunge, then the rewind swell
  crackle(0, COLD, 70, 0.08);
  heart(0.02, 1);
  whip(0.22, 0.12);
  thock(0.42, 95, 0.36, 0.5, 10, 0.8, 0.5);
  let lp = 0;
  addWrapped(out, COLD - 0.05, REWIND + 0.1, 0.5, (t) => {
    const k = Math.min(1, t / (REWIND + 0.1));
    lp += ((r() * 2 - 1) - lp) * (0.02 + 0.1 * k);
    return lp * k ** 2 * 0.16 + Math.sin(2 * Math.PI * (60 + 260 * k * k) * t) * k ** 2.5 * 0.05;
  });
  thock(COLD + REWIND, 150, 0.12, 0.5, 30, 0.3, 0.8); // landing back at the start

  for (const b of BEADS) {
    const e = sToR(b.eat);
    const pan = 0.5 + Math.max(-0.4, Math.min(0.4, b.x * 5));
    if (b.roll) {
      const from = sToR(11.4 + (b.eat - 12) * 0.2);
      let l2 = 0;
      addWrapped(out, from, e - from, pan, (t) => { l2 += ((r() * 2 - 1) - l2) * 0.03; return l2 * Math.sin(Math.PI * Math.min(1, t / (e - from))) * 0.05; });
      thock(e - 0.04, 230 + 40 * r(), 0.05, pan, 40, 0.25);
    } else {
      whip(sToR(b.eat - (b.big ? 0.9 : 0.55)), b.big ? 0.12 : 0.09, pan); // the harpoon shoots out
    }
    thock(e, b.big ? 120 : 170 + 30 * r(), b.big ? 0.32 : 0.2, pan, b.big ? 14 : 22, 0.5, 0.9);
    slurp(e + 0.03, b.big ? 0.4 : 0.22, b.big ? 0.07 : 0.045, pan);
  }
  // pounces: a lift and a deep landing
  for (const te of [3.6, 6.8, 10.6]) { slurp(sToR(te - 0.45), 0.2, 0.04); thock(sToR(te + 0.1), 75, 0.22, 0.5, 12, 0.6, 0.4); }
  // the struggle with the big bead
  for (let i = 0; i < 6; i++) slurp(sToR(9.4 + i * 0.2), 0.14, 0.04, 0.4 + 0.05 * i);
  crackle(sToR(15.6), sToR(18.2), 90, 0.06); // the crown bristles
  for (const [a, b] of BRISTLES) { crackle(a, a + 0.6, 60, 0.08); thock(a + 0.05, 90, 0.26, 0.5, 10, 0.7, 0.5); crackle(b - 0.5, b, 25, 0.05); }
  for (const h of heartbeats()) heart(sToR(h.t), h.g);
  slurp(sToR(HUNGRY.split[0]), 0.8, 0.06);
  thock(sToR(HUNGRY.split[1]) - 0.07, 210, 0.12, 0.5, 26, 0.3, 0.7);

  reverb(out, { room: 0.55, damp: 0.65, wet: 0.14, preDelayMs: 10, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (hungry liquid v2: cold open, harpoons, gulps, pounces)`);
  return rel;
}
