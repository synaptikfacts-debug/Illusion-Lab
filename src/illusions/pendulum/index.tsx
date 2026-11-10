import React from "react";
import { useCurrentFrame } from "remotion";
import type { z } from "zod";
import { defineEffect, type EffectDef } from "../../core/effect";
import type { Timeline } from "../../core/timing";
import { PendulumScene } from "../../scenes/pendulum/PendulumScene";
import { pendulumSchema } from "./schema";

type P = z.output<typeof pendulumSchema>;

function Story({ params, tl, offset }: { params: P; tl: Timeline; offset: number }) {
  const frame = useCurrentFrame() + offset;
  return <PendulumScene t={frame / tl.fps} dpr={params.dpr} zoom={params.zoom} />;
}

/** "Pendulum Helix": 5 tiers x 30 glossy pendulums in a dark studio - snakes, helices, line-up, stillness. */
export const pendulum: EffectDef = defineEffect({
  about: "Pendulum-wave sculpture: tiers of glossy spheres swing into snakes and helices, line up, then hang still.",
  schema: pendulumSchema,
  component: ({ params, tl }) => <Story params={params} tl={tl} offset={0} />,
});

export const pendulumContinue: EffectDef = defineEffect({
  about: "Continues pendulum through the transform phase.",
  schema: pendulumSchema,
  component: ({ params, tl }) => <Story params={params} tl={tl} offset={tl.transform.start} />,
});
