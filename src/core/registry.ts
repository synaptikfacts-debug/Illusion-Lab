import type { EffectDef } from "./effect";
import { bounceField, bounceFieldContinue } from "../illusions/bounceField";
import { expandingRings } from "../illusions/expandingRings";
import { livingAfterimage } from "../illusions/livingAfterimage";
import { livingSculpture } from "../illusions/livingSculpture";
import { morphChain } from "../transforms/morphChain";
import { vortexBloom } from "../transforms/vortexBloom";

// Add new effects here (one line each). Reels refer to them by key.
export const ILLUSIONS: Record<string, EffectDef> = {
  expandingRings,
  livingAfterimage,
  livingSculpture,
  bounceField,
};

export const TRANSFORMS: Record<string, EffectDef> = {
  vortexBloom,
  morphChain,
  bounceFieldContinue,
};

export function getEffect(kind: "illusion" | "transform", type: string): EffectDef {
  const table = kind === "illusion" ? ILLUSIONS : TRANSFORMS;
  const def = table[type];
  if (!def) throw new Error(`Unknown ${kind} "${type}". Known: ${Object.keys(table).join(", ")}`);
  return def;
}
