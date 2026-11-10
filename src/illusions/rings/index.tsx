import React from "react";
import { useCurrentFrame } from "remotion";
import type { z } from "zod";
import { defineEffect, type EffectDef } from "../../core/effect";
import type { Timeline } from "../../core/timing";
import { RingScene } from "../../scenes/rings/RingScene";
import { ringsSchema } from "./schema";

type P = z.output<typeof ringsSchema>;

function Story({ params, tl, offset }: { params: P; tl: Timeline; offset: number }) {
  const frame = useCurrentFrame() + offset;
  return <RingScene t={frame / tl.fps} dpr={params.dpr} zoom={params.zoom} />;
}

/** "Golden Rings": concentric gold rings swing with offset phases (spiral staircases, domes), fall into step, settle. */
export const rings: EffectDef = defineEffect({
  about: "Kinetic sculpture of 44 gold rings: phase-offset swings form spirals and domes, sync into one, settle flat.",
  schema: ringsSchema,
  component: ({ params, tl }) => <Story params={params} tl={tl} offset={0} />,
});

export const ringsContinue: EffectDef = defineEffect({
  about: "Continues rings through the transform phase.",
  schema: ringsSchema,
  component: ({ params, tl }) => <Story params={params} tl={tl} offset={tl.transform.start} />,
});
