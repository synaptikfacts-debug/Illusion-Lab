import { defineReel } from "../src/core/define";

// 0024 "This core is unlocking" (owner, Nov 16 2026: cyber/tech, pick #4 - "something nobody has done, beautiful,
// interesting, keeps everyone watching to the end"). A machined cryptex sphere: 8 black anodised outer bands + 6 chrome
// inner bands spin like combination dials and clack into place one by one; the seam lights up, the sphere explodes into
// floating bands, the inner shell unlocks too and a crystal core of living light ignites; the bands orbit it, come home
// one by one and the top cap clacks shut last. Last two reels: 0023 crimson ferrofluid lake, 0022 ferrofluid on a steel
// spiral (violet/aqua). This one: machined metal + glass, black/chrome + ice cyan, a vault-like studio.
// Picture: scripts/blender/core_unlock.py with frames from scripts/gen-core-frames.ts (timeline src/scenes/core/core.ts).
// v8 (delivered Nov 17): 0-1.8 HOOK inside the closed sphere on the liquid-metal core, the camera flies out through the
//  equator slit, the hemispheres clack shut;  2.25-3.45 the outer dials lock (data pulses race in along the circuit floor,
//  a laser ring scans the sphere);  3.9 the outer shell explodes open;  5.8-6.9 inner dials lock;  7.0 inner shell opens;
//  8.35 the liquid-metal core ignites (slow motion), every circuit trace fires;  15.4-18.4 the bands come home, the top
//  cap clacks shut last;  then the board glows, goes dark, fade. Music: electronic score (scripts/gen-music-core-synth.ts).
const clip = { src: "generated/0024-core-unlock.mp4", fade: [19.3, 20.95] as [number, number] };

export default defineReel({
  id: "0024-core-unlock",
  title: "This core is unlocking",
  seed: 2424,
  palette: { bg: "#000000", fg: "#e8f6ff", accent: "#3cc8ff", accent2: "#06213a" },
  phases: { hook: 0.6, challenge: 0, reveal: 0, transform: 20.5 },
  loop: false,
  illusion: { type: "clip", props: clip },
  transform: { type: "clipContinue", props: clip },
  audio: {
    lufs: -14,
    musicVolume: 0.9, // the electronic score sits on top; SFX underneath
    musicGen: { style: "core", bpm: 110, seed: 2424 },
    sfx: [{ at: 0, file: "generated/0024-core-unlock-sfx.wav", volume: 1 }],
  },
  cover: { at: 12.6 },
  publish: {
    youtube: { title: "This core is unlocking", caption: "A machined cryptex sphere unlocks itself dial by dial until its liquid-metal core ignites. Rendered, not filmed.", hashtags: ["#shorts", "#satisfying", "#3danimation"] },
    instagram: { caption: "This core is unlocking. Watch every dial click into place. Rendered, not filmed.", hashtags: ["#satisfying", "#oddlysatisfying", "#3danimation", "#cgi", "#cyberpunk"] },
    facebook: { caption: "A machined sphere unlocks itself dial by dial until its liquid-metal core comes alive. Rendered, not filmed.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "this core is unlocking (wait for the last click)", hashtags: ["#fyp", "#satisfying", "#oddlysatisfying", "#3danimation", "#blender3d"] },
    x: { caption: "This core is unlocking. Rendered, not filmed.", hashtags: ["#satisfying"] },
  },
});
