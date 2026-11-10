// SFX for "Pendulum Helix": one simple calm sound (owner's preference) - a soft, muted felt tick when a sphere of the
// front tier passes the bottom of its swing. Pitch rises slightly along the row, panned by the sphere's position,
// level follows the swing energy. Never two ticks within 0.11 s. The sync moment = one clear tick. Same motion as
// the picture.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { crossings, PD, SYNC_AT } from "../src/scenes/pendulum/pendulum";
import { addWrapped, Biquad, reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";

export function generatePendulumAudio(reel: Reel): string {
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const out = stereo(total);
  const r = rng(reel.seed, "pendulum-ticks");
  const tick = (at: number, f: number, g: number, pan: number) => {
    const lp = new Biquad().set("lp", 1100, 0.7);
    addWrapped(out, at, 0.08, pan, (t) => (Math.sin(2 * Math.PI * f * t) * 0.8 + lp.run(r() * 2 - 1) * 0.4) * Math.exp(-t * 60) * Math.min(1, t / 0.003) * g);
  };
  let lastAny = -1, n = 0;
  for (const c of crossings(0)) {
    if (c.t - lastAny < 0.11 || c.e < 0.05) continue;
    if (Math.abs(c.t - SYNC_AT) < 0.15) continue; // leave room for the sync tick
    lastAny = c.t;
    tick(c.t, 230 + c.k * 7, 0.2 * (0.25 + 0.75 * c.e), 0.2 + 0.6 * (c.k / (PD.cols - 1)));
    n++;
  }
  tick(SYNC_AT, 240, 0.3, 0.5);
  reverb(out, { room: 0.65, damp: 0.6, wet: 0.14, loop: false });
  const rel = `generated/${reel.id}-sfx.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (${n} soft ticks, sync tick at ${SYNC_AT} s)`);
  return rel;
}
