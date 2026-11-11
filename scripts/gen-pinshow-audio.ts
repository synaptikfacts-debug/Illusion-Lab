// SFX for "Singing Pins: the long show": calm and simple (owner rules). Sound only where the picture moves.
// Owner, Nov 11: "the sounds are overlapping and not accurate - a chaos of sounds". So no more per-pin taps:
//  - ONE creamy, muted thock per wave: each time the wave crest passes the centre of the wall (crests come at most
//    ~2 per second at the fast segment edges and thin out as the wall slows into each picture; never closer than
//    0.28 s and each thock dies in 0.22 s, so no two sounds ever overlap)
//  - one deeper, softer "settle" thock at the moment each picture locks in, and one as the final ring wave leaves
// No noise beds (owner: "ocean" sounds rejected), short dry-ish room, then silence through the fade.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { layoutShow, lockTimes, phaseAt, SHOW } from "../src/scenes/pins/show";
import { addWrapped, reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";

export function generatePinShowAudio(reel: Reel): string {
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const out = stereo(total);
  const r = rng(reel.seed, "pinshow-sfx");
  const pins = layoutShow();
  const centre = pins.reduce((a, b) => (b.dist < a.dist ? b : a));

  const thock = (at: number, f: number, amp: number, decay: number, len: number) => {
    let lp = 0;
    addWrapped(out, at, len, 0.5, (t) => {
      const body = Math.sin(2 * Math.PI * f * t * (1 - 0.6 * t)) * Math.exp(-t * decay) + 0.25 * Math.sin(2 * Math.PI * f * 1.5 * t) * Math.exp(-t * decay * 1.8);
      lp += ((r() * 2 - 1) - lp) * 0.06; // soft felted attack
      const puff = lp * Math.exp(-t * 160) * 0.5;
      return Math.min(1, t / 0.004) * (body + puff) * amp;
    });
  };

  // crest of the wave passing the centre of the wall
  const dt = 0.002;
  const crests: number[] = [];
  let prev = phaseAt(centre, 0) - 0.5;
  for (let t = dt; t < SHOW.fade[0]; t += dt) {
    const cur = phaseAt(centre, t) - 0.5;
    if (Math.floor(cur) !== Math.floor(prev)) crests.push(t - dt / 2);
    prev = cur;
  }
  const locks = lockTimes().filter((t) => t > 0.5 && t < SHOW.fade[0]);
  let last = -1, n = 0;
  for (const t of crests) {
    if (t - last < 0.28 || locks.some((l) => Math.abs(t - l) < 0.5)) continue;
    last = t;
    thock(t, 196 * (0.98 + r() * 0.04), 0.07, 30, 0.22);
    n++;
  }
  // a deeper settle as each picture locks in
  for (const l of locks) thock(l, 131, 0.085, 11, 0.6);
  // the melt's ring wave leaving the centre
  const ringAt = locks[locks.length - 1] + SHOW.hold;
  if (ringAt < SHOW.fade[0]) thock(ringAt, 147, 0.06, 9, 0.7);

  reverb(out, { room: 0.6, damp: 0.6, wet: 0.14, preDelayMs: 12, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (${n} wave thocks, ${locks.length} settle thocks, crests at ${crests.slice(0, 6).map((c) => c.toFixed(2)).join(" ")} ...)`);
  return rel;
}
