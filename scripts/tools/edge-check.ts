// Edge-band check for a finished video (Instagram flagged 0018 "your video has a border"): prints flat-edge shares.
// NOTE: thin smeared bands can still pass - also measure flat rows/columns at several times (see HANDOFF.md, 0028).
// Usage: npx tsx scripts/tools/edge-check.ts <video.mp4>
import { edgeCheck } from "../lib/edges";

const FILE_ARG = 2;
console.log(JSON.stringify(edgeCheck(process.argv[FILE_ARG]), null, 1));
