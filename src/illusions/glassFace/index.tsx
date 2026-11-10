import React, { useMemo } from "react";
import { useCurrentFrame } from "remotion";
import type { z } from "zod";
import { defineEffect, type EffectDef } from "../../core/effect";
import type { Timeline } from "../../core/timing";
import { GlassScene } from "../../scenes/glass/GlassScene";
import { glassCubes, glassParticles } from "../../scenes/glass/glassSim";
import { glassSchema } from "./schema";

type P = z.output<typeof glassSchema>;

function Story({ params, tl, offset, seed }: { params: P; tl: Timeline; offset: number; seed: number }) {
  const frame = useCurrentFrame() + offset;
  const cubes = useMemo(() => glassCubes(seed, params.cols), [seed, params.cols]);
  const parts = useMemo(() => glassParticles(cubes, seed), [cubes, seed]);
  return <GlassScene cubes={cubes} parts={parts} t={frame / tl.fps} dpr={params.dpr} zoom={params.zoom} glowBoost={params.glowBoost} />;
}

/** "The Face" v2: floating frosted-glass cubes in a dawn sky: storm, tornado, assemble, live, drift into the light. */
export const glassFace: EffectDef = defineEffect({
  about: "Glass-cube face in a dawn sky: burst storm, tornado, mid-air assembly, expressions, drifts up into the light.",
  schema: glassSchema,
  component: ({ params, reel, tl }) => <Story params={params} tl={tl} offset={0} seed={reel.seed} />,
});

export const glassFaceContinue: EffectDef = defineEffect({
  about: "Continues glassFace through the transform phase.",
  schema: glassSchema,
  component: ({ params, reel, tl }) => <Story params={params} tl={tl} offset={tl.transform.start} seed={reel.seed} />,
});
