// SFX for 0017 "Obsidian Heart" v6 - CREAMY, MUTED THOCKS (owner: "sounds are not tapping and CREAMY and MUTED").
// Built on the approved 0011 Singing Pins thock: a low sine body with a slight pitch drop, ~38/s decay, plus a
// low-passed (felted) noise puff - no bright clicks, no samples with hard transients. Every sound has a visible cause
// (src/scenes/shell/timeline.json, real time).
//  open (v7): the frosted ball close up - a heartbeat thock + soft chime on each light flare, quiet frost creaks
//  in between | peel: one thock per plate, faster and
//  faster | blast: a deep soft thock + muffled puff + scattered thocks | orbit: a few quiet thocks
//  grow: a muffled crackle (low-passed grains) | pulses: a warm low pulse + a soft muted chime (C# minor)
//  retract: thocks falling | slam: a spiral of thocks + a deep thock | ending: one last muted chime, then silence
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import TL from "../src/scenes/shell/timeline.json";
import { addWrapped, reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";

export function generateShellAudio(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "shell-thocks-v6");
  const attack = (t: number, a: number) => Math.min(1, t / a);

  // the 0011 thock: sine body with a slight pitch drop + a felted noise puff
  const thock = (at: number, f: number, amp: number, pan = 0.5, decay = 38, len = 0.25, puffAmt = 0.5) => {
    if (at < 0) return;
    let lp = 0;
    addWrapped(out, at, len, pan, (t) => {
      const body = Math.sin(2 * Math.PI * f * t * (1 - 0.6 * t)) * Math.exp(-t * decay)
        + 0.25 * Math.sin(2 * Math.PI * f * 1.5 * t) * Math.exp(-t * decay * 1.8);
      lp += ((r() * 2 - 1) - lp) * 0.06;
      return attack(t, 0.004) * (body + lp * Math.exp(-t * 160) * puffAmt) * amp;
    });
  };
  // deep soft thock for big moments: low body, long decay, a wide muffled puff
  const deep = (at: number, amp: number) => {
    thock(at, 62, amp, 0.5, 7, 1.0, 0.9);
    thock(at + 0.004, 124, amp * 0.35, 0.5, 14, 0.5, 0.3);
  };
  // muffled crackle grain (crystals growing): a tiny burst of heavily low-passed noise
  const grain = (at: number, amp: number, pan: number, tone: number) => {
    let lp = 0, lp2 = 0;
    addWrapped(out, at, 0.04, pan, (t) => {
      lp += ((r() * 2 - 1) - lp) * tone;
      lp2 += (lp - lp2) * tone;
      return attack(t, 0.002) * lp2 * Math.exp(-t * 140) * amp;
    });
  };
  // soft muted chime: rounded sine + one quiet partial, slow attack, no metallic ring
  const chime = (at: number, f: number, amp: number, pan = 0.5, len = 2.2) =>
    addWrapped(out, at, len, pan, (t) =>
      (Math.sin(2 * Math.PI * f * t) + 0.18 * Math.sin(2 * Math.PI * f * 2 * t) * Math.exp(-t * 4))
      * Math.exp(-t * 2.4) * attack(t, 0.012) * amp);
  // warm low pulse (C#2)
  const pulse = (at: number, amp: number, len = 0.9) => addWrapped(out, at, len, 0.5, (t) =>
    (Math.sin(2 * Math.PI * 69.3 * t) + 0.3 * Math.sin(2 * Math.PI * 138.6 * t)) * Math.sin(Math.PI * Math.min(1, t / len)) ** 2 * amp);
  // reversed swell: muffled noise rising into the moment it ends on (tape-rewind feel, no hiss)
  const swell = (from: number, to: number, amp: number) => {
    let lp = 0;
    const len = to - from;
    addWrapped(out, from, len, 0.5, (t) => {
      const x = t / len;
      lp += ((r() * 2 - 1) - lp) * (0.02 + 0.06 * x);
      return lp * x ** 2.2 * amp + Math.sin(2 * Math.PI * (55 + 40 * x) * t) * x ** 3 * amp * 0.25;
    });
  };

  // v7 opening: the frosted ball, close - its heart flares through the cracks (heartbeat thocks, each with a soft
  // chime), and the frost creaks quietly in between (sparse muffled grains)
  TL.heartbeats.forEach((hb, i) => {
    deep(hb, 0.26 - 0.03 * i);
    pulse(hb, 0.07, 0.7);
    chime(hb + 0.03, [277.2, 329.6, 277.2, 415.3][i], 0.03); // C#4 E4 C#4 G#4
  });
  for (let i = 0; i < 40; i++) grain(0.25 + r() * (TL.peel[0] - 0.4), 0.05 + 0.04 * r(), r(), 0.07);
  void swell;

  // peel: one thock per plate, accelerating like the picture (tp = p0 + (p1-p0) * x^0.55)
  const n = 70;
  for (let i = 0; i < n; i++) {
    const x = i / n;
    thock(TL.peel[0] + (TL.peel[1] - TL.peel[0]) * x ** 0.55, 185 + 120 * r() + 60 * x, 0.06 + 0.03 * x, 0.2 + 0.6 * r());
  }
  // blast
  deep(TL.blast[0], 0.34);
  pulse(TL.blast[0], 0.1, 1.2);
  for (let i = 0; i < 22; i++) thock(TL.blast[0] + 0.03 + r() * 0.5, 150 + 160 * r(), 0.045 * (1 - i / 30), r());
  // orbit: a few quiet thocks as plates swing past the lens
  for (let t = TL.blast[1] + 0.2; t < TL.grow[0]; t += 0.38 + 0.3 * r()) thock(t, 160 + 60 * r(), 0.028, 0.5 + 0.4 * Math.sin(t * 3), 30);
  // crystals grow: a muffled crackle, denser and slightly brighter as they grow
  for (let i = 0; i < 260; i++) {
    const x = i / 260;
    grain(TL.grow[0] + (TL.grow[1] - TL.grow[0]) * x + (r() - 0.5) * 0.02, 0.09 + 0.06 * x, r(), 0.08 + 0.1 * x);
  }
  for (let i = 0; i < 14; i++) thock(TL.grow[0] + (TL.grow[1] - TL.grow[0]) * (i + r()) / 14, 220 + 150 * (i / 14), 0.035, r());
  // light pulses: warm low pulse + a soft muted chime each (C#5, E5, G#5)
  TL.pulses.forEach((p, i) => { pulse(p - 0.05, 0.1); chime(p + 0.04, [554.4, 659.3, 830.6][i], 0.05, 0.3 + 0.2 * i); });
  // retract: thocks falling in pitch
  for (let i = 0; i < 26; i++) {
    const x = i / 26;
    thock(TL.retract[0] + (TL.retract[1] - TL.retract[0]) * x, 300 - 150 * x, 0.04, r());
  }
  // slam: a spiral of thocks rising, then a deep thock
  for (let i = 0; i < 50; i++) {
    const x = i / 50;
    thock(TL.slam[0] + (TL.slam[1] - TL.slam[0]) * (0.6 + 0.25 * x) / 1.25, 160 + 140 * x, 0.06, 0.2 + 0.6 * x);
  }
  deep(TL.slam[1] - 0.15, 0.36);
  pulse(TL.slam[1] - 0.15, 0.1, 1.2);
  // ending: one last muted chime under the final glow, rings into the fade
  pulse(TL.last - 0.05, 0.07, 1.2);
  chime(TL.last, 277.2, 0.045, 0.5, 3.2); // C#4

  reverb(out, { room: 0.6, damp: 0.65, wet: 0.16, preDelayMs: 12, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (obsidian heart v6 creamy thocks)`);
  return rel;
}
