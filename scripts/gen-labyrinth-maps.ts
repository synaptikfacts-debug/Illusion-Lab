// Ferrofluid Labyrinth: turns the simulated labyrinth field into the two maps the Blender scene is built from
// (16-bit PNG, 1080x1920, smooth bicubic upsampling, optional spiral twist):
//   height: the fluid's rounded surface (0 at the edge of a channel, 1 on its crest)
//   mask:   where there is fluid (soft edge, used by the material)
// Usage: npx tsx scripts/gen-labyrinth-maps.ts <outDir> [twist]
import { execFileSync } from "node:child_process";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { MAZE, simulateMaze } from "../src/scenes/labyrinth/maze";

const W = 1080, H = 1920;
const TH = 0.085; // fluid where the field is above this (same threshold as the look test)

function cubic(p0: number, p1: number, p2: number, p3: number, t: number) {
  return p1 + 0.5 * t * (p2 - p0 + t * (2 * p0 - 5 * p1 + 4 * p2 - p3 + t * (3 * (p1 - p2) + p3 - p0)));
}
function sampler(B: Float32Array) {
  const { w, h } = MAZE;
  const at = (i: number, j: number) => B[Math.min(h - 1, Math.max(0, j)) * w + Math.min(w - 1, Math.max(0, i))];
  return (x: number, y: number) => {
    const i = Math.floor(x), j = Math.floor(y), fx = x - i, fy = y - j;
    const row = (jj: number) => cubic(at(i - 1, jj), at(i, jj), at(i + 1, jj), at(i + 2, jj), fx);
    return cubic(row(j - 1), row(j), row(j + 1), row(j + 2), fy);
  };
}

export function writeLabyrinthMaps(outDir: string, twist = 0) {
  writeMapsFromField(simulateMaze(), outDir, "", twist);
}

/** Writes height<suffix>.png and mask<suffix>.png for one field. */
export function writeMapsFromField(B: Float32Array, outDir: string, suffix: string, twist = 0, rot = 0) {
  const s = sampler(B);
  const height = Buffer.alloc(W * H * 2), mask = Buffer.alloc(W * H * 2);
  for (let j = 0; j < H; j++)
    for (let i = 0; i < W; i++) {
      // q: -0.5..0.5 across the width (same convention as the shader look test)
      let qx = (i + 0.5) / W - 0.5, qy = (0.5 - (j + 0.5) / H) * (H / W);
      const r = Math.hypot(qx, qy), a = rot + twist * Math.exp(-r * 2.6), c = Math.cos(a), sn = Math.sin(a);
      [qx, qy] = [c * qx - sn * qy, sn * qx + c * qy];
      const u = (qx + 0.5) * MAZE.w - 0.5, v = (qy * (MAZE.w / MAZE.h) + 0.5) * MAZE.h - 0.5;
      const b = s(u, v);
      const hgt = Math.sqrt(Math.min(1, Math.max(0, (b - (TH - 0.02)) / 0.2)));
      const m = Math.min(1, Math.max(0, (b - (TH + 0.01)) / 0.05));
      const k = (j * W + i) * 2;
      height.writeUInt16LE(Math.round(hgt * 65535), k);
      mask.writeUInt16LE(Math.round(m * m * (3 - 2 * m) * 65535), k);
    }
  mkdirSync(outDir, { recursive: true });
  for (const [name, buf] of [["height", height], ["mask", mask]] as const) {
    const raw = join(outDir, `${name}${suffix}.${process.pid}.raw`); // unique per process (parallel workers)
    writeFileSync(raw, buf);
    execFileSync("ffmpeg", ["-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "gray16le", "-s", `${W}x${H}`, "-i", raw, "-pix_fmt", "gray16be", join(outDir, `${name}${suffix}.png`)]);
    rmSync(raw);
  }
}

if (/gen-labyrinth-maps\.ts$/.test(process.argv[1] ?? "")) writeLabyrinthMaps(process.argv[2] ?? "out/labyrinth-maps", Number(process.argv[3] ?? 0));
