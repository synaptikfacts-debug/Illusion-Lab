import React, { useMemo } from "react";
import { useCurrentFrame } from "remotion";
import type { z } from "zod";
import { defineEffect, type EffectDef } from "../../core/effect";
import type { Timeline } from "../../core/timing";
import { face, faceParticles, FSTORY, simulateFace } from "../../scenes/rods/faceSim";
import { RodScene, type RodStoryView } from "../../scenes/rods/RodScene";
import { faceSchema } from "./schema";

type P = z.output<typeof faceSchema>;

/** Camera [t, px, py, pz, lx, ly, lz]: close on the staring face, whip back with the shatter, spiral, wake, orbit,
 *  push in on the wink, ease back for the laugh, rise away as it sinks. */
const FACE_CAM: number[][] = [
  [0.0, 0, 9.6, 1.2, 0, 0, -0.3],
  [0.6, 0, 8.9, 1.1, 0, 0, -0.3],
  [1.7, 0, 10.8, 5.4, 0, 0, 0],
  [3.6, 0, 7.4, 7.4, 0, 0, 0],
  [5.2, 0, 6.4, 7.2, 0, 0, 0],
  [8.6, -1.4, 9.4, 6.2, 0, 0, 0],
  [12.2, 0, 13.3, 3.0, 0, 0, -0.1],
  [13.6, 0, 11.4, 2.0, 0, 0, -0.25],
  [16.0, 0.9, 10.8, 2.6, 0, 0, -0.25],
  [18.4, -0.8, 10.2, 2.4, 0, 0, -0.25],
  [19.4, 0.2, 9.0, 1.7, 0.18, 0, -0.5],
  [20.8, 0, 10.4, 2.2, 0, 0, -0.25],
  [23.0, 0, 11.0, 2.2, 0, 0, -0.25],
  [24.6, 0, 12.4, 2.6, 0, 0, -0.2],
  [27.2, 0, 15.0, 3.6, 0, 0.2, -0.2],
  [30.5, 0, 17.0, 4.2, 0, 0.4, -0.2],
];

function Story({ params, tl, offset, seed }: { params: P; tl: Timeline; offset: number; seed: number }) {
  const frame = useCurrentFrame() + offset;
  const sim = useMemo(() => simulateFace(tl.fps, params.grid, params.rows, params.spacing), [tl.fps, params.grid, params.rows, params.spacing]);
  const view = useMemo<RodStoryView>(
    () => ({ cam: FACE_CAM, fade: FSTORY.fade, thumbInside: (u, v, t) => face(u, v, t).white, parts: faceParticles(sim, seed) }),
    [sim, seed],
  );
  return <RodScene sim={sim} frame={frame} t={frame / tl.fps} look={params.look} dpr={params.dpr} zoom={params.zoom} glowBoost={params.glowBoost} view={view} />;
}

/** "The Face": chrome rod face stares, shatters, rebuilds, wakes, looks around, smiles, winks, laughs, sleeps, sinks. */
export const faceStory: EffectDef = defineEffect({
  about: "Chrome rod wall forms a living face: shatter hook, rebuild, wake, wink, laugh, closes its eyes, sinks (ending).",
  schema: faceSchema,
  component: ({ params, reel, tl }) => <Story params={params} tl={tl} offset={0} seed={reel.seed} />,
});

export const faceStoryContinue: EffectDef = defineEffect({
  about: "Continues faceStory through the transform phase.",
  schema: faceSchema,
  component: ({ params, reel, tl }) => <Story params={params} tl={tl} offset={tl.transform.start} seed={reel.seed} />,
});
