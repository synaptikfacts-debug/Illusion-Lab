import { defineReel } from "../src/core/define";

// 0016 "Urchin Heart" (owner's pick, Nov 13): a clear purple jelly sphere on black glass with a black ferrofluid heart
// inside, ray-traced in Blender (scripts/blender/urchin.py, timeline src/scenes/urchin/timeline.json). Loops.
// Different: the two best performers (jelly sphere + ferrofluid) in one object that cannot exist.
//  0-2     HOOK: a spike inside pokes the skin out like a finger in a balloon
//  2-6     heartbeats, the jelly ripples;  6-10 the heart crawls, the sphere rolls
//  10-15   urchin: spikes press the skin out;  15-19 the sphere splits in two, halves orbit
//  22.6    they slam back together;  23.4-26.8 SIGNATURE: spikes breach the skin, the gel heals around them
//  27-30   settles into the same wobble as frame 0 (seamless loop)
const clip = { src: "generated/0016-urchin-heart.mp4" };

export default defineReel({
  id: "0016-urchin-heart",
  title: "Urchin Heart",
  seed: 1616,
  palette: { bg: "#000000", fg: "#9b5cff", accent: "#22d8ff", accent2: "#5a1aa0" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 29.5 },
  loop: true,
  loopTolerance: 12,
  illusion: { type: "clip", props: clip },
  transform: { type: "clipContinue", props: clip },
  audio: {
    lufs: -14,
    musicVolume: 0.7,
    musicGen: { style: "urchin", bpm: 60, seed: 1616 },
    sfx: [{ at: 0, file: "generated/0016-urchin-heart-sfx.wav", volume: 1 }],
  },
  cover: { at: 24.5 },
  publish: {
    youtube: { title: "Something is alive inside this jelly", caption: "A jelly sphere with a magnetic liquid heart. Rendered, not filmed.", hashtags: ["#shorts", "#satisfying", "#jelly"] },
    instagram: { caption: "Something is alive inside this jelly. Rendered, not filmed.", hashtags: ["#reels", "#satisfying", "#oddlysatisfying", "#jelly", "#ferrofluid"] },
    facebook: { caption: "Something is alive inside this jelly. Rendered, not filmed.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "something is alive inside this jelly", hashtags: ["#fyp", "#satisfying", "#oddlysatisfying", "#jelly", "#ferrofluid"] },
    x: { caption: "Something is alive inside this jelly. Rendered, not filmed.", hashtags: ["#satisfying"] },
  },
});
