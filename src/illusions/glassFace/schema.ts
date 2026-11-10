import { z } from "zod";

export const glassSchema = z.object({
  cols: z.number().int().min(16).max(80).default(60),
  dpr: z.number().min(1).max(3).default(2),
  zoom: z.number().min(0.2).max(2).default(1),
  glowBoost: z.number().min(0.5).max(3).default(1),
});
