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
//  15.2      they MERGE (hit);  16-22 the heartbeat speeds up
//  22        PAYOFF: the CROWN (hit, D major release)
//  24.3-27.5 one long exhale, a last faint heartbeat;  27.5-30 ENDING: fade
const clip = { src: "generated/0012-ferro-music.mp4", fade: [27.5, 29.9] as [number, number] };

export default defineReel({
  id: "0012-ferro-music",
  title: "Ferrofluid vs Music",
  seed: 1212,
  palette: { bg: "#020206", fg: "#22d8ff", accent: "#ff2fa0", accent2: "#7a3dff" },
  phases: { hook: 0.5, challenge: 0, reveal: 0, transform: 29.5 },
  loop: false,
  illusion: { type: "clip", props: clip },
  transform: { type: "clipContinue", props: clip },
  audio: {
    lufs: -18,
    musicVolume: 0.75,
    musicGen: { style: "ferromusic", bpm: 100, seed: 1212 },
    sfx: [{ at: 0, file: "generated/0012-ferro-music-sfx.wav", volume: 1 }],
  },
  cover: { at: 22.9 },
  publish: {
    youtube: { title: "This liquid came alive", caption: "A pool of magnetic liquid with a heartbeat: it reaches out, crawls, splits in two, merges again and rises into a crown. Computer-made, ray-traced in Blender.", hashtags: ["#shorts", "#ferrofluid", "#satisfying"] },
    instagram: { caption: "This liquid came alive. Wait for the crown.", hashtags: ["#reels", "#ferrofluid", "#oddlysatisfying", "#satisfying", "#cinematic"] },
    facebook: { caption: "This liquid came alive. Wait for the crown.", hashtags: ["#reels", "#satisfying"] },
    tiktok: { caption: "this liquid came alive (wait for the crown)", hashtags: ["#fyp", "#ferrofluid", "#oddlysatisfying", "#satisfying", "#asmr"] },
    x: { caption: "A pool of magnetic liquid with a heartbeat comes alive.", hashtags: ["#satisfying"] },
  },
});
