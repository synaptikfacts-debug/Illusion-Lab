import React, { useMemo } from "react";
import { useCurrentFrame } from "remotion";
import type { z } from "zod";
import { defineEffect, type EffectDef } from "../../core/effect";
import type { Timeline } from "../../core/timing";
import { buildSand } from "../../scenes/sand/chladni";
import { SandScene } from "../../scenes/sand/SandScene";
import { sandSchema } from "./schema";

type P = z.output<typeof sandSchema>;

function Story({ params, tl, offset, seed }: { params: P; tl: Timeline; offset: number; seed: number }) {
  const frame = useCurrentFrame() + offset;
  const sand = useMemo(() => buildSand(seed, params.grains), [seed, params.grains]);
  return <SandScene sand={sand} t={frame / tl.fps} dpr={params.dpr} zoom={params.zoom} />;
}

/** "Sand Song": coloured sand on a vibrating plate hops into ever more complex Chladni figures. */
export const sand: EffectDef = defineEffect({
  about: "Coloured sand on a vibrating plate jumps into Chladni figures, one tone after another, then settles.",
  schema: sandSchema,
  component: ({ params, reel, tl }) => <Story params={params} tl={tl} offset={0} seed={reel.seed} />,
});

export const sandContinue: EffectDef = defineEffect({
  about: "Continues sand through the transform phase.",
  schema: sandSchema,
  component: ({ params, reel, tl }) => <Story params={params} tl={tl} offset={tl.transform.start} seed={reel.seed} />,
});
