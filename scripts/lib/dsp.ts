// Small DSP helpers for the in-house audio generators (deterministic, no dependencies).
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";

export const SR = 48000;
export type Stereo = [Float32Array, Float32Array];

export const stereo = (sec: number): Stereo => [new Float32Array(Math.ceil(sec * SR)), new Float32Array(Math.ceil(sec * SR))];
export const midiHz = (m: number) => 440 * Math.pow(2, (m - 69) / 12);

export class Biquad {
  private x1 = 0; private x2 = 0; private y1 = 0; private y2 = 0;
  private b0 = 0; private b1 = 0; private b2 = 0; private a1 = 0; private a2 = 0;
  set(type: "bp" | "lp" | "hp", f: number, q: number) {
    const w = (2 * Math.PI * Math.min(Math.max(f, 10), SR * 0.45)) / SR, a = Math.sin(w) / (2 * q), c = Math.cos(w), a0 = 1 + a;
    if (type === "bp") { this.b0 = a / a0; this.b1 = 0; this.b2 = -a / a0; }
    else if (type === "lp") { this.b0 = (1 - c) / 2 / a0; this.b1 = (1 - c) / a0; this.b2 = (1 - c) / 2 / a0; }
    else { this.b0 = (1 + c) / 2 / a0; this.b1 = -(1 + c) / a0; this.b2 = (1 + c) / 2 / a0; }
    this.a1 = (-2 * c) / a0; this.a2 = (1 - a) / a0;
    return this;
  }
  run(x: number) {
    const y = this.b0 * x + this.b1 * this.x1 + this.b2 * this.x2 - this.a1 * this.y1 - this.a2 * this.y2;
    this.x2 = this.x1; this.x1 = x; this.y2 = this.y1; this.y1 = y;
    return y;
  }
}

/** Adds `fn(t)` (mono, t = seconds since start) into the buffer at `start`, wrapping around for seamless loops. */
export function addWrapped(out: Stereo, start: number, sec: number, pan: number, fn: (t: number, i: number) => number) {
  const [L, R] = out, n = L.length, s0 = Math.round(start * SR), len = Math.round(sec * SR);
  const gl = Math.cos((pan * Math.PI) / 2), gr = Math.sin((pan * Math.PI) / 2);
  for (let i = 0; i < len; i++) {
    const v = fn(i / SR, i);
    const k = (((s0 + i) % n) + n) % n;
    L[k] += v * gl;
    R[k] += v * gr;
  }
}

/** Soft limiter + peak normalise to -1 dBFS, write 16-bit stereo WAV. */
export function writeWav(path: string, [L, R]: Stereo, drive = 1.2) {
  let peak = 1e-9;
  for (let i = 0; i < L.length; i++) {
    L[i] = Math.tanh(L[i] * drive);
    R[i] = Math.tanh(R[i] * drive);
    peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i]));
  }
  const g = 0.89 / peak, data = Buffer.alloc(L.length * 4);
  for (let i = 0; i < L.length; i++) {
    data.writeInt16LE(Math.round(L[i] * g * 32767), i * 4);
    data.writeInt16LE(Math.round(R[i] * g * 32767), i * 4 + 2);
  }
  const h = Buffer.alloc(44);
  h.write("RIFF", 0); h.writeUInt32LE(36 + data.length, 4); h.write("WAVE", 8); h.write("fmt ", 12);
  h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(2, 22); h.writeUInt32LE(SR, 24);
  h.writeUInt32LE(SR * 4, 28); h.writeUInt16LE(4, 32); h.writeUInt16LE(16, 34); h.write("data", 36); h.writeUInt32LE(data.length, 40);
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, Buffer.concat([h, data]));
}

/**
 * Freeverb-style stereo reverb (8 damped combs + 4 allpasses per side). Loop-aware: the dry buffer is processed
 * twice in a row and the second pass is kept, so tails from the end of the loop ring into its start.
 */
export function reverb([L, R]: Stereo, opts: { room?: number; damp?: number; wet?: number; preDelayMs?: number } = {}) {
  const room = opts.room ?? 0.84, damp = opts.damp ?? 0.35, wet = opts.wet ?? 0.3;
  const sc = SR / 44100, spread = 23;
  const combs = [1116, 1188, 1277, 1356, 1422, 1491, 1557, 1617], alls = [556, 441, 341, 225];
  const pre = Math.round(((opts.preDelayMs ?? 18) / 1000) * SR);
  const n = L.length;
  const side = (input: Float32Array, off: number) => {
    const cb = combs.map((d) => ({ buf: new Float32Array(Math.round((d + off) * sc)), i: 0, store: 0 }));
    const ab = alls.map((d) => ({ buf: new Float32Array(Math.round((d + off) * sc)), i: 0 }));
    const out = new Float32Array(n);
    for (let pass = 0; pass < 2; pass++)
      for (let k = 0; k < n; k++) {
        const x = input[(k - pre + n) % n] * 0.015;
        let y = 0;
        for (const c of cb) {
          const o = c.buf[c.i];
          c.store = o * (1 - damp) + c.store * damp;
          c.buf[c.i] = x + c.store * room;
          c.i = (c.i + 1) % c.buf.length;
          y += o;
        }
        for (const a of ab) {
          const o = a.buf[a.i];
          a.buf[a.i] = y + o * 0.5;
          a.i = (a.i + 1) % a.buf.length;
          y = o - y;
        }
        if (pass === 1) out[k] = y;
      }
    return out;
  };
  const wl = side(L, 0), wr = side(R, spread);
  for (let k = 0; k < n; k++) {
    L[k] = L[k] * (1 - wet * 0.5) + wl[k] * wet * 3;
    R[k] = R[k] * (1 - wet * 0.5) + wr[k] * wet * 3;
  }
}
