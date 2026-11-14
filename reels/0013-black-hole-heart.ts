import { defineReel } from "../src/core/define";

// 0013 "Black Hole Heart": a Schwarzschild black hole ray-traced per pixel on the GPU
// (scripts/blackhole/gpu_bh.py + bh.frag: geodesics through a thin black-body disk, Doppler colour, lensed sky).
// Last two reels used ferrofluid (black mirror / cyan-magenta) and pins. This one: a black hole, white-gold disk on
// deep space, coloured tidal streams, space sound design (scripts: audio_space.py), no music.
//  0-1.8     HOOK: cold open at the climax (fast close fly-past, twin stars torn, biggest impact), then a tape rewind
//  1.8-3     rush in from deep space; a background star is lensed into a ring
//  3-13      four stars torn apart one after another (blue, magenta, emerald, gold), each impact sends a ripple ring;
//            the camera rises, orbits, drops edge-on (Einstein ring) and pushes in
//  13-24     the middle at 2.5x: top-down vortex, rings, a dive into the white-blue act + pink nebula, dive back to gold
//  24-30     twin stars torn apart, the biggest heartbeat impact
//  30-33.5   ENDING: the hole swallows its disk, the camera eases away, fade to black
const clip = { src: "generated/0013-black-hole-heart.mp4", fade: [32.4, 33.45] as [number, number] };

export default defineReel({
  id: "0013-black-hole-heart",
  title: "A black hole eats four stars",
  seed: 1313,
  palette: { bg: "#03040a", fg: "#fff3e0", accent: "#ffb055", accent2: "#7a3dff" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 33.0 },
  loop: false,
  illusion: { type: "clip", props: clip },
  transform: { type: "clipContinue", props: clip },
  audio: {
    lufs: -14,
    sfx: [{ at: 0, file: "generated/0013-black-hole-heart-sfx.wav", volume: 1 }],
  },
  cover: { at: 4.8 }, // the blue star's ribbon sweeping over the hole
  publish: {
    youtube: {
      title: "A black hole eats four stars",
      caption: "Four stars fall into a black hole and get torn into glowing ribbons, while its gravity bends the light around it. Every frame was ray-traced with code on a GPU, following how light really curves near a black hole.",
      hashtags: ["#shorts", "#blackhole", "#space"],
    },
    instagram: { caption: "A black hole eats four stars. Watch the light bend around it.", hashtags: ["#reels", "#blackhole", "#space", "#astronomy", "#cinematic"] },
    facebook: { caption: "A black hole eats four stars. Watch the light bend around it.", hashtags: ["#reels", "#blackhole", "#space"] },
    tiktok: { caption: "a black hole eats four stars (watch the light bend)", hashtags: ["#fyp", "#blackhole", "#space", "#astronomy", "#satisfying"] },
    x: { caption: "A black hole eats four stars. Ray-traced with code, light bending and all.", hashtags: ["#blackhole", "#space"] },
  },
});
