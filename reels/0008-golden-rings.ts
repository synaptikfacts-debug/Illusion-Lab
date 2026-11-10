import { defineReel } from "../src/core/define";

// Abstract only, every reel different. Last three: rainbow orbs / black mirror / felt taps; neon liquid; chrome rods.
// This one: a kinetic sculpture of 44 polished GOLD rings in a deep emerald void, soft airy swishes, no music.
//  0-16    HOOK + build: the rings swing with offset phases - spiral staircases, breathing domes, a slow orbit
//  16-23.5 the offsets unwind: ring after ring falls into step
//  23.5    SYNC: all 44 rings swing as one (one fuller swish)
//  24.8-28.4 the swing dies down; the rings settle into a flat, still golden disc
//  28-30   fade to black
const g = { dpr: 2 };

export default defineReel({
  id: "0008-golden-rings",
  title: "Golden Rings",
  seed: 8008,
  palette: { bg: "#04150f", fg: "#f0c050", accent: "#f0c050", accent2: "#2fae8f" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 29.5 },
  loop: false,
  illusion: { type: "rings", props: g },
  transform: { type: "ringsContinue", props: g },
  audio: {
    lufs: -16,
    // one simple calm sound (owner): soft airy swishes only, no music
    sfx: [{ at: 0, file: "generated/0008-golden-rings-sfx.wav", volume: 1 }],
  },
  cover: { at: 8.0 },
  publish: {
    youtube: { title: "44 golden rings, one rhythm", caption: "Every ring swings on its own beat. Watch them fall into step.", hashtags: ["#shorts", "#satisfying", "#oddlysatisfying"] },
    instagram: { caption: "44 golden rings, each on its own beat. Wait for them to fall into step.", hashtags: ["#reels", "#oddlysatisfying", "#satisfying", "#3danimation", "#asmr"] },
    facebook: { caption: "44 golden rings, each on its own beat.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "wait for them to fall into step", hashtags: ["#fyp", "#oddlysatisfying", "#satisfying", "#3danimation", "#asmr"] },
    x: { caption: "44 golden rings, each on its own beat.", hashtags: ["#satisfying"] },
  },
});
