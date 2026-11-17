// 0024 score v3 - ELECTRONIC (owner, Nov 17: "use synths, effects, whatever is needed - orchestral music is absolutely
// unnecessary here"; the busy orchestral/harmony options were "a big mess of notes"). Sparse dark cinematic electronic in
// F minor, every element tied to the picture:
//   0-1.72  inside the sphere: low filtered drone + noise riser + reverse swell -> sub IMPACT on the clack
//   1.72-3.9 dials lock: 16th-note analog arp, filter opens with every lock, sub pulse -> riser into the open
//   3.9     bands explode: big impact, the arp stops, a wide pad blooms (Db), floating
//   5.8-7.0 inner dials: the arp comes back (Eb), riser; 7.9 a short DROP (near silence) before...
//   8.35    IGNITION: the biggest hit, wide supersaw pad, then the groove: soft kick, ducked sub, arp, Fm-Db-Ab-Eb
//   15.2    homecoming: kick stops, filter closes, pad walks home; 18.36 final click = last sub hit, Fm(add9) rings, fade
// Pure synthesis (no samples), deterministic. Writes assets/generated/0024-core-unlock-music.wav when called with --use,
// else out/0024-core-unlock/music-synth/score.wav.
import { join } from "node:path";
import { CORE } from "../src/scenes/core/core";
import { Biquad, midiHz, reverb, SR, stereo, writeWav, type Stereo } from "./lib/dsp";
import { ASSETS, ROOT } from "./lib/paths";

