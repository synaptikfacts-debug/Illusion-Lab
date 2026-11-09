import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { z } from "zod";
import { defineEffect } from "../../core/effect";
import { FixationDot } from "../../overlays/FixationDot";
import { SculptureScene } from "../../scenes/sculpture/SculptureScene";

const hex = z.string().regex(/^#[0-9a-fA-F]{6}$/);
export const sculptureLookSchema = z.object({
  bg0: hex.default("#070a24"),
  bg1: hex.default("#2a1260"),
  tint: hex.default("#22e3ff"),
  tint2: hex.default("#ff3fd8"),
});

const schema = z.object({
  look: sculptureLookSchema.default({ bg0: "#070a24", bg1: "#2a1260", tint: "#22e3ff", tint2: "#ff3fd8" }),
  /** Seconds the stare image needs to switch to its inverted colours. */
  invertSec: z.number().default(0.35),
});

/**
 * Negative afterimage on a living sculpture.
 * Hook: the sculpture moves. Challenge: it freezes in inverted colours (stare at the dot).
 * Reveal: instant switch to grayscale - the brain paints the real colours back in.
 */
export const livingAfterimage = defineEffect({
  about: "Living chrome sculpture; freezes in inverted colours for the stare, grayscale reveal shows colour.",
  schema,
  component: ({ params, reel, tl }) => {
    const frame = useCurrentFrame();
    const { width, height } = useVideoConfig();
    const freeze = tl.hook.end / tl.fps;
    const live = Math.min(frame, tl.hook.end) / tl.fps;
    const inv = frame >= tl.reveal.start ? 0 : interpolate(frame, [tl.challenge.start, tl.challenge.start + params.invertSec * tl.fps], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    const gray = frame >= tl.reveal.start ? 1 : 0;
    const bgMix = interpolate(frame, [tl.challenge.start, tl.challenge.start + params.invertSec * tl.fps], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

    // progress ring around the dot while staring (helps fixation, tiny area)
    const ringP = interpolate(frame, [tl.challenge.start, tl.challenge.end], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    const staring = frame >= tl.challenge.start && frame < tl.challenge.end;
    const cx = reel.challenge.focus.x * width, cy = reel.challenge.focus.y * height, R = 46;

    return (
      <AbsoluteFill>
        <SculptureScene
          seed={reel.seed}
          look={params.look}
          focusY={reel.challenge.focus.y}
          state={{ time: frame < tl.hook.end ? live : freeze, bgTime: live, inv, gray, bgMix }}
        />
        {frame >= tl.hook.end - 6 && <FixationDot reel={reel} />}
        {staring && (
          <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
            <circle cx={cx} cy={cy} r={R} fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth={5} />
            <circle
              cx={cx}
              cy={cy}
              r={R}
              fill="none"
              stroke="#ffffff"
              strokeWidth={5}
              strokeLinecap="round"
              strokeDasharray={`${2 * Math.PI * R * ringP} ${2 * Math.PI * R}`}
              transform={`rotate(-90 ${cx} ${cy})`}
            />
          </svg>
        )}
      </AbsoluteFill>
    );
  },
});
