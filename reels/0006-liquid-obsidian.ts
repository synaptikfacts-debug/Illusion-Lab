import { defineReel } from "../src/core/define";

// Abstract only (owner: no faces/pictures). Every reel different: last two = chrome rods (dark studio, teal/amber,
// piano) and dominoes (magenta/gold). This one: a smooth mirror-black LIQUID reflecting hot-pink/violet/warm-white
// neon; drops, rings, interference, rain, a cymatic star, a whirlpool, a collapse; harp/marimba/strings score.
//  0-1.4   HOOK: mid-impact giant crater ring racing outward, low and close
//  1-7     drops land, rings collide into interference patterns
//  7-11    an accelerating rain
//  11-16.6 the surface locks into a turning six-fold standing-wave star (cymatics)
//  15.6-22 it twists into a deep whirlpool with spiral arms
//  22      COLLAPSE: a jet leaps up and one giant ring sweeps across everything
//  23-30   ENDING: calm mirror, one last drop, fade to black
const l = { dpr: 2 };

export default defineReel({
  id: "0006-liquid-obsidian",
  title: "Liquid obsidian",
  seed: 6206,
  palette: { bg: "#020104", fg: "#ff3fa4", accent: "#ff3fa4", accent2: "#7a5cff" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 29.5 },
  loop: false,
  illusion: { type: "liquid", props: l },
  transform: { type: "liquidContinue", props: l },
  audio: {
    musicVolume: 0.5,
    musicGen: { style: "liquid", bpm: 76, seed: 62 },
    sfx: [{ at: 0, file: "generated/0006-liquid-obsidian-sfx.wav", volume: 1 }],
  },
  cover: { at: 19.2 },
  publish: {
    youtube: {
      title: "3600 chrome rods just winked at me",
      caption: "3600 polished rods, each moving on its own. Watch until it smiles.",
      hashtags: ["#shorts", "#satisfying", "#3danimation"],
    },
    instagram: {
      caption: "3600 chrome rods. Wait for the wink.",
      hashtags: ["#reels", "#oddlysatisfying", "#3danimation", "#cgi", "#satisfying"],
    },
    facebook: { caption: "3600 chrome rods. Wait for the wink.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "wait for the wink", hashtags: ["#fyp", "#oddlysatisfying", "#3danimation", "#cgi"] },
    x: { caption: "3600 chrome rods. Wait for the wink.", hashtags: ["#satisfying"] },
  },
});
