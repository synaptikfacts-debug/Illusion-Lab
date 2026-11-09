import type { ReelInput } from "./schema";

/** Typed helper for reel config files: `export default defineReel({...})`. Validation happens on load. */
export const defineReel = (reel: ReelInput): ReelInput => reel;
