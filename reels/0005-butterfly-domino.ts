import { defineReel } from "../src/core/define";

// Model (formula only): many simple objects with their own motion, emergent picture, motion-made sound.
// Ours (different from 0004 rods): 3432 obsidian dominoes whose hidden faces form a glowing butterfly.
//  0-0.6   HOOK: frame 0 = the finished glowing butterfly mosaic from above
//  0.6-1.6 REWIND: every domino springs back up in a wave from the edges in ("wait... how?")
//  2.2-5   a single line clicks up the centre (low macro tracking shot)
//  5-11.5  the chain bursts into a swirling spiral that topples outward; faces land and light up: the butterfly
//  13-19.5 the butterfly comes alive: wing dominoes lift and drop in waves = wing beats (last one slow)
//  19.5-24.5 ENDING: glow fades from the wingtips inward, the body glows last, camera eases away, fade to black
const d = { cols: 44, rows: 78, spacing: 0.1, dpr: 2 };

export default defineReel({
  id: "0005-butterfly-domino",
  title: "3432 dominoes hide a butterfly",
  seed: 5005,
  palette: { bg: "#050409", fg: "#e0309c", accent: "#e0309c", accent2: "#ffc24a" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 24.0 },
  loop: false,
  illusion: { type: "dominoStory", props: d },
  transform: { type: "dominoStoryContinue", props: d },
  audio: {
    musicVolume: 0.55,
    musicGen: { style: "dominoStory", bpm: 72, seed: 5 },
    sfx: [{ at: 0, file: "generated/0005-butterfly-domino-sfx.wav", volume: 1 }],
  },
  cover: { at: 13.0 },
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
