import { defineReel } from "../src/core/define";

// Model (formula only): thousands of simple objects with their own rhythm, emergent shapes, motion-synced sound, loop.
// Ours: a 48x48 wall of glowing pins on a dark mirror. Ripples and standing waves race across it, slow down,
// freeze into a hidden EYE (camera tilts over the top at ~11.1 s), dissolve back into waves and loop.
// Delivered silent (owner adds own sound).
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
  // silent: the owner adds their own sound (melody generator still available: add the generated file as an sfx cue)
  audio: { sfx: [] },
  cover: { at: 11.1 },
  publish: {
    youtube: {
      title: "2304 pins are hiding a picture",
      caption: "Every pin plays its own note. Watch until they stop moving.",
      hashtags: ["#shorts", "#satisfying", "#asmr"],
    },
    instagram: {
      caption: "2304 pins, each playing its own note. Wait for what they draw.",
      hashtags: ["#reels", "#oddlysatisfying", "#asmr", "#3danimation", "#generativeart"],
    },
    facebook: { caption: "2304 pins, each playing its own note. Wait for what they draw.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "wait for what the pins draw", hashtags: ["#fyp", "#oddlysatisfying", "#asmr", "#3danimation"] },
    x: { caption: "2304 pins, each playing its own note. Wait for what they draw.", hashtags: ["#satisfying"] },
  },
});
