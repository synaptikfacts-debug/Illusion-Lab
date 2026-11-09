import { z } from "zod";

// Pure zod (no React/three) so Node scripts (click-track generator) can parse the same params.
const hex = z.string().regex(/^#[0-9a-fA-F]{6}$/);

export const bounceSchema = z.object({
  count: z.number().int().min(100).max(8000).default(3000),
  discRadius: z.number().default(3),
  ballRadius: z.number().default(0.042),
  height: z.number().default(2.3),
  /** Must equal the reel length so every orb is back on top at the loop point. 0 = use the reel length. */
  loopSec: z.number().default(0),
  /** Bounces per loop; must be > pi * spread so no orb ever runs backwards. */
  baseBounces: z.number().int().min(1).default(24),
  /** Max centre-to-edge phase difference (bounces), reached mid-loop. More = more complex shapes. */
  spread: z.number().min(0).default(3),
  centerFast: z.boolean().default(true),
  sizeJitter: z.number().min(0).max(1).default(0.25),
  /** Camera sway amplitude (rad); completes whole cycles per loop. */
  sway: z.number().default(0.35),
  look: z
    .object({ background: hex, plate: hex, gradient: z.array(hex).min(2) })
    .default({ background: "#04050b", plate: "#e8ecf5", gradient: ["#ffffff", "#7df9ff", "#3a7bff", "#a23dff", "#ff2fa8"] }),
});
