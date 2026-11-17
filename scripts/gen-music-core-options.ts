// 0024 music OPTIONS (owner, Nov 17: "the music is the same every time and I don't like it - send others to choose from").
// Four scores that sound clearly different from the C-minor ostinato/brass/timpani score and from each other, all real
// samples (VSCO-2 CC0, Salamander piano CC BY 3.0), all driven by the same coreEvents() as the picture and resolving
// on the final click. Writes out/0024-core-unlock/music-options/<id>.wav. Usage: npx tsx scripts/gen-music-core-options.ts
import { mkdirSync } from "node:fs";
import { join } from "node:path";
import { CORE, coreEvents, IGNITE, realAt, HOOK_OUT } from "../src/scenes/core/core";
import { reverb, SR, stereo, writeWav } from "./lib/dsp";
import { ROOT } from "./lib/paths";
import { orch, piano, play, unpitched } from "./lib/sampler";

const R = realAt;
const IGN = R(IGNITE), OPEN = R(7.0), HOME0 = R(14.0), FIN = R(17.2), END = CORE.fade[1];
const EV = coreEvents();
const locks = EV.filter((e) => e.kind === "lock").map((e) => e.t);
const homes = EV.filter((e) => e.kind === "home" || e.kind === "final").map((e) => e.t);

type Out = ReturnType<typeof stereo>;
function mk() {
  const out = stereo(CORE.duration);
  const O = (inst: string, m: number, at: number, g: number, dur: number, pan = 0.5, rel = 0.6, soft = true) =>
    at >= 0 && at < CORE.duration && play(out, orch(inst, m, soft), at, g, pan, dur, rel, 0.6);
  const P = (m: number, at: number, g: number, dur = 1.5, pan = 0.5, rel = 1.2) =>
    at >= 0 && at < CORE.duration && play(out, piano(m), at, g, pan, dur, rel, 0.35);
  const chord = (inst: string, ms: number[], at: number, g: number, dur: number, rel = 1.2) =>
    ms.forEach((m, k) => O(inst, m, at, g, dur, 0.35 + 0.3 * (k / Math.max(1, ms.length - 1)), rel));
  return { out, O, P, chord };
}
function finish(out: Out, wet: number, room: number) {
  reverb(out, { room, damp: 0.45, wet, preDelayMs: 22, loop: false });
  const f0 = Math.round(CORE.fade[0] * SR), f1 = Math.round(END * SR);
  for (let k = f0; k < out[0].length; k++) { const g = k >= f1 ? 0 : (1 - (k - f0) / (f1 - f0)) ** 1.5; out[0][k] *= g; out[1][k] *= g; }
}

