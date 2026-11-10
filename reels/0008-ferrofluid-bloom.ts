import { defineReel } from "../src/core/define";

// Owner's pick (concept 3 of 5, Nov 10), in the family of the favourite "Liquid Obsidian" but new phenomena and
// palette: jet-black magnetic liquid in a studio of thin neon rings (magenta, cyan, violet, amber, rose, teal). v4
// (owner: "boring", wants Obsidian-level): neon-line reflections on every spike, waves breathing through the field,
// spiral arms that spin faster and faster (spike galaxy + whirlpool), a jet and one ring wave as the magnet cuts out.
//  0-6.8    HOOK: a ring of mirror spikes already standing; magnet pulses lift rings of spikes that run outward
//  6.8-11.5 the field grows from the centre over the whole pool
//  11.5-21  spiral arms sweep the field, spinning faster; camera rises to look down on the galaxy
//  21.6     the magnet switches off: a jet leaps from the centre, one big ring sweeps the pool
//  23-30    ENDING: a calm neon mirror, slow fade
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
    youtube: { title: "This magnetic liquid turns into a galaxy", caption: "Magnetic liquid turns into a spinning galaxy, then lets go. 100% computer-made 3D animation of ferrofluid.", hashtags: ["#shorts", "#satisfying", "#ferrofluid"] },
    instagram: { caption: "Magnetic liquid turns into a spinning galaxy, then lets go.", hashtags: ["#reels", "#ferrofluid", "#oddlysatisfying", "#satisfying", "#3danimation"] },
    facebook: { caption: "Magnetic liquid turns into a spinning galaxy, then lets go.", hashtags: ["#reels", "#ferrofluid"] },
    tiktok: { caption: "this magnetic liquid turns into a galaxy", hashtags: ["#fyp", "#ferrofluid", "#oddlysatisfying", "#satisfying", "#3danimation"] },
    x: { caption: "Magnetic liquid turns into a spinning galaxy, then lets go.", hashtags: ["#ferrofluid"] },
  },
});
