// Photosensitivity check (WCAG 2.x general-flash and red-flash rules, Harding/Ofcom-style area test).
// Each pixel tracks its luminance extreme; a reversal of >= 0.1 relative luminance (darker state < 0.8)
// is one "transition". When >= areaFraction of the frame transitions on the same frame, that frame holds
// a screen transition. A flash = a pair of opposing transitions. More than maxFlashesPerSecond flashes
// in any 1 s window fails. The same is done for saturated red.
import { FLASH_RULES } from "../../config/platforms";
import { probe, streamFrames } from "./ffmpeg";

const W = 108, H = 192, N = W * H;

const LIN = new Float32Array(256).map((_, i) => {
  const c = i / 255;
  return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
});

class Tracker {
  ref = new Float32Array(N);
  dir = new Int8Array(N);
  init = false;
  constructor(private delta: number, private darkerBelow: number) {}
  /** Returns how many pixels made a transition this frame. */
  step(v: Float32Array): number {
    if (!this.init) {
      this.ref.set(v);
      this.init = true;
      return 0;
    }
    let n = 0;
    const { ref, dir, delta, darkerBelow } = this;
    for (let i = 0; i < N; i++) {
      const x = v[i], r = ref[i], d = dir[i];
      if (d >= 0 && x > r && d === 1) ref[i] = x;
      else if (d <= 0 && x < r && d === -1) ref[i] = x;
      else if (Math.abs(x - r) >= delta && Math.min(x, r) < darkerBelow) {
        dir[i] = x > r ? 1 : -1;
        ref[i] = x;
        n++;
      }
    }
    return n;
  }
}

export interface FlashReport {
  pass: boolean;
  fps: number;
  frames: number;
  maxFlashesPerSec: { luminance: number; red: number };
  worstAt: { luminance: number; red: number }; // seconds (start of worst window)
  events: { luminance: number[]; red: number[] }; // seconds of every screen-level transition
}

export async function flashCheck(file: string): Promise<FlashReport> {
  const { fps } = await probe(file);
  const lum = new Tracker(FLASH_RULES.luminanceDelta, FLASH_RULES.darkerBelow);
  const red = new Tracker(FLASH_RULES.redDelta, Number.POSITIVE_INFINITY);
  const L = new Float32Array(N), Rv = new Float32Array(N);
  const lumEv: number[] = [], redEv: number[] = [];
  const minPixels = FLASH_RULES.areaFraction * N;

  const frames = await streamFrames(file, `scale=${W}:${H}:flags=area,format=rgb24`, N * 3, (buf, idx) => {
    for (let i = 0, j = 0; i < N; i++, j += 3) {
      const r = buf[j], g = buf[j + 1], b = buf[j + 2];
      L[i] = 0.2126 * LIN[r] + 0.7152 * LIN[g] + 0.0722 * LIN[b];
      const rs = r / 255, gs = g / 255, bs = b / 255, sum = rs + gs + bs;
      Rv[i] = sum > 0 && rs / sum >= 0.8 ? Math.max(0, rs - gs - bs) * 320 : 0;
    }
    if (lum.step(L) >= minPixels) lumEv.push(idx);
    if (red.step(Rv) >= minPixels) redEv.push(idx);
  });

  const worst = (ev: number[]) => {
    let best = 0, at = 0;
    for (let a = 0, b = 0; b < ev.length; b++) {
      while (ev[b] - ev[a] >= fps) a++;
      if (b - a + 1 > best) { best = b - a + 1; at = ev[a]; }
    }
    return { flashes: best / 2, at: at / fps };
  };
  const wl = worst(lumEv), wr = worst(redEv);
  return {
    pass: wl.flashes <= FLASH_RULES.maxFlashesPerSecond && wr.flashes <= FLASH_RULES.maxFlashesPerSecond,
    fps,
    frames,
    maxFlashesPerSec: { luminance: wl.flashes, red: wr.flashes },
    worstAt: { luminance: wl.at, red: wr.at },
    events: { luminance: lumEv.map((f) => +(f / fps).toFixed(3)), red: redEv.map((f) => +(f / fps).toFixed(3)) },
  };
}
