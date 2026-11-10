// "Golden Rings": a kinetic sculpture of ~44 concentric polished gold rings floating in a deep emerald void.
// Each ring tilts on a swinging axis with a phase offset by radius: de-phased they form spiral staircases and
// breathing domes; the offset slowly unwinds until every ring swings as ONE (sync moment), then the swing dies
// down and the rings settle into a flat, still disc stack (ending). Closed-form, shared with the sound generator.
// Every-reel-different check: last three = rainbow orbs / black mirror, neon liquid, chrome rods. This one =
// polished gold rings, deep emerald, soft airy swishes.

export const RP = {
  count: 44,
  r0: 0.3, // innermost ring radius
  dr: 0.082, // radius step
  tube: 0.03,
  f: 0.17, // swing frequency (Hz): slow, dreamy
  K: 1.25, // max phase spread across the rings (cycles): an ordered spiral, never a tangle
  unwind: [11.0, 23.5] as [number, number], // spread K -> 0 (rings fall into step)
  syncAt: 23.5,
  decay: [24.8, 28.4] as [number, number], // amplitude -> 0 (the swing dies down)
  ampMax: 0.5, // max tilt (rad)
  duration: 30,
  fade: [27.8, 29.8] as [number, number],
};

const sm = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

export const spread = (t: number) => RP.K * (1 - sm(RP.unwind[0], RP.unwind[1], t));
export const amp = (t: number) => RP.ampMax * (1 - sm(RP.decay[0], RP.decay[1], t));

/** Swing phase argument of ring i at time t (radians). */
export function phaseArg(i: number, t: number) {
  return 2 * Math.PI * (RP.f * t + spread(t) * (i / (RP.count - 1)));
}

/** Ring i at time t: tilt about its swing axis (rad) and the slow precession of that axis (rad). */
export function ringAt(i: number, t: number) {
  const tilt = amp(t) * Math.sin(phaseArg(i, t));
  const axis = 0.16 * t + i * 0.016; // the swing axis slowly precesses, a touch more per ring
  return { tilt, axis, radius: RP.r0 + i * RP.dr };
}

/** Swish events for sound: each ring passing through flat (max speed), with its current swing energy. */
export function swishes(): { t: number; i: number; e: number }[] {
  const out: { t: number; i: number; e: number }[] = [];
  const dt = 0.004;
  for (let i = 0; i < RP.count; i++) {
    let prev = Math.sin(phaseArg(i, 0));
    for (let t = dt; t < RP.decay[1]; t += dt) {
      const cur = Math.sin(phaseArg(i, t));
      if ((prev < 0 && cur >= 0) || (prev > 0 && cur <= 0)) out.push({ t, i, e: amp(t) / RP.ampMax });
      prev = cur;
    }
  }
  return out.sort((a, b) => a.t - b.t);
}
