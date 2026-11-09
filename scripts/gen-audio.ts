// In-house music bed + SFX, synthesised from code (seeded, so identical every run). No licensing needed.
// Writes to assets/music and assets/sfx. Run: `npm run assets` (render runs it automatically if files are missing).
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { rng } from "../src/core/seed";
import { ROOT } from "./lib/paths";

const SR = 48000;
type Stereo = [Float32Array, Float32Array];

const buf = (sec: number): Stereo => [new Float32Array(Math.round(sec * SR)), new Float32Array(Math.round(sec * SR))];
const midi = (n: number) => 440 * Math.pow(2, (n - 69) / 12);

class Biquad {
  private x1 = 0; private x2 = 0; private y1 = 0; private y2 = 0;
  private b0 = 0; private b1 = 0; private b2 = 0; private a1 = 0; private a2 = 0;
  set(type: "bp" | "lp", f: number, q: number) {
    const w = (2 * Math.PI * Math.min(f, SR * 0.45)) / SR, a = Math.sin(w) / (2 * q), c = Math.cos(w), a0 = 1 + a;
    if (type === "bp") { this.b0 = a / a0; this.b1 = 0; this.b2 = -a / a0; }
    else { this.b0 = (1 - c) / 2 / a0; this.b1 = (1 - c) / a0; this.b2 = (1 - c) / 2 / a0; }
    this.a1 = (-2 * c) / a0; this.a2 = (1 - a) / a0;
  }
  run(x: number) {
    const y = this.b0 * x + this.b1 * this.x1 + this.b2 * this.x2 - this.a1 * this.y1 - this.a2 * this.y2;
    this.x2 = this.x1; this.x1 = x; this.y2 = this.y1; this.y1 = y;
    return y;
  }
}

function writeWav(path: string, [l, r]: Stereo) {
  let peak = 1e-9;
  for (let i = 0; i < l.length; i++) peak = Math.max(peak, Math.abs(l[i]), Math.abs(r[i]));
  const g = 0.89 / peak; // -1 dBFS peak; final loudness is set after the mix
  const data = Buffer.alloc(l.length * 4);
  for (let i = 0; i < l.length; i++) {
    data.writeInt16LE(Math.round(Math.max(-1, Math.min(1, l[i] * g)) * 32767), i * 4);
    data.writeInt16LE(Math.round(Math.max(-1, Math.min(1, r[i] * g)) * 32767), i * 4 + 2);
  }
  const h = Buffer.alloc(44);
  h.write("RIFF", 0); h.writeUInt32LE(36 + data.length, 4); h.write("WAVE", 8); h.write("fmt ", 12);
  h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(2, 22); h.writeUInt32LE(SR, 24);
  h.writeUInt32LE(SR * 4, 28); h.writeUInt16LE(4, 32); h.writeUInt16LE(16, 34); h.write("data", 36); h.writeUInt32LE(data.length, 40);
  writeFileSync(path, Buffer.concat([h, data]));
  console.log("wrote", path);
}

/** Simple stereo feedback-delay "room" so things don't sound dry and synthetic. */
function room([l, r]: Stereo, mix = 0.25) {
  const taps = [[0.0297, 0.0371], [0.0411, 0.0437], [0.0533, 0.0491]].map(([a, b]) => [Math.round(a * SR), Math.round(b * SR)]);
  const ol = new Float32Array(l), or = new Float32Array(r);
  for (const [dl, dr] of taps)
    for (let i = 0; i < l.length; i++) {
      if (i >= dl) ol[i] += 0.55 * ol[i - dl] * mix;
      if (i >= dr) or[i] += 0.55 * or[i - dr] * mix;
    }
  l.set(ol); r.set(or);
}

