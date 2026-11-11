import { defineReel } from "../src/core/define";

// Owner (Nov 11): ferrofluid is the best performer (0010: 1.1k YouTube views on a new account) -> a ferrofluid series,
// each episode a new mechanic. Ep. 2 "Ferrofluid vs Music": a pool of black ferrofluid in a speaker dish, ray-traced
// in Blender (scripts/blender/ferro_music.py, look approved from ferro_speaker_look.py). One score
// (src/scenes/ferroMusic/score.ts) drives the spikes AND the piano: each note raises one ring of spikes (pitch ->
// radius), the last chord raises a crown, then the pool relaxes into a mirror. Differs from 0010 (flat labyrinth
// between glass, amber LED) and 0011 (pins): 3D spike field, speaker dish, cyan/magenta studio light, music-synced.
// v7 (owner, Nov 11: 'more alive, more details, no spinning, no dish, no brown'): the ferrofluid is a living creature
// on black mirror glass (scripts/blender/ferro_alive.py, timeline src/scenes/ferroMusic/creature.ts).
//  0-2.6     HOOK: mid-heartbeat, rings of spikes rushing out (lub-dub)
//  2.6-5     it reaches out (pseudopod);  5-10 it crawls, a ripple along its back, droplets get swallowed
//  10-15.2   it splits in two; the halves answer each other's heartbeats
//  15.2      they MERGE (hit)
//  15.6-19.6 a spiral wave runs over its spikes while droplets rain onto it
//  19.6-26.2 it splits into THREE, they circle and answer each other; 26.2 they slam together (hit)
//  27-33     the heartbeat speeds up;  33 PAYOFF: the CROWN + a burst of droplets (hit, D major)
//  35.3-38.5 one long exhale, the droplets pulled home, a last faint heartbeat;  38.5-42 ENDING: fade
const clip = { src: "generated/0012-ferro-music.mp4", fade: [38.5, 41.9] as [number, number] };

export default defineReel({
  id: "0012-ferro-music",
  title: "Ferrofluid vs Music",
  seed: 1212,
  palette: { bg: "#020206", fg: "#22d8ff", accent: "#ff2fa0", accent2: "#7a3dff" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 41.5 },
  loop: false,
  illusion: { type: "clip", props: clip },
  transform: { type: "clipContinue", props: clip },
  audio: {
    lufs: -18,
    musicVolume: 0.75,
    musicGen: { style: "ferromusic", bpm: 100, seed: 1212 },
    sfx: [{ at: 0, file: "generated/0012-ferro-music-sfx.wav", volume: 1 }],
  },
  cover: { at: 33.5 }, // the crown burst (thumbnails come from a 4K still)
  publish: {
    youtube: { title: "This liquid came alive", caption: "A pool of magnetic liquid with a heartbeat: it reaches out, crawls, splits in two, then in three, slams back together and rises into a crown. Computer-made, ray-traced in Blender.", hashtags: ["#shorts", "#ferrofluid", "#satisfying"] },
    instagram: { caption: "This liquid came alive. Wait for the crown.", hashtags: ["#reels", "#ferrofluid", "#oddlysatisfying", "#satisfying", "#cinematic"] },
    facebook: { caption: "This liquid came alive. Wait for the crown.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "this liquid came alive (wait for the crown)", hashtags: ["#fyp", "#ferrofluid", "#oddlysatisfying", "#satisfying", "#asmr"] },
    x: { caption: "A pool of magnetic liquid with a heartbeat comes alive.", hashtags: ["#satisfying"] },
  },
});
