// 0024 "This core is unlocking": per-frame data for scripts/blender/core_unlock.py.
// Usage: npx tsx scripts/gen-core-frames.ts <outDir> [fps] [onlyTimes,comma,separated]
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { CORE, coreFrame, INNER, OUTER } from "../src/scenes/core/core";
import { fxFrame } from "../src/scenes/core/fx";

const outDir = process.argv[2] ?? "out/core";
const fps = Number(process.argv[3] ?? 60);
const only = process.argv[4] ? process.argv[4].split(",").map(Number) : null;
mkdirSync(outDir, { recursive: true });
const times = only ?? Array.from({ length: Math.round(CORE.duration * fps) }, (_, f) => f / fps);
const frames = times.map((t) => { const f = coreFrame(t); return { ...f, fx: fxFrame(f.tau) }; });
writeFileSync(join(outDir, "frames.json"), JSON.stringify({ fps, n: frames.length, outer: OUTER, inner: INNER, fade: CORE.fade, times, frames }));
console.log(`wrote ${frames.length} frames to ${outDir}`);
