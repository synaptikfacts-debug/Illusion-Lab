import React from "react";
import { useCurrentFrame } from "remotion";
import type { z } from "zod";
import { defineEffect, type EffectDef } from "../../core/effect";
import type { Timeline } from "../../core/timing";
import { PinShowScene } from "../../scenes/pins/PinShowScene";
import { pinShowSchema } from "./schema";

type P = z.output<typeof pinShowSchema>;

function Story({ params, tl, offset }: { params: P; tl: Timeline; offset: number }) {
  const frame = useCurrentFrame() + offset;
  return <PinShowScene t={frame / tl.fps} dpr={params.dpr} />;
}

/** "Singing Pins: the long show": 4096 pins race in waves and freeze into rings, star, spiral, mandala, then melt calm. */
export const pinShow: EffectDef = defineEffect({
  about: "4096 glowing pins: waves freeze into four abstract pictures over a minute, then melt into a calm mirror.",
  schema: pinShowSchema,
  component: ({ params, tl }) => <Story params={params} tl={tl} offset={0} />,
});

export const pinShowContinue: EffectDef = defineEffect({
  about: "Continues pinShow through the transform phase.",
  schema: pinShowSchema,
  component: ({ params, tl }) => <Story params={params} tl={tl} offset={tl.transform.start} />,
});