const DUR = CORE.duration, N = Math.ceil(DUR * SR);
const dry = stereo(DUR), wet = stereo(DUR); // wet = reverb send
const duck = new Float32Array(N).fill(1); // sidechain gain from the kick (applied to pad + sub)
let seed = 0x2f6e2b1;
const noise = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 2 ** 31 - 1; };
const clamp = (x: number, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const sm = (a: number, b: number, x: number) => { const u = clamp((x - a) / (b - a)); return u * u * (3 - 2 * u); };

const T = { clack: 1.72, open: 3.9, inLock: 5.8, inOpen: 7.0, drop: 7.95, ign: 8.35, home: 15.2, fin: 18.36, end: CORE.fade[1] };
const BEAT = 60 / 110; // 110 BPM: 4 beats from the clack land on the open (1.72 + 2.18 = 3.9)
const S16 = BEAT / 4;

function put(t0: number, len: number, pan: number, send: number, fn: (t: number) => number, ducked = false) {
  const s0 = Math.round(t0 * SR), n = Math.round(len * SR);
  const gl = Math.cos((pan * Math.PI) / 2), gr = Math.sin((pan * Math.PI) / 2);
  for (let i = 0; i < n; i++) {
    const k = s0 + i;
    if (k < 0 || k >= N) continue;
    let v = fn(i / SR);
    if (ducked) v *= duck[k];
    dry[0][k] += v * gl; dry[1][k] += v * gr;
    wet[0][k] += v * gl * send; wet[1][k] += v * gr * send;
  }
}
// band-limited-ish saw (polyBLEP)
function saw(phase: number, dt: number) {
  let v = 2 * phase - 1;
  if (phase < dt) { const x = phase / dt; v -= x + x - x * x - 1; }
  else if (phase > 1 - dt) { const x = (phase - 1) / dt; v -= x * x + x + x + 1; }
  return v;
}

// ---- elements ----
/** supersaw pad: notes held from t0 for len, 5 detuned saws per note, lowpass cutoff(t) */
function pad(t0: number, len: number, notes: number[], g: number, cutoff: (t: number) => number, atk = 0.6, rel = 0.8, ducked = true) {
  [-1, 1].forEach((side) => {
    const lp = new Biquad(), lp2 = new Biquad();
    const voices = notes.flatMap((m) => [-14, -6, 0, 7, 15].map((c, j) => ({ f: midiHz(m) * 2 ** ((c * side + (j % 2 ? 3 : -3)) / 1200), ph: (j * 0.137 + m * 0.01) % 1 })));
    put(t0, len + rel, side < 0 ? 0.15 : 0.85, 0.45, (t) => {
      let s = 0;
      for (const v of voices) { v.ph = (v.ph + v.f / SR) % 1; s += saw(v.ph, v.f / SR); }
      const env = sm(0, atk, t) * (t > len ? Math.max(0, 1 - (t - len) / rel) : 1);
      const fc = cutoff(t0 + t);
      return lp2.set("lp", fc, 0.6).run(lp.set("lp", fc, 0.6).run(s)) * env * g / voices.length;
    }, ducked);
  });
}
/** pluck for the arp: saw + sub-octave square, filter envelope */
function pluck(t0: number, m: number, g: number, bright: number, pan: number) {
  const f = midiHz(m), lp = new Biquad();
  let ph = 0, ph2 = 0;
  put(t0, 0.32, pan, 0.35, (t) => {
    ph = (ph + f / SR) % 1; ph2 = (ph2 + f / 2 / SR) % 1;
    const s = 0.7 * saw(ph, f / SR) + 0.3 * (ph2 < 0.5 ? 1 : -1);
    const fc = 180 + bright * 5200 * Math.exp(-t * 22);
    return lp.set("lp", fc, 1.4).run(s) * Math.exp(-t * 9) * g;
  });
}
/** sub bass note (sine + a little drive) */
function sub(t0: number, len: number, m: number, g: number, ducked = true) {
  const f = midiHz(m);
  put(t0, len + 0.05, 0.5, 0, (t) => Math.tanh(1.6 * Math.sin(2 * Math.PI * f * t)) * sm(0, 0.01, t) * (t > len ? Math.max(0, 1 - (t - len) / 0.05) : 1) * g, ducked);
}
/** cinematic impact: sine drop + low noise thump + long tail into the reverb */
function impact(t0: number, g: number, f0 = 70, f1 = 32) {
  f0 *= 1.6; f1 = Math.max(46, f1 * 1.5); g *= 0.4;
  return impactRaw(t0, g, f0, f1);
}
function impactRaw(t0: number, g: number, f0: number, f1: number) {
  let ph = 0;
  const lp = new Biquad().set("lp", 900, 0.7);
  put(t0, 3.2, 0.5, 0.6, (t) => {
    const f = f1 + (f0 - f1) * Math.exp(-t * 7);
    ph += f / SR;
    const body = Math.tanh(2.2 * Math.sin(2 * Math.PI * ph)) * Math.exp(-t * 1.4);
    const thump = lp.run(noise()) * Math.exp(-t * 18) * 0.9;
    return (body + thump) * g;
  });
}
/** soft kick for the groove */
function kick(t0: number, g: number) {
  let ph = 0;
  put(t0, 0.45, 0.5, 0.05, (t) => { const f = 42 + 90 * Math.exp(-t * 35); ph += f / SR; return Math.sin(2 * Math.PI * ph) * Math.exp(-t * 7) * g; });
  const s0 = Math.round(t0 * SR);
  for (let i = 0; i < Math.round(0.4 * SR) && s0 + i < N; i++) duck[s0 + i] = Math.min(duck[s0 + i], 0.35 + 0.65 * sm(0, 0.38, i / SR));
}
/** filtered noise riser ending exactly at t1 */
function riser(t0: number, t1: number, g: number) {
  const bp = new Biquad();
  put(t0, t1 - t0 + 0.02, 0.5, 0.5, (t) => {
    const u = t / (t1 - t0);
    return bp.set("bp", 250 * 2 ** (u * 4.6), 2.2).run(noise()) * u ** 2.2 * g;
  });
}
/** reverse swell (a reversed decaying hiss) into t1 */
function swell(t1: number, len: number, g: number) {
  const lp = new Biquad().set("lp", 3000, 0.7);
  put(t1 - len, len, 0.5, 0.3, (t) => lp.run(noise()) * Math.exp(-(len - t) * 4.5) * g);
}
/** tiny glitch ticks (data) - very quiet, high, panned */
function tick(t0: number, g: number, pan: number) {
  const hp = new Biquad().set("hp", 6000, 0.7);
  put(t0, 0.03, pan, 0.4, (t) => hp.run(noise()) * Math.exp(-t * 260) * g);
}

// ---- the score (F minor) ----
const Fm = [53, 56, 60], Db = [49, 53, 56, 60], Ab = [56, 60, 63], Eb = [51, 55, 58, 62], Fmadd9 = [53, 56, 60, 67];
// HOOK: drone F/C, opening slowly; riser + reverse swell into the clack
pad(0, T.clack + 0.2, [41, 48, 53], 0.4, (t) => 140 + 700 * sm(0, T.clack, t), 0.15, 0.4, false);
riser(0.25, T.clack, 0.22); swell(T.clack, 1.1, 0.25);
impact(T.clack, 0.95);
// DIALS: arp on the 16th grid, brighter with every lock (the filter opens 1.72 -> 3.9), sub pulse on 8ths
const ARP = [0, 0, 12, 7, 0, 3, 12, 7];
for (let t = T.clack, i = 0; t < T.open - 0.02; t += S16, i++) pluck(t, 53 + ARP[i % 8], 0.187, 0.25 + 0.75 * sm(T.clack, T.open, t), i % 2 ? 0.62 : 0.38);
for (let t = T.clack; t < T.open - 0.02; t += BEAT / 2) sub(t, BEAT / 2 - 0.04, 41, 0.144, false);
pad(T.clack, T.open - T.clack, Fm, 0.16, (t) => 300 + 1200 * sm(T.clack, T.open, t), 0.4, 0.1, false);
riser(T.open - 1.4, T.open, 0.26); swell(T.open, 0.8, 0.3);
// OPEN: big hit, wide Db pad blooms, floating; data ticks drift like the motes
impact(T.open, 1.15, 80, 30);
pad(T.open, 1.0, Db, 0.3, (t) => 600 + 2600 * Math.exp(-(t - T.open) * 1.2), 0.05, 0.6, false);
pad(T.open + 1.0, T.inLock - T.open - 1.0, Ab, 0.24, () => 1400, 0.6, 0.5, false);
sub(T.open, T.inLock - T.open, 49, 0.126, false);
for (let k = 0; k < 14; k++) tick(T.open + 0.3 + k * 0.13 + 0.05 * Math.sin(k * 7.1), 0.12, 0.2 + 0.6 * ((k * 0.37) % 1));
// INNER DIALS: arp returns on Eb, faster brightening; riser through the inner open into the drop
for (let t = T.inLock, i = 0; t < T.drop; t += S16, i++) pluck(t, 51 + ARP[i % 8], 0.187, 0.4 + 0.6 * sm(T.inLock, T.drop, t), i % 2 ? 0.62 : 0.38);
for (let t = T.inLock; t < T.drop; t += BEAT / 2) sub(t, BEAT / 2 - 0.04, 39, 0.135, false);
pad(T.inLock, T.drop - T.inLock, Eb, 0.18, (t) => 500 + 2500 * sm(T.inLock, T.drop, t), 0.3, 0.05, false);
impact(T.inOpen, 0.6, 90, 40);
riser(T.inOpen - 0.2, T.ign, 0.3); swell(T.ign, 0.4, 0.4);
// IGNITION: the biggest hit, then the groove (Fm - Db - Ab - Eb, one chord per bar)
impact(T.ign, 1.35, 75, 28);
const BAR = BEAT * 4;
const prog: [number[], number][] = [[Fm, 29], [Db, 25], [Ab, 32], [Eb, 27]];
prog.forEach(([ch, root], k) => {
  const t0 = T.ign + k * BAR, len = Math.min(BAR, T.home - t0);
  pad(t0, len, [...ch, ch[0] + 12], 0.3, (t) => 900 + 2600 * sm(T.ign, T.ign + 2, t) - 900 * sm(T.home - 1.5, T.home, t), k === 0 ? 0.02 : 0.15, 0.25);
  for (let t = t0; t < t0 + len - 0.02; t += BEAT / 2) sub(t, BEAT / 2 - 0.05, root + 12, 0.15);
});
for (let t = T.ign + BEAT, i = 1; t < T.home - 0.05; t += BEAT, i++) kick(t, 0.5);
for (let t = T.ign + BEAT * 2, i = 0; t < T.home - 0.05; t += S16, i++) {
  const bar = Math.min(3, Math.floor((t - T.ign) / BAR));
  pluck(t, prog[bar][0][0] + 12 + ARP[i % 8], 0.128, 0.55 + 0.25 * Math.sin(i * 0.2), i % 2 ? 0.66 : 0.34);
}
for (let k = 0; k < 24; k++) tick(T.ign + 0.5 + k * BEAT * 0.25 * (1 + (k % 3)), 0.09, (k * 0.61) % 1);
// HOMECOMING: groove off, pad walks Db -> Eb(sus) -> home, arp slows and closes like the bands settling
pad(T.home, 1.5, Db, 0.24, (t) => 1600 - 900 * sm(T.home, T.home + 1.5, t), 0.3, 0.4, false);
pad(T.home + 1.5, T.fin - T.home - 1.5, [51, 56, 58, 63], 0.22, () => 900, 0.4, 0.3, false);
sub(T.home, 1.5, 37, 0.117, false); sub(T.home + 1.5, T.fin - T.home - 1.5, 39, 0.117, false);
for (let t = T.home, i = 0, step = S16; t < T.fin - 0.1; t += step, i++, step *= 1.06) pluck(t, 53 + ARP[i % 8], 0.14 * (1 - 0.6 * sm(T.home, T.fin, t)), 0.6 - 0.45 * sm(T.home, T.fin, t), i % 2 ? 0.6 : 0.4);
swell(T.fin, 0.9, 0.22);
// FINAL click: last sub hit, Fm(add9) rings out into the fade
impact(T.fin, 1.0, 60, 29);
pad(T.fin, T.end - T.fin, Fmadd9, 0.26, (t) => 1500 - 1000 * sm(T.fin, T.end, t), 0.05, 0.3, false);
sub(T.fin, 1.6, 41, 0.135, false);

// ---- mix: reverb on the send, gentle master fade ----
reverb(wet, { room: 0.9, damp: 0.55, wet: 1.0, preDelayMs: 25, loop: false });
const out: Stereo = stereo(DUR);
const hpL = new Biquad().set("hp", 35, 0.7), hpR = new Biquad().set("hp", 35, 0.7);
const f0 = Math.round(CORE.fade[0] * SR), f1 = Math.round(T.end * SR);
for (let k = 0; k < N; k++) {
  const g = k < f0 ? 1 : k >= f1 ? 0 : (1 - (k - f0) / (f1 - f0)) ** 1.5;
  out[0][k] = hpL.run((dry[0][k] + 0.42 * wet[0][k]) * g) * 0.6;
  out[1][k] = hpR.run((dry[1][k] + 0.42 * wet[1][k]) * g) * 0.6;
}
const path = process.argv.includes("--use") ? join(ASSETS, "generated", "0024-core-unlock-music.wav") : join(ROOT, "out", "0024-core-unlock", "music-synth", "score.wav");
writeWav(path, out, 0.9);
console.log(`wrote ${path}`);
