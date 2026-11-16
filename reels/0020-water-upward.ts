import { defineReel } from "../src/core/define";

// 0020 "This water falls upward" (owner's pick, Nov 15: "I'm seeing the same thing 3rd reel in a row" - new SUBJECT).
// Last two reels: black spiky ferrofluid (violet lake; emerald test). This one: clear real water in a glass on black
// stone, in front of a wall of moving blue pool-caustic light; harp + glassy shimmer score.
// Picture: scripts/blender/water_up.py (timeline src/scenes/water/timeline.json, events.json for the sound).
//  0-1 HOOK: cold open - a twisted rope of water slams into a glass ceiling and splashes; 1-1.8 a fast rewind
//  then: the glass trembles, the water bulges and RISES out of it in slow motion, twists into a three-strand rope,
//  hits the ceiling and spreads across it, rains back into the glass, the glass refills;  ENDING: settle + fade
const clip = { src: "generated/0020-water-upward.mp4", fade: [15.54, 17.10] as [number, number] };

export default defineReel({
  id: "0020-water-upward",
  title: "This water falls upward",
  seed: 2020,
  palette: { bg: "#00081c", fg: "#7fd4ff", accent: "#ffffff", accent2: "#0a3a8a" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 16.69 },
  loop: false,
  illusion: { type: "clip", props: clip },
  transform: { type: "clipContinue", props: clip },
  audio: {
    lufs: -14,
    musicVolume: 0.6,
    musicGen: { style: "water", bpm: 70, seed: 2020 },
    sfx: [{ at: 0, file: "generated/0020-water-upward-sfx.wav", volume: 1 }],
  },
  cover: { at: 0.4 },
  publish: {
    youtube: { title: "This water falls upward", caption: "A glass of water pours upward, twists into a rope and splashes on the ceiling. Rendered, not filmed.", hashtags: ["#satisfying", "#water", "#shorts"] },
    instagram: { caption: "This water falls upward. Watch the ceiling.", hashtags: ["#water", "#oddlysatisfying", "#satisfying", "#3danimation", "#reels"] },
    facebook: { caption: "This water falls upward. Watch the ceiling. Rendered, not filmed.", hashtags: ["#water", "#reels"] },
    tiktok: { caption: "this water falls upward (watch the ceiling)", hashtags: ["#fyp", "#water", "#oddlysatisfying", "#satisfying", "#3danimation"] },
    x: { caption: "This water falls upward. Rendered, not filmed.", hashtags: ["#satisfying"] },
  },
});
