# Handoff (Nov 16 2026, night) - read this first, then CLAUDE.md

The owner continues from another account (weekly limit hit). Nothing below is in local memory on the new account.

## Nov 17 2026 - owner's OpenArt drone video (READ FIRST)
- The owner made a 27 s 720p AI video on OpenArt (file on their Desktop: openart-cgt-20261117055510-...mp4): drones in
  a dark hangar draw squares, a ring, a coil and a double helix with light trails, a red laser grid, then land.
- Done: a 4K cover (ring frame at 9.3 s) + upload texts with AI labels ON (YouTube "altered or synthetic: YES", TikTok/IG
  AI label ON) in `publish/openart-drones/` (local only, not in git).
- AI tells: the drones have NO propellers; garbled lettering on the close-up drone (~19-21 s); drones merge/pop; lasers
  switch on without cause; soft 720p.
- **Next (owner): "rework the video so it doesn't look AI".** Offer two routes: (1) edit the clip - cut 19-21 s and the
  glitchy bits, upscale to 1080x1920, grade, real sound (props stay missing -> keep the AI label); (2) rebuild the idea in
  Blender with real drones (spinning props, LEDs, light-trail paths) - the 0025 drone work below
  (`scripts/blender/drone_model.py`, `drone_swarm.py`, `drone_anim.py`, `src/scenes/drones/timeline.json`) is the start.

## What happened on Nov 16 (night) - READ BEFORE PITCHING ANYTHING
- **0023 "Mercury learned to dance"** (32 mercury drops in patterns, magenta/lime bokeh): REJECTED - "super childish,
  effects super bad, I expected something professional like This thing eats steel". Archived in reels/archive/.
- **0023 v2 "This liquid became a storm"** (crimson ferrofluid lake: spike walls, vortex, tornado, collapse;
  `src/scenes/ferroMusic/storm.ts`, `ferro_alive.py` FERRO_LOOK=E): stills approved, then the owner changed direction.
  Not rendered/delivered. (Its hook first failed the flash check: a travelling spike wall swept dark crests over the
  bright lake - fixed by raising the wall in place.)
- **0024 "This core is unlocking"** (cyber/tech, owner pick: a black machined cryptex sphere, 8 anodised + 6 chrome dial
  bands clack into place, explode into floating bands, crystal core ignites; sparks/arcs/shockwaves in
  `src/scenes/core/fx.ts`, Blender `scripts/blender/core_unlock.py`, cinematic C-minor orchestral score
  `scripts/gen-music-core.ts`): REJECTED twice - "super boring, nothing happens at the start, almost no visual effects,
  just a ball" and "you clearly didn't ask yourself whether I would watch it". Not delivered.
- **Owner direction for the next reel:** cyber / tech / visual effects. NO cars, NO cities, NO AI video generators.
  Start by pitching 2-3 genuinely new concepts, each with the first 3 seconds described concretely; build nothing
  before the owner picks.

## Lessons (put these into memory on the new account)
- WATCH THE WHOLE DRAFT AS A STRANGER before sending it - not only the flash log and key-frame sheets. A single slow
  object in a dark room is a product shot, not a reel; effects bolted on top do not save it.
- Report every result the moment it lands, good or bad (a wait-loop that only matched success hid a FAILED render for
  15 min). Run long pipelines as ONE background command that exits on any outcome.
- Flash check: fix the effect, never the rule. Things that failed today: a spike wall sweeping over a bright lake; spark
  bursts flying straight into a macro lens (huge out-of-focus blobs).
- Music: the calm felt piano + harp score was "not the right music" for a tech video; for tech use a driving
  orchestral score (ostinato strings, low brass, timpani) - still real samples, never synth grooves.
- Blender 5.3 notes: AgX desaturates bright cyan emission to white - `core_unlock.py` uses "Khronos PBR Neutral";
  light linking keeps a strong core light off the background; compositor = `scene.compositing_node_group` + Glare
  node with a "Type" menu socket. A CPU worker (CORE_CPU=1 CORE_REVERSE=1) adds little - the GPU is the bottleneck.

## Older rules (from Nov 16 evening)
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
