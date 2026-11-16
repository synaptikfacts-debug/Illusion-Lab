// 0019 "This liquid has a heartbeat": per-frame data for scripts/blender/ferro_alive.py.
// Usage: npx tsx scripts/gen-heartbeat-frames.ts <outDir> [fps]
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { HB, heartbeatFrame } from "../src/scenes/ferroMusic/heartbeat";

const outDir = process.argv[2] ?? "out/heartbeat";
const fps = Number(process.argv[3] ?? 60);
mkdirSync(outDir, { recursive: true });
const N = Math.round(HB.duration * fps);
const frames: object[] = [];
for (let f = 0; f < N; f++) frames.push(heartbeatFrame(f / fps));
writeFileSync(join(outDir, "frames.json"), JSON.stringify({ fps, n: N, frames }));
console.log(`wrote ${N} frames to ${outDir}`);
