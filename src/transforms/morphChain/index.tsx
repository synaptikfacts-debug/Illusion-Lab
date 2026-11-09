import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { z } from "zod";
import { defineEffect } from "../../core/effect";
import { sculptureLookSchema } from "../../illusions/livingAfterimage";
import { orbit, SculptureScene } from "../../scenes/sculpture/SculptureScene";

const schema = z.object({
  look: sculptureLookSchema.default({ bg0: "#070a24", bg1: "#2a1260", tint: "#22e3ff", tint2: "#ff3fd8" }),
  count: z.number().int().min(1000).max(200000).default(80000),
  /** Seconds after the transform starts before the sculpture bursts. */
  burstAt: z.number().default(0.4),
  /** Stage lengths in seconds: [burst->galaxy, galaxy hold, ->knot, knot hold, ->heart, heart hold, ->sculpture]. */
  stages: z.array(z.number().positive()).length(7).default([2.4, 2.4, 2.0, 2.6, 2.0, 2.6, 2.8]),
  /** Seconds the colour takes to return after a grayscale reveal (0 when the illusion is already in colour). */
  colourBackSec: z.number().default(0),
});

const ramp = (t: number, a: number, b: number) => interpolate(t, [a, b], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

/** Heartbeat: lub-dub every 0.95 s. */
const beat = (t: number) => {
  const m = t % 0.95;
  return 1 + 0.07 * (Math.exp(-(((m - 0.05) / 0.06) ** 2)) + 0.6 * Math.exp(-(((m - 0.27) / 0.06) ** 2)));
};

/**
 * The sculpture bursts (shockwave) into particles -> spinning galaxy -> flowing rainbow torus knot ->
 * beating heart -> vortex back into the sculpture in its frame-0 pose. Seamless loop, no text needed.
 */
export const morphChain = defineEffect({
  about: "Sculpture -> particles -> galaxy -> torus knot -> beating heart -> sculpture (loops).",
  schema,
  component: ({ params, reel, tl }) => {
    const f = useCurrentFrame();
    const t = f / tl.fps;
    const totalSec = tl.total / tl.fps;
    const g = (tl.transform.start + f) / tl.fps; // global seconds
    const [sOut, gHold, sKnot, kHold, sHeart, hHold, sBack] = params.stages;
    const k0 = params.burstAt;
    const k1 = k0 + sOut + gHold;
    const k2 = k1 + sKnot + kHold;
    const k3 = k2 + sHeart + hHold;
    const stages = {
      out: ramp(t, k0, k0 + sOut),
      knot: ramp(t, k1, k1 + sKnot),
      heart: ramp(t, k2, k2 + sHeart),
      back: ramp(t, k3, k3 + sBack),
      beat: beat(t - k2),
    };
    const events = [k0, k1, k2, k3 + sBack * 0.85];
    const shock = Math.min(1, ...events.map((e) => (t >= e ? (t - e) / 1.4 : 1)));
    const startTime = tl.transform.start / tl.fps + k0;
    // the sculpture lands back on the pose it had this many seconds before the loop point
    const homeTime = -(totalSec - (tl.transform.start / tl.fps + k3 + sBack * 0.9));
    const visible = t < k3 ? 1 - ramp(t, k0, k0 + 0.8) : ramp(t, k3 + sBack * 0.55, k3 + sBack * 0.95);
    // keeps living the whole time; after the return its clock runs up to exactly the frame-0 pose
    const time = t < k3 ? g : g - totalSec;
    const colour = params.colourBackSec > 0 ? 1 - ramp(t, 0, params.colourBackSec) : 0;
    return (
      <SculptureScene
        seed={reel.seed}
        look={params.look}
        focusY={reel.challenge.focus.y}
        state={{
          time,
          bgTime: g,
          ...orbit(g, totalSec),
          shock,
          gray: colour,
          bgMix: colour,
          obj: visible,
          particles: { stages, t, startTime, homeTime, count: params.count },
        }}
      />
    );
  },
});
