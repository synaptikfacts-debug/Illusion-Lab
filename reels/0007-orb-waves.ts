import { defineReel } from "../src/core/define";

// Reference core idea kept (owner, Nov 10): thousands of glossy orbs, each bouncing at its own rhythm, folding into
// funnels/domes/spirals, a click per bounce. Ours: midnight studio, black-mirror disc with a gold rim, pearl ->
// peach -> coral -> magenta -> indigo orbs, slow orbiting camera, opens mid-pattern, in-phase climax, settle ending.
//  0-3     HOOK: low and close inside a spiral funnel already in full motion
//  3-24    camera rises and orbits: funnels, domes, spiral waves keep changing
//  25.2    CLIMAX: every orb lands at the same instant - the whole disc bounces as one
//  25.6-29 ENDING: the bounces die down, 4600 orbs come to rest on the mirror, fade to black
const o = { dpr: 2 };

export default defineReel({
  id: "0007-orb-waves",
  title: "Orb Waves",
  seed: 7207,
  palette: { bg: "#05040c", fg: "#ff6f7d", accent: "#d93fa8", accent2: "#6a43f2" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 29.5 },
  loop: false,
  illusion: { type: "orbs", props: o },
  transform: { type: "orbsContinue", props: o },
  audio: {
    lufs: -16,
    // owner picked option C: soft felt taps only, no music
    sfx: [{ at: 0, file: "generated/0007-orb-waves-sfx.wav", volume: 1 }],
  },
  cover: { at: 14.0 },
  publish: {
    youtube: { title: "4600 orbs, each with its own bounce", caption: "Every orb bounces at its own rhythm. Watch them all land together, then rest.", hashtags: ["#shorts", "#satisfying", "#oddlysatisfying"] },
    instagram: { caption: "4600 orbs, each with its own bounce. Wait for them to land together.", hashtags: ["#reels", "#oddlysatisfying", "#satisfying", "#3danimation", "#asmr"] },
    facebook: { caption: "4600 orbs, each with its own bounce. Wait for them to land together.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "wait for them to land together", hashtags: ["#fyp", "#oddlysatisfying", "#satisfying", "#3danimation", "#asmr"] },
    x: { caption: "4600 orbs, each with its own bounce.", hashtags: ["#satisfying"] },
  },
});
