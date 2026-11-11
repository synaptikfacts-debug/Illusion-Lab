import { defineReel } from "../src/core/define";

// Owner (Nov 11): "I absolutely love [0003 Singing Pins]. Recreate it with better quality, better effects, ~1 minute."
// Same idea and family as 0003 (owner's own reel), upgraded: 4096 pins (64x64), 2x supersampling, bloom, soft depth of
// field, mirror floor, film grain; four abstract pictures (abstract-only rule: no eye) each with its own colour story,
// and a real ending.
//  0-10.8   HOOK: the wall is already racing in waves -> freezes into RINGS (cyan/violet), dissolves
//  10.8-24  waves -> STAR (magenta/gold)
//  24-37    waves -> SPIRAL (mint/aqua)
//  37-45    waves -> MANDALA (violet/pink), holds
//  48-54    the mandala melts into a calm flat mirror, camera rises and pulls back
//  55.6-60  ENDING: slow fade
// v2 (owner, Nov 11: "slower", "ultra realistic", "fix the sound with the tap one"): waves slowed (base 12), ray-traced
// in Blender Cycles (scripts/blender/pinshow.py from scripts/gen-pinshow-frames.ts): brushed-steel pins, glossy coated
// tips, softbox studio, matte black floor, depth of field; sound = soft pin taps only. The three.js scene stays as the
// fast preview (illusion pinShow).
const clip = { src: "generated/0011-singing-pins-show.mp4", fade: [55.6, 59.7] as [number, number] };

export default defineReel({
  id: "0011-singing-pins-show",
  title: "Singing Pins: The Show",
  seed: 1111,
  palette: { bg: "#020208", fg: "#22e3ff", accent: "#9b3dff", accent2: "#ff2f8e" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 59.5 },
  loop: false,
  illusion: { type: "clip", props: clip },
  transform: { type: "clipContinue", props: clip },
  audio: {
    lufs: -20,
    sfx: [{ at: 0, file: "generated/0011-singing-pins-show-sfx.wav", volume: 1 }],
  },
  cover: { at: 43.5 },
  publish: {
    youtube: { title: "4096 pins draw four pictures", caption: "4096 pins, each moving to its own rhythm. Watch them freeze into rings, a star, a spiral and a mandala. 100% computer-made animation.", hashtags: ["#shorts", "#satisfying", "#asmr"] },
    instagram: { caption: "4096 pins, each with its own rhythm. Wait for what they draw.", hashtags: ["#reels", "#oddlysatisfying", "#asmr", "#3danimation", "#generativeart"] },
    facebook: { caption: "4096 pins, each with its own rhythm. Wait for what they draw.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "wait for what the pins draw", hashtags: ["#fyp", "#oddlysatisfying", "#asmr", "#3danimation"] },
    x: { caption: "4096 pins, each with its own rhythm. Wait for what they draw.", hashtags: ["#satisfying"] },
  },
});
