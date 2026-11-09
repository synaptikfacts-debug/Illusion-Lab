// npm run flashcheck -- path/to/video.mp4   (also runs automatically inside every render)
import { flashCheck } from "./lib/flash";

const file = process.argv[2];
if (!file) {
  console.error("usage: npm run flashcheck -- <video.mp4>");
  process.exit(1);
}
const r = await flashCheck(file);
console.log(JSON.stringify({ ...r, events: undefined }, null, 2));
console.log(r.pass ? "PASS" : "FAIL");
process.exit(r.pass ? 0 : 1);
