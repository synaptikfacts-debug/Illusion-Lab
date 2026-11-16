import { defineReel } from "../src/core/define";

// 0022 "This liquid climbs on its own" (owner, Nov 16 2026: picked idea 1, "make it 20 sec"; back to the liquid line
// after 0021's space theme got poor views, but with 0021's look). Ferrofluid climbs a polished steel corkscrew tower.
// Owner feedback on the stills: "I don't like crystals, use spikes" (smooth cones), "bigger spikes", "use the colours
// from the previous video" (0021 swirl palette: violet -> blue -> aqua), and no needle crown -> a floating liquid halo.
// Last two reels: 0020 clear water, 0021 beads + gas giant in space. This one: liquid metal on a steel spiral, studio.
// Picture: scripts/blender/ferro_climb.py; sound follows the same beat map (src/scenes/climb/timeline.json). Real time:
//  0-0.6    HOOK: the spiked halo above the fully coated tower flares its spikes
//  0.6-2.0  fast smooth rewind down to the puddle
//  2.0-3.5  the pool wakes: spikes rise across it
//  3.5-12.5 it climbs the corkscrew turn by turn (a thock per turn), slips near the top, pushes on
//  12.2-13.2 a drop gathers on the rod and blooms into a turning halo ring of spikes
//  14.5-18  ENDING: it lets go - spikes melt, the liquid drains back down into a smooth mirror pool
//  18-19.8  fade to black on the last drip
const clip = { src: "generated/0022-liquid-climb.mp4", fade: [18.0, 19.8] as [number, number] };

export default defineReel({
  id: "0022-liquid-climb",
  title: "This Liquid Climbs",
  seed: 2222,
  palette: { bg: "#000000", fg: "#35d0d6", accent: "#2b5cff", accent2: "#6a3dff" },
  phases: { hook: 0.6, challenge: 0, reveal: 0, transform: 19.5 },
  loop: false,
  illusion: { type: "clip", props: clip },
  transform: { type: "clipContinue", props: clip },
  audio: {
    lufs: -14,
    musicVolume: 0.6,
    musicGen: { style: "climb", bpm: 60, seed: 2222 },
    sfx: [{ at: 0, file: "generated/0022-liquid-climb-sfx.wav", volume: 1 }],
  },
  cover: { at: 13.6 }, // the halo over the fully coated spiral
  publish: {
    youtube: { title: "This liquid climbs on its own", caption: "A magnetic liquid wakes up, climbs a steel spiral turn by turn, and blooms into a floating ring of spikes. Rendered, not filmed.", hashtags: ["#shorts", "#satisfying", "#ferrofluid"] },
    instagram: { caption: "It climbs on its own. Wait for the top. Rendered, not filmed.", hashtags: ["#satisfying", "#ferrofluid", "#oddlysatisfying", "#3danimation", "#cgi"] },
    facebook: { caption: "A magnetic liquid climbs a steel spiral on its own. Rendered, not filmed.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "this liquid climbs on its own", hashtags: ["#fyp", "#satisfying", "#ferrofluid", "#oddlysatisfying", "#3danimation"] },
    x: { caption: "This liquid climbs on its own. Rendered, not filmed.", hashtags: ["#satisfying"] },
  },
});
