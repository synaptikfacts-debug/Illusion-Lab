// Phase timeline in frames. Pure (no Remotion imports) so Node scripts can use it too.

export type PhaseName = "hook" | "challenge" | "reveal" | "transform";
export interface Span {
  start: number;
  end: number; // exclusive
  dur: number;
}
export interface Timeline {
  fps: number;
  hook: Span;
  challenge: Span;
  reveal: Span;
  transform: Span;
  total: number;
  bridge: Span; // loop crossfade into frame 0
}

interface TimingInput {
  fps: number;
  phases: Record<PhaseName, number>;
  loopBridgeSec: number;
}

export function timeline(r: TimingInput): Timeline {
  const f = (s: number) => Math.round(s * r.fps);
  let t = 0;
  const span = (sec: number): Span => {
    const s = { start: t, end: t + f(sec), dur: f(sec) };
    t = s.end;
    return s;
  };
  const hook = span(r.phases.hook);
  const challenge = span(r.phases.challenge);
  const reveal = span(r.phases.reveal);
  const transform = span(r.phases.transform);
  const bdur = Math.min(f(r.loopBridgeSec), transform.dur);
  return { fps: r.fps, hook, challenge, reveal, transform, total: t, bridge: { start: t - bdur, end: t, dur: bdur } };
}

/** Resolves a TimeRef (seconds or "phase+offset") to an absolute frame. */
export function resolveTime(ref: number | string, tl: Timeline): number {
  if (typeof ref === "number") return Math.round(ref * tl.fps);
  const m = /^(hook|challenge|reveal|transform|end)([+-]\d+(?:\.\d+)?)?$/.exec(ref);
  if (!m) throw new Error(`Bad time reference: ${ref}`);
  const base = m[1] === "end" ? tl.total : tl[m[1] as PhaseName].start;
  return Math.max(0, Math.min(tl.total - 1, base + Math.round(Number(m[2] ?? 0) * tl.fps)));
}

/** 0..1 progress of `frame` through a span (clamped). */
export const progress = (frame: number, s: Span) => Math.min(1, Math.max(0, (frame - s.start) / Math.max(1, s.dur)));
