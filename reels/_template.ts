import { defineReel } from "../src/core/define";

// Template for `npm run new -- NNNN-name`. Times are seconds, or phase-relative strings
// like "challenge+2", "reveal-0.5", "end-3". Effects: see src/core/registry.ts.
export default defineReel({
  id: "__ID__",
  title: "__TITLE__",
  seed: 0, // set from the reel id by `npm run new`
  palette: { bg: "#0b0f2a", fg: "#ffd166", accent: "#ef476f", accent2: "#118ab2" },
  hook: { text: "Stare at the dot", sub: "15 seconds. Don't look away." },
  challenge: { instruction: "Keep staring...", countdown: true, focus: { x: 0.5, y: 0.5 } },
  reveal: { text: "Now look!" },
  endText: "Did it work on you? 👇",
  phases: { hook: 1.5, challenge: 18, reveal: 6, transform: 4.5 },
  loopBridgeSec: 0.6,
  illusion: { type: "expandingRings", props: {} },
  transform: { type: "vortexBloom", props: {} },
  intense: false,
  audio: {
    music: "music/inhouse-bed-a.wav",
    musicVolume: 0.6,
    vo: null, // e.g. "vo/0001.wav" - then add captions below
    sfx: [
      { at: "transform-2", file: "sfx/inhouse-riser.wav" },
      { at: "transform+1.6", file: "sfx/inhouse-impact.wav" },
    ],
  },
  captions: [
    // { at: "challenge+1", dur: 2.5, text: "Keep your eyes on the dot" },
  ],
  cover: { at: 0.8, title: "Stare test", sub: "Does it work on you?" },
  publish: {
    youtube: { title: "", caption: "", hashtags: ["#shorts", "#illusion", "#opticalillusion"] },
    instagram: { caption: "", hashtags: ["#reels", "#opticalillusion", "#illusion"] },
    facebook: { caption: "", hashtags: ["#reels", "#opticalillusion"] },
    tiktok: { caption: "", hashtags: ["#fyp", "#opticalillusion", "#illusion"] },
    x: { caption: "", hashtags: ["#opticalillusion"] },
  },
});
