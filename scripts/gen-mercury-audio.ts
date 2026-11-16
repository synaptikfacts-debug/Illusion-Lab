// SFX for 0023 "Mercury learned to dance" - creamy, muted THOCKS tied to what the drops visibly do
// (src/scenes/mercury/events.json, written by scripts/blender/mercury_dance.py):
//  open = the bass hit that threw the drops (a deep soft boom + a felted puff) | rewind = a soft swell falling back
//  beats = a low bass pulse + the drops landing (a pattering of tiny thocks) | vib = a gentle bass pulse
//  merges = a creamy thock per merge (lower as the drops grow), the last one a deep splash | splash droplets landing
//  = tiny soft thocks | settle = one last pulse, then silence into the fade
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import EV from "../src/scenes/mercury/events.json";
import { addWrapped, reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";

export function generateMercuryAudio(reel: Reel): string {
  const tl = timeline(reel);
  const out = stereo(tl.total / tl.fps);
  const r = rng(reel.seed, "mercury-thocks-v1");
  const att = (t: number, a: number) => Math.min(1, t / a);
  const thock = (at: number, f: number, amp: number, pan = 0.5, decay = 30, len = 0.35, puffAmt = 0.5) => {
    if (at < 0 || at > EV.duration) return;
    let lp = 0;
    addWrapped(out, at, len, pan, (t) => {
      const body = Math.sin(2 * Math.PI * f * t * (1 - 0.6 * t)) * Math.exp(-t * decay)
        + 0.25 * Math.sin(2 * Math.PI * f * 1.5 * t) * Math.exp(-t * decay * 1.8);
      lp += ((r() * 2 - 1) - lp) * 0.06;
      return att(t, 0.004) * (body + lp * Math.exp(-t * 150) * puffAmt) * amp;
    });
  };
  const bass = (at: number, amp: number, len = 0.9) => addWrapped(out, at, len, 0.5, (t) =>
    (Math.sin(2 * Math.PI * 49 * t) + 0.3 * Math.sin(2 * Math.PI * 98 * t)) * Math.exp(-t * 4) * att(t, 0.01) * amp);
  const pitter = (at: number, n: number, amp: number) => {
    for (let i = 0; i < n; i++) thock(at + 0.02 + r() * 0.16, 260 + 180 * r(), amp * (0.5 + 0.5 * r()), r(), 45, 0.18, 0.35);
  };

  // the cold open: the boom that threw everything, held in the air
  bass(EV.open[0] + 0.02, 0.38, 1.4);
  thock(0.02, 60, 0.3, 0.5, 6, 1.0, 0.9);
  // the rewind: a soft swell falling back down, the drops landing at its end
  let lp = 0;
  const [rw0, rw1] = EV.rewind;
  addWrapped(out, rw0, rw1 - rw0 + 0.1, 0.5, (t) => {
    const k = Math.min(1, t / (rw1 - rw0));
    lp += ((r() * 2 - 1) - lp) * (0.1 - 0.08 * k);
    return lp * Math.sin(Math.PI * k) * 0.12 + Math.sin(2 * Math.PI * (260 - 180 * k) * t) * Math.sin(Math.PI * k) * 0.04;
  });
  pitter(rw1 - 0.05, 16, 0.05);
  // the drum: a bass pulse on every beat, the drops patter as they land
  for (const b of EV.beats) { bass(b, 0.3); pitter(b + 0.45, 14, 0.05); }
  for (const v of EV.vib) bass(v, 0.16, 0.6);
  // every merge: a creamy thock, lower as the drops grow; the last one is a deep splash
  for (const m of EV.merges) {
    const n = m.count;
    const f = 300 - 40 * m.level;
    for (let k = 0; k < Math.min(n, 8); k++) thock(m.t - 0.04 + k * 0.035, f + 20 * r(), 0.12 + 0.03 * m.level, 0.2 + 0.6 * (k / 7), 22, 0.4, 0.6);
    if (n === 1) { thock(m.t, 58, 0.38, 0.5, 5, 1.4, 0.9); bass(m.t, 0.34, 1.4); }
  }
  for (const t of EV.splashLand) thock(t, 340 + 120 * r(), 0.05, r(), 40, 0.2, 0.4);
  // the settle: one last soft pulse under the wobble
  bass(EV.settle[0] + 1.2, 0.12, 1.2);

  reverb(out, { room: 0.55, damp: 0.6, wet: 0.15, preDelayMs: 10, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (mercury dance thocks)`);
  return rel;
}
