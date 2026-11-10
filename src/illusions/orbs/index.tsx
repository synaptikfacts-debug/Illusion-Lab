import React, { useMemo } from "react";
import { useCurrentFrame } from "remotion";
import type { z } from "zod";
import { defineEffect, type EffectDef } from "../../core/effect";
import type { Timeline } from "../../core/timing";
import { OrbScene } from "../../scenes/orbs/OrbScene";
import { orbLayout } from "../../scenes/orbs/orbs";
import { orbSchema } from "./schema";

type P = z.output<typeof orbSchema>;

function Story({ params, tl, offset, seed }: { params: P; tl: Timeline; offset: number; seed: number }) {
  const frame = useCurrentFrame() + offset;
  const orbs = useMemo(() => orbLayout(seed), [seed]);
  return <OrbScene orbs={orbs} t={frame / tl.fps} dpr={params.dpr} zoom={params.zoom} />;
}

/** "Orb Waves": thousands of glossy orbs bouncing at their own rhythms, all in phase at the climax, then at rest. */
export const orbs: EffectDef = defineEffect({
  about: "Thousands of glossy orbs on a black-mirror disc, each with its own bounce rhythm; in-phase climax; settle ending.",
  schema: orbSchema,
  component: ({ params, reel, tl }) => <Story params={params} tl={tl} offset={0} seed={reel.seed} />,
});

export const orbsContinue: EffectDef = defineEffect({
  about: "Continues orbs through the transform phase.",
  schema: orbSchema,
  component: ({ params, reel, tl }) => <Story params={params} tl={tl} offset={tl.transform.start} seed={reel.seed} />,
});
