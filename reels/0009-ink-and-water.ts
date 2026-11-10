import { defineReel } from "../src/core/define";

// Owner's pick (concept 5, Nov 10). Differs from 0008 Ferrofluid (3D neon mirror spikes) and 0007 Orb Waves: flat
// top-down water, realistic translucent inks (key light, self-shadow, Beer-Lambert depth) (cyan, magenta, gold, violet, mint, rose) on deep navy.
// The reel opens at story 26 s (t0): the drop effect (owner, Nov 10, final: start where the drops land, add more drops,
// sound only where it matches the picture).
//  0-9     drops land one after another in the marbled water and bloom (a soft plip on each landing)
//  9-23    a slow whirlpool winds the colours while more drops land in it
//  23-27   the last drops, the spiral drifts
//  27-30   ENDING: slow fade
const f = { dpr: 2, t0: 26.0 }; // opens at story 26 s: the drop effect (owner, Nov 10, final)

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
  cover: { at: 18.0 },
  publish: {
    youtube: { title: "Six inks, one whirlpool", caption: "Drop after drop of ink lands in dark water and a slow whirlpool winds them into one spiral. 100% computer-made animation.", hashtags: ["#shorts", "#satisfying", "#ink"] },
    instagram: { caption: "Six glowing inks, one slow whirlpool.", hashtags: ["#reels", "#inkinwater", "#oddlysatisfying", "#satisfying", "#relaxing"] },
    facebook: { caption: "Six glowing inks, one slow whirlpool.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "six inks, one whirlpool", hashtags: ["#fyp", "#inkinwater", "#oddlysatisfying", "#satisfying", "#relaxing"] },
    x: { caption: "Six glowing inks, one slow whirlpool.", hashtags: ["#satisfying"] },
  },
});
