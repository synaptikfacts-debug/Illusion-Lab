// Edge-band check (owner, Nov 15 2026: Instagram flagged 0018 "Your video has a border" because large flat, single-colour
// areas sat along the frame edges). Samples frames, measures how much detail each edge strip has compared with the
// middle of the frame, and reports the share of frames where an edge strip is nearly flat. Runs inside every render.
import { spawnSync } from "node:child_process";

export interface EdgeReport { pass: boolean; flatShare: number; worstEdge: string; perEdge: Record<string, number> }

const W = 108, H = 192;

export function edgeCheck(file: string, fps = 2): EdgeReport {
  const r = spawnSync("ffmpeg", ["-v", "error", "-i", file, "-vf", `fps=${fps},scale=${W}:${H},format=gray`, "-f", "rawvideo", "-"], { maxBuffer: 1 << 28 });
  const buf = r.stdout as Buffer;
  const n = Math.floor(buf.length / (W * H));
  const strips: Record<string, [number, number, number, number]> = {
    top: [0, W, 0, Math.round(H * 0.14)],
    bottom: [0, W, H - Math.round(H * 0.14), H],
    left: [0, Math.round(W * 0.1), 0, H],
    right: [W - Math.round(W * 0.1), W, 0, H],
  };
  const flatCount: Record<string, number> = { top: 0, bottom: 0, left: 0, right: 0 };
  let anyFlat = 0, counted = 0;
  for (let f = 0; f < n; f++) {
    const o = f * W * H;
    // skip near-black frames (fades) - they are not a border
    let mean = 0;
    for (let i = 0; i < W * H; i++) mean += buf[o + i];
    mean /= W * H;
    if (mean < 12) continue;
    counted++;
    let flatHere = false;
    for (const [name, [x0, x1, y0, y1]] of Object.entries(strips)) {
      // local detail: mean absolute difference between neighbouring pixels (texture, edges, objects)
      let d = 0, c = 0;
      for (let y = y0; y < y1 - 1; y++)
        for (let x = x0; x < x1 - 1; x++) {
          const p = buf[o + y * W + x];
          d += Math.abs(p - buf[o + y * W + x + 1]) + Math.abs(p - buf[o + (y + 1) * W + x]);
          c += 2;
        }
      if (d / c < 0.9) { flatCount[name]++; flatHere = true; }
    }
    if (flatHere) anyFlat++;
  }
  const perEdge = Object.fromEntries(Object.entries(flatCount).map(([k, v]) => [k, counted ? +(v / counted).toFixed(2) : 0]));
  const worstEdge = Object.entries(perEdge).sort((a, b) => b[1] - a[1])[0][0];
  const flatShare = counted ? +(anyFlat / counted).toFixed(2) : 0;
  return { pass: flatShare < 0.3, flatShare, worstEdge, perEdge };
}
