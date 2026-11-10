import { defineReel } from "../src/core/define";

// Reference formula (owner's particlesflow reel): many glossy balls, satisfying physics, a sound on every hit,
// clean stage, satisfying end. Ours (different mechanic): a Galton board - 3000 candy marbles pour through chrome
// pins into a rainbow bell curve; the last marble is GOLD and lands on top of the peak.
//  0-2     HOOK: close on the pins, marbles already streaming through, clicking
//  2-17    pull back: the rainbow bell curve grows layer by layer (colour follows release time)
//  17-19.4 the stream stops; silence for a beat
//  19.6    the GOLD marble drops, zig-zags straight down the middle, lands on the peak
//  22-27   ENDING: camera eases back over the finished rainbow curve, fade to black
const g = { dpr: 2 };

export default defineReel({
  id: "0007-marble-cascade",
  title: "Marble Cascade",
  seed: 7107,
  palette: { bg: "#050507", fg: "#ffc23d", accent: "#ff3d6e", accent2: "#3db8ff" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 26.5 },
  loop: false,
  illusion: { type: "galton", props: g },
  transform: { type: "galtonContinue", props: g },
  audio: {
    musicVolume: 0.45,
    musicGen: { style: "galton", bpm: 80, seed: 71 },
    sfx: [{ at: 0, file: "generated/0007-marble-cascade-sfx.wav", volume: 1 }],
  },
  cover: { at: 21.2 },
  publish: {
    youtube: { title: "3000 marbles, one golden finish", caption: "Every marble picks left or right 14 times. Watch where the gold one lands.", hashtags: ["#shorts", "#satisfying", "#oddlysatisfying"] },
    instagram: { caption: "3000 marbles. Watch where the gold one lands.", hashtags: ["#reels", "#oddlysatisfying", "#satisfying", "#3danimation", "#asmr"] },
    facebook: { caption: "3000 marbles. Watch where the gold one lands.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "watch where the gold one lands", hashtags: ["#fyp", "#oddlysatisfying", "#satisfying", "#3danimation", "#asmr"] },
    x: { caption: "3000 marbles. Watch where the gold one lands.", hashtags: ["#satisfying"] },
  },
});
