import { defineReel } from "../src/core/define";

// Pure visual reel: no words on screen. Something new happens every 2-4 seconds; the end flows into frame 1.
// Timeline (transform-relative): 0.4 burst | 2.8 galaxy | 5.2 -> knot | 9.8 -> heart | 14.4 -> sculpture | 19 loop
const look = { bg0: "#070a24", bg1: "#2a1260", tint: "#22e3ff", tint2: "#ff3fd8" };

export default defineReel({
  id: "0001-living-afterimage",
  title: "Liquid chrome becomes a galaxy, a knot and a heart",
  seed: 4242,
  palette: { bg: "#070a24", fg: "#7ff3ff", accent: "#22e3ff", accent2: "#ff3fd8" },
  challenge: { countdown: false, focus: { x: 0.5, y: 0.5 } },
  phases: { hook: 4.5, challenge: 0, reveal: 0, transform: 19 },
  illusion: { type: "livingSculpture", props: { look } },
  transform: { type: "morphChain", props: { look, count: 80000 } },
  audio: {
    music: "music/inhouse-bed-a.wav",
    musicVolume: 0.6,
    sfx: [
      { at: "transform+0.35", file: "sfx/inhouse-impact.wav", volume: 0.9 },
      { at: "transform+4.9", file: "sfx/inhouse-whoosh.wav", volume: 0.7 },
      { at: "transform+9.5", file: "sfx/inhouse-whoosh.wav", volume: 0.7 },
      { at: "transform+9.8", file: "sfx/inhouse-heartbeat.wav", volume: 0.8 },
      { at: "transform+14.6", file: "sfx/inhouse-riser.wav", volume: 0.7 },
      { at: "transform+16.7", file: "sfx/inhouse-impact.wav", volume: 0.5 },
    ],
  },
  cover: { at: "transform+11.5" },
  publish: {
    youtube: {
      title: "Liquid chrome turns into a galaxy, then a heart",
      caption: "Watch it all the way to the end. Which shape was your favourite?",
      hashtags: ["#shorts", "#satisfying", "#3danimation"],
    },
    instagram: {
      caption: "Liquid chrome, a galaxy, a knot and a heart. Which shape was your favourite?",
      hashtags: ["#reels", "#satisfying", "#3danimation", "#oddlysatisfying"],
    },
    facebook: { caption: "Liquid chrome turns into a galaxy, a knot and a heart.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "Wait for the heart", hashtags: ["#fyp", "#satisfying", "#3danimation"] },
    x: { caption: "Liquid chrome turns into a galaxy, a knot and a heart.", hashtags: ["#satisfying"] },
  },
});
