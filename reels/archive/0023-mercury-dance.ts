import { defineReel } from "../src/core/define";

// 0023 "Mercury learned to dance" (HANDOFF Nov 16: concept stills shown, owner: "make it incredible, with effects that
// keep everyone watching to the end"). Liquid-chrome (mercury) drops on a black glass drum, magenta + lime light,
// white panels for silver reflections. Last two reels: 0022 ferrofluid on a steel spiral (violet/aqua), 0021 beads +
// gas giant in space. This one: liquid chrome drops that merge (metaballs), magenta/lime, a drum that makes them dance.
// Picture: scripts/blender/mercury_dance.py; sound + score: src/scenes/mercury/events.json.
//  0-0.6    HOOK: a bass hit has thrown 32 drops into the air - frozen mid-flight, close and low
//  0.6-1.6  fast rewind: they fall back onto the glass
//  2-6      every bass pulse makes them hop on the drum
//  6-12     the vibration sorts them: a double RING -> merge -> a SPIRAL -> merge -> a STAR
//  12-15.6  the last ones orbit faster and faster and merge 8 -> 4 -> 2 -> 1 with a splash crown
//  15.6-20  ONE big mirror sphere wobbles, the splash droplets roll back into it, it settles; fade
const clip = { src: "generated/0023-mercury-dance.mp4", fade: [18.4, 19.9] as [number, number] };

export default defineReel({
  id: "0023-mercury-dance",
  title: "Mercury learned to dance",
  seed: 2323,
  palette: { bg: "#000000", fg: "#e8e8f0", accent: "#ff1a99", accent2: "#8cff1a" },
  phases: { hook: 0.6, challenge: 0, reveal: 0, transform: 19.5 },
  loop: false,
  illusion: { type: "clip", props: clip },
  transform: { type: "clipContinue", props: clip },
  audio: {
    lufs: -14,
    musicVolume: 0.6,
    musicGen: { style: "mercury", bpm: 75, seed: 2323 },
    sfx: [{ at: 0, file: "generated/0023-mercury-dance-sfx.wav", volume: 1 }],
  },
  cover: { at: 16.2 },
  publish: {
    youtube: { title: "Mercury learned to dance", caption: "Drops of liquid metal hop on a drum, sort themselves into a ring, a spiral and a star, and merge into one mirror sphere. Rendered, not filmed.", hashtags: ["#shorts", "#satisfying", "#mercury"] },
    instagram: { caption: "Mercury learned to dance. Wait for the last drop. Rendered, not filmed.", hashtags: ["#satisfying", "#mercury", "#oddlysatisfying", "#3danimation", "#cgi"] },
    facebook: { caption: "Drops of liquid metal dance on a drum and merge into one mirror sphere. Rendered, not filmed.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "mercury learned to dance (wait for the last drop)", hashtags: ["#fyp", "#satisfying", "#mercury", "#oddlysatisfying", "#3danimation"] },
    x: { caption: "Mercury learned to dance. Rendered, not filmed.", hashtags: ["#satisfying"] },
  },
});
