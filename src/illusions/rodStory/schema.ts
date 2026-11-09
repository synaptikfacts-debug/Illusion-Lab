import { z } from "zod";

const hex = z.string().regex(/^#[0-9a-fA-F]{6}$/);

// Pure zod (no React/three) so the sound generators can parse the same params.
export const rodSchema = z.object({
  grid: z.number().int().min(8).max(64).default(31),
  rows: z.number().int().min(8).max(96).default(55),
  spacing: z.number().default(0.14),
  /** Supersampling factor for the 3D render (2 = render at 2x and downsample: clean HD edges). */
  dpr: z.number().min(1).max(3).default(2),
  look: z
    .object({ rod: hex, plate: hex, background: hex, glowA: hex, glowB: hex, key: hex, rim: hex })
    .default({ rod: "#8d939e", plate: "#14161b", background: "#06070a", glowA: "#2fd8ff", glowB: "#ffb347", key: "#fff1e0", rim: "#9cc8ff" }),
});
