import type React from "react";
import type { z } from "zod";
import type { Reel } from "./schema";
import type { Timeline } from "./timing";

/**
 * Contract for every illusion and transformation.
 * - Illusions render from frame 0 until the transform begins (useCurrentFrame() = absolute frame).
 * - Transformations render inside the transform phase (useCurrentFrame() = frames since the phase began).
 * `params` = the reel's `props`, parsed with the effect's own zod schema (so defaults apply).
 */
export interface EffectProps<P = Record<string, unknown>> {
  params: P;
  reel: Reel;
  tl: Timeline;
}

export interface EffectDef<S extends z.ZodTypeAny = z.ZodTypeAny> {
  schema: S;
  component: React.FC<EffectProps<z.output<S>>>;
  about: string;
}

export const defineEffect = <S extends z.ZodTypeAny>(def: EffectDef<S>): EffectDef => def as unknown as EffectDef;
