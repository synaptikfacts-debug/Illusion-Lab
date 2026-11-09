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
