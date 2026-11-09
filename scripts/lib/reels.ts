import { existsSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { ReelSchema, type Reel } from "../../src/core/schema";
import { ASSETS, REELS } from "./paths";

export function listReelIds(): string[] {
  return readdirSync(REELS)
    .filter((f) => /^\d{4}-[\w-]+\.ts$/.test(f))
    .map((f) => f.replace(/\.ts$/, ""))
    .sort();
}

export async function loadReel(id: string): Promise<Reel> {
  const file = join(REELS, `${id}.ts`);
  if (!existsSync(file)) throw new Error(`No reel config at reels/${id}.ts`);
  const mod = await import(pathToFileURL(file).href);
  const parsed = ReelSchema.safeParse(mod.default);
  if (!parsed.success) {
    const msg = parsed.error.issues.map((i) => `  ${i.path.join(".")}: ${i.message}`).join("\n");
    throw new Error(`reels/${id}.ts is invalid:\n${msg}`);
  }
  if (parsed.data.id !== id) throw new Error(`reels/${id}.ts has id "${parsed.data.id}" - it must match the file name`);
  return parsed.data;
}

/** Every asset path the reel references, so a missing file fails before rendering starts. */
export function assetPaths(reel: Reel): string[] {
  const a = reel.audio;
  return [a.music, a.vo, ...a.sfx.map((s) => s.file)].filter((p): p is string => !!p).map((p) => join(ASSETS, p));
}