// A "CLOCKWORK GLASS" - D major: marimba + glockenspiel + pizzicato strings tick like a precision mechanism, every lock is
// a glockenspiel note climbing the scale, the unlock opens into harp + legato strings, ignition = a bright string chord.
function clockwork(): Out {
  const { out, O, chord } = mk();
  const D = [62, 64, 66, 69, 71, 74, 76, 78, 81, 83, 86, 88, 90, 93];
  // hook: a shimmer on held violins + a soft glock bell as we leave the sphere
  O("violins", 74, 0, 0.022, 1.8, 0.6, 0.4); O("violas", 66, 0.1, 0.02, 1.7, 0.4, 0.4);
  O("harp", 50, 1.72, 0.12, 2, 0.45); O("glockenspiel", 86, 1.72, 0.06, 2, 0.6);
  // dials: marimba 8ths on D-A-F#-A, pizz bass on the beat, accelerating with the dials
  for (let t = HOOK_OUT, i = 0; t < OPEN - 0.05; i++) {
    const step = 0.28 - 0.1 * Math.min(1, (t - HOOK_OUT) / (OPEN - HOOK_OUT));
    O("marimba", [62, 69, 66, 69, 64, 69, 66, 71][i % 8], t, 0.07, 0.3, 0.4 + 0.2 * (i % 2));
    if (i % 4 === 0) O("celliPizz", [38, 38, 43, 45][(i / 4) % 4 | 0], t, 0.09, 0.5, 0.45);
    t += step;
  }
  locks.forEach((t, n) => O("glockenspiel", D[Math.min(D.length - 1, n + 3)] + 12 * (n > 9 ? 0 : 0), t, 0.055, 1.2, 0.3 + 0.4 * (n % 2)));
  // unlock: harp glissando + strings open up
  for (let k = 0; k < 14; k++) O("harp", D[k] - 12, OPEN - 0.35 + k * 0.025, 0.07, 1.5, 0.3 + k * 0.03);
  chord("violins", [74, 78, 81], OPEN, 0.022, IGN - OPEN, 1.0); chord("celli", [50, 57], OPEN, 0.035, IGN - OPEN, 1.0);
  for (let t = OPEN + 0.3, i = 0; t < IGN - 0.1; t += 0.2, i++) O("violinsPizz", [74, 78, 81, 78][i % 4], t, 0.05, 0.3, 0.6);
  // ignition: bright G-major-lift chord (IV) resolving to D, glock sparkle, marimba ripples through the payoff
  chord("violins", [79, 83, 86], IGN, 0.03, 2.2, 1.2); chord("violas", [67, 71], IGN, 0.03, 2.2); O("basses", 43, IGN, 0.05, 2.2);
  chord("violins", [78, 81, 86], IGN + 2.2, 0.028, HOME0 - IGN - 2.2, 1.2); O("basses", 38, IGN + 2.2, 0.05, HOME0 - IGN - 2.2);
  for (let t = IGN + 0.2, i = 0; t < HOME0; t += 0.18, i++) O("marimba", [74, 78, 81, 86, 81, 78][i % 6], t, 0.04 + 0.02 * (i % 6 === 0 ? 1 : 0), 0.25, 0.3 + 0.4 * ((i % 6) / 5));
  [0, 1.1, 2.3, 3.4].forEach((d) => O("glockenspiel", [93, 90, 88, 86][[0, 1.1, 2.3, 3.4].indexOf(d)], IGN + 0.4 + d, 0.05, 1.5, 0.65));
  // homecoming: each band home = a marimba+pizz note walking DOWN the scale, the last one lands on D
  homes.forEach((t, k) => { const m = D[Math.max(0, homes.length - 1 - k)]; O("marimba", m, t, 0.08, 0.6, 0.45); O("celliPizz", m - 24, t, 0.08, 0.6, 0.5); });
  chord("violins", [74, 78, 81], FIN + 0.05, 0.026, END - FIN, 1.6); O("celli", 50, FIN + 0.05, 0.04, END - FIN, 0.45, 1.6); O("glockenspiel", 86, FIN + 0.05, 0.06, 3, 0.55);
  finish(out, 0.26, 0.8);
  return out;
}

