// Plays real recorded instruments into a Stereo buffer (deterministic, offline).
// Piano: Salamander Grand Piano V3 (Alexander Holm, CC BY 3.0) - credit required in the YouTube description.
// Orchestra: VSCO-2 Community Edition via tiny-orchestra (CC0).
// Samples live in ./samples (git-ignored, see README "Setup").
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { SR, type Stereo } from "./dsp";
import { ROOT } from "./paths";

const DIR = join(ROOT, "samples");
const cache = new Map<string, Stereo>();

function decode(file: string): Stereo {
  const hit = cache.get(file);
  if (hit) return hit;
  if (!existsSync(file)) throw new Error(`Missing sample ${file} - see README "Setup: instrument samples"`);
  const raw = execFileSync("ffmpeg", ["-nostdin", "-v", "error", "-i", file, "-f", "f32le", "-ac", "2", "-ar", String(SR), "-"], { maxBuffer: 1 << 28 });
  const f = new Float32Array(raw.buffer, raw.byteOffset, raw.byteLength / 4);
  const n = f.length / 2, L = new Float32Array(n), R = new Float32Array(n);
  for (let i = 0; i < n; i++) { L[i] = f[i * 2]; R[i] = f[i * 2 + 1]; }
  const s: Stereo = [L, R];
  cache.set(file, s);
  return s;
}

interface Voice { sample: Stereo; rate: number; loop?: [number, number] }

const PIANO_NAMES = ["C", "D#", "F#", "A"]; // Salamander is sampled every minor third
function pianoVoice(midi: number, layer: "v6" | "v10"): Voice {
  let best = 0, bestD = 99;
  for (let m = 21; m <= 108; m++) {
    const pc = m % 12;
    if (![0, 3, 6, 9].includes(pc)) continue;
    const d = Math.abs(m - midi);
    if (d < bestD) { bestD = d; best = m; }
  }
  const name = PIANO_NAMES[[0, 3, 6, 9].indexOf(best % 12)] + (Math.floor(best / 12) - 1);
  return { sample: decode(join(DIR, `piano-${layer}`, "audio", `${name}${layer}.mp3`)), rate: Math.pow(2, (midi - best) / 12) };
}

let manifest: { instruments: Record<string, { samples: { file: string; midi?: number; vel?: number; tune?: number; loopStart?: number; loopEnd?: number }[] }> } | null = null;
function orchVoice(instrument: string, midi: number, soft: boolean): Voice {
  manifest ??= JSON.parse(readFileSync(join(DIR, "orchestra", "samples", "manifest.json"), "utf8"));
  const list = manifest!.instruments[instrument].samples;
  const pool = list.filter((s) => (soft ? (s.vel ?? 1) < 0.8 : true));
  const cands = (pool.length ? pool : list).filter((s) => s.midi !== undefined);
  const s = cands.reduce((a, b) => (Math.abs(b.midi! - midi) < Math.abs(a.midi! - midi) ? b : a));
  const rate = Math.pow(2, (midi - s.midi! - (s.tune ?? 0) / 100) / 12);
  return {
    sample: decode(join(DIR, "orchestra", "samples", s.file)),
    rate,
    loop: s.loopStart !== undefined ? [Math.round(s.loopStart * SR), Math.round(s.loopEnd! * SR)] : undefined,
  };
}

export function unpitched(instrument: string, index = 0): Voice {
  manifest ??= JSON.parse(readFileSync(join(DIR, "orchestra", "samples", "manifest.json"), "utf8"));
  const s = manifest!.instruments[instrument].samples[index % manifest!.instruments[instrument].samples.length];
  return { sample: decode(join(DIR, "orchestra", "samples", s.file)), rate: 1 };
}

/**
 * Renders a voice into `out` at `at` seconds (wrapping around the end for loops). `dur` = how long the note is held
 * (sustained instruments loop until then); `release` = fade after dur. `tone` = 0..1 lowpass amount (0 = untouched).
 */
export function play(out: Stereo, v: Voice, at: number, gain: number, pan = 0.5, dur?: number, release = 0.6, tone = 0) {
  const [L, R] = out, n = L.length, [sl, sr] = v.sample;
  const len = sl.length;
  const holdS = dur !== undefined ? dur * SR : Infinity;
  const total = Math.min(dur !== undefined ? (dur + release) * SR : Infinity, v.loop ? Infinity : len / v.rate, 40 * SR);
  const gl = Math.cos((pan * Math.PI) / 2) * gain, gr = Math.sin((pan * Math.PI) / 2) * gain;
  const s0 = Math.round(at * SR);
  const a = tone > 0 ? Math.exp((-2 * Math.PI * (9000 - 7500 * tone)) / SR) : 0; // one-pole lowpass ("felt")
  let yl = 0, yr = 0;
  for (let i = 0; i < total; i++) {
    let pos = i * v.rate;
    if (v.loop && pos >= v.loop[1]) pos = v.loop[0] + ((pos - v.loop[0]) % (v.loop[1] - v.loop[0]));
    const p = Math.floor(pos), fr = pos - p;
    if (p + 1 >= len) break;
    let xl = sl[p] * (1 - fr) + sl[p + 1] * fr, xr = sr[p] * (1 - fr) + sr[p + 1] * fr;
    if (a) { yl = xl * (1 - a) + yl * a; yr = xr * (1 - a) + yr * a; xl = yl; xr = yr; }
    const env = i < holdS ? Math.min(1, i / (0.004 * SR)) : Math.max(0, 1 - (i - holdS) / (release * SR));
    if (i >= holdS && env <= 0) break; // released and faded out
    const k = (s0 + i) % n;
    L[k] += xl * env * gl;
    R[k] += xr * env * gr;
  }
}

export const piano = (midi: number, soft = true) => pianoVoice(midi, soft ? "v6" : "v10");
export const orch = (instrument: string, midi: number, soft = true) => orchVoice(instrument, midi, soft);
