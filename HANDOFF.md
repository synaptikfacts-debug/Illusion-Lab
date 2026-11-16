# Handoff (Nov 16 2026, evening) - read this first, then CLAUDE.md

The owner continues from another account. Everything below was decided in chat and is not obvious from the code.

## Owner rules learned today (also add them to memory)
- **Language:** the owner writes Bulgarian now -> answer in Bulgarian. Code, comments, commits, upload texts stay English.
- **Two videos per reel:** `SHORT_<id>.mp4` (YouTube: SFX + score) and `SOCIALS_<id>.mp4` (= the TT export, sounds
  only, posted on TikTok/Instagram/Facebook/X). Move the other exports to `out/<id>/extra-exports`.
- **Every delivery:** send the 2 videos, then PASTE the upload texts in chat, each field in its own code block
  (YouTube title/description/tags, TikTok, Instagram, Facebook, X + settings lines), unasked. Then commit the repo.
- `npm run render` wipes `publish/<id>/` - write `upload_texts.md` AFTER it (keep a copy in `out/`).
- **Look:** the owner loves 0021's look. No crystal/faceted spikes - smooth glossy cones only. No needle "crowns"
  (read as crystals/flowers). No plain white objects. Chrome needs bright panels around it to reflect.
- **Theme:** stay in the liquid/sphere line (0021 space got poor views). Never re-pitch a made concept
  (heartbeat=0019, eats steel=0018, came alive=0012, galaxy, black hole=0013, glass, pins=0011, ink=0009, climb=0022).
- The owner is impatient with long waits: give minute + clock-time ETAs, skip the preview if they say so.

## State
- 0021 The Break (60 s) and 0022 This Liquid Climbs (20 s) are delivered and committed.
- **Next reel 0023 "Mercury learned to dance" - concept stills shown, owner wants it "incredible, with effects that
  keep everyone watching to the end".** Concept scene: `scripts/blender/concepts_0023.py` (liquid-chrome drops on
  black glass, magenta + lime light, white strip panels for reflections; looks A/B/C below).
  Story (~20 s): 0-0.6 a bass hit throws dozens of mercury drops into the air, frozen -> fast rewind; 2-6 drops
  tremble and bounce on the black glass drum; 6-12 the vibration sorts them into patterns (ring -> spiral -> wave
  star) and they merge into bigger drops; 12-16 the last big drops orbit faster and merge with a splash into ONE big
  mirror sphere; 16-20 it wobbles, settles, fade. Sound: a creamy thock on every merge + soft bass pulses; score on
  harp + glockenspiel rising with each pattern.
- To build it, follow `scripts/blender/ferro_climb.py` + `scripts/gen-climb-audio.ts` / `gen-music-climb.ts` /
  `src/scenes/climb/timeline.json` / `reels/0022-liquid-climb.ts` as the template (new musicGen style wired in
  `src/core/schema.ts`, `scripts/gen-music.ts`, `scripts/render.ts`, `scripts/gen-sound.ts`).
- Render: Blender at `/c/Program Files/Blender Foundation/Blender 5.3/blender.exe`, 3 workers
  (`-- <outdir> 48 60 <k> 3`), ~45 frames/min at 1080x1920 -> a 20 s reel renders in ~30 min. Encode with
  `ffmpeg -framerate 60 -i f_%04d.png -c:v libx264 -crf 12 -pix_fmt yuv420p assets/generated/<id>.mp4`, then
  `npm run render -- <id>`.
