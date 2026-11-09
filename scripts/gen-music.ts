// Catchy in-house background track for the YouTube version (owner rule: music only on YouTube).
// Four-on-the-floor groove in a minor key, vi-IV-I-V progression, a hooky 16th-note pluck riff, offbeat bass,
// pumping (side-chained) pad. The bar before `dropAt` is a breakdown (drums out, riser), the groove drops back
// in on the next bar. Length = reel length; every note wraps around the end, so the track loops seamlessly.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { resolveTime, timeline } from "../src/core/timing";
import { addWrapped, Biquad, midiHz, SR, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";

export function generateMusic(reel: Reel): string {
  const cfg = reel.audio.musicGen!;
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const beat = 60 / cfg.bpm, bar = beat * 4, s16 = beat / 4;
  const bars = Math.round(total / bar);
  const out = stereo(total);
  const r = rng(cfg.seed, reel.id, "music");
  const root = cfg.key; // e.g. 57 = A3
  // vi-IV-I-V in the minor key (Am F C G), chord tones as semitones from root
  const chords = [[0, 3, 7], [-4, 0, 3], [3, 7, 10], [-2, 2, 5]];
  const dropBar = cfg.dropAt !== undefined ? Math.ceil(resolveTime(cfg.dropAt, tl) / tl.fps / bar) : -1;
  const breakdown = (b: number) => b === dropBar - 1;

  // hook riff: indexes into [chord tones + octave], -1 = rest. Same shape every bar -> earworm.
  const riff = [0, -1, 2, 1, -1, 2, 3, -1, 2, -1, 1, 0, -1, 2, 3, 2];

  for (let b = 0; b < bars; b++) {
    const t0 = b * bar, ch = chords[b % 4];
    const bd = breakdown(b);
    const tones = [...ch, ch[0] + 12].map((s) => root + s);

    // drums
    if (!bd) {
      for (let k = 0; k < 4; k++) {
        addWrapped(out, t0 + k * beat, 0.4, 0.5, (t) => {
          const f = 48 + 110 * Math.exp(-t * 32);
          return Math.sin(2 * Math.PI * f * t - 0.02 * Math.exp(-t * 32)) * Math.exp(-t * 7) * 0.9;
        });
      }
      for (const k of [1, 3]) {
        const bp = new Biquad().set("bp", 1500, 0.9);
        addWrapped(out, t0 + k * beat, 0.25, 0.5, (t) => {
          const env = Math.exp(-t * 26) + 0.6 * Math.exp(-Math.max(0, t - 0.012) * 30) * (t > 0.012 ? 1 : 0);
          return bp.run(r() * 2 - 1) * env * 0.55;
        });
      }
      for (let k = 0; k < 8; k++) {
        const hp = new Biquad().set("hp", 7000, 0.7);
        const open = k % 2 === 1;
        addWrapped(out, t0 + k * beat * 0.5, open ? 0.12 : 0.04, open ? 0.62 : 0.38, (t) => hp.run(r() * 2 - 1) * Math.exp(-t * (open ? 30 : 90)) * (open ? 0.22 : 0.12));
      }
    } else {
      // riser through the breakdown
      const bp = new Biquad();
      addWrapped(out, t0, bar, 0.5, (t, i) => {
        if (i % 64 === 0) bp.set("bp", 400 * Math.pow(20, t / bar), 3);
        return bp.run(r() * 2 - 1) * Math.pow(t / bar, 2) * 0.5;
      });
    }

    // bass: offbeat 8ths on the chord root (out in the breakdown)
    if (!bd)
      for (let k = 0; k < 4; k++) {
        const f = midiHz(root + ch[0] - 24);
        const lp = new Biquad();
        addWrapped(out, t0 + k * beat + beat / 2, beat * 0.45, 0.5, (t, i) => {
          if (i % 32 === 0) lp.set("lp", 200 + 1400 * Math.exp(-t * 18), 1.2);
          const saw = 2 * ((f * t) % 1) - 1;
          return lp.run(saw) * Math.min(1, t * 400) * Math.exp(-t * 3) * 0.55;
        });
      }

    // hook riff: plucky saw, 16ths, stereo echo (keeps playing in the breakdown, filtered)
    riff.forEach((idx, k) => {
      if (idx < 0) return;
      const f = midiHz(tones[idx] + 12);
      for (const [delay, pan, g] of [[0, 0.5, 1], [s16 * 3, 0.15, 0.35], [s16 * 6, 0.85, 0.2]] as const) {
        const lp = new Biquad();
        addWrapped(out, t0 + k * s16 + delay, 0.3, pan, (t, i) => {
          if (i % 32 === 0) lp.set("lp", (bd ? 900 : 2600) + 5000 * Math.exp(-t * 25), 1.5);
          const saw = 2 * ((f * t) % 1) - 1 + 0.5 * (2 * ((f * 1.005 * t) % 1) - 1);
          return lp.run(saw) * Math.min(1, t * 600) * Math.exp(-t * 14) * 0.16 * g;
        });
      }
    });

    // pad: detuned saw chord, side-chained to the kick (pumps), louder in the breakdown
    const lpL = new Biquad().set("lp", 1400, 0.7), lpR = new Biquad().set("lp", 1400, 0.7);
    const [L, R] = out, n = L.length;
    for (let i = 0; i < Math.round(bar * SR); i++) {
      const t = i / SR;
      const pump = bd ? 0.9 : 0.25 + 0.75 * Math.min(1, (t % beat) / (beat * 0.45));
      let vl = 0, vr = 0;
      for (const s of ch) {
        const f = midiHz(root + s);
        vl += 2 * ((f * 0.997 * t) % 1) - 1;
        vr += 2 * ((f * 1.003 * t) % 1) - 1;
      }
      const k = (Math.round(t0 * SR) + i) % n;
      L[k] += lpL.run(vl) * 0.06 * pump * (bd ? 1.6 : 1);
      R[k] += lpR.run(vr) * 0.06 * pump * (bd ? 1.6 : 1);
    }
  }

  const rel = `generated/${reel.id}-music.wav`;
  writeWav(join(ASSETS, rel), out, 1.1);
  console.log(`wrote assets/${rel} (${cfg.bpm} BPM, ${bars} bars${dropBar >= 0 ? `, breakdown bar ${dropBar}, drop at ${(dropBar * bar).toFixed(2)} s` : ""}, ${SR} Hz)`);
  return rel;
}
