import { defineReel } from "../src/core/define";

const look = { bg0: "#070a24", bg1: "#2a1260", tint: "#22e3ff", tint2: "#ff3fd8" };

export default defineReel({
  id: "0001-living-afterimage",
  title: "Your brain will colour this in",
  seed: 4242,
  palette: { bg: "#070a24", fg: "#7ff3ff", accent: "#22e3ff", accent2: "#ff3fd8" },
  hook: { text: "Your brain will colour this in", sub: "Stare at the dot" },
  challenge: { instruction: "Don't move your eyes", focus: { x: 0.5, y: 0.57 } },
  reveal: { text: "It's black and white" },
  endText: "Did it work on you? 👇",
  phases: { hook: 2.5, challenge: 12, reveal: 4, transform: 7 },
  illusion: { type: "livingAfterimage", props: { look } },
  transform: { type: "particleGalaxy", props: { look, count: 60000 } },
  intense: false,
  audio: {
    music: "music/inhouse-bed-a.wav",
    musicVolume: 0.7,
    sfx: [
      { at: "reveal", file: "sfx/inhouse-whoosh.wav", volume: 0.7 },
      { at: "transform-1.6", file: "sfx/inhouse-riser.wav", volume: 0.8 },
      { at: "transform+0.5", file: "sfx/inhouse-impact.wav", volume: 0.9 },
    ],
  },
  captions: [],
  cover: { at: 1.2, title: "Stare test", sub: "Your brain adds the colour" },
  publish: {
    youtube: {
      title: "Stare at the dot for 12 seconds - your brain will colour this in",
      caption: "Keep your eyes on the dot until the countdown ends. The last image is fully black and white.",
      hashtags: ["#shorts", "#opticalillusion", "#illusion"],
    },
    instagram: {
      caption: "Stare at the dot for 12 seconds. The last image is black and white - what colours did you see?",
      hashtags: ["#reels", "#opticalillusion", "#illusion", "#brain"],
    },
    facebook: { caption: "Stare at the dot for 12 seconds. The last image is black and white.", hashtags: ["#reels", "#opticalillusion"] },
    tiktok: { caption: "Stare at the dot for 12 seconds. The last image is black and white", hashtags: ["#fyp", "#opticalillusion", "#illusion"] },
    x: { caption: "Stare at the dot for 12 seconds. The last image is black and white. What colours did you see?", hashtags: ["#opticalillusion"] },
  },
});
