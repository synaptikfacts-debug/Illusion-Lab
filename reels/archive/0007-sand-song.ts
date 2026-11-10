// ARCHIVED (Nov 10 2026): rejected at preview ("NO... I want something as satisfying as possible").
import { defineReel } from "../../src/core/define";

// Abstract only, every reel different. Last two: 0006 mirror-black neon liquid (pink/violet, harp/marimba),
// 0004 chrome rods (dark studio, teal/amber, piano). This one: bright warm daylight, coloured SAND (gold, rust,
// ivory, turquoise) on a deep navy plate with a brass rim; the plate sings and the sand dances into Chladni figures;
// sound = the plate's own tone + sand hiss; score = flute, clarinet, pizzicato strings.
//  0-2.8   HOOK: low macro inside a cloud of hopping sand forming the first figure
//  2.8-11  each new tone: the sand leaps and rebuilds a more complex figure (top-down)
//  11-19   a fast rising run of tones, sweeping camera passes through the dancing grains (climax)
//  19.4    the grand final figure, the highest tone
//  24-28   ENDING: the tone stops, the last grains settle, camera rises, fade to warm cream
const s = { grains: 110000, dpr: 2 };

export default defineReel({
  id: "0007-sand-song",
  title: "Sand Song",
  seed: 7007,
  palette: { bg: "#e9d8c2", fg: "#e8b04a", accent: "#2fa7a0", accent2: "#c4552d" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 27.5 },
  loop: false,
  illusion: { type: "sand", props: s },
  transform: { type: "sandContinue", props: s },
  audio: {
    musicVolume: 0.5,
    musicGen: { style: "sand", bpm: 84, seed: 7 },
    sfx: [{ at: 0, file: "generated/0007-sand-song-sfx.wav", volume: 1 }],
  },
  cover: { at: 21.0 },
  publish: {
    youtube: { title: "Sound turns sand into this", caption: "Every tone moves the sand into a new shape. Wait for the last one.", hashtags: ["#shorts", "#satisfying", "#oddlysatisfying"] },
    instagram: { caption: "Every tone, a new shape. Wait for the last one.", hashtags: ["#reels", "#oddlysatisfying", "#satisfying", "#3danimation", "#asmr"] },
    facebook: { caption: "Every tone, a new shape. Wait for the last one.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "wait for the last shape", hashtags: ["#fyp", "#oddlysatisfying", "#satisfying", "#3danimation", "#asmr"] },
    x: { caption: "Every tone moves the sand into a new shape.", hashtags: ["#satisfying"] },
  },
});
