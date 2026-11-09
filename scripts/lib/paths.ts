import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
export const REELS = join(ROOT, "reels");
export const ASSETS = join(ROOT, "assets");
export const OUT = join(ROOT, "out");
export const PUBLISH = join(ROOT, "publish");
export const ENTRY = join(ROOT, "src/index.ts");
