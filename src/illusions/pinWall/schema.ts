import { z } from "zod";

// Pure zod (no React/three) so the melody generator can parse the same params.
const hex = z.string().regex(/^#[0-9a-fA-F]{6}$/);

export const pinSchema = z.object({
  grid: z.number().int().min(8).max(96).default(48),
  spacing: z.number().default(0.125),
  maxHeight: z.number().default(1.1),
  /** 0 = use the reel length (must match it for a seamless loop). */
  loopSec: z.number().default(0),
  /** Even number of up/down cycles per loop (fast near the loop point, still when the picture forms). */
  baseCycles: z.number().int().min(2).default(20),
  ripple: z.number().default(2.5),
  image: z.enum(["eye", "star", "spiral", "rings"]).default("eye"),
  /** Where in the loop the video starts (0..1), so frame 1 is already moving. */
  startAt: z.number().min(0).max(1).default(0.08),
  sway: z.number().default(0.3),
  look: z
    .object({ background: hex, tips: z.array(hex).min(2), shaft: hex })
    .default({ background: "#03040a", tips: ["#3b1aa8", "#a23dff", "#22e3ff", "#f2fdff"], shaft: "#3a3f52" }),
  /** Melody: MIDI root note and every Nth pin plays. */
  rootNote: z.number().int().default(57),
  voiceEvery: z.number().int().min(1).default(3),
});
