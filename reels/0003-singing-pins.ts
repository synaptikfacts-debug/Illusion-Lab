import { defineReel } from "../src/core/define";

// Model (formula only): thousands of simple objects with their own rhythm, emergent shapes, motion-synced sound, loop.
// Ours: a 48x48 wall of glowing pins on a dark mirror. Ripples and standing waves race across it, slow down,
// freeze into a hidden EYE (camera tilts over the top at ~11.1 s), dissolve back into waves and loop.
// Sound: SFX from the pin physics on every version; YouTube also gets an in-house track that drops after the eye.
const pins = {
  grid: 48,
  baseCycles: 20,
  ripple: 2.5,
  image: "eye" as const,
  startAt: 0.13,
};

export default defineReel({
  id: "0003-singing-pins",
  title: "2304 singing pins hide a picture",
  seed: 3003,
  palette: { bg: "#03040a", fg: "#22e3ff", accent: "#a23dff", accent2: "#f2fdff" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 29.5 },
  loopBridgeSec: 0.1,
  loopTolerance: 6,
  illusion: { type: "pinWall", props: pins },
  transform: { type: "pinWallContinue", props: pins },
  // SFX on every version (pin ticks, motion whoosh, lock); catchy in-house music on YouTube only (owner rule)
  audio: {
    musicVolume: 0.55,
    musicGen: { bpm: 120, dropAt: 11.1, key: 57, seed: 3 },
    sfx: [{ at: 0, file: "generated/0003-singing-pins-sfx.wav", volume: 1 }],
  },
  cover: { at: 11.1 },
  publish: {
    youtube: {
      title: "2304 pins are hiding a picture",
      caption: "2304 pins, each moving to its own rhythm. Watch until they stop moving.",
      hashtags: ["#shorts", "#satisfying", "#asmr"],
    },
    instagram: {
      caption: "2304 pins, each moving to its own rhythm. Wait for what they draw.",
      hashtags: ["#reels", "#oddlysatisfying", "#asmr", "#3danimation", "#generativeart"],
    },
    facebook: { caption: "2304 pins, each moving to its own rhythm. Wait for what they draw.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "wait for what the pins draw", hashtags: ["#fyp", "#oddlysatisfying", "#asmr", "#3danimation"] },
    x: { caption: "2304 pins, each moving to its own rhythm. Wait for what they draw.", hashtags: ["#satisfying"] },
  },
});
