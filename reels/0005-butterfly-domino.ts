import { defineReel } from "../src/core/define";

// Model (formula only): many simple objects with their own motion, emergent picture, motion-made sound.
// Ours (different from 0004 rods): 3432 obsidian dominoes whose hidden faces form a glowing butterfly.
//  0-1.4   HOOK: low and close INSIDE the crashing swirl: glowing faces flipping toward the camera, sparks flying
//  1.4-2.3 REWIND: time visibly runs backwards (tape rewind look + sound), everything un-falls, camera whips up
//  2.5-5.6 a single gold fuse line clicks up the centre (low macro tracking, spark riding the chain)
//  5.6-13.5 the burst: a swirling spiral topples outward, faces land with sparks and light up -> the butterfly
//  15-25.5 it comes alive: 6 wing beats shedding golden dust, camera arcs to 3/4 views so the wings lift in 3D
//  25.5-32 ENDING: it dissolves into rising golden dust from the wingtips in, body last, fade to black
const d = { cols: 44, rows: 78, spacing: 0.1, dpr: 2 };

export default defineReel({
  id: "0005-butterfly-domino",
  title: "3432 dominoes hide a butterfly",
  seed: 5005,
  palette: { bg: "#050409", fg: "#e0309c", accent: "#e0309c", accent2: "#ffc24a" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 31.6 },
  loop: false,
  illusion: { type: "dominoStory", props: d },
  transform: { type: "dominoStoryContinue", props: d },
  audio: {
    musicVolume: 0.55,
    musicGen: { style: "dominoStory", bpm: 72, seed: 5 },
    sfx: [{ at: 0, file: "generated/0005-butterfly-domino-sfx.wav", volume: 1 }],
  },
  cover: { at: 15.0 },
  publish: {
    youtube: {
      title: "3432 dominoes are hiding a butterfly",
      caption: "Every domino has a coloured face underneath. Watch what they make when they fall.",
      hashtags: ["#shorts", "#satisfying", "#dominoes"],
    },
    instagram: {
      caption: "3432 dominoes. One hidden butterfly.",
      hashtags: ["#reels", "#oddlysatisfying", "#dominoes", "#3danimation", "#satisfying"],
    },
    facebook: { caption: "3432 dominoes. One hidden butterfly.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "wait for the wings", hashtags: ["#fyp", "#oddlysatisfying", "#dominoes", "#3danimation"] },
    x: { caption: "3432 dominoes. One hidden butterfly.", hashtags: ["#satisfying"] },
  },
});
