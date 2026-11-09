import React from "react";
import { Easing, interpolate, useCurrentFrame } from "remotion";
import { z } from "zod";
import { defineEffect } from "../../core/effect";
import { sculptureLookSchema } from "../../illusions/livingAfterimage";
import { SculptureScene } from "../../scenes/sculpture/SculptureScene";

const schema = z.object({
  look: sculptureLookSchema.default({ bg0: "#070a24", bg1: "#2a1260", tint: "#22e3ff", tint2: "#ff3fd8" }),
  count: z.number().int().min(1000).max(200000).default(60000),
  /** Seconds the colour takes to return after the grayscale reveal. */
  colourBackSec: z.number().default(0.6),
});

/**
 * Pairs with livingAfterimage: the sculpture wakes up in colour, bursts into particles that swirl into a galaxy,
 * then the galaxy pulls back into the sculpture in its frame-0 pose (seamless loop).
 */
export const particleGalaxy = defineEffect({
  about: "Sculpture bursts into 60k particles -> spinning galaxy -> reforms into the sculpture (loops).",
  schema,
  component: ({ params, reel, tl }) => {
    const f = useCurrentFrame();
    const sec = f / tl.fps;
    const dur = (tl.transform.dur - tl.bridge.dur) / tl.fps;
    const p = interpolate(sec, [0, dur], [0, 1], { extrapolateRight: "clamp", easing: Easing.inOut(Easing.sin) });
    const startTime = tl.hook.end / tl.fps;
    const homeTime = 0; // particles land on the frame-0 pose
    const colour = interpolate(sec, [0, params.colourBackSec], [1, 0], { extrapolateRight: "clamp" });
    const out = interpolate(p, [0.04, 0.3], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    const back = interpolate(p, [0.84, 0.99], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    // sculpture keeps living while it dissolves; reappears in the exact frame-0 pose so the loop has no ghost
    const time = p < 0.5 ? startTime + sec : 0;
    return (
      <SculptureScene
        seed={reel.seed}
        look={params.look}
        focusY={reel.challenge.focus.y}
        state={{
          time,
          bgTime: startTime + sec,
          gray: colour,
          bgMix: colour,
          obj: p < 0.5 ? out : back,
          particles: { p, t: sec, startTime, homeTime, count: params.count },
        }}
      />
    );
  },
});
