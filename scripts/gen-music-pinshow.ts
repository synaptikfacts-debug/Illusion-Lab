// Score for "Singing Pins: The Show" (owner, Nov 11: "sounds not enough, looks boring and unfinished").
// The pins SING: every wave crest that leaves the centre of the wall plays one soft felt-piano note from the current
// chord (a slow rising arpeggio that follows the picture exactly), over warm sustained strings in D major. Each
// picture locking in blooms a full piano chord with a high sparkle; the melt resolves on D major and rings out.
// Salamander felt piano (CC BY 3.0, credited in captions), VSCO-2 strings (CC0).
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { timeline } from "../src/core/timing";
import { layoutShow, lockTimes, phaseAt, SHOW } from "../src/scenes/pins/show";
import { reverb, SR, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, piano, play } from "./lib/sampler";

export function pinShowCrests(): number[] {
  const pins = layoutShow();
  const centre = pins.reduce((a, b) => (b.dist < a.dist ? b : a));
  const out: number[] = [];
  const dt = 0.002;
  let prev = phaseAt(centre, 0) - 0.5;
  for (let t = dt; t < SHOW.fade[0]; t += dt) {
    const cur = phaseAt(centre, t) - 0.5;
    if (Math.floor(cur) !== Math.floor(prev)) out.push(t - dt / 2);
    prev = cur;
  }
  return out;
}

export function generatePinShowMusic(reel: Reel): string {
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const out = stereo(total);
  const r = rng(reel.seed, "pinshow-music");
  const P = (m: number, at: number, g: number, pan = 0.5, dur = 2.5, rel = 1.8) => play(out, piano(m, true), at + (r() - 0.5) * 0.015, g, pan, dur, rel, 0.8);
  const Str = (inst: string, m: number, at: number, g: number, dur: number, pan = 0.5) => play(out, orch(inst, m, true), at, g, pan, dur, 2.0, 0.7);

  const locks = lockTimes();
  const end = SHOW.fade[1];
  // chord plan: [start time, root (bass), chord tones (for the arpeggio)] - D major, warm, no tension
  const plan: [number, number, number[]][] = [
    [0, 38, [62, 66, 69, 73, 76]], // Dmaj9
    [locks[0], 47, [62, 66, 69, 71, 74]], // Bm7(11)
    [locks[0] + 6.5, 43, [62, 66, 67, 71, 74]], // Gmaj7
    [locks[1], 40, [62, 64, 67, 71, 74]], // Em9
    [locks[1] + 6.5, 42, [61, 64, 66, 69, 73]], // F#m7
    [locks[2], 43, [62, 66, 69, 71, 74]], // Gmaj9 (6/9)
    [locks[2] + 6, 45, [62, 64, 69, 71, 76]], // Asus
    [locks[3], 38, [62, 66, 69, 73, 78]], // D major: the mandala, resolution
  ];
  const chordAt = (t: number) => { let c = plan[0]; for (const p of plan) if (t >= p[0] - 0.05) c = p; return c; };

  // strings: one long chord per plan entry
  plan.forEach(([t0, root, tones], i) => {
    const t1 = i + 1 < plan.length ? plan[i + 1][0] : end;
    const len = t1 - t0 + 0.4;
    Str("celli", root + 12, t0, 0.05, len, 0.42);
    Str("violas", tones[1], t0 + 0.15, 0.032, len, 0.58);
    if (i >= 3) Str("violins", tones[3] + 12, t0 + 0.3, 0.018, len, 0.66);
    P(root, t0, 0.09, 0.45, Math.min(4, len), 2.0);
  });

  // the pins sing: one note per wave crest, rising through the chord, wrapping back down
  let idx = 0, last = -1, prevChord: number[] | null = null;
  for (const t of pinShowCrests()) {
    if (t - last < 0.28 || locks.some((l) => Math.abs(t - l) < 0.5) || t > locks[3] + 1) continue;
    last = t;
    const tones = chordAt(t)[2];
    if (tones !== prevChord) { idx = 0; prevChord = tones; }
    const m = tones[idx % tones.length] + (Math.floor(idx / tones.length) % 2 ? 12 : 0);
    P(m, t, 0.06, 0.35 + 0.3 * ((idx % 3) / 2), 1.4, 1.4);
    idx++;
  }

  // each picture locks in: a soft chord bloom and a high sparkle
  locks.forEach((l, k) => {
    const tones = chordAt(l + 0.1)[2];
    tones.slice(0, 4).forEach((m, j) => P(m + 12, l + 0.05 + j * 0.09, 0.055, 0.35 + 0.1 * j, 3.0, 2.5));
    P(tones[4] + 24, l + 0.5, 0.035, 0.7, 2.5, 2.5);
    if (k === locks.length - 1) P(tones[2] + 24, l + 0.9, 0.03, 0.3, 3, 3);
  });

  // the melt: a slow descending line back to D, then ring out through the fade
  const m0 = locks[3] + SHOW.hold;
  [81, 78, 76, 74].forEach((m, j) => P(m, m0 + j * 1.3, 0.05, 0.4 + 0.08 * j, 2.4, 2.2));
  P(38, m0 + 5.4, 0.1, 0.45, 6, 3);
  [62, 66, 69, 74].forEach((m, j) => P(m, m0 + 5.5 + j * 0.14, 0.05, 0.4 + 0.06 * j, 6, 3));

  reverb(out, { room: 0.9, damp: 0.45, wet: 0.34, preDelayMs: 22, loop: false });
  const f0 = Math.round(SHOW.fade[0] * SR), f1 = Math.round(SHOW.fade[1] * SR);
  for (let k = f0; k < out[0].length; k++) {
    const g = k >= f1 ? 0 : (1 - (k - f0) / (f1 - f0)) ** 1.5;
    out[0][k] *= g;
    out[1][k] *= g;
  }
  const rel = `generated/${reel.id}-music.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (singing-pins score, D major)`);
  return rel;
}
