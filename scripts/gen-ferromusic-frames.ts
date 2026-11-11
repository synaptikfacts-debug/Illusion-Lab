// Ferrofluid vs Music: per-frame spike heights (float32 per site), dome, light colours and camera for the Blender
// renderer, from the timeline in src/scenes/ferroMusic/score.ts.
// Usage: npx tsx scripts/gen-ferromusic-frames.ts <outDir> [fps]
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { camAt, FM, sites, stateAt } from "../src/scenes/ferroMusic/score";

const outDir = process.argv[2] ?? "out/ferromusic";
const fps = Number(process.argv[3] ?? 60);
mkdirSync(outDir, { recursive: true });
const ss = sites();
const N = Math.round(FM.duration * fps);
const buf = new Float32Array(N * ss.length);
const frames: object[] = [];
for (let f = 0; f < N; f++) {
  const t = f / fps;
  const st = stateAt(ss, t);
  buf.set(st.amp, f * ss.length);
  frames.push({ ...camAt(t), dome: st.dome, lightA: st.lightA, lightB: st.lightB });
}
writeFileSync(join(outDir, "amps.bin"), Buffer.from(buf.buffer));
writeFileSync(join(outDir, "frames.json"), JSON.stringify({ fps, n: N, rPool: FM.rPool, spacing: FM.spacing, sites: ss.map((s) => [s.x, s.y]), cams: frames }));
console.log(`wrote ${N} frames x ${ss.length} sites to ${outDir}`);
