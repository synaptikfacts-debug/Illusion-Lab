import { defineReel } from "../src/core/define";

// Owner's pick (concept 3 of 5, Nov 10), in the family of the favourite "Liquid Obsidian" but new phenomena and
// palette: jet-black magnetic liquid, teal + electric-violet softboxes, white ring lights.
//  0-6.4    HOOK: a ring of mirror spikes already standing; magnet pulses lift rings of spikes that run outward
//  6.8-11.5 the field grows from the centre over the whole pool
//  12-17    the spikes bloom into a slowly turning six-petal flower
//  17-19    a tall crown rises in the centre
//  21.6     the magnet switches off: the spikes melt, one ripple runs out
//  23-30    ENDING: a calm black mirror, fade
const f = { dpr: 2 };

export default defineReel({
  id: "0008-ferrofluid-bloom",
  title: "Ferrofluid Bloom",
  seed: 8208,
  palette: { bg: "#020205", fg: "#3fe0d0", accent: "#3fe0d0", accent2: "#9a5cff" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 29.5 },
  loop: false,
  illusion: { type: "ferro", props: f },
  transform: { type: "ferroContinue", props: f },
  audio: {
    lufs: -16,
    sfx: [{ at: 0, file: "generated/0008-ferrofluid-bloom-sfx.wav", volume: 1 }],
  },
  cover: { at: 16.0 },
  publish: {
    youtube: { title: "This liquid is magnetic", caption: "Ferrofluid follows a magnet. Watch it bloom, then melt.", hashtags: ["#shorts", "#satisfying", "#ferrofluid"] },
    instagram: { caption: "Magnetic liquid. Watch it bloom, then melt.", hashtags: ["#reels", "#ferrofluid", "#oddlysatisfying", "#satisfying", "#3danimation"] },
    facebook: { caption: "Magnetic liquid. Watch it bloom, then melt.", hashtags: ["#reels", "#ferrofluid"] },
    tiktok: { caption: "this liquid is magnetic", hashtags: ["#fyp", "#ferrofluid", "#oddlysatisfying", "#satisfying", "#3danimation"] },
    x: { caption: "Magnetic liquid. Watch it bloom, then melt.", hashtags: ["#ferrofluid"] },
  },
});
