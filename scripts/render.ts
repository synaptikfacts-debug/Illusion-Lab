// npm run render -- <reel-id> [--draft]
// master render (GPU) -> flash check -> loop check -> loudness -> platform exports -> cover -> publish/<id>/
// --draft: half size, no platform exports or publish folder (quick look at a change).
import { bundle } from "@remotion/bundler";
import { renderMedia, renderStill, selectComposition } from "@remotion/renderer";
import { copyFileSync, existsSync, mkdirSync, rmSync, statSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { DELIVERY_MAX_MIB, PLATFORMS, type PlatformId } from "../config/platforms";
import type { Reel } from "../src/core/schema";
import { resolveTime, timeline } from "../src/core/timing";
import { webpackOverride } from "../src/webpack-override";
import { generateInhouseAudio } from "./gen-audio";
import { generateBounceAudio } from "./gen-bounce-audio";
import { generatePinAudio } from "./gen-pin-audio";
import { generateRodAudio } from "./gen-rod-audio";
import { generateDominoAudio } from "./gen-domino-audio";
import { generateFaceAudio } from "./gen-face-audio";
import { generateLiquidAudio } from "./gen-liquid-audio";
import { generateSandAudio } from "./gen-sand-audio";
import { generateGaltonAudio } from "./gen-galton-audio";
import { generateOrbAudio } from "./gen-orb-audio";
import { generateRingsAudio } from "./gen-rings-audio";
import { generatePendulumAudio } from "./gen-pendulum-audio";
import { generateFerroAudio } from "./gen-ferro-audio";
import { generateInkAudio } from "./gen-ink-audio";
import { generateMusic } from "./gen-music";
import { loopDiff, normaliseLoudness } from "./lib/checks";
import { run } from "./lib/ffmpeg";
import { flashCheck } from "./lib/flash";
import { ASSETS, ENTRY, OUT, PUBLISH } from "./lib/paths";
import { assetPaths, loadReel } from "./lib/reels";

// GPU WebGL via ANGLE; "error" hides three.js deprecation chatter from the browser console.
// CC BY 3.0 requires this credit wherever the in-house music (sampled piano) is published.
const MUSIC_CREDIT = "Music: Illusion Lab. Piano samples: Salamander Grand Piano by Alexander Holm (CC BY 3.0).";
const NO_PIANO_STYLES = ["liquid", "sand"]; // scores without the Salamander piano need no CC BY credit
const MUSIC_CREDIT_SHORT = "Piano: Salamander Grand, A. Holm, CC BY 3.0"; // X (280 chars)

const BROWSER = { chromiumOptions: { gl: "angle" as const }, logLevel: "error" as const };

export async function bundleProject(): Promise<string> {
  const t = Date.now();
  const url = await bundle({ entryPoint: ENTRY, publicDir: ASSETS, webpackOverride });
  console.log(`bundled in ${((Date.now() - t) / 1000).toFixed(1)} s`);
  return url;
}

/** Fails early (before any rendering) on anything a platform would reject. */
export function preflight(reel: Reel): string[] {
  const errors: string[] = [];
  const sec = timeline(reel).total / reel.fps;
  for (const [pid, spec] of Object.entries(PLATFORMS) as [PlatformId, (typeof PLATFORMS)[PlatformId]][]) {
    const text = reel.publish[pid];
    if (sec < spec.minSec || sec > spec.maxSec) errors.push(`${spec.label}: ${sec.toFixed(1)} s is outside ${spec.minSec}-${spec.maxSec} s`);
    if (text.hashtags.length > spec.maxHashtags) errors.push(`${spec.label}: ${text.hashtags.length} hashtags (max ${spec.maxHashtags})`);
    if (!text.caption.trim()) errors.push(`${spec.label}: caption is empty`);
    const full = fullCaption(text.caption, text.hashtags);
    if (full.length > spec.captionMax) errors.push(`${spec.label}: caption ${full.length} chars (max ${spec.captionMax})`);
    if (spec.titleMax !== null) {
      if (!text.title?.trim()) errors.push(`${spec.label}: title is empty`);
      else if (text.title.length > spec.titleMax) errors.push(`${spec.label}: title ${text.title.length} chars (max ${spec.titleMax})`);
    }
  }
  return errors;
}

const fullCaption = (caption: string, tags: string[]) => (tags.length ? `${caption.trim()}\n\n${tags.join(" ")}` : caption.trim());

function step<T>(label: string, fn: () => Promise<T>): Promise<T> {
  const t = Date.now();
  process.stdout.write(`- ${label}... `);
  return fn().then((v) => {
    console.log(`done (${((Date.now() - t) / 1000).toFixed(1)} s)`);
    return v;
  });
}

export async function renderReel(id: string, opts: { serveUrl?: string; draft?: boolean; reuseVideo?: boolean } = {}) {
  const t0 = Date.now();
  const reel = await loadReel(id);
  const draft = !!opts.draft;
  console.log(`\n== ${id}${draft ? " (draft)" : ""} ==`);

  const errors = preflight(reel);
  if (!draft && errors.length) throw new Error(`Preflight failed:\n  ${errors.join("\n  ")}`);
  if (draft && errors.length) console.log(`(preflight warnings, ignored in draft)\n  ${errors.join("\n  ")}`);

  if (assetPaths(reel).some((p) => /inhouse-/.test(p) && !existsSync(p))) generateInhouseAudio();
  // generated, picture-synced audio (always rebuilt: it depends on the reel params)
  const usesGenerated = assetPaths(reel).some((p) => /[\\/]generated[\\/]/.test(p));
  if (usesGenerated && reel.illusion.type === "bounceField") generateBounceAudio(reel);
  if (usesGenerated && reel.illusion.type === "pinWall") generatePinAudio(reel);
  if (usesGenerated && reel.illusion.type === "rodStory") generateRodAudio(reel);
  if (usesGenerated && reel.illusion.type === "dominoStory") generateDominoAudio(reel);
  if (usesGenerated && reel.illusion.type === "faceStory") generateFaceAudio(reel);
  if (usesGenerated && reel.illusion.type === "liquid") generateLiquidAudio(reel);
  if (usesGenerated && reel.illusion.type === "sand") generateSandAudio(reel);
  if (usesGenerated && reel.illusion.type === "galton") generateGaltonAudio(reel);
  if (usesGenerated && reel.illusion.type === "orbs") generateOrbAudio(reel);
  if (usesGenerated && reel.illusion.type === "rings") generateRingsAudio(reel);
  if (usesGenerated && reel.illusion.type === "pendulum") generatePendulumAudio(reel);
  if (usesGenerated && reel.illusion.type === "ferro") generateFerroAudio(reel);
  if (usesGenerated && reel.illusion.type === "ink") generateInkAudio(reel);
  if (reel.audio.musicGen) generateMusic(reel);
  const missing = assetPaths(reel).filter((p) => !existsSync(p));
  if (missing.length) throw new Error(`Missing assets:\n  ${missing.join("\n  ")}`);

  const dir = join(OUT, id);
  mkdirSync(dir, { recursive: true });
  const serveUrl = opts.serveUrl ?? (await bundleProject());
  const composition = await selectComposition({ serveUrl, id, inputProps: {}, ...BROWSER });
  const master = join(dir, draft ? "draft-video.mp4" : "master.mp4");
  const hasMusic = !!(reel.audio.music || reel.audio.musicGen);
  const sfxMix = join(dir, "mix-sfx.wav"), sfxNorm = join(dir, "mix-sfx-norm.wav");
  const musicMix = join(dir, "mix-music.wav"), musicNorm = join(dir, "mix-music-norm.wav");

  let lastPct = -1;
  // --reuse-video: keep the existing master picture (sound-only changes), redo mixes, checks and exports
  if (!(opts.reuseVideo && existsSync(master))) await step(`render video ${composition.durationInFrames} frames @ ${draft ? "540x960" : "1080x1920"}`, () =>
    renderMedia({
      composition,
      serveUrl,
      codec: "h264",
      crf: draft ? 22 : 12,
      x264Preset: draft ? "veryfast" : "medium",
      imageFormat: "jpeg",
      jpegQuality: 95,
      scale: draft ? 0.5 : 1,
      muted: true,
      ...BROWSER,
      outputLocation: master,
      onProgress: ({ progress }) => {
        const pct = Math.floor(progress * 10) * 10;
        if (pct !== lastPct) process.stdout.write(`${(lastPct = pct)}% `);
      },
    }),
  );
  // two mixes: SFX only (Instagram/TikTok/Facebook/X) and SFX + music (YouTube)
  const audioComp = (withMusic: boolean) => selectComposition({ serveUrl, id, inputProps: { withMusic }, ...BROWSER });
  await step("render SFX mix", async () =>
    renderMedia({ composition: await audioComp(false), serveUrl, codec: "wav", outputLocation: sfxMix, inputProps: { withMusic: false }, timeoutInMilliseconds: 180000, ...BROWSER }),
  );
  if (hasMusic)
    await step("render music mix (YouTube)", async () =>
      renderMedia({ composition: await audioComp(true), serveUrl, codec: "wav", outputLocation: musicMix, inputProps: { withMusic: true }, timeoutInMilliseconds: 180000, ...BROWSER }),
    );

  const flash = await step("photosensitivity check", () => flashCheck(master));
  const loop = await step("loop check", () => loopDiff(master, composition.durationInFrames));
  const loud = await step("loudness -14 LUFS (SFX mix)", () => normaliseLoudness(sfxMix, sfxNorm, reel.audio.lufs));
  const loudMusic = hasMusic ? await step("loudness -14 LUFS (music mix)", () => normaliseLoudness(musicMix, musicNorm, reel.audio.lufs)) : null;
  const mixFor = (music: boolean) => (music && hasMusic ? musicNorm : sfxNorm);
  const report = { id, draft, seconds: composition.durationInFrames / reel.fps, flash, loop: { diff: loop, tolerance: reel.loopTolerance }, loudness: { sfx: loud, music: loudMusic } };
  writeFileSync(join(dir, "report.json"), JSON.stringify(report, null, 2));

  console.log(
    `  flashes/s: luminance ${flash.maxFlashesPerSec.luminance}, red ${flash.maxFlashesPerSec.red} (max 3) | loop diff ${loop.toFixed(2)} (max ${reel.loopTolerance}) | SFX ${loud.silent ? "SILENT" : `${loud.outputLUFS} LUFS`}${loudMusic ? ` | music mix ${loudMusic.outputLUFS} LUFS` : ""}`,
  );
  if (!flash.pass)
    throw new Error(
      `PHOTOSENSITIVITY FAIL: ${flash.maxFlashesPerSec.luminance} luminance / ${flash.maxFlashesPerSec.red} red flashes per second ` +
        `(worst window at ${flash.worstAt.luminance.toFixed(2)} s / ${flash.worstAt.red.toFixed(2)} s). See out/${id}/report.json`,
    );
  if (loud.silent) throw new Error("SOUND FAIL: the SFX mix is silent - every version needs sound effects (owner rule)");
  if (reel.loop && loop > reel.loopTolerance) throw new Error(`LOOP FAIL: last frame differs from frame 0 by ${loop.toFixed(2)} (max ${reel.loopTolerance})`);

  if (draft) {
    const files: string[] = [];
    for (const [name, music] of [["draft-youtube.mp4", true], ["draft-sfx.mp4", false]] as const) {
      if (music && !hasMusic) continue;
      const preview = join(dir, name);
      await step(`mux ${name}`, () =>
        run("ffmpeg", ["-y", "-v", "error", "-i", master, "-i", mixFor(music), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", preview]),
      );
      files.push(preview);
    }
    rmSync(master);
    console.log(`draft ready: ${files.join(", ")} (${((Date.now() - t0) / 1000).toFixed(0)} s total)`);
    return { id, dir, files };
  }

  const pub = join(PUBLISH, id);
  rmSync(pub, { recursive: true, force: true });
  mkdirSync(pub, { recursive: true });
  const files: string[] = [];
  for (const [pid, spec] of Object.entries(PLATFORMS) as [PlatformId, (typeof PLATFORMS)[PlatformId]][]) {
    const out = join(pub, `${spec.filePrefix}_${id}.mp4`);
    const gop = String(spec.fps * 2);
    // fit under the delivery cap (MiB) with 8% headroom for container + VBR overshoot
    const capKbps = Math.floor(((DELIVERY_MAX_MIB * 8 * 1048576) / 1000 / (composition.durationInFrames / reel.fps)) * 0.8) - spec.audioKbps;
    const vKbps = Math.min(spec.videoKbps, capKbps), maxKbps = Math.min(spec.maxrateKbps, Math.round(capKbps * 1.25));
    await step(`export ${spec.label} ${spec.width}x${spec.height}`, () =>
      run("ffmpeg", [
        "-y", "-v", "error", "-i", master, "-i", mixFor(spec.music), "-map", "0:v:0", "-map", "1:a:0",
        "-vf", `scale=${spec.width}:${spec.height}:flags=lanczos,fps=${spec.fps}`,
        "-c:v", "libx264", "-profile:v", "high", "-level:v", "4.2", "-preset", "slow", "-pix_fmt", "yuv420p",
        "-b:v", `${vKbps}k`, "-maxrate", `${maxKbps}k`, "-bufsize", `${maxKbps * 2}k`,
        "-g", gop, "-keyint_min", gop, "-sc_threshold", "0",
        "-c:a", "aac", "-b:a", `${spec.audioKbps}k`, "-ar", String(spec.sampleRate), "-ac", "2",
        "-shortest", "-movflags", "+faststart", out,
      ]),
    );
    const mb = statSync(out).size / 1024 / 1024;
    if (mb > Math.min(spec.maxFileMB, DELIVERY_MAX_MIB)) throw new Error(`${spec.label}: ${mb.toFixed(1)} MiB is over the limit`);
    const text = reel.publish[pid];
    writeFileSync(
      join(pub, `${pid}.txt`),
      [
        `PLATFORM: ${spec.label}`,
        `VIDEO: ${spec.filePrefix}_${id}.mp4 (${mb.toFixed(1)} MB)`,
        `COVER: cover.jpg`,
        `SOUND: ${spec.music && hasMusic ? "SFX + in-house music" : "SFX only"}`,
        ...(spec.titleMax !== null ? ["", "TITLE:", text.title ?? ""] : []),
        "",
        spec.titleMax !== null ? "DESCRIPTION:" : "CAPTION:",
        spec.music && hasMusic && !NO_PIANO_STYLES.includes(reel.audio.musicGen?.style ?? "")
          ? fullCaption(`${text.caption.trim()}

${pid === "x" ? MUSIC_CREDIT_SHORT : MUSIC_CREDIT}`, text.hashtags)
          : fullCaption(text.caption, text.hashtags),
        "",
      ].join("\n"),
    );
    files.push(out);
  }

  const tl = timeline(reel);
  const coverComp = await selectComposition({ serveUrl, id, inputProps: { coverMode: true }, ...BROWSER });
  const coverPng = join(dir, "cover.png");
  await step("cover", async () => {
    await renderStill({ composition: coverComp, serveUrl, frame: resolveTime(reel.cover.at, tl), output: coverPng, inputProps: { coverMode: true }, ...BROWSER });
    await run("ffmpeg", ["-y", "-v", "error", "-i", coverPng, "-q:v", "2", join(pub, "cover.jpg")]);
  });
  copyFileSync(join(dir, "report.json"), join(pub, "checks.json"));
  console.log(`published to ${pub} (${((Date.now() - t0) / 1000).toFixed(0)} s total)`);
  return { id, dir: pub, files };
}

if (/render\.ts$/.test(process.argv[1] ?? "")) {
  const args = process.argv.slice(2);
  const id = args.find((a) => !a.startsWith("--"));
  if (!id) {
    console.error("usage: npm run render -- <reel-id> [--draft]");
    process.exit(1);
  }
  renderReel(id, { draft: args.includes("--draft"), reuseVideo: args.includes("--reuse-video") }).catch((e) => {
    console.error(`\nRENDER FAILED: ${e.message}`);
    process.exit(1);
  });
}
