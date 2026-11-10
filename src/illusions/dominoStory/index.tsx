import React, { useMemo } from "react";
import { useCurrentFrame } from "remotion";
import type { z } from "zod";
import { defineEffect, type EffectDef } from "../../core/effect";
import type { Timeline } from "../../core/timing";
import { DominoScene } from "../../scenes/dominoes/DominoScene";
import { simulateDominoes } from "../../scenes/dominoes/sim";
import { dominoSchema } from "./schema";

type P = z.output<typeof dominoSchema>;

function Story({ params, tl, offset }: { params: P; tl: Timeline; offset: number }) {
  const frame = useCurrentFrame() + offset;
  const sim = useMemo(() => simulateDominoes(tl.fps, params.cols, params.rows, params.spacing), [tl.fps, params.cols, params.rows, params.spacing]);
  return <DominoScene sim={sim} frame={frame} t={frame / tl.fps} look={params.look} dpr={params.dpr} zoom={params.zoom} glowBoost={params.glowBoost} />;
}

/** "The Butterfly Domino": rewind hook, a lane of dominoes, a swirling bloom reveals a butterfly, wings beat, glow fades. */
export const dominoStory: EffectDef = defineEffect({
  about: "Obsidian domino field: rewind hook -> lane -> swirling bloom reveals a glowing butterfly -> wings beat -> fade.",
  schema: dominoSchema,
  component: ({ params, tl }) => <Story params={params} tl={tl} offset={0} />,
});

export const dominoStoryContinue: EffectDef = defineEffect({
  about: "Continues dominoStory through the transform phase.",
  schema: dominoSchema,
  component: ({ params, tl }) => <Story params={params} tl={tl} offset={tl.transform.start} />,
});