// B "WONDER" - E-flat major, warm legato strings only (no drums, no brass hits): a slow chord progression where every
// lock adds a voice, the unlock swells, the ignition blooms into a high violin melody, horns hum the homecoming.
function wonder(): Out {
  const { out, O, chord } = mk();
  O("celli", 51, 0, 0.04, 1.9, 0.45, 0.6); O("violas", 63, 0.2, 0.025, 1.7, 0.55, 0.6); O("violins", 70, 0.6, 0.02, 1.3, 0.6, 0.6);
  O("harp", 39, 1.72, 0.14, 2.5, 0.45); O("harp", 51, 1.75, 0.1, 2.5, 0.5);
  const prog: [number, number[]][] = [[R(1.6), [39, 55, 58, 63]], [R(3.0), [36, 55, 60, 63]], [R(4.6), [44, 56, 60, 63]], [R(5.8), [46, 58, 62, 65]]];
  prog.forEach(([at, ms], k) => { const to = k + 1 < prog.length ? prog[k + 1][0] : OPEN; O("basses", ms[0], at, 0.05, to - at, 0.5, 0.8); ms.slice(1).forEach((m, j) => O(j === 0 ? "celli" : "violas", m, at, 0.032, to - at, 0.4 + 0.1 * j, 0.8)); });
  const melo = [70, 72, 74, 75, 77, 79, 82, 84, 82, 79, 77, 75, 74, 79];
  locks.forEach((t, n) => O("violins", melo[Math.min(melo.length - 1, n)], t, 0.03, 0.45, 0.62, 0.5));
  // unlock swell -> ignition bloom
  chord("violins", [70, 75, 79], OPEN, 0.024, IGN - OPEN, 1.0); chord("celli", [39, 51], OPEN, 0.04, IGN - OPEN, 1.0); O("horn", 58, OPEN + 0.4, 0.05, IGN - OPEN - 0.4, 0.55, 1.0);
  O("timpaniRoll", 46, IGN - 1.2, 0.08, 1.2, 0.5, 0.1);
  chord("violins", [79, 82, 87], IGN, 0.03, HOME0 - IGN, 1.4); chord("violas", [63, 70], IGN, 0.03, HOME0 - IGN, 1.4); O("basses", 39, IGN, 0.06, HOME0 - IGN, 0.5, 1.4); O("celli", 51, IGN, 0.04, HOME0 - IGN, 0.45, 1.4);
  [[87, 0], [89, 0.9], [91, 1.8], [94, 2.7], [91, 3.6], [89, 4.3], [87, 5.0]].forEach(([m, d]) => O("violins", m - 12, IGN + 0.8 + d, 0.035, 0.9, 0.62, 0.6));
  for (let k = 0; k < 12; k++) O("harp", [63, 67, 70, 75, 79, 82][k % 6] + (k > 5 ? 12 : 0), IGN + k * 0.06, 0.06, 2, 0.35 + k * 0.03);
  // homecoming: horns + celli descend, the final click lands on the tonic
  homes.forEach((t, k) => O("horn", [70, 68, 67, 65, 63, 62, 60, 58, 56, 55, 53, 51, 51, 51][Math.min(13, k)], t, 0.04, 0.5, 0.55, 0.5));
  chord("violins", [67, 70, 75], HOME0, 0.022, FIN - HOME0, 1.0); chord("celli", [44, 51], HOME0, 0.035, FIN - HOME0, 1.0);
  chord("violins", [70, 75, 79], FIN + 0.05, 0.026, END - FIN, 1.8); chord("celli", [39, 51], FIN + 0.05, 0.045, END - FIN, 1.8); O("harp", 39, FIN, 0.14, 3, 0.45);
  finish(out, 0.32, 0.88);
  return out;
}

