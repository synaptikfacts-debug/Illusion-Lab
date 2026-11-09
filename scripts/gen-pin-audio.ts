// Melody for a pinWall reel, computed from the same physics as the picture: every Nth pin plays a soft
// pentatonic pluck at the moment it reaches its top, so waves crossing the wall become harp sweeps.
// When the pins freeze into the picture, a sustained chord swells in. Writes assets/generated/<id>-melody.wav.
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { timeline } from "../src/core/timing";
import { pinSchema } from "../src/illusions/pinWall/schema";
import { layout, peakTimes } from "../src/scenes/pins/physics";
import { ASSETS } from "./lib/paths";

const SR = 48000;
const PENTA = [0, 2, 4, 7, 9];
const midiHz = (m: number) => 440 * Math.pow(2, (m - 69) / 12);

export function generatePinAudio(reel: Reel): string {
  const params = pinSchema.parse(reel.illusion.props);
  const tl = timeline(reel);
  const L = params.loopSec || tl.total / tl.fps;
  const p = { ...params, loopSec: L };
  const pins = layout(p);
  const n = Math.ceil(L * SR);
  const Lc = new Float32Array(n), Rc = new Float32Array(n);
  const offset = params.startAt * L; // pin time = video time + offset
  const noteLen = Math.round(0.5 * SR);
  let notes = 0;

  pins.forEach((pin, i) => {
    if (i % params.voiceEvery !== 0) return;
    // scale degree from position: sweeps across the wall become runs, rings become chords
    const deg = Math.round((pin.u + 1) * 3 + (1 - pin.v) * 2.5);
    const midi = params.rootNote + 12 * Math.floor(deg / 5) + PENTA[((deg % 5) + 5) % 5];
    const f = midiHz(midi);
    const pan = 0.5 + 0.4 * (pin.x - pin.z) / (params.grid * params.spacing);
    const amp = 0.02 * (0.6 + 0.4 * pin.target);
    for (const tp of peakTimes(pin, p)) {
      const s0 = Math.round((((tp - offset) % L) + L) % L * SR);
      notes++;
      for (let k = 0; k < noteLen; k++) {
        const t = k / SR;
        const env = Math.exp(-t * 7) * Math.min(1, t * 900);
        const v = (Math.sin(2 * Math.PI * f * t) + 0.25 * Math.sin(4 * Math.PI * f * t) * Math.exp(-t * 12)) * env * amp;
        const j = (s0 + k) % n;
        Lc[j] += v * (1 - pan);
        Rc[j] += v * pan;
      }
    }
  });

  // chord swell when the picture forms (pin time L/2)
  const center = (((L / 2 - offset) % L) + L) % L;
  const chord = [0, 7, 14, 16, 24].map((s) => midiHz(params.rootNote - 12 + s));
  for (let k = Math.round((center - 3) * SR); k < Math.round((center + 4) * SR); k++) {
    const t = k / SR - center;
    const env = Math.exp(-((t / (t < 0 ? 1.6 : 2.2)) ** 2));
    let v = 0;
    chord.forEach((f, ci) => (v += Math.sin(2 * Math.PI * f * t * (1 + ci * 0.0007)) / chord.length));
    const j = ((k % n) + n) % n;
    Lc[j] += v * env * 0.22;
    Rc[j] += v * env * 0.22;
  }

  // gentle limiter + normalise to -1 dBFS (loudness is set later in the pipeline)
  let peak = 1e-9;
  for (let i = 0; i < n; i++) {
    Lc[i] = Math.tanh(Lc[i] * 1.2);
    Rc[i] = Math.tanh(Rc[i] * 1.2);
    peak = Math.max(peak, Math.abs(Lc[i]), Math.abs(Rc[i]));
  }
  const g = 0.89 / peak, data = Buffer.alloc(n * 4);
  for (let i = 0; i < n; i++) {
    data.writeInt16LE(Math.round(Lc[i] * g * 32767), i * 4);
    data.writeInt16LE(Math.round(Rc[i] * g * 32767), i * 4 + 2);
  }
  const h = Buffer.alloc(44);
  h.write("RIFF", 0); h.writeUInt32LE(36 + data.length, 4); h.write("WAVE", 8); h.write("fmt ", 12);
  h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(2, 22); h.writeUInt32LE(SR, 24);
  h.writeUInt32LE(SR * 4, 28); h.writeUInt16LE(4, 32); h.writeUInt16LE(16, 34); h.write("data", 36); h.writeUInt32LE(data.length, 40);
  const rel = `generated/${reel.id}-melody.wav`;
  mkdirSync(join(ASSETS, "generated"), { recursive: true });
  writeFileSync(join(ASSETS, rel), Buffer.concat([h, data]));
  console.log(`wrote assets/${rel} (${notes} pin notes, chord at ${center.toFixed(2)} s)`);
  return rel;
}
