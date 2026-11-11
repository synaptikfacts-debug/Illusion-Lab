// Singing Pins: The Show - per-frame data for the Blender (Cycles) renderer, from the same story as the three.js
// preview (src/scenes/pins/show.ts): pin heights (uint16), camera, and the tip colour stops per frame.
// Usage: npx tsx scripts/gen-pinshow-frames.ts <outDir> [fps]
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { camShow, heightAt, layoutShow, SHOW, tipsAt } from "../src/scenes/pins/show";

const outDir = process.argv[2] ?? "out/pinshow-blender";
const fps = Number(process.argv[3] ?? 30);
mkdirSync(outDir, { recursive: true });
const pins = layoutShow();
const N = Math.round(SHOW.duration * fps);
const heights = new Uint16Array(N * pins.length);
const hex = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16) / 255);
const frames: { cam: number[]; look: number[]; stops: number[][] }[] = [];
for (let f = 0; f < N; f++) {
  const t = f / fps;
  pins.forEach((p, i) => { heights[f * pins.length + i] = Math.round((heightAt(p, t) / SHOW.maxHeight) * 65535); });
  const c = camShow(t);
  const tp = tipsAt(t);
  const stops = tp.a.map((a, k) => { const A = hex(a), B = hex(tp.b[k]); return A.map((v, j) => v + (B[j] - v) * tp.mix); });
  frames.push({ cam: c.pos, look: c.look, stops });
}
writeFileSync(join(outDir, "heights.bin"), Buffer.from(heights.buffer));
writeFileSync(join(outDir, "frames.json"), JSON.stringify({ fps, n: N, maxHeight: SHOW.maxHeight, spacing: SHOW.spacing, pins: pins.map((p) => [p.x, p.z]), frames }));
console.log(`wrote ${N} frames x ${pins.length} pins to ${outDir}`);
