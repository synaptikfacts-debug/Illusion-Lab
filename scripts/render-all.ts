// npm run render:all [-- --draft]  - bundles once, renders every reels/NNNN-*.ts in order.
import { bundleProject, renderReel } from "./render";
import { listReelIds } from "./lib/reels";

const draft = process.argv.includes("--draft");
const ids = listReelIds();
const serveUrl = await bundleProject();
const results: { id: string; ok: boolean; note: string }[] = [];
for (const id of ids) {
  try {
    const r = await renderReel(id, { serveUrl, draft });
    results.push({ id, ok: true, note: r.dir });
  } catch (e) {
    console.error(`\n${id} FAILED: ${(e as Error).message}`);
    results.push({ id, ok: false, note: (e as Error).message.split("\n")[0] });
  }
}
console.log("\nSummary");
for (const r of results) console.log(`  ${r.ok ? "OK  " : "FAIL"} ${r.id}  ${r.note}`);
process.exit(results.every((r) => r.ok) ? 0 : 1);
