import { defineReel } from "../src/core/define";

// Pipeline test reel: short phases so a full render takes a few minutes.
export default defineReel({
  id: "0000-placeholder",
  title: "Pipeline placeholder",
  seed: 1,
  palette: { bg: "#120a2a", fg: "#9ff7e4", accent: "#4b2bd6", accent2: "#1f9bb8" },
  hook: { text: "Stare at the red dot", sub: "Don't look away" },
  challenge: { instruction: "Keep staring...", focus: { x: 0.5, y: 0.52 } },
  reveal: { text: "Now the rings shrink!" },
  endText: "Did it work on you? 👇",
  phases: { hook: 1.5, challenge: 6, reveal: 2.5, transform: 3 },
  illusion: { type: "expandingRings", props: { speed: 0.8, density: 7 } },
  transform: { type: "vortexBloom", props: {} },
  intense: true,
  audio: {
    music: "music/inhouse-bed-a.wav",
    musicVolume: 0.7,
    sfx: [
      { at: "transform-2", file: "sfx/inhouse-riser.wav", volume: 0.8 },
      { at: "transform+1.6", file: "sfx/inhouse-impact.wav", volume: 0.9 },
      { at: "reveal", file: "sfx/inhouse-whoosh.wav", volume: 0.6 },
    ],
  },
  captions: [],
  cover: { at: 0.6, title: "Stare test", sub: "Does it work on you?" },
  publish: {
    youtube: {
      title: "Stare at the red dot for 6 seconds",
      caption: "Pipeline test. Not for upload.",
      hashtags: ["#shorts", "#illusion", "#opticalillusion"],
    },
    instagram: { caption: "Pipeline test. Not for upload.", hashtags: ["#reels", "#illusion"] },
    facebook: { caption: "Pipeline test. Not for upload.", hashtags: ["#reels"] },
    tiktok: { caption: "Pipeline test. Not for upload.", hashtags: ["#fyp", "#illusion"] },
    x: { caption: "Pipeline test. Not for upload.", hashtags: ["#illusion"] },
  },
});
