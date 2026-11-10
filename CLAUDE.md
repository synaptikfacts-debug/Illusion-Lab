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

## RULE: sound (owner, Nov 9 2026; updated Nov 10 2026)
- EVERY version has sound effects synced to the motion. Never silent.
- MUSIC ON EVERY PLATFORM (owner, Nov 10: the 0004 YouTube mix "was really good"): YouTube, Instagram, TikTok,
  Facebook and X all get the same SFX + in-house story score (platforms.ts `music: true` everywhere). The old
  "no music on IG/TT" rule is replaced.
- Music: CALM, satisfying, real sampled instruments (felt piano, strings, harp, pizzicato, glockenspiel), written to
  the story beats and resolving on the ending (scripts/gen-music-story.ts style). Never synth grooves ("cringe, AI slop").
- SFX style: calm and satisfying, from the simulation's own events, real recorded samples.
- The piano is CC BY 3.0: the render adds the credit line to every caption that carries music.

## RULE: quality bar for every reel (owner, Nov 10 2026: "no ending, not HD, AI slop, cheap sounds")
- STORY WITH AN ENDING: hook on frame 0 -> build -> payoff -> a clear, final ending moment (something settles, closes,
  lands last), then quiet. Write the beat sheet in the reel file first. Loops are a bonus, never instead of an ending.
- HD, REAL-LOOKING: physical materials (metal/glass with PBR + environment), raking key light + soft shadows, depth of
  field on close shots, bloom only on true emissive parts, ACES, 2x supersampling (dpr 2). Fewer, bigger, readable
  objects over thousands of tiny dots; fill the 9:16 frame. No film grain (kills the bitrate). Check native-res crops.
- SOUND HAS A VISIBLE CAUSE: drive SFX from the same simulation as the picture (events -> sounds), use real recorded
  samples (VSCO-2 percussion, Salamander piano), accents on every story beat, silence after the ending.
- YouTube music follows the story beats and resolves on the ending (scripts/gen-music-story.ts is the model).
- HOOK (owner, Nov 10: "not catchy at the start AT ALL"): frame 0 already shows the most striking image of the reel
  (the payoff itself, e.g. the glowing eye staring at the viewer), moving, and within ~0.6 s something dramatic
  happens to it (it shatters) so the viewer stays to see it come back. Never open on a calm, empty or grey shot.
- ENDING (owner, Nov 10: "it's just ending like boom"): never cut, never crossfade back to frame 0. Settle slowly
  (2-4 s): the subject closes/rests, the camera eases away, one last small detail (ember) fades, fade to black while
  the last sound rings out. Reels with an ending set `loop: false`.
- HOOK PATTERN that works (owner, Nov 10 on 0005 v1: "doesn't look catchy at the beginning"): never open on a still,
  top-down picture. Open MID-ACTION at the story's most dynamic moment (low, close, things flying toward the lens,
  sparks), then make time visibly run backwards (tape-rewind look + sound) and play the story from the start.
  Implemented as a real-time -> story-time map (dominoes/sim.ts tauAt + scripts/lib/domino-time.ts for audio).
- VISUAL FX baseline: GPU particles from the simulation (sparks on impacts, dust, a dissolve ending), camera that
  arcs to 3/4 angles so motion reads in 3D. Length ~30-35 s is fine when every second moves.

## RULE: EVERY REEL MUST LOOK DIFFERENT (owner, Nov 10 2026 - after 0006 v1 reused 0004's rods and colours)
"Same effects" means the same QUALITY (physical materials, strong hook, real ending, particles, sound from the
motion) - NOT the same objects, materials, colours or effects. Each new reel needs its own:
- object / material (rods, dominoes, glass, liquid, sand, cloth, light... never the previous reel's),
- palette and lighting mood (dark studio vs bright dawn vs neon night...; never the last reel's colours),
- signature visual effect and camera language,
- sound palette (different instruments/samples and a different key/feel for the score).
Before building, write one line: "Last two reels used X/Y. This one uses Z" and check nothing repeats.
History: 0004 chrome rods, dark studio, teal/amber, piano score. 0005 obsidian dominoes, magenta/gold (rejected).
0006 v1 = rods again (rejected for repeating 0004). 0006 v2 = floating glass cubes, bright dawn, harp/marimba.

## RULE: ABSTRACT, MESMERIZING EFFECTS - NO FACES, NO PICTURES (owner, Nov 10 2026)
The owner does not want reels that form a face, an eye, a butterfly or any picture ("why is there even a face?").
What attracts viewers is pure, satisfying, abstract motion - e.g. the 0004 moment where a perfect ring/crater ripples
through thousands of rods (screenshot reference). Build reels from mesmerizing physical phenomena: ripples, rings,
interference, vortexes, spirals, waves, cascades, blooms - one after another, each more striking, with the quality bar
(hook, physical look, ending, motion-driven sound) and the every-reel-different rule.

## RULE: PREVIEW FIRST, ALWAYS (owner, Nov 10 2026)
Every new reel (and every big change): send a preview first - a key-frame sheet + a half-size motion clip WITH sound
(`npm run render -- <id> --draft`) - and WAIT for the owner to approve or reject. No full render, no exports, no
thumbnails, no upload texts until the owner says yes.

## CLARIFIED (owner, Nov 10 2026): what "like this reference" means
Keep the reference's CORE IDEA and mechanic (e.g. thousands of glossy orbs bouncing at their own rhythms, forming
shapes, a click per bounce). Make only the look ours: colours, plate/stage, camera, hook and ending. Do NOT swap in
a different mechanic (Galton board, sand, liquid were all rejected as "nothing to do with the one I sent").
