// SFX for "Golden Rings" (one simple calm sound, per the owner's 0007 feedback): a soft airy swish each time a
// ring sweeps through flat (its fastest moment). Pitch slightly lower for the big outer rings, panned by the ring's
// swing axis, level following the swing energy so everything fades out as the sculpture settles. Never two swishes
// within 0.1 s. The sync moment = one slightly fuller swish; then silence. Same closed-form motion as the picture.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { ringAt, RP, swishes } from "../src/scenes/rings/rings";
import { addWrapped, Biquad, reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";

export function generateRingsAudio(reel: Reel): string {
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const out = stereo(total);
  const r = rng(reel.seed, "ring-swish");
  const swish = (at: number, f0: number, g: number, pan: number, dur = 0.34) => {
    const bp = new Biquad();
    addWrapped(out, at, dur, pan, (t, k) => {
      const x = t / dur;
      if (k % 64 === 0) bp.set("bp", f0 * (1 + 0.8 * Math.sin(Math.PI * x)), 0.9);
      return bp.run(r() * 2 - 1) * Math.sin(Math.PI * x) ** 2 * g;
    });
  };
  let lastAny = -1, n = 0;
  const last = new Array(RP.count).fill(-1);
  for (const s of swishes()) {
    if (s.t - lastAny < 0.1 || s.t - last[s.i] < 0.6) continue;
    if (s.e < 0.06) continue;
    lastAny = s.t;
    last[s.i] = s.t;
    const k = s.i / (RP.count - 1);
    const pan = 0.5 + 0.3 * Math.sin(ringAt(s.i, s.t).axis);
    swish(s.t, 900 - 420 * k + r() * 80, 0.16 * (0.25 + 0.75 * s.e) * (0.6 + 0.4 * k), pan);
    n++;
  }
  // the sync moment: one fuller, longer swish as every ring sweeps through together
  swish(RP.syncAt, 520, 0.3, 0.5, 0.7);
  reverb(out, { room: 0.78, damp: 0.5, wet: 0.22, preDelayMs: 14, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (${n} soft swishes, sync swish at ${RP.syncAt} s)`);
  return rel;
}
