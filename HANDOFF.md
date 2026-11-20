# Nov 20 2026, night - HANDOVER (read this first, then CLAUDE.md)
The owner continues from ANOTHER ACCOUNT. Local Claude memory may not be visible there, so everything important is
here. Reply in Bulgarian; code, commits and upload texts stay English. Follow THE LAW in CLAUDE.md.

## 1. Done today
- **0028 "What Happens When a Glass Ball Hits Black Ink"**: delivered, and the owner liked it ("брутално").
  - Scene: `scripts/milk_ink_v2.py` with `MI_OPEN=ball` (own 2D ink-in-milk marble solver). A dark glass ball flies in from the corner, hits a black ink drop at 0.35 s, the drop shatters into black marble, small ink jets pop, the heavy ball sinks and vanishes.
  - Sound: `scripts/gen-ink-ball-audio.ts`. Water sounds only: plips, bubbles, a plunge, and one glass ting on the impact.
  - Files: `publish/0028-glass-ball-black-ink/` (local, git-ignored). Already posted by the owner.

## 2. In progress: reel 0031 "hexagon columns" (NOT approved yet)
Concepts tried today, in order:
- **Geode (crystals in a cracked rock):** REJECTED. `scripts/blender/geode.py`
- **Kinetic sand cutting:** REJECTED as "very childish" (pastel). `scripts/blender/sand_cut.py`
- **Flip-tile wall (10,000 gold/black tiles):** still shown, the owner moved on. `scripts/blender/flip_tiles.py`
- **Hexagon columns** (owner pick; the 0011 "4096 pins" formula): `scripts/blender/hex_columns.py` (scene + still).
  - Test 1 (calm, `hex_anim.py` early version): "looks super".
  - Test 2 (realism, thin glow): "colours boring, effects boring, nothing holds me".
  - Test 3 (sparks, bounce, eruption tower, current `hex_anim.py`): REJECTED. "Not ASMR, not pleasant, I don't like the sparks."
  - Calm version (`hex_calm.py`, flower/star mandala shapes): REJECTED. "No star or flower shapes, they look bad."
  - **CURRENT: `scripts/blender/hex_waves.py`.** Smooth, beautiful, "brutal" physical phenomena, no sparks, no bouncing:
    - 0-2.6 s: three chrome spheres glide in and settle; their ripples interfere (ice/silver);
    - 4-7.4 s: a deep whirlpool with glowing spiral grooves; the spheres orbit it (violet/cyan);
    - 7.6 s: the funnel rebounds into a huge smooth ring wave across the field (magenta -> gold), then everything settles;
    - the colour travels column by column with each wave.
    - Probes looked good. The 12 s full-HD test was rendering into `out/0031/wavetest/` when the session ended (48 of 360 frames done). Out/ is git-ignored, so re-render on the new account.
  - Sound: `scripts/gen_hex_audio.py` (Python). It reads `events.json` beats (land, swirl, wave) and column crossings, and makes soft tactile taps.

### Finish the 0031 test
```
blender -b --factory-startup -P scripts/blender/hex_waves.py -- out/0031/wavetest 12 30      # env HX_RES=1080x1920 HX_SAMPLES=48
   (resume a range: ... 12 30 48 359  - the field state is computed for every frame, so partial ranges are exact)
ffmpeg -framerate 30 -i out/0031/wavetest/f_%04d.png -c:v libx264 -crf 14 -pix_fmt yuv420p out/0031/wavetest/video.mp4
python scripts/gen_hex_audio.py out/0031/wavetest out/0031/wavetest/sfx_raw.wav   (Blender's python works)
ffmpeg -i sfx_raw.wav -af highpass=f=60,highpass=f=60 sfx_hp.wav ; bash scripts/tools/master_audio.sh sfx_hp.wav sfx.wav
mux (crf 19, aac 192k) -> npx tsx scripts/flashcheck.ts <file>  (MUST pass) -> send as "ТЕСТ ..." and wait for the owner
```
- **Speed (measured):** about 2-2.3 s per full-HD frame at 48 samples on the RTX 4070 Ti; a half-size probe frame takes about 1 s.
- **Full reel estimate:** about 35 s at 60 fps is about 80 min; at 30 fps about 40 min. Time a probe before promising.
- **Blender:** `C:\Program Files\Blender Foundation\Blender 5.3\blender.exe`. Python: the `...\5.3\python\bin\python.exe` inside it.

