import { defineReel } from "../src/core/define";

// Owner's pick (concept 5, Nov 10). Differs from 0008 Ferrofluid (3D neon mirror spikes) and 0007 Orb Waves: flat
// top-down water, realistic translucent inks (key light, self-shadow, Beer-Lambert depth) (cyan, magenta, gold, violet, mint, rose) on deep navy.
//  0-4     HOOK: six inks land together in a ring and spin into a pinwheel (camera pulls back from close)
//  4-10    slow currents stretch the pinwheel into marbled ribbons; a gold drop lands at 6 s
//  10-20   a slow vortex winds every ink into one spiral; a magenta drop lands in its eye at 15 s
//  20-27   the vortex lets go, the marbled galaxy drifts and settles
//  27-30   ENDING: slow fade
const f = { dpr: 2 };

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
    lufs: -16,
    sfx: [{ at: 0, file: "generated/0009-ink-and-water-sfx.wav", volume: 1 }],
  },
  cover: { at: 21.0 },
  publish: {
    youtube: { title: "Six inks, one whirlpool", caption: "Six inks land in dark water together, spin into a pinwheel, then a slow whirlpool winds them into one galaxy. 100% computer-made animation.", hashtags: ["#shorts", "#satisfying", "#ink"] },
    instagram: { caption: "Six glowing inks, one slow whirlpool.", hashtags: ["#reels", "#inkinwater", "#oddlysatisfying", "#satisfying", "#relaxing"] },
    facebook: { caption: "Six glowing inks, one slow whirlpool.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "six inks, one whirlpool", hashtags: ["#fyp", "#inkinwater", "#oddlysatisfying", "#satisfying", "#relaxing"] },
    x: { caption: "Six glowing inks, one slow whirlpool.", hashtags: ["#satisfying"] },
  },
});
