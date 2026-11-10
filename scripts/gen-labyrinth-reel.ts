// Ferrofluid Labyrinth full reel: per-frame maps for the Blender renderer, following src/scenes/labyrinth/story.ts.
// The growth is simulated once; snapshots are kept (8-bit, every SNAP steps) so any frame can show any moment of the
// growth, forwards or backwards (rewind, retraction), interpolated between snapshots.
// Usage: npx tsx scripts/gen-labyrinth-reel.ts <outDir> [fromFrame] [toFrame]
import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { MAZE, simulateGrowth } from "../src/scenes/labyrinth/maze";
import { LSTORY, stateAt } from "../src/scenes/labyrinth/story";
import { writeMapsFromField } from "./gen-labyrinth-maps";

const outDir = process.argv[2] ?? "out/labyrinth-reel";
const N = Math.round(LSTORY.total * LSTORY.fps);
const from = Number(process.argv[3] ?? 0), to = Math.min(N - 1, Number(process.argv[4] ?? N - 1));
const FILL = 11200, SNAP = 20, QMAX = 0.4;
const sm = (a: number, b: number, x: number) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };

const snaps: Uint8Array[] = [];
const t0 = Date.now();
const cache = join(outDir, "snaps.bin"); // the growth is simulated once and shared by parallel workers
const cells = MAZE.w * MAZE.h;
if (existsSync(cache)) {
  const buf = readFileSync(cache);
  for (let o = 0; o + cells <= buf.length; o += cells) snaps.push(new Uint8Array(buf.buffer, buf.byteOffset + o, cells));
  console.log(`loaded ${snaps.length} snapshots`);
} else {
  simulateGrowth(FILL, SNAP, (_step, B) => {
    const q = new Uint8Array(B.length);
    for (let k = 0; k < B.length; k++) q[k] = Math.round(Math.min(1, Math.max(0, B[k] / QMAX)) * 255);
    snaps.push(q);
  });
  mkdirSync(outDir, { recursive: true });
  writeFileSync(cache + ".tmp", Buffer.concat(snaps.map((q) => Buffer.from(q.buffer))));
  renameSync(cache + ".tmp", cache);
  console.log(`simulated ${snaps.length} snapshots (${((Date.now() - t0) / 1000).toFixed(0)} s)`);
}

const { w, h } = MAZE;
function fieldAt(s: number): Float32Array {
  const x = Math.min(snaps.length - 1.001, Math.max(0, s * (snaps.length - 1)));
  const i = Math.floor(x), f = x - i, a = snaps[i], b = snaps[i + 1];
  const out = new Float32Array(w * h);
  for (let k = 0; k < out.length; k++) out[k] = ((a[k] * (1 - f) + b[k] * f) / 255) * QMAX;
  return out;
}
/** blends a solid round drop into the field (amount 0..1) */
function withDrop(B: Float32Array, amount: number) {
  for (let j = 0; j < h; j++)
    for (let i = 0; i < w; i++) {
      const x = (i - w / 2) / (w / 2), y = (j - h / 2) / (w / 2), th = Math.atan2(y, x);
      const R = 0.13 * (1 + 0.05 * Math.sin(3 * th + 1.3) + 0.035 * Math.sin(7 * th + 0.4) + 0.025 * Math.sin(11 * th + 2.2));
      const d = 0.3 * sm(R + 0.012, R - 0.02, Math.hypot(x, y)) * amount;
      const k = j * w + i;
      if (d > B[k]) B[k] = d;
    }
}

mkdirSync(outDir, { recursive: true });
const frames: { frame: number; dist: number }[] = [];
for (let f = 0; f < N; f++) {
  const st = stateAt(f / LSTORY.fps);
  frames.push({ frame: f, dist: st.dist });
  if (f < from || f > to || existsSync(join(outDir, `mask_${String(f).padStart(4, "0")}.png`))) continue;
  const B = fieldAt(st.s);
  if (st.solid > 0.001) withDrop(B, st.solid);
  writeMapsFromField(B, outDir, `_${String(f).padStart(4, "0")}`, st.twist, st.rot);
  if (f % 30 === 0) console.log(`frame ${f}/${N - 1}`);
}
writeFileSync(join(outDir, "frames.json"), JSON.stringify({ fps: LSTORY.fps, frames }));
console.log(`maps ready in ${outDir} (${((Date.now() - t0) / 60000).toFixed(1)} min)`);
