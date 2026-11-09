import type { EffectDef } from "./effect";
import { expandingRings } from "../illusions/expandingRings";
import { vortexBloom } from "../transforms/vortexBloom";

// Add new effects here (one line each). Reels refer to them by key.
export const ILLUSIONS: Record<string, EffectDef> = {
  expandingRings,
};

export const TRANSFORMS: Record<string, EffectDef> = {
  vortexBloom,
};

export function getEffect(kind: "illusion" | "transform", type: string): EffectDef {
  const table = kind === "illusion" ? ILLUSIONS : TRANSFORMS;
  const def = table[type];
  if (!def) throw new Error(`Unknown ${kind} "${type}". Known: ${Object.keys(table).join(", ")}`);
  return def;
}
