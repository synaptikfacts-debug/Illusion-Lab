import { z } from "zod";

const hex = z.string().regex(/^#[0-9a-fA-F]{6}$/);

// Pure zod (no React/three) so the sound generators can parse the same params.
export const dominoSchema = z.object({
  cols: z.number().int().min(8).max(80).default(44),
  rows: z.number().int().min(8).max(140).default(78),
  spacing: z.number().default(0.1),
  dpr: z.number().min(1).max(3).default(2),
  zoom: z.number().min(0.2).max(2).default(1),
  glowBoost: z.number().min(0.5).max(3).default(1),
  look: z
    .object({ body: hex, plate: hex, background: hex, key: hex, rim: hex })
    .default({ body: "#0c0b12", plate: "#0b0a14", background: "#050409", key: "#ffe9d6", rim: "#b9a6ff" }),
});
