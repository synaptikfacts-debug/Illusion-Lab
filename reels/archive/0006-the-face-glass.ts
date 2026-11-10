// ARCHIVED (Nov 10 2026): glass-cube face, stopped by the owner - no faces/pictures, abstract effects only.
import { defineReel } from "../../src/core/define";

// Every reel looks different (owner rule). Last two: 0004 chrome rods / dark studio / teal-amber / piano,
// 0005 obsidian dominoes / magenta-gold. This one: ~2000 floating frosted-glass cubes, bright dawn sky
// (peach, rose, lavender), pearl/rose/sapphire, sparkles, fade to WHITE; harp + marimba + strings score.
//  0-0.6     HOOK: a glass face in the dawn sky staring at you, sapphire eyes glowing
//  0.6-8.6   it BURSTS into a glass storm swirling around the camera, ribbons of cubes in 3D
//  8.6-12.4  the storm tightens into a spinning tornado
//  12.6      the cubes fly back and ASSEMBLE the face mid-air, centre first, eyes closed
//  13.4-21.5 it wakes, looks left and right, smiles, WINKS (camera pushes in), laughs
//  22-24     closes its eyes peacefully
//  24.2-30.5 ENDING: the cubes lift off one by one and drift up into the light; fade to white
const g = { cols: 60, dpr: 2 };

export default defineReel({
  id: "0006-the-face-glass",
  title: "2000 glass cubes come alive",
  seed: 6106,
  palette: { bg: "#ffe4c6", fg: "#5a86ff", accent: "#ff6f95", accent2: "#5a86ff" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 30.0 },
  loop: false,
  illusion: { type: "glassFace", props: g },
  transform: { type: "glassFaceContinue", props: g },
  audio: {
    musicVolume: 0.5,
    musicGen: { style: "glassFace", bpm: 76, seed: 61 },
    sfx: [{ at: 0, file: "generated/0006-the-face-sfx.wav", volume: 1 }],
  },
  cover: { at: 20.9 },
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
