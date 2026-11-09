import React from "react";
import { Easing, interpolate, useCurrentFrame } from "remotion";
import { z } from "zod";
import { defineEffect } from "../../core/effect";
import { rgb, ShaderPlane, vec2 } from "../../gl/ShaderPlane";
import frag from "./vortex.frag.glsl";

const schema = z.object({
  speed: z.number().default(0.8),
  density: z.number().default(7),
  glow: z.string().default("#ffffff"),
});

export const vortexBloom = defineEffect({
  about: "Placeholder: ring field twists into a vortex, blooms once, settles on the background.",
  schema,
  component: ({ params, reel, tl }) => {
    const frame = useCurrentFrame();
    // finish the morph before the loop bridge starts
    const p = interpolate(frame, [0, tl.transform.dur - tl.bridge.dur], [0, 1], {
      extrapolateRight: "clamp",
      easing: Easing.inOut(Easing.cubic),
    });
    return (
      <ShaderPlane
        frag={frag}
        uniforms={{
          uP: p,
          uTime: tl.challenge.end / tl.fps,
          uSpeed: params.speed,
          uDensity: params.density,
          uFocus: vec2(reel.challenge.focus.x, reel.challenge.focus.y),
          uA: rgb(reel.palette.accent),
          uB: rgb(reel.palette.accent2),
          uBg: rgb(reel.palette.bg),
          uGlow: rgb(params.glow),
        }}
      />
    );
  },
});
