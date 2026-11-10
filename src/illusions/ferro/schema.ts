import { z } from "zod";

export const ferroSchema = z.object({
  dpr: z.number().min(1).max(3).default(2),
  zoom: z.number().min(0.2).max(2).default(1),
});
