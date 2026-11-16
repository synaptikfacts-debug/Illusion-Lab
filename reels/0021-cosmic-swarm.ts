import { defineReel } from "../src/core/define";

// 0021 "Cosmic Swarm" (owner, Nov 15 2026: "something like 0011 Singing Pins, but not identical"; liked all three
// concept stills -> "create a preview with all the 3 mixed", in SPACE colours; creamy thock sounds; music on the YT
// Short only, TikTok/Instagram sounds only).
// Reference (0011) does: 4096 pins in a floor grid rise into patterns. Ours (director's cut "The Break", owner Nov 15:
// "build it like a director"): a REAL PHYSICS SIMULATION - 2000 anodized beads (swirl palette mint -> aqua -> blue ->
// violet) in black space, a heavy chrome cue ball, a gas giant with storm bands. Last two reels: 0019 emerald
// ferrofluid, 0020 clear water. Picture: scripts/blender/cosmos_break.py (bake + render); sound = the simulation's own
// collision log (src/scenes/cosmos/break_events.json). Real time:
//  0-0.35  HOOK: close low 3/4 on the glistening cluster - the cue ball streaks in -> IMPACT at 0.35 s
//  0.4-2.0 slow motion: the cluster explodes, beads collide and fly at and past the lens
//  2.2-2.9 speed ramps back: a fly-in with the debris towards the gas giant
//  2.9-4.2 the debris hammers the planet and splashes off (real bounces)
//  4.2-6.0 its gravity sweeps the beads into streams across its face
//  6.0-8.6 the streams wind into a ring in the swirl gradient
//  9.75   HIT 2 (slow motion): a bigger chrome ball tears through the ring, it shatters into a cloud
//  11.6-15.5 the planet catches the beads again: the ring re-forms, tilted the other way
// Extended to ~1 minute (owner, Nov 16 2026: "that beauty reel should be longer"); 0-15.5 s unchanged:
//  17-25.5 a grey moon drifts past and tears the ring's outer edge into a stream that slingshots back
//  27, 29.5, 32, 34.5  four chrome meteors strike the near side of the ring, one after another (slow motion)
//  38-42.4 the ring lets go: everything rains spiralling into the planet
//  42.5   they all bounce back up off the surface at the lens
//  43-50  the planet catches them in TWO crossed rings
//  52-60  ENDING: the two rings settle, the camera pulls back, fade 58.4-59.9
const clip = { src: "generated/0021-cosmic-swarm.mp4", fade: [58.4, 59.9] as [number, number] };

export default defineReel({
  id: "0021-cosmic-swarm",
  title: "The Break",
  seed: 2121,
  palette: { bg: "#000000", fg: "#7dffb3", accent: "#1fd0e0", accent2: "#6a3dff" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 59.5 },
  loop: false,
  illusion: { type: "clip", props: clip },
  transform: { type: "clipContinue", props: clip },
  audio: {
    lufs: -14,
    musicVolume: 0.6,
    musicGen: { style: "cosmos", bpm: 60, seed: 2121 },
    sfx: [{ at: 0, file: "generated/0021-cosmic-swarm-sfx.wav", volume: 1 }],
  },
  cover: { at: 8.6 }, // the gas giant with its first ring
  publish: {
    youtube: { title: "One hit broke 2000 beads into a planet ring", caption: "A chrome ball smashes a cluster of 2000 metal beads in deep space. The debris hits a gas giant and its gravity winds every bead into a ring. Real physics, every sound is a collision. Rendered, not filmed.", hashtags: ["#shorts", "#satisfying", "#space"] },
    instagram: { caption: "One hit. 2000 beads. A new planet ring. Rendered, not filmed.", hashtags: ["#satisfying", "#space", "#physics", "#3danimation", "#cgi"] },
    facebook: { caption: "A chrome ball smashes 2000 metal beads, and a gas giant catches them in a ring. Rendered, not filmed.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "one hit broke 2000 beads into a planet ring", hashtags: ["#fyp", "#satisfying", "#space", "#physics", "#3danimation"] },
    x: { caption: "One hit broke 2000 beads into a planet ring. Rendered, not filmed.", hashtags: ["#satisfying"] },
  },
});
