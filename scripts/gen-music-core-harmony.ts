// 0024 music options, round 2 (owner, Nov 17, a musician: "none of them, it's the same music - change the CHORDS").
// Round 1 failed because all four held static diatonic triads with a static bass - only the timbre changed. Here the
// HARMONY leads: every lock in the picture is a new chord, extended voicings (maj7/9/11/13, sus, #11, alt), chromatic
// mediants, modal interchange and moving bass lines, with automatic voice leading. Each option = a chord chart (time ->
// chord) + a texture. Writes out/0024-core-unlock/music-options-2/<id>.wav and <id>-chords.txt.
// Real event times (s): hook 0-1.8 (clack 1.72) | outer locks 2.25..3.45 | seam 3.65 | outer open 3.9 | inner locks
// 5.8..6.9 | inner open 7.0 | ignite 8.35 (slow motion) | bands home 15.36..18.08 | final click 18.36 | fade 19.3-20.95
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { CORE, coreEvents } from "../src/scenes/core/core";
import { reverb, SR, stereo, writeWav } from "./lib/dsp";
import { ROOT } from "./lib/paths";
import { orch, piano, play } from "./lib/sampler";

const EV = coreEvents();
const at = (k: string) => EV.filter((e) => e.kind === k).map((e) => e.t);
const LOCK = at("lock"), HOME = [...at("home"), ...at("final")].sort((a, b) => a - b);
const T = { clack: 1.72, seam: 3.65, open: 3.9, float: 4.9, inOpen: 7.0, ign: 8.35, fin: HOME[HOME.length - 1], end: CORE.fade[1] };

