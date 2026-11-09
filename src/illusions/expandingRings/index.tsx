import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { z } from "zod";
import { defineEffect } from "../../core/effect";
import { rgb, ShaderPlane, vec2 } from "../../gl/ShaderPlane";
import { FixationDot } from "../../overlays/FixationDot";
import frag from "./rings.frag.glsl";

const schema = z.object({
  speed: z.number().default(0.8),
  density: z.number().default(7),
  revealGray: z.number().min(0).max(1).default(0),
});

export const expandingRings = defineEffect({
  about: "Placeholder: soft rings drift outward, then freeze (they seem to shrink).",
  schema,
  component: ({ params, reel, tl }) => {
    const frame = useCurrentFrame();
    const moving = Math.min(frame, tl.challenge.end);
    const inReveal = frame >= tl.reveal.start;
    return (
      <AbsoluteFill>
        <ShaderPlane
          frag={frag}
          uniforms={{
            uTime: moving / tl.fps,
            uSpeed: params.speed,
            uDensity: params.density,
            uGray: inReveal ? params.revealGray : 0,
            uFocus: vec2(reel.challenge.focus.x, reel.challenge.focus.y),
            uA: rgb(reel.palette.accent),
            uB: rgb(reel.palette.accent2),
            uBg: rgb(reel.palette.bg),
          }}
        />
        <FixationDot reel={reel} />
      </AbsoluteFill>
    );
  },
});
