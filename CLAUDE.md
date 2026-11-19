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
- TWO VIDEOS PER REEL (owner, Nov 16 2026 - replaces the Nov 15 per-platform rule): deliver exactly 2 files -
  (1) the YouTube Short: SFX + the in-house story score; (2) ONE sounds-only file the owner posts on TikTok,
  Instagram, Facebook AND X (the owner adds music inside those apps). Set in config/platforms.ts (`music: true` only
  for youtube). Hand the owner just these two (+ thumbnails and texts), not five exports.
- SFX are creamy, muted THOCKS (the 0011 Singing Pins thock: low sine body with a slight pitch drop + a felted
  low-passed puff); no bright clicks or woodblocks.
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
Nov 10-11: 0010 frost on a window and 0010 liquid-gold black hole (browser shaders) were rejected as "boring, AI slop,
not realistic". 0010 Ferrofluid Labyrinth was APPROVED: ray-traced in Blender (real glass, macro lens, LED backlight),
amber->magenta->violet light, calm felt-piano taps + strings in C# major (first busy mix was "annoying").

## RULE: ULTRA-REALISTIC = BLENDER (owner, Nov 11 2026)
The owner wants ultra-realistic HD; the browser-shader look reads as CG. Realistic reels are ray-traced in Blender
(Cycles, GPU/OptiX on the RTX 4070 Ti), scenes built in Python scripts (scripts/blender/, no .blend files in git), then
played through the normal Remotion pipeline (`clip` effect) for sound, checks and exports. Before animating, send ONE
still for approval, then a short motion test. Render fast: parallel map workers, frames rendered as soon as their
inputs exist, adaptive sampling + OptiX denoiser (owner expects ~30 min, not hours). Stay in the LIQUID line
(0006/0008/0009/0010) unless the owner says otherwise. Sound must be calm: few soft sounds, no drums/rumble/plucks.

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

## RULE: THE SWIPE TEST - be the stranger in the feed (owner, Nov 15 2026, on 0021 v1: "pretend you are the watcher,
## will you watch this or swipe immediately? I am 100% sure you will swipe")
Before sending ANY still or preview, watch it as a stranger scrolling Shorts/Reels with the sound on, and answer in
writing, honestly, in the message: "Would I stop and watch, or swipe?" If the honest answer is swipe, do not send it -
fix it first. It fails (= swipe) if ANY of these is true:
- the first 0.5 s is not the most striking image of the reel, or nothing dramatic happens in it;
- it looks cheap, CG or "AI slop": plain white/grey untextured objects, flat even lighting, thousands of tiny identical
  dots, a flat noise backdrop, glows that look pasted on;
- the materials don't carry the colour of the scene (objects must reflect/refract their world - e.g. in space, chrome
  and glass full of nebula colour, never plain white balls);
- the theme the owner asked for (e.g. "cosmic / space colours") is not obvious in the very first frame;
- it does not look like a professional studio render: one strong key light, deep blacks, rich colour, real depth.
Say which of these you checked and what you changed. The owner should never have to point these out.

## RULE: OWNER CHECKLIST - run it on the key stills BEFORE every preview (owner, Nov 15 2026: "remember everything I
## said, don't make me fix your mistakes every time and waste credits")
- HOOK: frame 0 is the climax/most striking moving image, a dramatic event within 0.5 s (cold open + fast rewind works);
  something new every 1-2 s; honestly ask "would I swipe?".
- LOOK: ultra realistic (Blender Cycles), bright enough to see everything, a NEW palette every reel (0012-0018 were purple/cyan, 0019 emerald) - no brown/orange;
  no cheap/AI-looking glows; subjects are full 3D forms; every reel looks different from the last one.
- FRAMING: subject centred and fully in frame all the time; camera pulls back as things grow/spread; never blurry.
- SOUND: creamy, muted, soft thocks tied to visible events; no bright clicks/woodblocks, no noise beds, never childish.
- ENDING: settle + fade. Previews 30 fps, finals 60 fps, 4 GPU workers, 4K thumbnails, texts for every platform.
- EDGES: no large flat single-colour areas along the frame edges - Instagram flagged 0018 "Your video has a border".
  Fill the top/bottom/sides with real detail (lit background with depth, soft bokeh shapes, objects). The render now
  runs an edge-band check (scripts/lib/edges.ts) and prints a WARNING; fix it before delivering.

## RULE: TIME BUDGET + NO LOST WORK (owner, Nov 19 2026 - after 0028 ink took a whole day: "a similar Short took 30
## MINUTES", "you lost 4 hours of my time") - the owner pays for every message and is short of money
- A reel must fit ~30-60 min of wall time from approval to delivery. BEFORE building, research the method yourself and
  time a short probe on this machine INCLUDING its heaviest part (e.g. late, ink-filled simulation frames). If the full
  job won't fit, pick a lighter method - never make the owner wait hours.
- Blender fluid (Mantaflow) bakes on the CPU only; the GPU only speeds up Cycles rendering. Bake cost grows as the
  fluid fills the domain - measure late frames.
- ETAs only from measurements, with margin. Never promise a time you have not measured.
- Check sharpness at full 1080p and sound on the phone band (>200 Hz, ~-20 LUFS) yourself before sending anything; do
  not make the owner find blur or silence.
- Ask the owner only real taste decisions, in ONE question; research and decide everything else yourself.
- NEVER experiment on live work: copy first. Never point a second Blender process at a live fluid cache - it deletes it.
- Start long jobs detached (PowerShell Start-Process) so a session restart can't kill them; chain bake -> render ->
  encode automatically.

## RULE: RESEARCH EVERYTHING, PROPOSE, REPORT PROBLEMS (owner, Nov 19 2026 - in capitals, "ALWAYS, ABSOLUTELY ALWAYS")
- For EVERY video, before building: research what the owner asked for and what wins on Shorts/Reels/TikTok right now
  (top-performing similar videos, hooks, effects, pacing, length, sound), then send a short proposal: how it would look
  most beautiful, which effects to use, and what holds every viewer to the end. Recommend the most winning (earning)
  variant, and say why.
- Use full capacity and the best, fastest tools for the job; find the fastest route to the same or better quality
  (time a probe first - see TIME BUDGET).
- When a PROBLEM appears (something fails, gets slow, looks worse, costs time or risks work): tell the owner AT ONCE
  with the facts, the options and a recommendation - do NOT take a unilateral "fix" that can cost hours. Routine
  technical details stay mine to decide; anything that affects time, quality, cost or risk goes to the owner first.
