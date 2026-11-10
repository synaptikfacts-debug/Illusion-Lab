import { z } from "zod";

export const inkSchema = z.object({
  dpr: z.number().min(1).max(3).default(2),
  zoom: z.number().min(0.2).max(2).default(1),
  /** story time (s) at the first frame: lets the reel open in the middle of the action */
  t0: z.number().default(0),
});
