import React from "react";
import { useCurrentFrame } from "remotion";
import type { z } from "zod";
import { defineEffect, type EffectDef } from "../../core/effect";
import type { Timeline } from "../../core/timing";
import { FerroScene } from "../../scenes/ferro/FerroScene";
import { ferroSchema } from "./schema";

type P = z.output<typeof ferroSchema>;

function Story({ params, tl, offset }: { params: P; tl: Timeline; offset: number }) {
  const frame = useCurrentFrame() + offset;
  return <FerroScene t={frame / tl.fps} dpr={params.dpr} zoom={params.zoom} />;
}

/** "Ferrofluid Bloom": black mirror magnetic liquid rises into spike rings, a turning spike flower and a crown, then melts. */
export const ferro: EffectDef = defineEffect({
  about: "Ferrofluid: magnet pulses raise rings of mirror-black spikes, a six-petal bloom and a crown, then it melts calm.",
  schema: ferroSchema,
  component: ({ params, tl }) => <Story params={params} tl={tl} offset={0} />,
});

export const ferroContinue: EffectDef = defineEffect({
  about: "Continues ferro through the transform phase.",
  schema: ferroSchema,
  component: ({ params, tl }) => <Story params={params} tl={tl} offset={tl.transform.start} />,
});
