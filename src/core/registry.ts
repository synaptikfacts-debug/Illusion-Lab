import type { EffectDef } from "./effect";
import { bounceField, bounceFieldContinue } from "../illusions/bounceField";
import { dominoStory, dominoStoryContinue } from "../illusions/dominoStory";
import { expandingRings } from "../illusions/expandingRings";
import { faceStory, faceStoryContinue } from "../illusions/faceStory";
import { pinWall, pinWallContinue } from "../illusions/pinWall";
import { rodStory, rodStoryContinue } from "../illusions/rodStory";
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
  pinWall,
  rodStory,
  dominoStory,
  faceStory,
};

export const TRANSFORMS: Record<string, EffectDef> = {
  vortexBloom,
  morphChain,
  bounceFieldContinue,
  pinWallContinue,
  rodStoryContinue,
  dominoStoryContinue,
  faceStoryContinue,
};

export function getEffect(kind: "illusion" | "transform", type: string): EffectDef {
  const table = kind === "illusion" ? ILLUSIONS : TRANSFORMS;
  const def = table[type];
  if (!def) throw new Error(`Unknown ${kind} "${type}". Known: ${Object.keys(table).join(", ")}`);
  return def;
}