// C "MYSTERY" - D dorian: clarinet + flute arpeggios over a celli pizzicato walk, harp and marimba answers - curious,
// a machine waking up; the unlock turns the arpeggios into running 16ths, the ignition brings an oboe line on strings.
function mystery(): Out {
  const { out, O, chord } = mk();
  O("flute", 74, 0, 0.03, 1.8, 0.6, 0.5); O("clarinet", 62, 0.3, 0.03, 1.5, 0.4, 0.5); O("celli", 50, 0, 0.03, 1.9, 0.45, 0.5);
  O("harp", 38, 1.72, 0.13, 2, 0.45); O("marimba", 62, 1.72, 0.06, 1, 0.55);
  const arp = [62, 65, 69, 72, 71, 69, 65, 64];
  for (let t = HOOK_OUT, i = 0; t < OPEN - 0.05; i++) {
    const step = 0.24 - 0.07 * Math.min(1, (t - HOOK_OUT) / (OPEN - HOOK_OUT));
    O("clarinet", arp[i % 8] - 12, t, 0.035, step * 0.9, 0.35, 0.15);
    if (i % 4 === 0) O("celliPizz", [38, 41, 43, 45, 43, 41][(i / 4) % 6 | 0], t, 0.1, 0.5, 0.5);
    t += step;
  }
  locks.forEach((t, n) => { O("harp", [74, 77, 81, 79, 76, 84, 86, 81, 77, 88, 89, 86, 84, 93][Math.min(13, n)], t, 0.07, 1, 0.65); O("marimba", 50 + (n % 3) * 7, t, 0.04, 0.4, 0.4); });
  chord("violas", [57, 62], R(4.0), 0.02, OPEN - R(4.0), 0.8);
  // unlock: running 16ths on flute + clarinet
  for (let t = OPEN, i = 0; t < IGN - 0.1; t += 0.12, i++) { O("flute", arp[i % 8] + 12, t, 0.024, 0.11, 0.62, 0.08); if (i % 2 === 0) O("clarinet", arp[(i + 4) % 8], t, 0.022, 0.2, 0.38, 0.1); }
  chord("celli", [38, 50], OPEN, 0.035, IGN - OPEN, 0.8); O("timpaniRoll", 50, IGN - 1.0, 0.06, 1.0, 0.5, 0.1);
  // ignition: an oboe melody over a D minor -> F major string bed, harp ripples, marimba pulse
  chord("violins", [65, 69, 74], IGN, 0.024, 3, 1.2); chord("celli", [38, 50], IGN, 0.04, 3, 1.2);
  chord("violins", [65, 69, 72], IGN + 3, 0.024, HOME0 - IGN - 3, 1.2); chord("celli", [41, 53], IGN + 3, 0.04, HOME0 - IGN - 3, 1.2);
  [[74, 0, 0.8], [76, 0.8, 0.4], [77, 1.2, 1.2], [76, 2.4, 0.6], [74, 3.0, 0.6], [72, 3.6, 1.4], [69, 5.0, 1.2]].forEach(([m, d, l]) => O("oboe", m, IGN + 0.5 + d, 0.045, l, 0.58, 0.4));
  for (let t = IGN, i = 0; t < HOME0; t += 0.24, i++) O("marimba", [50, 57, 62, 57][i % 4], t, 0.035, 0.3, 0.42);
  for (let k = 0; k < 10; k++) O("harp", [62, 65, 69, 72, 74][k % 5] + (k > 4 ? 12 : 0), IGN + k * 0.07, 0.06, 2, 0.35 + k * 0.035);
  homes.forEach((t, k) => { O("celliPizz", [57, 55, 53, 52, 50, 48, 47, 45, 43, 41, 40, 38, 38, 38][Math.min(13, k)], t, 0.1, 0.6, 0.5); O("clarinet", [69, 67, 65, 64, 62, 60, 59, 57, 55, 53, 52, 50, 50, 50][Math.min(13, k)], t, 0.03, 0.35, 0.38, 0.2); });
  // the end lifts to D MAJOR (Picardy third) - the mystery solved
  chord("violins", [66, 69, 74], FIN + 0.05, 0.025, END - FIN, 1.8); chord("celli", [38, 50], FIN + 0.05, 0.045, END - FIN, 1.8); O("flute", 78, FIN + 0.3, 0.03, END - FIN - 0.3, 0.6, 1.6); O("harp", 38, FIN, 0.14, 3, 0.45);
  finish(out, 0.28, 0.82);
  return out;
}

