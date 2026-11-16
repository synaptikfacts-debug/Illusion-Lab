import { defineReel } from "../src/core/define";

// 0019 "This liquid has a heartbeat" (owner, Nov 15: after 0018 "This thing eats steel" hit ~1.2k in a day - same
// living-ferrofluid formula, but it must clearly be LIQUID). Last two reels: 0018 spiky ball on a violet lake, 0012
// puddle on a black mirror. This one: a glossy black puddle on dark smoky glass with blurred city-style lights behind.
// Timeline: src/scenes/ferroMusic/heartbeat.ts; picture: scripts/blender/ferro_alive.py (FERRO_LOOK=D,
// FERRO_DOMEH=0.25, FERRO_JUMPERS=60); frames: scripts/gen-heartbeat-frames.ts.
//  0-0.35 HOOK: a drop falls into view and SPLASHES into a crown of spikes, droplets flung up
//  1.6-5.5 every heartbeat: the puddle jumps into spikes and melts back into a smooth black mirror
//  6-12 the heartbeat speeds up, the liquid climbs into a tower, drops drip off it
//  12.2 PAYOFF: the tower collapses and throws a sheet of drops that rains back
//  14-17.5 ripples settle, one last slow beat;  17.5-19.5 ENDING: fade to black
const clip = { src: "generated/0019-liquid-heartbeat.mp4", fade: [17.5, 19.5] as [number, number] };

export default defineReel({
  id: "0019-liquid-heartbeat",
  title: "This liquid won't stay flat", // owner, Nov 15: "This sphere has a heartbeat" already exists
  seed: 1919,
  palette: { bg: "#000000", fg: "#9b5cff", accent: "#22d8ff", accent2: "#3a1070" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 19.0 },
  loop: false,
  illusion: { type: "clip", props: clip },
  transform: { type: "clipContinue", props: clip },
  audio: {
    lufs: -14,
    musicVolume: 0.6,
    musicGen: { style: "heartbeat", bpm: 70, seed: 1919 },
    sfx: [{ at: 0, file: "generated/0019-liquid-heartbeat-sfx.wav", volume: 1 }],
  },
  cover: { at: 11.6 },
  publish: {
    youtube: { title: "This liquid won't stay flat", caption: "A puddle of magnetic liquid (ferrofluid) that keeps jumping into spikes, climbs into a tower and rains back down. Rendered, not filmed.", hashtags: ["#ferrofluid", "#satisfying", "#shorts"] },
    instagram: { caption: "This liquid won't stay flat. Wait for the tower.", hashtags: ["#ferrofluid", "#oddlysatisfying", "#satisfying", "#3danimation", "#reels"] },
    facebook: { caption: "This liquid won't stay flat. Wait for the tower. Rendered, not filmed.", hashtags: ["#ferrofluid", "#reels"] },
    tiktok: { caption: "this liquid won't stay flat (wait for the tower)", hashtags: ["#fyp", "#ferrofluid", "#oddlysatisfying", "#satisfying", "#3danimation"] },
    x: { caption: "This liquid won't stay flat. Rendered, not filmed.", hashtags: ["#ferrofluid"] },
  },
});