## 3. Owner lessons from today (MUST follow)
1. **Opening that wins:** an object flies in on frame 0 (big, near the lens) and hits at about 0.35 s ("A Glass Ball Hit It", 1.2K views). Heavy objects must sink or settle; never leave one hanging without logic.
2. **Calm, eye-pleasing ASMR**, hypnotic like 0011:
   - REJECTED: sparks, bounces, eruptions, white-hot glare, game-like busyness;
   - REJECTED: flower, star or mandala shapes, faces, pictures;
   - REJECTED: pastel, "childish" looks.
   - Wanted: ripples, interference, vortices, big smooth waves, deep rich colours (calm areas near-black, colour blooms on the waves).
3. **"Boring"** means add beauty and new phenomena. It does not mean add noise.
4. **Two misses in a row:** confirm the core look in ONE line before rendering again.
5. **Sounds:**
   - liquid reels: water sounds (plips, bubbles, plunge), NO bells, harp or glockenspiel, no thocks;
   - mechanical reels: soft tactile taps;
   - phone band (>200 Hz) about -15 to -20 LUFS; high-pass the mix at 60-70 Hz.
6. **Flash check is non-negotiable:** fix the effect, never the rules. Large bright areas must brighten over 0.5-0.8 s and fade slowly; no one-frame jumps, no oscillating glow (`heat_s` attack/release in `hex_anim.py` / `hex_waves.py`).
7. **Frame edges:** after a full render, measure flat or smeared rows and columns at several times (`edges.ts` missed a 6% smear in 0028). Keep the camera clamped inside the scene.
8. **"Improve reel X"** means fix that exact video, never rebuild it. Every still must answer: "would a stranger name the subject in 1 s?"
9. **Delivery format:**
   - one message per video with a big label ("ТОВА Е ЗА YOUTUBE" / "...ЗА TIKTOK, INSTAGRAM, FACEBOOK И X");
   - an under-30 MiB copy (2-pass);
   - a 4K cover plus thumbnails;
   - upload texts pasted as copy boxes;
   - commit (push only when the owner asks).
10. **Public YouTube views on Nov 20** (channel Nevoxia):
    - about 1.1-1.2K each: Glass Ball Hit It, came alive, Core Unlocking, eats steel, 4096 pins, galaxy;
    - One Hit Broke 2000 Beads: 818.
    - The genre "Every X = Y... until..." (rule plus escalation) was getting 9.8K in 10 h in search results.

## 4. Tools
- Audio mastering: `scripts/tools/master_audio.sh`. Edge check: `scripts/tools/edge-check.ts`. Flash check: `scripts/flashcheck.ts`.
- **Chrome extension** was not connected. YouTube can be read through the app's built-in browser (reject non-essential cookies).

# Nov 17 2026, night - state (read first)
- Delivered today: 0024 v9 (liked), 0027 liquid machine (owner: effects too weak), 0028 black ink in milk (owner: "slop",
  sounds unpleasant, too fast). Owner is exhausted and unsure whether to continue; be calm, brief, no pitching.
- Uncommitted WIP: scripts/milk_cosmos.py slowed to ~33 s (rate 0.6 -> 0.32) + scripts/gen-milk-cosmos-audio.ts (soft
  thocks/bloops). Low-res flash check of the slow version is in the task log; nothing re-delivered.
- Lessons (also in memory): confirm the core look in ONE line before building (base, dominant colour, mechanic); never reuse
  a past reel's effect; give clock ETAs only after a quick check passes; 2D sims read flat - "brutal" needs real 3D.

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
