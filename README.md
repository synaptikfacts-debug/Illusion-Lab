# Illusion Lab

Code-driven reel factory: an **optical-illusion challenge** (hook) that resolves into an **impossible
transformation** (payoff), ending on a frame that loops back to frame 1. Remotion + Three.js/GLSL on the GPU,
ffmpeg for platform exports. Every render is deterministic (seeded, frame-driven).

## Setup (once)

- Node 20+ and ffmpeg/ffprobe on PATH.
- `npm install`
- `npm run assets` (regenerates the in-house music bed and SFX; render also does this when they are missing)
- Instrument samples for the YouTube music (git-ignored, ~60 MB) into `samples/`:
  `npm pack @audio-samples/piano-mp3-velocity6@1.0.5 @audio-samples/piano-mp3-velocity10@1.0.5 tiny-orchestra@0.2.0`,
  extract each and move its `package` folder to `samples/piano-v6`, `samples/piano-v10`, `samples/orchestra`.
- Ray-traced reels (e.g. 0010 Ferrofluid Labyrinth) need Blender 5.3 (`winget install BlenderFoundation.Blender`)
  and an NVIDIA GPU for Cycles/OptiX. Picture pipeline:
  `npx tsx scripts/gen-labyrinth-reel.ts out/labyrinth-reel` (per-frame maps; parallel ranges allowed) ->
  `blender -b --factory-startup -P scripts/blender/labyrinth_anim.py -- <mapsDir> <framesDir> 32 <k> <n>` (run n
  instances, k = 0..n-1) -> encode the frames to `assets/generated/<id>.mp4` -> `npm run render -- <id>`.

## Sound rule
Every version gets motion-synced, calm sound effects. Music goes ONLY on the YouTube file (in-house, calm,
real sampled piano/strings/harp); Instagram, TikTok, Facebook and X get SFX only so the owner can add a trending
track. `npm run sound -- <id>` rebuilds a reel's generated audio without rendering video.

Remotion licence: free for individuals and companies with up to 3 employees (remotion.dev/license).

## Commands

| Command | What it does |
|---|---|
| `npm run studio` | Remotion Studio: live preview, every config field editable in the props panel. Turn on `showSafeZone` to see the platform-UI zones. |
| `npm run new -- 0003-count-the-dots "Title"` | New reel config from `reels/_template.ts` |
| `npm run render -- <id> --draft` | Half-size quick render with checks (`out/<id>/draft.mp4`), no exports |
| `npm run render -- <id>` | Master 1080x1920@60 → checks → per-platform files → cover → `publish/<id>/` |
| `npm run render:all` | Every `reels/NNNN-*.ts`, one bundle, summary at the end (non-zero exit if any fail) |
| `npm run flashcheck -- file.mp4` | Photosensitivity check on any video |
| `npm run typecheck` | TypeScript check |

## Make a reel in under 10 minutes

1. `npm run new -- 0007-stare-tiger "Stare at the tiger"`
2. Open `reels/0007-stare-tiger.ts` and fill in:
   - `hook.text` (on screen from frame 0), `challenge.instruction`, `reveal.text`, `endText`
   - `phases` (seconds): hook ≤ 3, challenge, reveal, transform
   - `illusion` / `transform`: a `type` from `src/core/registry.ts` plus its `props` (see that effect's zod schema for options and defaults)
   - `palette`, `audio` (paths are relative to `assets/`; SFX `at` can be `"transform-2"`, `"reveal"`, `"end-3"`, or seconds)
   - `captions` (required if there is a voiceover), `cover`, and `publish` text for each platform
3. `npm run studio`, pick the reel, scrub it, toggle `showSafeZone`.
4. `npm run render -- 0007-stare-tiger --draft`, watch `out/0007-stare-tiger/draft.mp4`.
5. `npm run render -- 0007-stare-tiger` → upload from `publish/0007-stare-tiger/`.

No core code changes are needed: `src/Root.tsx` picks up every `reels/NNNN-*.ts` automatically.

## What a render checks (and fails on)

- **Preflight** (before rendering): length within every platform's min/max, captions not empty, title/caption length and
  hashtag count within limits, all referenced asset files exist.
- **Photosensitivity**: WCAG general-flash and red-flash rules. A flash = a pair of opposite luminance changes of
  ≥ 0.1 (darker state < 0.8) over ≥ 25% of the frame; more than 3 per second in any 1-second window fails the render.
  Limits live in `config/platforms.ts` (`FLASH_RULES`). There is no override flag.
- **Loop**: the last frame must match frame 0 (mean difference ≤ `loopTolerance`, default 4/255). The engine crossfades
  the final `loopBridgeSec` into a frozen copy of frame 0, so this holds for any effect.
- **Loudness**: two-pass EBU R128 to -14 LUFS integrated, -1 dBTP.
- **File size** per platform.

Results go to `out/<id>/report.json` and `publish/<id>/checks.json`.

## Layout

```
config/platforms.ts   every platform limit + safe zone + flash + loudness rules (with sources and check date)
reels/                one config file per reel (+ _template.ts)
src/Root.tsx          auto-registers reels as compositions
src/Reel.tsx          timeline engine: hook → challenge → reveal → transform → loop bridge
src/core/             schema (zod), timing, seeded RNG, effect contract, registry
src/illusions/<name>/ index.tsx (zod props + component) + GLSL
src/transforms/<name>/
src/gl/ShaderPlane    full-frame GLSL on the GPU, uniforms updated per frame
src/overlays/         hook, instruction, countdown, reveal/end text, captions, intensity notice, safe zone, cover
src/audio/            music bed, voiceover slot, SFX cues
scripts/              render, render-all, new, gen-audio, flashcheck, lib/ (ffmpeg, checks, flash, reels)
assets/               fonts, music, sfx, vo, images + LICENSES.md (audio files are git-ignored)
out/, publish/        render output (git-ignored)
```

## Writing a new effect

1. Create `src/illusions/<name>/index.tsx` (or `src/transforms/...`) exporting `defineEffect({ about, schema, component })`.
   - `schema`: zod object with defaults; becomes the `props` a reel can set.
   - `component({ params, reel, tl })`: illusions get the absolute frame from `useCurrentFrame()`; transforms get frames
     since the transform began. Use `tl` (frame spans for each phase) instead of hard-coded times.
   - Animate only from the frame number and `reel.seed` (`src/core/seed.ts`): no `Math.random()`, no clocks.
2. Add one line to `src/core/registry.ts`.
3. GLSL: `import frag from "./x.frag.glsl"` and render with `<ShaderPlane frag uniforms />`; use `rgb()` for colours.

## Platform outputs

| File | Platform | Size | Notes |
|---|---|---|---|
| `SHORT_<id>.mp4` | YouTube Shorts | 1080x1920 60 fps, 12 Mbps | ≤ 3 min |
| `IG_<id>.mp4` | Instagram Reels | 1080x1920 60 fps, 10 Mbps, AAC 128k | ≤ 300 MB |
| `FB_<id>.mp4` | Facebook Reels | 1080x1920 60 fps, 10 Mbps | 3-90 s |
| `TT_<id>.mp4` | TikTok | 1080x1920 60 fps, 10 Mbps | publish limit 3 min |
| `X_<id>.mp4` | X | 720x1280 60 fps, 6 Mbps | free accounts ≤ 2:20 |

All H.264 High, yuv420p, closed 2 s GOP, AAC-LC 48 kHz stereo, faststart. Change numbers in `config/platforms.ts`.
