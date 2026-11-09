// ARCHIVED (Nov 9 2026): too close to the reference reel (particlesflow bouncing orbs). Not for upload.
// Kept only as code reference for bounceField. Files in reels/archive/ are not rendered.
import { defineReel } from "../../src/core/define";

// 3000 glossy orbs, each bouncing at its own rhythm. They start as a flat disc, fold into funnels, cylinders,
// domes and waves (most complex at 15 s), then unwind and land back in a flat disc exactly at 30 s (loop).
// Sound = one glassy click per impact, generated from the same physics (assets/generated/...).
const bounce = {
  count: 3000,
  baseBounces: 24,
  spread: 3,
  centerFast: true,
  look: { background: "#04050b", plate: "#e8ecf5", gradient: ["#ffffff", "#7df9ff", "#3a7bff", "#a23dff", "#ff2fa8"] },
};

export default defineReel({
  id: "0002-bounce-orbs",
  title: "3000 orbs, each with its own bounce",
  seed: 2002,
  palette: { bg: "#04050b", fg: "#7df9ff", accent: "#3a7bff", accent2: "#ff2fa8" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 29.5 },
  loopBridgeSec: 0.1,
  loopTolerance: 6,
  illusion: { type: "bounceField", props: bounce },
  transform: { type: "bounceFieldContinue", props: bounce },
  audio: {
    music: "music/inhouse-bed-a.wav",
    musicVolume: 0.25,
    sfx: [{ at: 0, file: "generated/0002-bounce-orbs-bounces.wav", volume: 1 }],
  },
  cover: { at: 9.5 },
  publish: {
    youtube: {
      title: "3000 orbs, each with its own bounce",
      caption: "Every orb bounces at its own rhythm. Watch them all land together at the end.",
      hashtags: ["#shorts", "#satisfying", "#asmr"],
    },
    instagram: {
      caption: "3000 orbs, each with its own bounce. Wait for the end.",
      hashtags: ["#reels", "#oddlysatisfying", "#asmr", "#3danimation", "#simulation"],
    },
    facebook: { caption: "3000 orbs, each with its own bounce. Wait for the end.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "3000 orbs, each with its own bounce", hashtags: ["#fyp", "#oddlysatisfying", "#asmr", "#3danimation"] },
    x: { caption: "3000 orbs, each with its own bounce. Wait for the end.", hashtags: ["#satisfying"] },
  },
});
