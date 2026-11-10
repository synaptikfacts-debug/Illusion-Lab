import { defineReel } from "../src/core/define";

// Owner's pick (Nov 10): "Ferrofluid Labyrinth", ray-traced in Blender (scripts/blender/labyrinth_*.py, maps from
// scripts/gen-labyrinth-reel.ts) - approved look still and motion test. Story and beat sheet: src/scenes/labyrinth/story.ts.
// Reference does (0008, best performer): 3D black ferrofluid spikes reflecting neon rings. Ours does: a macro shot of
// ferrofluid between glass plates on an LED panel; a drop bursts into a labyrinth, winds into a spiral, and at the
// very end retracts into one mirror drop. Palette: amber core -> magenta -> violet light, black glossy fluid.
// Sound (owner, Nov 11: calm and satisfying): a few soft felt-piano taps on the visible moments, slow strings and
// spacious piano chords in C# major, resolving as the drop settles, then silence.
export default defineReel({
  id: "0010-ferro-labyrinth",
  title: "Ferrofluid Labyrinth",
  seed: 10303,
  palette: { bg: "#000000", fg: "#ff9a3c", accent: "#ff2f8a", accent2: "#5a1aa0" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 30.5 },
  loop: false,
  illusion: { type: "clip", props: { src: "generated/0010-ferro-labyrinth.mp4", fade: [29.2, 31.0] } },
  transform: { type: "clipContinue", props: { src: "generated/0010-ferro-labyrinth.mp4", fade: [29.2, 31.0] } },
  audio: {
    lufs: -20, // calm (owner, Nov 11: first mix "annoying")
    musicVolume: 0.5,
    musicGen: { style: "labyrinth", bpm: 60, seed: 1030 },
    sfx: [{ at: 0, file: "generated/0010-ferro-labyrinth-sfx.wav", volume: 1 }],
  },
  cover: { at: 23.0 },
  publish: {
    youtube: { title: "This magnetic liquid draws a maze", caption: "A drop of ferrofluid between two glass plates bursts into a labyrinth, winds into a spiral, then pulls back into one drop. Computer-made, ray-traced.", hashtags: ["#shorts", "#ferrofluid", "#satisfying"] },
    instagram: { caption: "This magnetic liquid draws a maze. Watch the end.", hashtags: ["#reels", "#ferrofluid", "#oddlysatisfying", "#satisfying", "#magnetic"] },
    facebook: { caption: "This magnetic liquid draws a maze. Watch the end.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "this magnetic liquid draws a maze (watch the end)", hashtags: ["#fyp", "#ferrofluid", "#oddlysatisfying", "#satisfying", "#magnetic"] },
    x: { caption: "This magnetic liquid draws a maze. Watch the end.", hashtags: ["#satisfying"] },
  },
});
