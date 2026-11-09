import React from "react";
import { useCurrentFrame } from "remotion";
import type { z } from "zod";
import { defineEffect, type EffectDef } from "../../core/effect";
import type { Reel } from "../../core/schema";
import type { Timeline } from "../../core/timing";
import { PinScene } from "../../scenes/pins/PinScene";
import { pinSchema } from "./schema";

type P = z.output<typeof pinSchema>;

/** Seconds into the pin loop for a given absolute frame (same formula as the melody generator). */
export function pinTime(frame: number, params: P, tl: Timeline) {
  const L = params.loopSec || tl.total / tl.fps;
  return { t: (frame / tl.fps + params.startAt * L) % L, L };
}

function Wall({ params, tl, offset }: { params: P; reel: Reel; tl: Timeline; offset: number }) {
  const { t, L } = pinTime(useCurrentFrame() + offset, params, tl);
  return <PinScene t={t} params={{ ...params, loopSec: L }} look={params.look} sway={params.sway * Math.sin((2 * Math.PI * t) / L)} />;
}

/** 2304 singing pins: ripples and standing waves, pause to form a hidden picture, dissolve, loop. */
export const pinWall: EffectDef = defineEffect({
  about: "Grid of glowing pins with their own phases: waves -> hidden picture mid-loop -> waves; melody from the pins.",
  schema: pinSchema,
  component: ({ params, reel, tl }) => <Wall params={params} reel={reel} tl={tl} offset={0} />,
});

export const pinWallContinue: EffectDef = defineEffect({
  about: "Continues pinWall through the transform phase (one continuous piece).",
  schema: pinSchema,
  component: ({ params, reel, tl }) => <Wall params={params} reel={reel} tl={tl} offset={tl.transform.start} />,
});
