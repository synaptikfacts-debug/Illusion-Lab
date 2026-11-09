// One place for every platform limit. Update here when a platform changes its rules.
// `verified` = date the numbers were last checked against `sources`.
// Where official pages disagree or only cover the API, the conservative value is used and `notes` says so.

export type PlatformId = "youtube" | "instagram" | "facebook" | "tiktok" | "x";

export interface PlatformSpec {
  label: string;
  filePrefix: string;
  width: number;
  height: number;
  fps: number;
  videoKbps: number;
  maxrateKbps: number;
  audioKbps: number;
  sampleRate: number;
  minSec: number;
  maxSec: number;
  maxFileMB: number;
  titleMax: number | null; // null = platform has no separate title
  captionMax: number;
  maxHashtags: number;
  verified: string;
  sources: string[];
  notes: string;
}

/** Fractions of the 1080x1920 frame covered by platform UI. Keep text and focal points inside. */
export const SAFE_ZONE = { top: 0.15, bottom: 0.25, left: 0.06, right: 0.14 } as const;

/** Photosensitivity limits (WCAG 2.x general flash + red flash thresholds). */
export const FLASH_RULES = {
  maxFlashesPerSecond: 3,
  /** Share of the frame that must change together to count as a flash (Ofcom/Harding use 25% of screen). */
  areaFraction: 0.25,
  luminanceDelta: 0.1, // relative luminance change
  darkerBelow: 0.8, // the darker state must be below this
  redDelta: 20, // WCAG red-flash measure: change in (R-G-B)*320 where R/(R+G+B) >= 0.8
} as const;

/** Owner rule: every delivered file must be under 30 MiB so it reaches the phone. Video bitrate is lowered to fit. */
export const DELIVERY_MAX_MIB = 29;

export const LOUDNESS = { integratedLUFS: -14, truePeakDb: -1, lra: 11 } as const;

export const PLATFORMS: Record<PlatformId, PlatformSpec> = {
  youtube: {
    label: "YouTube Shorts",
    filePrefix: "SHORT",
    width: 1080,
    height: 1920,
    fps: 60,
    videoKbps: 12000,
    maxrateKbps: 16000,
    audioKbps: 192,
    sampleRate: 48000,
    minSec: 1,
    maxSec: 180,
    maxFileMB: 2000,
    titleMax: 100,
    captionMax: 5000,
    maxHashtags: 3,
    verified: "2026-11-09",
    sources: ["https://support.google.com/youtube/answer/15424877"],
    notes:
      "Square/vertical up to 3 min counts as a Short. Over 1 min with any active copyright claim = blocked worldwide, so keep music in-house or licensed. Hashtag cap is house style (more than ~3 dilutes).",
  },
  instagram: {
    label: "Instagram Reels",
    filePrefix: "IG",
    width: 1080,
    height: 1920,
    fps: 60,
    videoKbps: 10000,
    maxrateKbps: 14000,
    audioKbps: 128,
    sampleRate: 48000,
    minSec: 3,
    maxSec: 180,
    maxFileMB: 300,
    titleMax: null,
    captionMax: 2200,
    maxHashtags: 5,
    verified: "2026-11-09",
    sources: ["https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media"],
    notes:
      "API allows 3 s to 15 min, VBR max 25 Mbps, 300 MB, closed GOP, AAC 48 kHz 128 kbps. maxSec 180 = longest Reel still recommended to non-followers. Hashtag cap 5 is Instagram's current limit (not on the API page; check in-app).",
  },
  facebook: {
    label: "Facebook Reels",
    filePrefix: "FB",
    width: 1080,
    height: 1920,
    fps: 60,
    videoKbps: 10000,
    maxrateKbps: 14000,
    audioKbps: 192,
    sampleRate: 48000,
    minSec: 3,
    maxSec: 90,
    maxFileMB: 1000,
    titleMax: null,
    captionMax: 2200,
    maxHashtags: 5,
    verified: "2026-11-09",
    sources: ["https://developers.facebook.com/docs/video-api/guides/reels-publishing"],
    notes:
      "Reels API: 3-90 s, 9:16, 24-60 fps fixed, closed GOP 2-5 s, AAC-LC stereo 48 kHz >= 128 kbps. App uploads may allow longer; 90 s keeps every route open.",
  },
  tiktok: {
    label: "TikTok",
    filePrefix: "TT",
    width: 1080,
    height: 1920,
    fps: 60,
    videoKbps: 10000,
    maxrateKbps: 14000,
    audioKbps: 192,
    sampleRate: 48000,
    minSec: 3,
    maxSec: 180,
    maxFileMB: 4000,
    titleMax: null,
    captionMax: 2200,
    maxHashtags: 5,
    verified: "2026-11-09",
    sources: ["https://developers.tiktok.com/doc/content-posting-api-media-transfer-guide"],
    notes:
      "Upload up to 10 min / 4 GB, 23-60 fps, but the publish limit for ALL creators is 3 min (some get 5-10). Caption cap kept at 2200 to be safe.",
  },
  x: {
    label: "X",
    filePrefix: "X",
    width: 720,
    height: 1280,
    fps: 60,
    videoKbps: 6000,
    maxrateKbps: 9000,
    audioKbps: 192,
    sampleRate: 48000,
    minSec: 1,
    maxSec: 140,
    maxFileMB: 512,
    titleMax: null,
    captionMax: 280,
    maxHashtags: 2,
    verified: "2026-11-09",
    sources: ["https://docs.x.com/x-api/media/quickstart/best-practices"],
    notes:
      "Docs: max 1280x1024 box, portrait 720x1280 recommended (1080p only for subscribers), <= 60 fps, >= 5 Mbps video, AAC-LC, no open GOP. Duration: API says 20 min default, but free accounts posting in-app are capped at 2:20, so 140 s.",
  },
};
