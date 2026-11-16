import { defineReel } from "../src/core/define";

// 0023 v2 "This liquid became a storm" (owner, Nov 16: v1 "Mercury learned to dance" rejected as "super childish, effects
// super bad - I expected something professional like This thing eats steel"; wants "spikes, brutal, beautiful,
// catchy"). A whole black lake of magnetic liquid, crimson + steel white, dark studio with blurred light strips.
// Last reels: 0022 ferrofluid on a steel spiral (violet/aqua), 0021 space. This one: a lake that becomes a storm.
// Picture: scripts/blender/ferro_alive.py (FERRO_LOOK=E FERRO_DOME=0 FERRO_DOMEH=0 FERRO_RIP=0.12 FERRO_JUMPERS=40)
// with frames from scripts/gen-storm-frames.ts (timeline src/scenes/ferroMusic/storm.ts).
//  0-0.7    HOOK: a wall of huge spikes races at the lens and crests;  0.7-1.6 fast rewind to a calm mirror
//  2.2      a bass hit: a ring of spikes bursts out;  3.6 / 5.2 spike fronts rip across the lake
//  7-11     a vortex of spikes, faster and faster;  11-14 a twisting spiked tornado rises
//  14.0     COLLAPSE: droplets fly, a giant ring of spikes races out;  15-20 aftershocks, calm, fade
const clip = { src: "generated/0023-liquid-storm.mp4", fade: [18.2, 19.9] as [number, number] };

export default defineReel({
  id: "0023-liquid-storm",
  title: "This liquid became a storm",
  seed: 2323,
  palette: { bg: "#000000", fg: "#f2f2f2", accent: "#e0101c", accent2: "#5a0008" },
  phases: { hook: 0.7, challenge: 0, reveal: 0, transform: 19.5 },
  loop: false,
  illusion: { type: "clip", props: clip },
  transform: { type: "clipContinue", props: clip },
  audio: {
    lufs: -14,
    musicVolume: 0.6,
    musicGen: { style: "storm", bpm: 70, seed: 2323 },
    sfx: [{ at: 0, file: "generated/0023-liquid-storm-sfx.wav", volume: 1 }],
  },
  cover: { at: 13.6 },
  publish: {
    youtube: { title: "This liquid became a storm", caption: "A black lake of magnetic liquid (ferrofluid) turns into waves of spikes, a vortex and a spiked tornado, then collapses. Rendered, not filmed.", hashtags: ["#shorts", "#satisfying", "#ferrofluid"] },
    instagram: { caption: "This liquid became a storm. Wait for the tornado. Rendered, not filmed.", hashtags: ["#ferrofluid", "#satisfying", "#oddlysatisfying", "#3danimation", "#cgi"] },
    facebook: { caption: "A black lake of magnetic liquid becomes a storm of spikes. Rendered, not filmed.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "this liquid became a storm (wait for the tornado)", hashtags: ["#fyp", "#ferrofluid", "#satisfying", "#oddlysatisfying", "#3danimation"] },
    x: { caption: "This liquid became a storm. Rendered, not filmed.", hashtags: ["#satisfying"] },
  },
});
