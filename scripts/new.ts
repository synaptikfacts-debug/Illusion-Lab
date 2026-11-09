// npm run new -- 0003-count-the-dots ["Optional title"]
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { hash } from "../src/core/seed";
import { REELS } from "./lib/paths";

const [id, ...titleParts] = process.argv.slice(2);
if (!id || !/^\d{4}-[a-z0-9-]+$/.test(id)) {
  console.error('usage: npm run new -- NNNN-short-name ["Title"]   (e.g. 0003-count-the-dots)');
  process.exit(1);
}
const file = join(REELS, `${id}.ts`);
if (existsSync(file)) {
  console.error(`reels/${id}.ts already exists`);
  process.exit(1);
}
const title = titleParts.join(" ") || id.slice(5).replace(/-/g, " ");
const src = readFileSync(join(REELS, "_template.ts"), "utf8")
  .replace("__ID__", id)
  .replace("__TITLE__", title.replace(/"/g, '\\"'))
  .replace(/seed: 0,.*$/m, `seed: ${hash(id) % 100000},`);
writeFileSync(file, src);
console.log(`created reels/${id}.ts - open it, then: npm run studio  (or npm run render -- ${id} --draft)`);