// D "PULSE" - A minor -> C major, a minimal modern piano pulse (repeated 8ths, one hand, soft layer) over celli drones;
// every lock moves the bass one step, the unlock doubles the pulse with violas, the ignition opens to C major with violins.
function pulse(): Out {
  const { out, O, P, chord } = mk();
  P(81, 0, 0.12, 1.8, 0.6); P(76, 0.45, 0.1, 1.4, 0.55); P(72, 0.9, 0.09, 1.0, 0.5); O("celli", 45, 0, 0.035, 1.9, 0.45, 0.5);
  P(45, 1.72, 0.22, 2.5, 0.45); P(57, 1.72, 0.14, 2.5, 0.5);
  const bass = [45, 43, 41, 40, 38, 41, 43, 45, 47, 48, 47, 45, 43, 45];
  const cell = [[69, 72, 76], [67, 71, 74], [65, 69, 72], [64, 67, 71]];
  let bi = 0, nextLock = 0;
  for (let t = HOOK_OUT, i = 0; t < OPEN - 0.05; i++) {
    while (nextLock < locks.length && locks[nextLock] <= t) { bi = nextLock + 1; nextLock++; }
    const c = cell[Math.floor(bi / 2) % 4];
    P(c[i % 3], t, 0.075 + (i % 3 === 0 ? 0.02 : 0), 0.32, 0.5 + 0.08 * ((i % 3) - 1), 0.4);
    t += 0.24 - 0.06 * Math.min(1, (t - HOOK_OUT) / (OPEN - HOOK_OUT));
  }
  locks.forEach((t, n) => { P(bass[Math.min(13, n)], t, 0.16, 0.9, 0.42); O("celli", bass[Math.min(13, n)] + 12, t, 0.025, 0.9, 0.42, 0.6); });
  // unlock: violas double the pulse, celli drone
  chord("celli", [45, 52], OPEN, 0.035, IGN - OPEN, 0.8);
  for (let t = OPEN, i = 0; t < IGN - 0.1; t += 0.17, i++) { P([76, 72, 69, 72][i % 4], t, 0.07, 0.3, 0.55, 0.3); if (i % 2 === 0) O("violas", [64, 60][(i / 2) % 2 | 0], t, 0.02, 0.32, 0.4, 0.2); }
  // ignition: C major opens - low C octave, violins chord, piano melody in long notes
  P(36, IGN, 0.24, 4, 0.45); P(48, IGN, 0.18, 4, 0.5); chord("violins", [72, 76, 79], IGN, 0.026, HOME0 - IGN, 1.4); chord("celli", [48, 55], IGN, 0.04, HOME0 - IGN, 1.4); O("basses", 36, IGN, 0.05, HOME0 - IGN, 0.5, 1.4);
  [[84, 0.6], [83, 1.6], [79, 2.4], [81, 3.4], [76, 4.4], [79, 5.2]].forEach(([m, d]) => P(m, IGN + d, 0.13, 1.6, 0.58));
  for (let t = IGN + 0.3, i = 0; t < HOME0; t += 0.3, i++) P([60, 64, 67, 64][i % 4], t, 0.05, 0.4, 0.45, 0.4);
  // homecoming: the pulse slows, each band home is a soft low piano note walking down to C
  homes.forEach((t, k) => P([60, 59, 57, 55, 53, 52, 50, 48, 47, 45, 43, 41, 40, 36][Math.min(13, k)], t, 0.15, 1.2, 0.45));
  chord("violins", [67, 72, 76], HOME0, 0.02, FIN - HOME0, 1.0);
  P(36, FIN + 0.02, 0.26, 4, 0.45); P(48, FIN + 0.02, 0.18, 4, 0.5); P(64, FIN + 0.5, 0.1, 3.5, 0.55); P(72, FIN + 1.0, 0.08, 3, 0.6);
  chord("violins", [72, 76, 79], FIN + 0.05, 0.024, END - FIN, 1.8); chord("celli", [36, 48], FIN + 0.05, 0.045, END - FIN, 1.8);
  finish(out, 0.3, 0.85);
  return out;
}

const dir = join(ROOT, "out", "0024-core-unlock", "music-options");
mkdirSync(dir, { recursive: true });
for (const [id, fn] of [["A-clockwork", clockwork], ["B-wonder", wonder], ["C-mystery", mystery], ["D-pulse", pulse]] as const) {
  writeWav(join(dir, `${id}.wav`), fn(), 1.0);
  console.log(`wrote ${id}`);
}
