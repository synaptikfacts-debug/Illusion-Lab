import { defineReel } from "../src/core/define";

// 0017 "Obsidian Heart" (owner's reference, Nov 14: a black sphere of cracked plates in space that bursts open on a
// glowing core, is hit by black beads and turns into an urchin; "recreate it - better quality, ultra realistic, better
// effects"). Same core idea, our look: ray-traced in Blender (scripts/blender/shell.py, timeline
// src/scenes/shell/timeline.json): polished obsidian plates, a violet plasma core leaking light through the cracks,
// deep space with a faint purple nebula. New effects: light ripples through the cracks on every hit, shockwave rings,
// a wave lifting the plates, and the signature galaxy swirl of plates that spiral home and click in one by one.
//  v4 (owner, Nov 14: 'core looks cheap, too boring - make it go viral'), 16 s, the core is real amethyst crystal:
//  0 HOOK: the cracked sphere glows; 0.3-2.8 plates pop off one by one, faster (a tap each), crystals glimpsed inside
//  2.8 BLAST: the shell flies apart around a cluster of amethyst;  3.6-6 plates orbit the crystal heart
//  6-8.3 the crystals grow out into a giant amethyst urchin;  8.6/9.3/10 light pulses run through them
//  10.5-11.8 they pull back;  12-13.4 the plates spiral home and slam shut;  14.2 a last glow;  14.4-15.9 fade
const clip = { src: "generated/0017-obsidian-heart.mp4", fade: [16.6, 18.1] as [number, number] };

export default defineReel({
  id: "0017-obsidian-heart",
  title: "Obsidian Heart",
  seed: 1717,
  palette: { bg: "#000000", fg: "#9b5cff", accent: "#22d8ff", accent2: "#3a1070" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 17.7 },
  loop: false,
  illusion: { type: "clip", props: clip },
  transform: { type: "clipContinue", props: clip },
  audio: {
    lufs: -14,
    musicVolume: 0.6,
    musicGen: { style: "shell", bpm: 60, seed: 1717 },
    sfx: [{ at: 0, file: "generated/0017-obsidian-heart-sfx.wav", volume: 1 }],
  },
  cover: { at: 0.4 }, // the amethyst urchin among the orbiting plates
  publish: {
    youtube: { title: "What is inside this black sphere", caption: "A sphere of obsidian plates with an amethyst heart. Rendered, not filmed.", hashtags: ["#shorts", "#satisfying", "#3d"] },
    instagram: { caption: "What is inside this black sphere? Rendered, not filmed.", hashtags: ["#reels", "#satisfying", "#oddlysatisfying", "#3dart", "#cgi"] },
    facebook: { caption: "What is inside this black sphere? Rendered, not filmed.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "what is inside this black sphere", hashtags: ["#fyp", "#satisfying", "#oddlysatisfying", "#3dart", "#cgi"] },
    x: { caption: "What is inside this black sphere? Rendered, not filmed.", hashtags: ["#satisfying"] },
  },
});
