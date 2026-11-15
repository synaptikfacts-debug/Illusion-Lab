import { defineReel } from "../src/core/define";

// 0018 "This liquid is hungry" (owner's pick, Nov 15: build on the most viewed reels - 0012 "This liquid came alive"
// 1,239 views). The same ferrofluid creature on black mirror glass hunts polished steel beads, swallows them and grows.
// Timeline: src/scenes/ferroMusic/hungry.ts; picture: scripts/blender/ferro_alive.py (frames: gen-hungry-frames.ts).
//  v2 (owner: "everyone will swipe - I want a good hook"): 0-1 COLD OPEN on the bristling crown, a spike-harpoon lunges
//  at the lens; 1-1.8 a fast rewind; then the story below at 1.45x with harpoon strikes and pounces (18.6 s)
//  0-1.2 the arm already around a bead - gulp;  1.2-7.2 three more beads, faster, it gets greedy
//  8.4-11 a BIG bead: struggle, wrap, gulp;  11.6-14.6 the remaining beads roll in on their own - a chain of gulps
//  15-18 full: it swells, the heartbeat races, a crown rises;  18.4-20 it splits into twins
//  20-22.5 they settle, a last slow heartbeat;  22.5-24.4 ENDING: fade to black
const clip = { src: "generated/0018-hungry-liquid.mp4", fade: [17.32, 18.5] as [number, number] };

export default defineReel({
  id: "0018-hungry-liquid",
  title: "This liquid is hungry",
  seed: 1818,
  palette: { bg: "#000000", fg: "#9b5cff", accent: "#22d8ff", accent2: "#3a1070" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 18.1 },
  loop: false,
  illusion: { type: "clip", props: clip },
  transform: { type: "clipContinue", props: clip },
  audio: {
    lufs: -14,
    musicVolume: 0.6,
    musicGen: { style: "hungry", bpm: 120, seed: 1818 },
    sfx: [{ at: 0, file: "generated/0018-hungry-liquid-sfx.wav", volume: 1 }],
  },
  cover: { at: 0.1 },
  publish: {
    youtube: { title: "This thing eats steel", caption: "A spiky ball of magnetic fluid (ferrofluid) hunts steel beads, swallows them, grows and splits in two. Rendered, not filmed.", hashtags: ["#shorts", "#ferrofluid", "#satisfying"] },
    instagram: { caption: "This thing eats steel. Wait for the big one.", hashtags: ["#reels", "#ferrofluid", "#oddlysatisfying", "#satisfying", "#3danimation"] },
    facebook: { caption: "This thing eats steel. Wait for the big one. Rendered, not filmed.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "this thing eats steel (wait for the big one)", hashtags: ["#fyp", "#ferrofluid", "#oddlysatisfying", "#satisfying", "#3danimation"] },
    x: { caption: "This thing eats steel. Rendered, not filmed.", hashtags: ["#satisfying"] },
  },
});
