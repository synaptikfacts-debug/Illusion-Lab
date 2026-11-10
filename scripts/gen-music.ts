// Calm, satisfying background track for the YouTube version (owner rule: music only on YouTube; owner feedback
// Nov 9: "calm and satisfying, not AI slop"). Real recorded instruments: soft felt piano (Salamander Grand),
// VSCO-2 violas/celli bed and harp. Slow tempo, lush reverb, gentle humanised timing, one simple melody.
// A harp glissando rises into `dropAt` (the reel's big moment) and a soft high chord blooms there.
// Length = reel length and every note wraps around the end, so the track loops seamlessly.
import { join } from "node:path";
import type { Reel } from "../src/core/schema";
import { rng } from "../src/core/seed";
import { resolveTime, timeline } from "../src/core/timing";
import { reverb, stereo, writeWav } from "./lib/dsp";
import { ASSETS } from "./lib/paths";
import { orch, piano, play } from "./lib/sampler";
import { generateStoryMusic } from "./gen-music-story";
import { generateDominoMusic } from "./gen-music-domino";
import { generateFaceMusic } from "./gen-music-face";
import { generateLiquidMusic } from "./gen-music-liquid";
import { generateSandMusic } from "./gen-music-sand";
import { generateGaltonMusic } from "./gen-music-galton";
import { generateOrbMusic } from "./gen-music-orbs";

// key of F: Fmaj7, Am7, Dm9, Bbmaj9 ... ending on Csus4, which resolves into Fmaj7 at the loop point
const CHORDS: { root: number; tones: number[] }[] = [
  { root: 41, tones: [0, 4, 7, 11] }, // Fmaj7
  { root: 45, tones: [0, 3, 7, 10] }, // Am7
  { root: 38, tones: [0, 3, 7, 10, 14] }, // Dm9
  { root: 46, tones: [0, 4, 7, 11, 14] }, // Bbmaj9
];
const LAST = { root: 48, tones: [0, 5, 7, 10] }; // C7sus4
const MELODY = [[0, 4], [2, 3], [1, 4], [3, 2]]; // per chord: [tone index, beat] pairs, one note each half

export function generateMusic(reel: Reel): string {
  const cfg = reel.audio.musicGen!;
  if (cfg.style === "rodStory") return generateStoryMusic(reel);
  if (cfg.style === "dominoStory") return generateDominoMusic(reel);
  if (cfg.style === "faceStory") return generateFaceMusic(reel);
  if (cfg.style === "liquid") return generateLiquidMusic(reel);
  if (cfg.style === "sand") return generateSandMusic(reel);
  if (cfg.style === "galton") return generateGaltonMusic(reel);
  if (cfg.style === "orbs") return generateOrbMusic(reel);
  const tl = timeline(reel);
  const total = tl.total / tl.fps;
  const bpm = cfg.bpm > 90 ? 72 : cfg.bpm; // calm by default
  const bars = Math.max(1, Math.round(total / ((60 / bpm) * 4)));
  const bar = total / bars, beat = bar / 4; // stretch slightly so bars fill the loop exactly
  const out = stereo(total);
  const r = rng(cfg.seed, reel.id, "calm");
  const human = () => (r() - 0.5) * 0.02; // +-10 ms
  const bloom = cfg.dropAt !== undefined ? resolveTime(cfg.dropAt, tl) / tl.fps : -1;
  const up = (m: number, min: number) => { while (m < min) m += 12; return m; };

  for (let b = 0; b < bars; b++) {
    const ch = b === bars - 1 && bars > 2 ? LAST : CHORDS[b % CHORDS.length];
    const t0 = b * bar;
    // left hand: low root, fifth on beat 3
    play(out, piano(ch.root), t0 + human(), 0.55, 0.42, bar * 0.95, 1.2, 0.6);
    play(out, piano(ch.root + 7), t0 + 2 * beat + human(), 0.32, 0.45, bar * 0.45, 1.0, 0.6);
    // right hand: slow broken chord in 8ths, some rests so it breathes
    const rh = ch.tones.map((t) => up(ch.root + t, 60)).sort((a, b2) => a - b2);
    const gates = [1, 0, 1, 1, 0, 1, 1, 0];
    gates.forEach((g, k) => {
      if (!g) return;
      const note = rh[(k + b) % rh.length] + (k >= 6 ? 12 : 0);
      play(out, piano(note), t0 + k * beat * 0.5 + human(), 0.22 + r() * 0.1, 0.38 + r() * 0.24, beat * 0.9, 0.9, 0.65);
    });
    // melody: two soft notes per bar, an octave above the arpeggio
    const m = MELODY[b % MELODY.length];
    play(out, piano(up(ch.root + ch.tones[m[0] % ch.tones.length], 72)), t0 + human(), 0.3, 0.55, bar * 0.45, 1.4, 0.5);
    play(out, piano(up(ch.root + ch.tones[m[1] % ch.tones.length], 72)), t0 + 2 * beat + 0.5 * beat + human(), 0.26, 0.55, bar * 0.4, 1.4, 0.5);
    // string bed: violas on the 3rd/5th, celli on the root, very soft
    play(out, orch("celli", ch.root + 12), t0, 0.16, 0.35, bar, 1.6, 0.4);
    play(out, orch("violas", up(ch.root + ch.tones[1], 57)), t0, 0.12, 0.65, bar, 1.6, 0.4);
  }

  if (bloom >= 0) {
    // harp glissando up the bar's chord, landing on the big moment
    const b = Math.min(bars - 1, Math.floor(bloom / bar));
    const ch = CHORDS[b % CHORDS.length];
    const notes: number[] = [];
    for (let o = 0; o < 3; o++) for (const t of ch.tones) notes.push(ch.root + 12 + t + o * 12);
    const gl = notes.filter((n) => n <= 96).slice(0, 14);
    gl.forEach((n, i) => play(out, orch("harp", n), bloom - 1.2 + (i / gl.length) * 1.2, 0.3, 0.3 + (i / gl.length) * 0.4));
    // soft high chord blooms on the moment
    for (const t of ch.tones.slice(0, 4)) play(out, piano(up(ch.root + t, 76)), bloom + human(), 0.2, 0.5, 2.5, 2.0, 0.55);
    play(out, orch("violins", up(ch.root + ch.tones[2], 67), true), bloom - 0.4, 0.1, 0.6, 3.2, 2.0, 0.5);
  }

  reverb(out, { room: 0.88, damp: 0.4, wet: 0.38, preDelayMs: 22 });
  const rel = `generated/${reel.id}-music.wav`;
  writeWav(join(ASSETS, rel), out, 1.0);
  console.log(`wrote assets/${rel} (calm piano/strings/harp, ${bars} bars at ~${Math.round(60 / beat)} BPM${bloom >= 0 ? `, harp bloom at ${bloom.toFixed(2)} s` : ""})`);
  return rel;
}
