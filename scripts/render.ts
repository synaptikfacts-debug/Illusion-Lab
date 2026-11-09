// npm run render -- <reel-id> [--draft]
// master render (GPU) -> flash check -> loop check -> loudness -> platform exports -> cover -> publish/<id>/
// --draft: half size, no platform exports or publish folder (quick look at a change).
import { bundle } from "@remotion/bundler";
import { renderMedia, renderStill, selectComposition } from "@remotion/renderer";
import { copyFileSync, existsSync, mkdirSync, rmSync, statSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { PLATFORMS, type PlatformId } from "../config/platforms";
import type { Reel } from "../src/core/schema";
import { resolveTime, timeline } from "../src/core/timing";
import { webpackOverride } from "../src/webpack-override";
import { generateInhouseAudio } from "./gen-audio";
import { generateBounceAudio } from "./gen-bounce-audio";
import { generatePinAudio } from "./gen-pin-audio";
import { loopDiff, normaliseLoudness } from "./lib/checks";
import { run } from "./lib/ffmpeg";
import { flashCheck } from "./lib/flash";
import { ASSETS, ENTRY, OUT, PUBLISH } from "./lib/paths";
import { assetPaths, loadReel } from "./lib/reels";

// GPU WebGL via ANGLE; "error" hides three.js deprecation chatter from the browser console.
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

export async function renderReel(id: string, opts: { serveUrl?: string; draft?: boolean } = {}) {
  const t0 = Date.now();
  const reel = await loadReel(id);
  const draft = !!opts.draft;
  console.log(`\n== ${id}${draft ? " (draft)" : ""} ==`);

  const errors = preflight(reel);
  if (!draft && errors.length) throw new Error(`Preflight failed:\n  ${errors.join("\n  ")}`);
  if (draft && errors.length) console.log(`(preflight warnings, ignored in draft)\n  ${errors.join("\n  ")}`);

  if (assetPaths(reel).some((p) => /inhouse-/.test(p) && !existsSync(p))) generateInhouseAudio();
  // generated, picture-synced audio (always rebuilt: it depends on the reel params)
  if (reel.illusion.type === "bounceField") generateBounceAudio(reel);
  if (reel.illusion.type === "pinWall") generatePinAudio(reel);
  const missing = assetPaths(reel).filter((p) => !existsSync(p));
  if (missing.length) throw new Error(`Missing assets:\n  ${missing.join("\n  ")}`);

  const dir = join(OUT, id);
  mkdirSync(dir, { recursive: true });
  const serveUrl = opts.serveUrl ?? (await bundleProject());
  const composition = await selectComposition({ serveUrl, id, inputProps: {}, ...BROWSER });
  const master = join(dir, draft ? "draft-video.mp4" : "master.mp4");
  const mix = join(dir, "mix.wav");
  const mixNorm = join(dir, "mix-norm.wav");

  let lastPct = -1;
  await step(`render video ${composition.durationInFrames} frames @ ${draft ? "540x960" : "1080x1920"}`, () =>
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
  await step("render audio", () =>
    renderMedia({ composition, serveUrl, codec: "wav", outputLocation: mix, ...BROWSER }),
  );

  const flash = await step("photosensitivity check", () => flashCheck(master));
  const loop = await step("loop check", () => loopDiff(master, composition.durationInFrames));
  const loud = await step("loudness -14 LUFS", () => normaliseLoudness(mix, mixNorm));
  const report = { id, draft, seconds: composition.durationInFrames / reel.fps, flash, loop: { diff: loop, tolerance: reel.loopTolerance }, loudness: loud };
  writeFileSync(join(dir, "report.json"), JSON.stringify(report, null, 2));

  console.log(
    `  flashes/s: luminance ${flash.maxFlashesPerSec.luminance}, red ${flash.maxFlashesPerSec.red} (max 3) | loop diff ${loop.toFixed(2)} (max ${reel.loopTolerance}) | ${loud.silent ? "silent" : `${loud.outputLUFS} LUFS, TP ${loud.truePeak} dB`}`,
  );
  if (!flash.pass)
    throw new Error(
      `PHOTOSENSITIVITY FAIL: ${flash.maxFlashesPerSec.luminance} luminance / ${flash.maxFlashesPerSec.red} red flashes per second ` +
        `(worst window at ${flash.worstAt.luminance.toFixed(2)} s / ${flash.worstAt.red.toFixed(2)} s). See out/${id}/report.json`,
    );
  if (loop > reel.loopTolerance) throw new Error(`LOOP FAIL: last frame differs from frame 0 by ${loop.toFixed(2)} (max ${reel.loopTolerance})`);

  if (draft) {
    const preview = join(dir, "draft.mp4");
    await step("mux draft", () =>
      run("ffmpeg", ["-y", "-v", "error", "-i", master, "-i", mixNorm, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", preview]),
    );
    rmSync(master);
    console.log(`draft ready: ${preview} (${((Date.now() - t0) / 1000).toFixed(0)} s total)`);
    return { id, dir, files: [preview] };
  }

  const pub = join(PUBLISH, id);
  rmSync(pub, { recursive: true, force: true });
  mkdirSync(pub, { recursive: true });
  const files: string[] = [];
  for (const [pid, spec] of Object.entries(PLATFORMS) as [PlatformId, (typeof PLATFORMS)[PlatformId]][]) {
    const out = join(pub, `${spec.filePrefix}_${id}.mp4`);
    const gop = String(spec.fps * 2);
    await step(`export ${spec.label} ${spec.width}x${spec.height}`, () =>
      run("ffmpeg", [
        "-y", "-v", "error", "-i", master, "-i", mixNorm, "-map", "0:v:0", "-map", "1:a:0",
        "-vf", `scale=${spec.width}:${spec.height}:flags=lanczos,fps=${spec.fps}`,
        "-c:v", "libx264", "-profile:v", "high", "-level:v", "4.2", "-preset", "slow", "-pix_fmt", "yuv420p",
        "-b:v", `${spec.videoKbps}k`, "-maxrate", `${spec.maxrateKbps}k`, "-bufsize", `${spec.maxrateKbps * 2}k`,
        "-g", gop, "-keyint_min", gop, "-sc_threshold", "0",
        "-c:a", "aac", "-b:a", `${spec.audioKbps}k`, "-ar", String(spec.sampleRate), "-ac", "2",
        "-shortest", "-movflags", "+faststart", out,
      ]),
    );
    const mb = statSync(out).size / 1024 / 1024;
    if (mb > spec.maxFileMB) throw new Error(`${spec.label}: ${mb.toFixed(1)} MB is over ${spec.maxFileMB} MB`);
    const text = reel.publish[pid];
    writeFileSync(
      join(pub, `${pid}.txt`),
      [
        `PLATFORM: ${spec.label}`,
        `VIDEO: ${spec.filePrefix}_${id}.mp4 (${mb.toFixed(1)} MB)`,
        `COVER: cover.jpg`,
        ...(spec.titleMax !== null ? ["", "TITLE:", text.title ?? ""] : []),
        "",
        spec.titleMax !== null ? "DESCRIPTION:" : "CAPTION:",
        fullCaption(text.caption, text.hashtags),
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
  renderReel(id, { draft: args.includes("--draft") }).catch((e) => {
    console.error(`\nRENDER FAILED: ${e.message}`);
    process.exit(1);
  });
}
