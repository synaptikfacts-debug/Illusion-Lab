# Asset licences

Every file in `assets/` must be listed here before a reel using it is published.
Only royalty-free / properly licensed material. Audio files are not committed to git (see .gitignore);
in-house files are regenerated with `npm run assets`.

| File | Source | Licence | Notes |
|---|---|---|---|
| fonts/Outfit-700.ttf, fonts/Outfit-900.ttf | Outfit Project Authors, github.com/Outfitio/Outfit-Fonts | SIL Open Font License 1.1 (fonts/OFL-Outfit.txt) | |
| music/inhouse-bed-a.wav | Made in-house by `scripts/gen-audio.ts` (synthesised, seeded) | Own work | |
| sfx/inhouse-riser.wav, sfx/inhouse-impact.wav, sfx/inhouse-whoosh.wav | Made in-house by `scripts/gen-audio.ts` | Own work | |
| music/generated (YouTube music) piano | Salamander Grand Piano V3, Alexander Holm (via npm @audio-samples/piano-mp3-velocity6/10) | CC BY 3.0 - credit required: render adds it to the YouTube description | samples/ (git-ignored) |
| music/generated strings, harp, woodblock | VSCO-2 Community Edition (via npm tiny-orchestra 0.2.0) | CC0 | samples/ (git-ignored) |
| generated/*-sfx.wav, *-music.wav | Made in-house from the reel physics (scripts/gen-pin-audio.ts, gen-music.ts) | Own work | |
