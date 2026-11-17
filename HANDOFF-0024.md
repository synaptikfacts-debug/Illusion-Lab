# 0024 DELIVERED (Nov 17 2026, v9 - replaces v8) - read this first
- v9 (owner: "quality from 5 s on is bad, looks like AI"): haze OFF (milky wash), no painted circuit pattern in the bands,
  64 samples + adaptive 0.01, AgX "Medium High Contrast", softer bloom; wall light rings removed (owner); a strip-light
  gleam sweeps the chrome on the opens/ignition/final click (light-linked to the machine only) + a slowly drifting key.
- Delivered as ONE sounds-only video (owner: no music on YouTube this time): publish/0024-core-unlock/0024-core-unlock.mp4.

## v8 notes
- Hook A: starts inside the closed sphere on a liquid-metal (mercury) core, camera flies out through the equator slit.
- Effects: the mote galaxy was rejected ("looks like a planet with stars, copies the space video"); now a CIRCUIT FLOOR
  (PCB traces, data pulses arrive on every lock, fire out on ignition) + a laser SCAN RING (src/scenes/core/fx.ts fxFrame).
- Music: owner (a musician) rejected orchestral + 8 orchestral/harmony options; approved an ELECTRONIC score
  (scripts/gen-music-core-synth.ts, F minor 110 BPM, pure synthesis, wired via generateCoreMusic). No piano credit.
- Speed: Cycles hook frames took 23 s/frame (haze volume + chrome bounces with the camera inside) -> cut while inside,
  now ~2.5 s/frame; 1260 frames at 60 fps rendered in ~40 min. Edge check fixed with rack light columns on the wall.
- Delivered: publish/0024-core-unlock/ SHORT + SOCIALS + cover_4k.jpg + upload_texts.md (local, not in git).

# Handoff: 0024 "This core is unlocking" - draft state (Nov 17 2026)

Read CLAUDE.md and HANDOFF.md first. This file is only about 0024. Answer the owner in Bulgarian.

## Status in one line
Draft v3 (with VFX + cinematic score) was sent to the owner and **REJECTED: "super boring, everything, just a ball;
you clearly didn't ask yourself whether I'd watch it"**. Not delivered. The final 60 fps render was started and
stopped. If the owner wants 0024 continued, the job is to make it genuinely exciting, not to polish it.

## What it is
A black machined cryptex sphere (8 anodised outer dial bands + 6 chrome inner bands) hovering over a machined base in a
dark vault studio (cyan/violet light, thin haze). Story, real time (21 s, `loop: false`):
- 0-0.6 cold open on the climax (open bands around the blazing crystal core; a core eruption at 0.3 s with sparks,
  arcs, floor shockwave) -> 0.6-1.6 fast rewind (sparks fly backwards), sphere slams shut
- 1.6-6.5 dials spin (grind sparks from a pawl) and clack into place one by one (spark burst, energy pulse round the
  band, floor shockwave, seam arc); macro camera pass along the seam at ~5.5 s
- 6.75 light pulse up the seam -> 7-8.6 outer shell explodes into a floating stack (circuit traces glow inside the bands)
- 8.3-10 inner chrome dials lock; inner shell opens
- ~11.5 (slow motion 0.4x around it) the crystal core ignites; 12-14 bands orbit/wobble, arcs core->bands, motes,
  flares at story 12.05/12.7/13.35
- 14-17.2 story: bands come home one by one, top cap clicks last (real ~18.2 s); seam fades; fade 19.3-20.95

## Files (all committed)
- `reels/0024-core-unlock.ts` - reel config (clip `generated/0024-core-unlock.mp4`, musicGen style `core`, cover 12.6 s)
- `src/scenes/core/core.ts` - timeline: schedules, `tauAt` (real->story time incl. cold open, rewind, slow-mo), `realAt`,
  `bandsAt`, `coreFrame`, `coreEvents` (sound events in real time)
- `src/scenes/core/fx.ts` - VFX as polylines: grind sparks, lock/home bursts (sideways along the seam - NOT at the lens),
  unlock/ignite/flare bursts, floor shockwaves, band pulses, seam/unlock/core arcs, orbiting motes
- `scripts/gen-core-frames.ts` - `npx tsx scripts/gen-core-frames.ts <outDir> [fps] [t1,t2,...]` -> frames.json
- `scripts/blender/core_unlock.py` - Cycles scene: bands (bmesh spin + notch boolean + bevel), engraved anodised/chrome
  shaders, circuit traces (object prop "glow"), crystal + energy-vein heart, base, floor, vault wall, wash spots,
  haze volume, light linking, FX ribbon mesh rebuilt per frame, Glare bloom, view transform "Khronos PBR Neutral"
- `scripts/gen-core-audio.ts` - SFX (creamy double thocks, felted whirrs, puffs, booms, hums) from coreEvents
- `scripts/gen-music-core.ts` - v2 score: cinematic C minor orchestra (ostinato celli/basses, brass + timpani hits per
  lock, timpani roll into ignition, full chord, horns; strings fade). The v1 piano/harp score was rejected as wrong.

## Commands
```
# frame data (30 fps draft / 60 fps final)
npx tsx scripts/gen-core-frames.ts out/core30 30
# render (3 GPU workers; env CORE_RES=540x960 for drafts; CORE_FORCE=1 re-renders existing; CORE_CPU=1 CORE_REVERSE=1
# adds a CPU worker from the end - small gain, GPU is the bottleneck at 99%)
"/c/Program Files/Blender Foundation/Blender 5.3/blender.exe" -b --factory-startup -P scripts/blender/core_unlock.py -- out/core30 out/core30/frames 24 <k> 3
# encode + pipeline
ffmpeg -framerate 30 -i out/core30/frames/f_%04d.png -c:v libx264 -crf 14 -pix_fmt yuv420p assets/generated/0024-core-unlock.mp4
npm run render -- 0024-core-unlock --draft      # final: without --draft (60 fps frames, crf 12)
```
Speed: 540x960 ~1.6 s/frame per GPU worker (3 workers ~100 frames/min); 1080p final estimated ~30-35 min for 1260 frames.
Upload texts draft (English, AI-free claims ok - this one is rendered): `out/0024_upload_texts.md` (local, not in git;
title "This Core Is Unlocking"); `npm run render` wipes `publish/<id>/`, write texts after it.

## Checks on the last draft
- Flash: 2/s (max 3) - PASS. Earlier fail (3.5/s at 5.6 s) came from lock sparks flying into the macro lens -> fixed.
- Edge band: WARNING, 40% of frames have a flat dark TOP edge (vault wall above the sphere). Unfixed - brighten/texture
  the upper wall or lower the camera horizon before any delivery.
- Loudness: SFX -14.85, music mix -14.51 LUFS.

## Why it failed (do not repeat)
- A single slow object in a dark room reads as a product shot. The closed-sphere phase (1.6-6.5 s) is "just a ball"
  even with sparks; the effects are small in frame; colours are dark navy/grey.
- I sent drafts after checking flash logs and key-frame sheets only - never watched the motion as a stranger.
- If continuing: cut the closed phase to ~1.5 s, make the explosion/core the main body of the reel, bigger and closer
  effects, brighter frame, faster camera; then watch the whole draft honestly before sending ("would I swipe?").
