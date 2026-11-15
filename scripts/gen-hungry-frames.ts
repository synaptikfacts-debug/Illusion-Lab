// 0018 "This liquid is hungry": per-frame creature data for scripts/blender/ferro_alive.py.
// Usage: npx tsx scripts/gen-hungry-frames.ts <outDir> [fps]
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { hungryReal, REAL_DURATION } from "../src/scenes/ferroMusic/hungry";

const outDir = process.argv[2] ?? "out/hungry";
const fps = Number(process.argv[3] ?? 60);
mkdirSync(outDir, { recursive: true });
const N = Math.round(REAL_DURATION * fps);
const frames: object[] = [];
for (let f = 0; f < N; f++) frames.push(hungryReal(f / fps));
writeFileSync(join(outDir, "frames.json"), JSON.stringify({ fps, n: N, frames }));
console.log(`wrote ${N} frames to ${outDir}`);
