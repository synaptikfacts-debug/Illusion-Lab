// 0023 v2 "This liquid became a storm": per-frame data for scripts/blender/ferro_alive.py.
// Usage: npx tsx scripts/gen-heartbeat-frames.ts <outDir> [fps]
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { STORM, stormFrame } from "../src/scenes/ferroMusic/storm";

const outDir = process.argv[2] ?? "out/storm";
const fps = Number(process.argv[3] ?? 60);
mkdirSync(outDir, { recursive: true });
const N = Math.round(STORM.duration * fps);
const frames: object[] = [];
for (let f = 0; f < N; f++) frames.push(stormFrame(f / fps));
writeFileSync(join(outDir, "frames.json"), JSON.stringify({ fps, n: N, frames }));
console.log(`wrote ${N} frames to ${outDir}`);
