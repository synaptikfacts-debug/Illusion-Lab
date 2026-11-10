import { defineReel } from "../src/core/define";

// Owner's pick (concept 5, Nov 10). Differs from 0008 Ferrofluid (3D neon mirror spikes) and 0007 Orb Waves: flat
// top-down water, realistic translucent inks (key light, self-shadow, Beer-Lambert depth) (cyan, magenta, gold, violet, mint, rose) on deep navy.
// The reel opens at story 17 s (t0), mid-whirlpool (owner pick A, Nov 10: the burst opening was still boring).
//  0-3.5   HOOK: the whirlpool is already spinning, the magenta eye winds up
//  3.5-9   the whirlpool lets go, the marbled galaxy drifts
//  9.5-17  a second wave: cyan, gold, violet, rose drops land in the marbled water and bloom
//  18-28   a second slow whirlpool winds everything into one final spiral
//  27-30   ENDING: slow fade
const f = { dpr: 2, t0: 17.0 }; // opens at story 17 s: mid-whirlpool (owner pick A, Nov 10)

export default defineReel({
  id: "0009-ink-and-water",
  title: "Ink and Water",
  seed: 9309,
  palette: { bg: "#010205", fg: "#1ad8ff", accent: "#ff1f8c", accent2: "#ffad1f" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 29.5 },
  loop: false,
  illusion: { type: "ink", props: f },
  transform: { type: "inkContinue", props: f },
  audio: {
    lufs: -20,
    sfx: [{ at: 0, file: "generated/0009-ink-and-water-sfx.wav", volume: 1 }],
  },
  cover: { at: 5.0 },
  publish: {
    youtube: { title: "Six inks, one whirlpool", caption: "A whirlpool of six inks, fresh drops landing in the marble, then one last spiral. 100% computer-made animation.", hashtags: ["#shorts", "#satisfying", "#ink"] },
    instagram: { caption: "Six glowing inks, one slow whirlpool.", hashtags: ["#reels", "#inkinwater", "#oddlysatisfying", "#satisfying", "#relaxing"] },
    facebook: { caption: "Six glowing inks, one slow whirlpool.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "six inks, one whirlpool", hashtags: ["#fyp", "#inkinwater", "#oddlysatisfying", "#satisfying", "#relaxing"] },
    x: { caption: "Six glowing inks, one slow whirlpool.", hashtags: ["#satisfying"] },
  },
});
