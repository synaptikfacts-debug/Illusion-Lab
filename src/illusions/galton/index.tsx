import React, { useMemo } from "react";
import { useCurrentFrame } from "remotion";
import type { z } from "zod";
import { defineEffect, type EffectDef } from "../../core/effect";
import type { Timeline } from "../../core/timing";
import { buildMarbles } from "../../scenes/galton/galton";
import { GaltonScene } from "../../scenes/galton/GaltonScene";
import { galtonSchema } from "./schema";

type P = z.output<typeof galtonSchema>;

function Story({ params, tl, offset, seed }: { params: P; tl: Timeline; offset: number; seed: number }) {
  const frame = useCurrentFrame() + offset;
  const marbles = useMemo(() => buildMarbles(seed), [seed]);
  return <GaltonScene marbles={marbles} t={frame / tl.fps} dpr={params.dpr} zoom={params.zoom} />;
}

/** "Marble Cascade": glossy marbles through chrome pins stack into a rainbow bell curve; a gold marble tops it. */
export const galton: EffectDef = defineEffect({
  about: "Galton board: 1500 glossy marbles through chrome pins into a rainbow bell curve, gold marble finale.",
  schema: galtonSchema,
  component: ({ params, reel, tl }) => <Story params={params} tl={tl} offset={0} seed={reel.seed} />,
});

export const galtonContinue: EffectDef = defineEffect({
  about: "Continues galton through the transform phase.",
  schema: galtonSchema,
  component: ({ params, reel, tl }) => <Story params={params} tl={tl} offset={tl.transform.start} seed={reel.seed} />,
});