const Q: Record<string, number[]> = {
  "": [0, 4, 7], m: [0, 3, 7], add9: [0, 4, 7, 14], madd9: [0, 3, 7, 14], maj7: [0, 4, 7, 11], maj9: [0, 4, 7, 11, 14],
  "maj7#11": [0, 4, 7, 11, 18], "maj9#11": [0, 4, 11, 14, 18], m7: [0, 3, 7, 10], m9: [0, 3, 7, 10, 14], m11: [0, 3, 10, 14, 17],
  mmaj7: [0, 3, 7, 11], "7": [0, 4, 7, 10], "9": [0, 4, 10, 14], "13": [0, 4, 10, 14, 21], "13#11": [0, 4, 10, 18, 21],
  "7b9": [0, 4, 7, 10, 13], "7#9": [0, 4, 10, 15], "7alt": [0, 4, 10, 13, 20], sus2: [0, 2, 7], sus4: [0, 5, 7],
  "7sus4": [0, 5, 7, 10], "13sus": [0, 5, 10, 14, 21], "9sus": [0, 5, 10, 14], dim7: [0, 3, 6, 9], m7b5: [0, 3, 6, 10],
  "69": [0, 4, 9, 14], q: [0, 5, 10, 15], q5: [0, 5, 10, 15, 20],
};
const PC: Record<string, number> = { C: 0, "C#": 1, Db: 1, D: 2, "D#": 3, Eb: 3, E: 4, F: 5, "F#": 6, Gb: 6, G: 7, "G#": 8, Ab: 8, A: 9, "A#": 10, Bb: 10, B: 11 };
/** "F#m7b5/C" -> { bass midi (oct 2), upper pitch classes } */
function parse(sym: string) {
  const [main, slash] = sym.split("/");
  const root = main.match(/^[A-G](#|b)?/)![0];
  const qual = main.slice(root.length);
  if (!(qual in Q)) throw new Error(`unknown chord ${sym}`);
  const r = PC[root];
  const bassPc = slash ? PC[slash] : r;
  return { bass: 36 + ((bassPc + 12 - 0) % 12) + (bassPc < 4 ? 12 : 0), ints: Q[qual].map((i) => r + i), sym };
}
/** voice leading: upper voices = chord tones (minus a doubled root when there are 5+), closest to the previous voicing */
function voice(ints: number[], prev: number[] | null, lo = 55, hi = 79): number[] {
  const pcs = [...new Set(ints.map((i) => ((i % 12) + 12) % 12))];
  const top = pcs.length > 4 ? pcs.filter((p) => p !== ((ints[0] % 12) + 12) % 12) : pcs;
  const cands: number[][] = [];
  for (let base = lo; base < lo + 12; base++) {
    const v = top.map((p) => { let m = base + ((p - base) % 12 + 12) % 12; return m; }).sort((a, b) => a - b);
    if (v[v.length - 1] <= hi) cands.push(v);
  }
  if (!prev) return cands[Math.floor(cands.length / 2)];
  const cost = (v: number[]) => v.reduce((s, m) => s + Math.min(...prev.map((p) => Math.abs(p - m))), 0) + Math.abs(v[v.length - 1] - prev[prev.length - 1]) * 0.5;
  return cands.reduce((a, b) => (cost(b) < cost(a) ? b : a));
}

type Chart = [number, string][];
interface Opt { id: string; title: string; chart: Chart; texture: (out: ReturnType<typeof stereo>, ch: { t0: number; t1: number; bass: number; up: number[]; sym: string; i: number }[]) => void; wet: number }

function render(o: Opt) {
  const out = stereo(CORE.duration);
  let prev: number[] | null = null;
  const ch = o.chart.map(([t0, sym], i) => {
    const p = parse(sym);
    const up = voice(p.ints, prev);
    prev = up;
    return { t0, t1: i + 1 < o.chart.length ? o.chart[i + 1][0] : T.end, bass: p.bass, up, sym, i };
  });
  o.texture(out, ch);
  reverb(out, { room: 0.84, damp: 0.45, wet: o.wet, preDelayMs: 20, loop: false });
  const f0 = Math.round(CORE.fade[0] * SR), f1 = Math.round(T.end * SR);
  for (let k = f0; k < out[0].length; k++) { const g = k >= f1 ? 0 : (1 - (k - f0) / (f1 - f0)) ** 1.5; out[0][k] *= g; out[1][k] *= g; }
  return out;
}
const O = (out: ReturnType<typeof stereo>, inst: string, m: number, t: number, g: number, dur: number, pan = 0.5, rel = 0.5, soft = true) =>
  t >= 0 && t < CORE.duration && play(out, orch(inst, m, soft), t, g, pan, dur, rel, 0.55);
const P = (out: ReturnType<typeof stereo>, m: number, t: number, g: number, dur: number, pan = 0.5, rel = 0.9) =>
  t >= 0 && t < CORE.duration && play(out, piano(m), t, g, pan, dur, rel, 0.3);
const stringsFor = (m: number) => (m >= 67 ? "violins" : m >= 57 ? "violas" : "celli");

// the two lock runs + homes get one chord each; these builders keep the charts readable
const locks = (syms: string[], from: number) => syms.map((s, k) => [LOCK[from + k], s] as [number, string]);
const homes = (syms: string[]) => syms.map((s, k) => [HOME[k], s] as [number, string]);

const OPTS: Opt[] = [
  {
    id: "1-mediants", title: "Chromatic mediants - E minor -> E major (legato strings + horns)", wet: 0.3,
    chart: [
      [0, "Emadd9"], [T.clack, "Cmaj7#11/E"],
      ...locks(["E", "G", "Bb", "Db", "E", "G", "Bb", "Db"], 0),      // planing major triads a minor third apart (octatonic)
      [T.seam, "B7sus4"], [T.open, "Cmaj9#11"], [T.float, "Am9"], [5.35, "Fmaj7#11"],
      ...locks(["Abmaj7", "Fm9", "Dbmaj7", "Bbm9", "Gbmaj7#11", "B7sus4"], 8),
      [T.inOpen, "B7b9"], [T.ign, "Emaj9"], [10.0, "C#m11"], [11.4, "Amaj7#11"], [12.6, "Cmaj7#11"], [13.7, "Emaj9/G#"], [14.6, "F#13sus"],
      ...homes(["E", "B/D#", "C#m7", "Amaj7/C#", "B/D#", "E", "Amaj7", "G#m7", "F#m9", "Cmaj7#11", "B7sus4", "B7", "Emaj9", "Emaj9"]),
    ],
    texture: (out, ch) => ch.forEach((c) => {
      const d = c.t1 - c.t0 + 0.08;
      c.up.forEach((m, j) => O(out, stringsFor(m), m, c.t0, 0.026, d, 0.3 + 0.4 * (j / Math.max(1, c.up.length - 1)), 0.35));
      O(out, "basses", c.bass, c.t0, 0.05, d, 0.5, 0.35); O(out, "celli", c.bass + 12, c.t0, 0.03, d, 0.45, 0.35);
      if (d > 0.9) O(out, "horn", c.up[c.up.length - 2], c.t0 + 0.05, 0.05, d - 0.1, 0.6, 0.5);
    }),
  },
  {
    id: "2-neosoul", title: "Neo-soul / jazz - Db major, ii-V chains, tritone subs (Salamander piano + celli + flute)", wet: 0.22,
    chart: [
      [0, "Dbmaj9"], [T.clack, "Ab13sus"],
      ...locks(["Ebm9", "Ab13", "Dbm9", "Gb13", "Bm9", "E13", "Am9", "D13"], 0), // ii-V chain falling in whole tones
      [T.seam, "G7alt"], [T.open, "Cmaj9#11"], [T.float, "Bbm11"], [5.35, "Eb9sus"],
      ...locks(["Bmaj7#11", "Bbm9", "Ebm9", "Ab13sus", "Ab13", "Ab7#9"], 8),
      [T.inOpen, "Ab7alt"], [T.ign, "Dbmaj9"], [9.8, "Bbm11"], [10.9, "Gbmaj9#11"], [11.9, "F7#9"], [12.8, "Bbm9"], [13.6, "Eb13"], [14.4, "Ebm9"], [14.9, "Ab13sus"],
      ...homes(["Gbmaj7", "Fm7", "E13#11", "Ebm9", "D13#11", "Dbmaj7", "Cm7b5", "F7alt", "Bbm9", "Eb13", "Ebm9", "Ab13sus", "Dbmaj9", "Db69"]),
    ],
    texture: (out, ch) => ch.forEach((c) => {
      const d = c.t1 - c.t0;
      c.up.forEach((m, j) => P(out, m, c.t0 + j * 0.018, 0.075, d + 0.1, 0.4 + 0.08 * j));   // rolled voicing
      P(out, c.bass, c.t0, 0.13, d + 0.2, 0.42); O(out, "celli", c.bass + 12, c.t0, 0.022, d + 0.05, 0.45, 0.3);
      if (d > 1.0) for (let t = c.t0 + 0.5, k = 0; t < c.t1 - 0.2; t += 0.5, k++) P(out, c.up[(k + 1) % c.up.length], t, 0.04, 0.4, 0.55);
      if (c.t0 >= T.ign && c.t0 < 15) O(out, "flute", c.up[c.up.length - 1] + 12, c.t0 + 0.1, 0.03, d * 0.9, 0.62, 0.4);
    }),
  },
  {
    id: "3-lament", title: "Lament bass - A minor -> A major, descending/ascending chromatic bass (pizzicato + harp + celli)", wet: 0.26,
    chart: [
      [0, "Amadd9"], [T.clack, "Am/G"],
      ...locks(["Am", "Ammaj7/G#", "Am7/G", "D9/F#", "Fmaj7", "E7sus4", "E7", "Am"], 0), // the lament: chromatic bass down
      [T.seam, "E7b9"], [T.open, "Fmaj9"], [T.float, "Dm9"], [5.35, "G13"],
      ...locks(["Cmaj7", "C#dim7", "Dm9", "D#dim7", "E7sus4", "E7b9"], 8), // and back up, chromatically
      [T.inOpen, "E7alt"], [T.ign, "Amaj9"], [10.0, "F#m11"], [11.3, "Dmaj7#11"], [12.5, "Fmaj7#11"], [13.6, "Amaj7/C#"], [14.3, "Bm11"], [14.8, "E13sus"],
      ...homes(["A", "E/G#", "F#m7", "Amaj7/E", "Dmaj7", "A/C#", "Bm7", "Fmaj7#11", "E7sus4", "E7", "D/E", "E7sus4", "Aadd9", "Aadd9"]),
    ],
    texture: (out, ch) => ch.forEach((c) => {
      const d = c.t1 - c.t0;
      O(out, "celliPizz", c.bass, c.t0, 0.12, 0.6, 0.48); O(out, "basses", c.bass, c.t0, 0.035, d + 0.05, 0.5, 0.3);
      const step = d < 0.4 ? d / 2 : 0.15;
      for (let t = c.t0, k = 0; t < c.t1 - 0.02; t += step, k++) O(out, "violinsPizz", c.up[k % c.up.length] + (k >= c.up.length ? 12 : 0), t, 0.05, 0.3, 0.35 + 0.3 * ((k % c.up.length) / c.up.length));
      if (d > 0.6) { c.up.forEach((m, j) => O(out, "harp", m, c.t0 + j * 0.04, 0.06, 1.6, 0.6)); c.up.forEach((m) => O(out, m >= 62 ? "violas" : "celli", m - 12, c.t0, 0.016, d, 0.4, 0.4)); }
    }),
  },
  {
    id: "4-quartal", title: "Quartal / suspended - G lydian, parallel 4ths, never resolving until the end (harp + marimba + horns + strings)", wet: 0.3,
    chart: [
      [0, "Gq5"], [T.clack, "Eq"],
      ...locks(["Dq", "Eq", "Fq", "Gq", "Aq", "Bbmaj7#11", "Cq", "Dq5"], 0), // parallel quartal stacks climbing
      [T.seam, "D7sus4"], [T.open, "Ebmaj7#11"], [T.float, "Cm9"], [5.35, "F13sus"],
      ...locks(["Bbmaj9", "Abmaj7#11", "Gm11", "Fq", "Ebmaj7#11", "D9sus"], 8),
      [T.inOpen, "D7b9"], [T.ign, "Gmaj9#11"], [10.0, "Em11"], [11.3, "Cmaj9#11"], [12.5, "Ebmaj7#11"], [13.6, "Bm11"], [14.3, "Am11"], [14.8, "D13sus"],
      ...homes(["Gq", "Fq", "Eq", "Dq", "Cmaj7#11", "Bm11", "Am11", "Ebmaj7#11", "Dq", "D9sus", "Cq", "D9sus", "G69", "G69"]),
    ],
    texture: (out, ch) => ch.forEach((c) => {
      const d = c.t1 - c.t0;
      for (let t = c.t0, k = 0; t < c.t1 - 0.02; t += Math.min(0.13, d / 3), k++) O(out, k % 2 ? "harp" : "marimba", [...c.up, ...c.up.map((m) => m + 12)][k % (c.up.length * 2)], t, 0.05, 0.6, 0.3 + 0.4 * ((k % 4) / 3));
      O(out, "horn", c.bass + 12, c.t0, 0.06, d + 0.05, 0.45, 0.4); O(out, "basses", c.bass, c.t0, 0.04, d + 0.05, 0.5, 0.4);
      if (d > 0.8) c.up.forEach((m, j) => O(out, stringsFor(m), m, c.t0, 0.02, d, 0.35 + 0.1 * j, 0.6));
    }),
  },
];

const dir = join(ROOT, "out", "0024-core-unlock", "music-options-2");
mkdirSync(dir, { recursive: true });
for (const o of OPTS) {
  writeWav(join(dir, `${o.id}.wav`), render(o), 1.0);
  writeFileSync(join(dir, `${o.id}-chords.txt`), `${o.title}\n` + o.chart.map(([t, s]) => `${t.toFixed(2).padStart(6)}  ${s}`).join("\n") + "\n");
  console.log(`wrote ${o.id}`);
}