/** Calm, slightly mysterious pad (D minor colour) with soft plucked chord tones. 40 s. */
function bed(seed: number): Stereo {
  const sec = 40, out = buf(sec), [L, R] = out, rand = rng(seed, "bed");
  const chords = [[50, 57, 60, 64, 65], [46, 53, 57, 62], [53, 60, 64, 69], [48, 55, 58, 62, 64]];
  const chordLen = 5;
  for (let c = 0; c < sec / chordLen; c++) {
    const notes = chords[c % chords.length];
    const t0 = c * chordLen;
    for (const n of notes) {
      const f = midi(n), det = 1 + (rand() - 0.5) * 0.004, ph = rand() * 6.28;
      const start = Math.round(Math.max(0, t0 - 1) * SR), end = Math.min(L.length, Math.round((t0 + chordLen + 1.5) * SR));
      for (let i = start; i < end; i++) {
        const t = i / SR - (t0 - 1);
        const env = Math.min(1, t / 1.8) * Math.min(1, Math.max(0, (chordLen + 2.5 - t) / 2));
        const vib = 1 + 0.0015 * Math.sin(2 * Math.PI * 4.8 * t);
        const w = 2 * Math.PI * f * vib * (i / SR);
        const v = (Math.sin(w + ph) + 0.28 * Math.sin(2 * w) + 0.1 * Math.sin(3 * w)) * env * 0.06;
        L[i] += v * 0.6;
        R[i] += 0.6 * (Math.sin(w * det + ph) + 0.28 * Math.sin(2 * w * det)) * env * 0.06;
      }
    }
    // plucks: eighth notes at 96 BPM, chord tones up an octave
    const step = 60 / 96 / 2;
    for (let k = 0; k < chordLen / step; k++) {
      if (rand() < 0.35) continue;
      const n = notes[Math.floor(rand() * notes.length)] + 12;
      const f = midi(n), s0 = Math.round((t0 + k * step) * SR), pan = 0.3 + rand() * 0.4;
      for (let i = 0; i < SR * 1.2 && s0 + i < L.length; i++) {
        const t = i / SR, env = Math.exp(-t * 5) * Math.min(1, t * 400);
        const v = (Math.sin(2 * Math.PI * f * t) + 0.2 * Math.sin(4 * Math.PI * f * t)) * env * 0.035;
        L[s0 + i] += v * (1 - pan); R[s0 + i] += v * pan;
      }
    }
  }
  // airy noise bed
  const bl = new Biquad(), br = new Biquad();
  for (let i = 0; i < L.length; i++) {
    if (i % 256 === 0) { const f = 1800 + 900 * Math.sin(i / SR * 0.3); bl.set("bp", f, 0.7); br.set("bp", f * 1.1, 0.7); }
    L[i] += bl.run(rand() * 2 - 1) * 0.012; R[i] += br.run(rand() * 2 - 1) * 0.012;
  }
  room(out, 0.35);
  // 1.5 s fade in/out so the bed can loop with the reel
  for (let i = 0; i < L.length; i++) {
    const t = i / SR, g = Math.min(1, t / 0.4) * Math.min(1, (sec - t) / 1.5);
    L[i] *= g; R[i] *= g;
  }
  return out;
}

function riser(seed: number): Stereo {
  const sec = 2.2, out = buf(sec), [L, R] = out, rand = rng(seed, "riser"), bl = new Biquad(), br = new Biquad();
  let ph = 0;
  for (let i = 0; i < L.length; i++) {
    const p = i / L.length, f = 300 * Math.pow(12, p);
    if (i % 64 === 0) { bl.set("bp", f * 2, 2.5); br.set("bp", f * 2.1, 2.5); }
    ph += (2 * Math.PI * f) / SR;
    const env = Math.pow(p, 2.2);
    const tone = Math.sin(ph) * 0.25 + Math.sin(ph * 1.5) * 0.12;
    L[i] = (bl.run(rand() * 2 - 1) * 1.6 + tone) * env;
    R[i] = (br.run(rand() * 2 - 1) * 1.6 + tone) * env;
  }
  room(out, 0.3);
  return out;
}

function impact(seed: number): Stereo {
  const sec = 2.5, out = buf(sec), [L, R] = out, rand = rng(seed, "impact"), lp = new Biquad();
  let ph = 0;
  for (let i = 0; i < L.length; i++) {
    const t = i / SR, f = 38 + 70 * Math.exp(-t * 9);
    ph += (2 * Math.PI * f) / SR;
    if (i % 64 === 0) lp.set("lp", 200 + 5000 * Math.exp(-t * 14), 0.7);
    const boom = Math.sin(ph) * Math.exp(-t * 2.4) * Math.min(1, t * 2000);
    const crack = lp.run(rand() * 2 - 1) * Math.exp(-t * 7) * 0.7;
    L[i] = boom + crack; R[i] = boom + crack * 0.9;
  }
  room(out, 0.45);
  return out;
}

function whoosh(seed: number): Stereo {
  const sec = 1.2, out = buf(sec), [L, R] = out, rand = rng(seed, "whoosh"), bl = new Biquad(), br = new Biquad();
  for (let i = 0; i < L.length; i++) {
    const p = i / L.length, f = 400 + 3000 * Math.sin(Math.PI * p);
    if (i % 64 === 0) { bl.set("bp", f, 1.4); br.set("bp", f * 1.15, 1.4); }
    const env = Math.pow(Math.sin(Math.PI * p), 2);
    L[i] = bl.run(rand() * 2 - 1) * env * (1 - 0.5 * p);
    R[i] = br.run(rand() * 2 - 1) * env * (0.5 + 0.5 * p);
  }
  return out;
}

export function generateInhouseAudio() {
  const music = join(ROOT, "assets/music"), sfx = join(ROOT, "assets/sfx");
  mkdirSync(music, { recursive: true });
  mkdirSync(sfx, { recursive: true });
  writeWav(join(music, "inhouse-bed-a.wav"), bed(7));
  writeWav(join(sfx, "inhouse-riser.wav"), riser(7));
  writeWav(join(sfx, "inhouse-impact.wav"), impact(7));
  writeWav(join(sfx, "inhouse-whoosh.wav"), whoosh(7));
}

if (/gen-audio\.ts$/.test(process.argv[1] ?? "")) generateInhouseAudio();
