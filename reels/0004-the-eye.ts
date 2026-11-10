import { defineReel } from "../src/core/define";

// Model (formula only): many simple objects with their own motion, emergent shapes, motion-made sound.
// Ours: 1705 polished chrome rods in a studio. Story with an ending:
//  0-0.6   HOOK: frame 0 = a glowing eye filling the screen, staring at you, pupil tightening
//  0.6-2   it SHATTERS: every rod launches in a glowing shockwave, camera whips back
//  2-8.6   the wall settles; drops land in the corners, rings collide
//  8.6-12.6 waves wind into a rising spiral (tension: is it coming back?)
//  12.6    SNAP: the eye is back, rods slam into place cascading from the centre
//  12.6-21 the eye lives: looks left and right, blinks, pupil widens at you, slowly closes
//  21-24  the closed eye exhales flat, slow wave from the outside in, camera rises and pulls away
//  24-28.6 the last rod settles with a fading amber ember; fade to black while the last chord rings out. THE END
const rods = { grid: 31, rows: 55, spacing: 0.14, dpr: 2 };

export default defineReel({
  id: "0004-the-eye",
  title: "1705 chrome rods open an eye",
  seed: 4004,
  palette: { bg: "#06070a", fg: "#2fd8ff", accent: "#2fd8ff", accent2: "#ffb347" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 28.1 },
  loop: false,
  illusion: { type: "rodStory", props: rods },
  transform: { type: "rodStoryContinue", props: rods },
  audio: {
    musicVolume: 0.5,
    musicGen: { style: "rodStory", bpm: 72, seed: 4 },
    sfx: [{ at: 0, file: "generated/0004-the-eye-sfx.wav", volume: 1 }],
  },
  cover: { at: 14.6 },
  publish: {
    youtube: {
      title: "1705 chrome rods are about to open an eye",
      caption: "1705 polished rods, each moving on its own. Wait for the eye to look at you.",
      hashtags: ["#shorts", "#satisfying", "#3danimation"],
    },
    instagram: {
      caption: "1705 chrome rods. Wait for the eye to look at you.",
      hashtags: ["#reels", "#oddlysatisfying", "#3danimation", "#cgi", "#satisfying"],
    },
    facebook: { caption: "1705 chrome rods. Wait for the eye to look at you.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "wait for it to look at you", hashtags: ["#fyp", "#oddlysatisfying", "#3danimation", "#cgi"] },
    x: { caption: "1705 chrome rods. Wait for the eye to look at you.", hashtags: ["#satisfying"] },
  },
});
