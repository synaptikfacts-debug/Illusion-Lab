import React, { useMemo } from "react";
import { useCurrentFrame } from "remotion";
import type { z } from "zod";
import { defineEffect, type EffectDef } from "../../core/effect";
import type { Timeline } from "../../core/timing";
import { RodScene } from "../../scenes/rods/RodScene";
import { simulate } from "../../scenes/rods/sim";
import { rodSchema } from "./schema";

type P = z.output<typeof rodSchema>;

function Story({ params, tl, offset }: { params: P; tl: Timeline; offset: number }) {
  const frame = useCurrentFrame() + offset;
  const sim = useMemo(() => simulate(tl.fps, params.grid, params.rows, params.spacing), [tl.fps, params.grid, params.rows, params.spacing]);
  return <RodScene sim={sim} frame={frame} t={frame / tl.fps} look={params.look} dpr={params.dpr} />;
}

/** "The Eye": chrome rod wall with a story and an ending (pop, ripples, spiral, eye, blink, close, last rod). */
export const rodStory: EffectDef = defineEffect({
  about: "Chrome rod wall: ripples -> spiral -> snaps into a living eye -> closes -> last rod drops (ending).",
  schema: rodSchema,
  component: ({ params, tl }) => <Story params={params} tl={tl} offset={0} />,
});

export const rodStoryContinue: EffectDef = defineEffect({
  about: "Continues rodStory through the transform phase.",
  schema: rodSchema,
  component: ({ params, tl }) => <Story params={params} tl={tl} offset={tl.transform.start} />,
});
