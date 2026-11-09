import React from "react";
import { useCurrentFrame } from "remotion";
import { z } from "zod";
import { defineEffect } from "../../core/effect";
import { orbit, SculptureScene } from "../../scenes/sculpture/SculptureScene";
import { sculptureLookSchema } from "../livingAfterimage";

const schema = z.object({
  look: sculptureLookSchema.default({ bg0: "#070a24", bg1: "#2a1260", tint: "#22e3ff", tint2: "#ff3fd8" }),
});

/** Pure visual opener: the living chrome sculpture, slowly orbiting. No text, no task. */
export const livingSculpture = defineEffect({
  about: "Living liquid-chrome sculpture with droplets, orbiting camera; pure visual hook.",
  schema,
  component: ({ params, reel, tl }) => {
    const g = useCurrentFrame() / tl.fps;
    return (
      <SculptureScene
        seed={reel.seed}
        look={params.look}
        focusY={reel.challenge.focus.y}
        state={{ time: g, bgTime: g, ...orbit(g, tl.total / tl.fps) }}
      />
    );
  },
});
