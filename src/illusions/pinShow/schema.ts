import { z } from "zod";

export const pinShowSchema = z.object({
  dpr: z.number().min(1).max(3).default(2),
});
