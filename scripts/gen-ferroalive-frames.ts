// 0012 v7 "alive": per-frame creature parameters (blobs, heartbeat rings, crawl wave, crown, lean), light colours and
// camera for scripts/blender/ferro_alive.py. Usage: npx tsx scripts/gen-ferroalive-frames.ts <outDir> [fps]
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { LIFE, lifeAt, lifeCam, lightsAt } from "../src/scenes/ferroMusic/creature";

const outDir = process.argv[2] ?? "out/ferroalive";
const fps = Number(process.argv[3] ?? 60);
mkdirSync(outDir, { recursive: true });
const N = Math.round(LIFE.duration * fps);
const frames: object[] = [];
for (let f = 0; f < N; f++) {
  const t = f / fps;
  const L = lightsAt(t);
  frames.push({ ...lifeCam(t), ...lifeAt(t), lightA: L.a, lightB: L.b });
}
writeFileSync(join(outDir, "frames.json"), JSON.stringify({ fps, n: N, frames }));
console.log(`wrote ${N} frames to ${outDir}`);
