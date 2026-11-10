import { defineReel } from "../src/core/define";

// Owner's pick (concept 1 of 6), dark studio for a calm feel. Every reel different: last = rainbow orbs on a black
// mirror; this = 90 glossy pendulum spheres on fine threads in 3 tiers, moonlight-blue -> teal -> amber, soft ticks.
//  0-30    the rows pass through two interleaved lines, three, four, one long wave (alternate tiers mirrored)

//  27      SYNC: every sphere lines up in perfect rows (one clear tick)
//  27.4-30 ENDING: the swing dies down, the spheres hang still, fade to black
const p = { dpr: 2 };

export default defineReel({
  id: "0008-pendulum-helix",
  title: "Pendulum Helix",
  seed: 8108,
  palette: { bg: "#0b0c11", fg: "#5fd1c4", accent: "#7fa6ff", accent2: "#ffc27a" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 29.5 },
  loop: false,
  illusion: { type: "pendulum", props: p },
  transform: { type: "pendulumContinue", props: p },
  audio: {
    lufs: -16,
    // one simple calm sound: soft felt ticks only, no music
    sfx: [{ at: 0, file: "generated/0008-pendulum-helix-sfx.wav", volume: 1 }],
  },
  cover: { at: 12.0 },
  publish: {
    youtube: { title: "90 pendulums, one perfect line", caption: "Every pendulum swings at its own speed. Watch them line up at the end.", hashtags: ["#shorts", "#satisfying", "#oddlysatisfying"] },
    instagram: { caption: "90 pendulums, each at its own speed. Wait for the perfect line.", hashtags: ["#reels", "#oddlysatisfying", "#satisfying", "#3danimation", "#asmr"] },
    facebook: { caption: "90 pendulums, each at its own speed.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "wait for the perfect line", hashtags: ["#fyp", "#oddlysatisfying", "#satisfying", "#3danimation", "#asmr"] },
    x: { caption: "90 pendulums, each at its own speed.", hashtags: ["#satisfying"] },
  },
});
