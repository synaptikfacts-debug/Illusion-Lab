import { z } from "zod";
import { SAFE_ZONE } from "../../config/platforms";

/** Seconds (number) or a phase-relative reference: "hook", "challenge+2", "reveal-0.5", "transform+1", "end-3". */
export const TimeRef = z.union([z.number(), z.string().regex(/^(hook|challenge|reveal|transform|end)([+-]\d+(\.\d+)?)?$/)]);

const hex = z.string().regex(/^#[0-9a-fA-F]{6}$/);

export const EffectSchema = z.object({
  type: z.string(),
  props: z.record(z.string(), z.unknown()).default({}),
});

const PlatformText = z.object({
  title: z.string().optional(),
  caption: z.string(),
  hashtags: z.array(z.string().regex(/^#\S+$/)).default([]),
});

export const ReelSchema = z
  .object({
    id: z.string().regex(/^\d{4}-[a-z0-9-]+$/),
    title: z.string(),
    fps: z.number().int().default(60),
    width: z.number().int().default(1080),
    height: z.number().int().default(1920),
    seed: z.number().int(),
    palette: z.object({ bg: hex, fg: hex, accent: hex, accent2: hex }),
    /** All on-screen words are optional: leave them out for a pure visual reel. */
    hook: z.object({ text: z.string().optional(), sub: z.string().optional() }).default({}),
    challenge: z.object({
      instruction: z.string().optional(),
      countdown: z.boolean().default(true),
      /** Illusion focal point in frame fractions; must sit inside the safe zone. */
      focus: z.object({ x: z.number(), y: z.number() }).default({ x: 0.5, y: 0.5 }),
    })
      .default({ countdown: false, focus: { x: 0.5, y: 0.5 } }),
    reveal: z.object({ text: z.string().optional() }).default({}),
    endText: z.string().optional(),
    phases: z.object({
      hook: z.number().min(0.5).max(8),
      challenge: z.number().min(0),
      reveal: z.number().min(0),
      transform: z.number().min(1),
    }),
    /** Last N seconds crossfade into frame 0 so the reel loops seamlessly. */
    loopBridgeSec: z.number().min(0.1).max(2).default(0.6),
    /** false = the reel has a real ending: no crossfade back into frame 0 and no loop check. */
    loop: z.boolean().default(true),
    illusion: EffectSchema,
    transform: EffectSchema,
    /** Shows the "intense visual pattern" notice at the start. */
    intense: z.boolean().default(false),
    postfx: z.array(EffectSchema).default([]),
    audio: z
      .object({
        /** Music file (assets/...). YOUTUBE ONLY - other platforms get the SFX mix (owner adds trending music). */
        music: z.string().nullable().default(null),
        /** Generate a catchy in-house track for YouTube (scripts/gen-music.ts) instead of a file. */
        musicGen: z
          .object({ style: z.enum(["loop", "rodStory", "dominoStory"]).default("loop"), bpm: z.number().default(120), dropAt: TimeRef.optional(), key: z.number().int().default(57), seed: z.number().int().default(1) })
          .optional(),
        musicVolume: z.number().min(0).max(1).default(0.6),
        vo: z.string().nullable().default(null),
        voVolume: z.number().min(0).max(1).default(1),
        sfx: z
          .array(z.object({ at: TimeRef, file: z.string(), volume: z.number().min(0).max(1).default(1) }))
          .default([]),
      })
      .default({ music: null, musicVolume: 0.6, vo: null, voVolume: 1, sfx: [] }),
    /** Burned-in captions (required for every voiceover line). */
    captions: z.array(z.object({ at: TimeRef, dur: z.number().positive(), text: z.string() })).default([]),
    cover: z.object({ at: TimeRef.default(0.8), title: z.string().optional(), sub: z.string().optional() }),
    publish: z.object({
      youtube: PlatformText,
      instagram: PlatformText,
      facebook: PlatformText,
      tiktok: PlatformText,
      x: PlatformText,
    }),
    /** Max mean abs difference (0-255) between last frame and frame 0. */
    loopTolerance: z.number().default(4),
  })
  .superRefine((r, ctx) => {
    const { x, y } = r.challenge.focus;
    if (x < SAFE_ZONE.left || x > 1 - SAFE_ZONE.right || y < SAFE_ZONE.top || y > 1 - SAFE_ZONE.bottom)
      ctx.addIssue({ code: "custom", path: ["challenge", "focus"], message: "focus point is outside the safe zone" });
    if (r.audio.vo && r.captions.length === 0)
      ctx.addIssue({ code: "custom", path: ["captions"], message: "voiceover needs burned-in captions" });
  });

export type ReelInput = z.input<typeof ReelSchema>;
export type Reel = z.output<typeof ReelSchema>;

/** Props of the Remotion composition: the reel plus preview toggles (editable live in Studio). */
export const CompositionSchema = ReelSchema.safeExtend({
  showSafeZone: z.boolean().default(false),
  coverMode: z.boolean().default(false),
  /** false = SFX-only mix (Instagram/TikTok/Facebook/X); true = with music (YouTube). */
  withMusic: z.boolean().default(true),
});
export type CompositionProps = z.output<typeof CompositionSchema>;
