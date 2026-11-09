# Illusion Lab - guide for Claude Code sessions

Owner: devkata (Sofia, UTC+2). Repo synaptikfacts-debug/Illusion-Lab is PRIVATE and stays private.
Commit author dev8xx <milenalbeev@gmail.com>. Code and text only in git, never renders or audio.
Never upload or post anything to any platform; `publish/` is a local folder the owner posts from.

- Read README.md first (commands, reel config, effect contract, checks).
- Work milestone by milestone; after each one render a preview and tell the owner what to look at.
- Ask before adding any paid service or API.
- The photosensitivity check is non-negotiable: fix the effect, never loosen FLASH_RULES to make a render pass.
- Everything must be deterministic: frame-driven animation, seeded randomness (src/core/seed.ts).
- Platform limits live only in config/platforms.ts; re-check sources there before relying on them.
- Package versions are pinned exactly; all @remotion/* packages must stay on the same version.

## RULE: references are a MODEL, never a copy (owner, Nov 9 2026 - main goal)
When the owner shares a reel as a reference ("do something like this"), take the FORMULA, not the content:
what makes it work (e.g. thousands of simple objects, each with its own rhythm -> emergent shapes, sound triggered
by the motion, clean stage, perfect loop, no text). Then invent a NEW mechanic, object, stage, palette and payoff.
Never reproduce its specific setup, layout, camera, colours or effect. Before building, write one line:
"Reference does X. Ours does Y instead" and check Y is clearly different. Reel 0002 (bounce orbs) broke this rule
and is archived in reels/archive/.

## RULE: sound (owner, Nov 9 2026)
- EVERY version has sound effects synced to the motion (ticks, whooshes, impacts, textures). Never silent.
- NO music on Instagram, TikTok, Facebook or X: the owner adds a trending track in the app. SFX must not be tonal
  melodies that would clash with that track.
- YouTube ONLY: SFX + a CALM, satisfying background track made in-house from real sampled instruments (felt piano,
  soft strings, harp; scripts/gen-music.ts), synced to the reel's big moment. Never synth grooves (owner: "cringe, AI slop").
- SFX style: calm and satisfying (soft rounded taps, dark air, gentle settles), never harsh ticks or synth risers.
- The pipeline does this automatically: `audio.music` / `audio.musicGen` go only into SHORT_ (platforms.ts `music: true`).

## RULE: quality bar for every reel (owner, Nov 10 2026: "no ending, not HD, AI slop, cheap sounds")
- STORY WITH AN ENDING: hook on frame 0 -> build -> payoff -> a clear, final ending moment (something settles, closes,
  lands last), then quiet. Write the beat sheet in the reel file first. Loops are a bonus, never instead of an ending.
- HD, REAL-LOOKING: physical materials (metal/glass with PBR + environment), raking key light + soft shadows, depth of
  field on close shots, bloom only on true emissive parts, ACES, 2x supersampling (dpr 2). Fewer, bigger, readable
  objects over thousands of tiny dots; fill the 9:16 frame. No film grain (kills the bitrate). Check native-res crops.
- SOUND HAS A VISIBLE CAUSE: drive SFX from the same simulation as the picture (events -> sounds), use real recorded
  samples (VSCO-2 percussion, Salamander piano), accents on every story beat, silence after the ending.
- YouTube music follows the story beats and resolves on the ending (scripts/gen-music-story.ts is the model).
