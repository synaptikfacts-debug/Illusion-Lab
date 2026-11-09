// ASMR click track for a bounceField reel: one glassy "tock" per orb impact, computed from the same physics
// as the picture, so every click lands exactly on its frame. Writes assets/generated/<reel-id>-bounces.wav.
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { bounceSchema } from "../src/illusions/bounceField/schema";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { impactTimes, layout } from "../src/scenes/bounce/physics";
import { ASSETS } from "./lib/paths";

const SR = 48000;

export function bounceAudioPath(id: string) {
  return `generated/${id}-bounces.wav`;
}

export function generateBounceAudio(reel: Reel): string {
  const params = bounceSchema.parse(reel.illusion.props);
  const tl = timeline(reel);
  const loopSec = params.loopSec || tl.total / tl.fps;
  const bp = { ...params, loopSec };
  if (bp.baseBounces <= Math.PI * bp.spread) throw new Error("bounceField: baseBounces must be > pi * spread");
  const orbs = layout(bp, reel.seed);
  const n = Math.ceil(loopSec * SR);
  const L = new Float32Array(n), R = new Float32Array(n);
  const r = rng(reel.seed, "clicks");
  // one click shape per orb: pitch from size + ring (glass marbles ~1.8-4.5 kHz), short decay
  const len = Math.round(0.045 * SR);
  for (const o of orbs) {
    const f0 = 1800 + 2600 * (1 - o.r01) * 0.6 + r() * 900;
    const f1 = f0 * (2.4 + r() * 0.6);
    const amp = 0.035 * (0.7 + r() * 0.6);
    const pan = 0.5 + 0.45 * (o.x / params.discRadius);
    const jitter = Math.round(r() * 0.0015 * SR); // a hair of spread so rings rattle instead of one hard hit
    for (const t of impactTimes(o, bp)) {
      const s0 = Math.round(t * SR) + jitter;
      for (let i = 0; i < len; i++) {
        const k = (s0 + i) % n; // wraps: clicks near the loop point continue at the start
        const tt = i / SR;
        const env = Math.exp(-tt * 140) * Math.min(1, tt * 8000);
        const v = (Math.sin(2 * Math.PI * f0 * tt) + 0.35 * Math.sin(2 * Math.PI * f1 * tt) * Math.exp(-tt * 260)) * env * amp;
        L[k] += v * (1 - pan);
        R[k] += v * pan;
      }
    }
  }
  // soft-knee limiter so dense moments (whole rings landing together) don't clip harshly
  let peak = 1e-9;
  for (let i = 0; i < n; i++) {
    L[i] = Math.tanh(L[i] * 1.5);
    R[i] = Math.tanh(R[i] * 1.5);
    peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i]));
  }
  const g = 0.89 / peak, data = Buffer.alloc(n * 4);
  for (let i = 0; i < n; i++) {
    data.writeInt16LE(Math.round(L[i] * g * 32767), i * 4);
    data.writeInt16LE(Math.round(R[i] * g * 32767), i * 4 + 2);
  }
  const h = Buffer.alloc(44);
  h.write("RIFF", 0); h.writeUInt32LE(36 + data.length, 4); h.write("WAVE", 8); h.write("fmt ", 12);
  h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(2, 22); h.writeUInt32LE(SR, 24);
  h.writeUInt32LE(SR * 4, 28); h.writeUInt16LE(4, 32); h.writeUInt16LE(16, 34); h.write("data", 36); h.writeUInt32LE(data.length, 40);
  const rel = bounceAudioPath(reel.id);
  mkdirSync(join(ASSETS, "generated"), { recursive: true });
  writeFileSync(join(ASSETS, rel), Buffer.concat([h, data]));
  const impacts = orbs.length * bp.baseBounces;
  console.log(`wrote assets/${rel} (${orbs.length} orbs, ${impacts} clicks)`);
  return rel;
}
