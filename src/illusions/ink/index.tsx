import React from "react";
import { useCurrentFrame } from "remotion";
import type { z } from "zod";
import { defineEffect, type EffectDef } from "../../core/effect";
import type { Timeline } from "../../core/timing";
import { InkScene } from "../../scenes/ink/InkScene";
import { inkSchema } from "./schema";

type P = z.output<typeof inkSchema>;

function Story({ params, tl, offset }: { params: P; tl: Timeline; offset: number }) {
  const frame = useCurrentFrame() + offset;
  return <InkScene t={frame / tl.fps + params.t0} dpr={params.dpr} />;
}

/** "Ink and Water": glowing inks drop into dark water, bloom, marble in the currents, wind into one vortex, settle. */
export const ink: EffectDef = defineEffect({
  about: "Ink and Water: glowing inks bloom in dark water, marble in slow currents, spiral into a vortex, then settle.",
  schema: inkSchema,
  component: ({ params, tl }) => <Story params={params} tl={tl} offset={0} />,
});

export const inkContinue: EffectDef = defineEffect({
  about: "Continues ink through the transform phase.",
  schema: inkSchema,
  component: ({ params, tl }) => <Story params={params} tl={tl} offset={tl.transform.start} />,
});
