// ARCHIVED (Nov 10 2026): v1 of 0006, rejected - it repeated 0004s rods and colours. Rebuilt as glass cubes (reels/0006-the-face.ts).
import { defineReel } from "../../src/core/define";

// Same chrome-rod world as 0004 (owner: "the previous reel was much better"), new story:
//  0-0.6     HOOK: frame 0 = a chrome face staring at you with glowing teal/amber eyes
//  0.6-2     it SHATTERS: glowing shockwave from the centre, rods launch, sparks fly, camera whips back
//  2-8.6     drops and colliding ripples; 8.6-12.6 a rising glowing spiral (will it come back?)
//  12.6      SNAP: the face rebuilds itself, cascading from the centre, eyes closed
//  13.4-14   it WAKES: the eyes open and glow
//  14.3-17.5 looks left, looks right; 17.3-18.5 a slow smile, cheeks rise
//  19-19.75  it WINKS at you (camera pushes in)
//  20.3-21.5 big warm laugh, mouth opens, the glow pulses
//  22-24     calm, closes its eyes peacefully, glowing dust drifts up
//  24.4-30.5 ENDING: the face sinks back into the wall, last amber ember, fade to black
const f = { grid: 45, rows: 80, spacing: 0.096, dpr: 2 };

export default defineReel({
  id: "0006-the-face-rods",
  title: "3600 chrome rods come alive",
  seed: 6006,
  palette: { bg: "#06070a", fg: "#2fd8ff", accent: "#2fd8ff", accent2: "#ffb347" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 30.0 },
  loop: false,
  illusion: { type: "faceStory", props: f },
  transform: { type: "faceStoryContinue", props: f },
  audio: {
    musicVolume: 0.5,
    musicGen: { style: "faceStory", bpm: 72, seed: 6 },
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
