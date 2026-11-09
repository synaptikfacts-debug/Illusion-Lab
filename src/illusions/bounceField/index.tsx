import React from "react";
import { useCurrentFrame } from "remotion";
import type { z } from "zod";
import { defineEffect, type EffectDef } from "../../core/effect";
import type { Reel } from "../../core/schema";
import type { Timeline } from "../../core/timing";
import { BounceScene } from "../../scenes/bounce/BounceScene";
import { bounceSchema } from "./schema";

type P = z.output<typeof bounceSchema>;

function Field({ params, reel, tl, offset }: { params: P; reel: Reel; tl: Timeline; offset: number }) {
  const f = useCurrentFrame() + offset;
  const loopSec = params.loopSec || tl.total / tl.fps;
  const t = f / tl.fps;
  return (
    <BounceScene
      t={t}
      seed={reel.seed}
      params={{ ...params, loopSec }}
      look={params.look}
      sway={params.sway * Math.sin((2 * Math.PI * t) / loopSec)}
    />
  );
}

/** Physics-style ASMR: thousands of orbs, each bouncing at its own rhythm, folding into shapes. Loops. */
export const bounceField: EffectDef = defineEffect({
  about: "Disc of glossy orbs, each bouncing with its own period (pendulum-wave shapes); loops exactly.",
  schema: bounceSchema,
  component: ({ params, reel, tl }) => <Field params={params} reel={reel} tl={tl} offset={0} />,
});

/** Same scene used as the 'transform' so a reel can be one continuous simulation. */
export const bounceFieldContinue: EffectDef = defineEffect({
  about: "Continues bounceField through the transform phase (one continuous simulation).",
  schema: bounceSchema,
  component: ({ params, reel, tl }) => <Field params={params} reel={reel} tl={tl} offset={tl.transform.start} />,
});
