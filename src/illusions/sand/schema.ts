import { z } from "zod";

export const sandSchema = z.object({
  grains: z.number().int().min(5000).max(200000).default(110000),
  dpr: z.number().min(1).max(3).default(2),
  zoom: z.number().min(0.2).max(2).default(1),
});
