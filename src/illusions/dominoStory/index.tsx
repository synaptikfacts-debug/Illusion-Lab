import React, { useMemo } from "react";
import { useCurrentFrame } from "remotion";
import type { z } from "zod";
import { defineEffect, type EffectDef } from "../../core/effect";
import type { Timeline } from "../../core/timing";
import { DominoScene } from "../../scenes/dominoes/DominoScene";
import { buildParticles } from "../../scenes/dominoes/particles";
import { simulateDominoes, tauAt } from "../../scenes/dominoes/sim";
import { dominoSchema } from "./schema";

type P = z.output<typeof dominoSchema>;

function Story({ params, tl, offset, seed }: { params: P; tl: Timeline; offset: number; seed: number }) {
  const frame = useCurrentFrame() + offset;
  const sim = useMemo(() => simulateDominoes(tl.fps, params.cols, params.rows, params.spacing), [tl.fps, params.cols, params.rows, params.spacing]);
  const parts = useMemo(() => buildParticles(sim, seed), [sim, seed]);
  const t = frame / tl.fps, tau = tauAt(t);
  const simFrame = Math.max(0, Math.min(sim.frames - 1, Math.round(tau * tl.fps)));
  return (
    <DominoScene sim={sim} parts={parts} frame={simFrame} t={t} tau={tau} look={params.look} dpr={params.dpr} zoom={params.zoom} glowBoost={params.glowBoost} />
  );
}

/** "The Butterfly Domino": rewind hook, a lane of dominoes, a swirling bloom reveals a butterfly, wings beat, glow fades. */
export const dominoStory: EffectDef = defineEffect({
  about: "Obsidian domino field: rewind hook -> lane -> swirling bloom reveals a glowing butterfly -> wings beat -> fade.",
  schema: dominoSchema,
  component: ({ params, reel, tl }) => <Story params={params} tl={tl} offset={0} seed={reel.seed} />,
});

export const dominoStoryContinue: EffectDef = defineEffect({
  about: "Continues dominoStory through the transform phase.",
  schema: dominoSchema,
  component: ({ params, reel, tl }) => <Story params={params} tl={tl} offset={tl.transform.start} seed={reel.seed} />,
});
