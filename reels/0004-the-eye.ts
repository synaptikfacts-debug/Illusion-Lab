import { defineReel } from "../src/core/define";

// Model (formula only): many simple objects with their own motion, emergent shapes, motion-made sound.
// Ours: 1705 polished chrome rods in a studio. Story with an ending:
//  0-2 s   macro close-up, one rod pops (tock) -> ripple
//  2-7     pull back, drops land in the corners, rings collide
//  7-11    waves wind into a rising spiral (tension)
//  11      SNAP: rods slam into a giant eye, cascading out from the centre
//  11-19   the eye lives: looks left and right, blinks, pupil widens at you, slowly closes
//  19-23   closed eye melts flat, camera sinks back to the start, last rod drops: THE END (and it loops)
const rods = { grid: 31, rows: 55, spacing: 0.14, dpr: 2 };

export default defineReel({
  id: "0004-the-eye",
  title: "1705 chrome rods open an eye",
  seed: 4004,
  palette: { bg: "#06070a", fg: "#2fd8ff", accent: "#2fd8ff", accent2: "#ffb347" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 22.5 },
  loopBridgeSec: 0.12,
  loopTolerance: 8,
  illusion: { type: "rodStory", props: rods },
  transform: { type: "rodStoryContinue", props: rods },
  audio: {
    musicVolume: 0.5,
    musicGen: { style: "rodStory", bpm: 72, seed: 4 },
    sfx: [{ at: 0, file: "generated/0004-the-eye-sfx.wav", volume: 1 }],
  },
  cover: { at: 13.0 },
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
