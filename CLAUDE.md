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
- YouTube ONLY: SFX + a catchy background track made in-house (scripts/gen-music.ts), synced to the reel's big moment.
- The pipeline does this automatically: `audio.music` / `audio.musicGen` go only into SHORT_ (platforms.ts `music: true`).
