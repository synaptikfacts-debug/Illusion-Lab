import React, { useMemo } from "react";
import { useCurrentFrame } from "remotion";
import type { z } from "zod";
import { defineEffect, type EffectDef } from "../../core/effect";
import type { Timeline } from "../../core/timing";
import { LiquidScene } from "../../scenes/liquid/LiquidScene";
import { drops } from "../../scenes/liquid/waves";
import { liquidSchema } from "./schema";

type P = z.output<typeof liquidSchema>;

function Story({ params, tl, offset, seed }: { params: P; tl: Timeline; offset: number; seed: number }) {
  const frame = useCurrentFrame() + offset;
  const d = useMemo(() => drops(seed), [seed]);
  return <LiquidScene drops={d} t={frame / tl.fps} dpr={params.dpr} zoom={params.zoom} />;
}

/** "Liquid Obsidian": mirror-black liquid with neon reflections: crater hook, interference, rain, standing-wave star, vortex, collapse, calm. */
export const liquid: EffectDef = defineEffect({
  about: "Mirror-black liquid surface with neon reflections: impact rings, interference, rain, cymatic star, vortex, collapse, calm.",
  schema: liquidSchema,
  component: ({ params, reel, tl }) => <Story params={params} tl={tl} offset={0} seed={reel.seed} />,
});

export const liquidContinue: EffectDef = defineEffect({
  about: "Continues liquid through the transform phase.",
  schema: liquidSchema,
  component: ({ params, reel, tl }) => <Story params={params} tl={tl} offset={tl.transform.start} seed={reel.seed} />,
});
