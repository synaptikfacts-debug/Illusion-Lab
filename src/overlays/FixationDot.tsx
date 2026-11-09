import React from "react";
import { useVideoConfig } from "remotion";
import type { Reel } from "../core/schema";

/** The point viewers stare at. Shared by illusions so it looks the same in every reel. */
export const FixationDot: React.FC<{ reel: Reel; size?: number; color?: string }> = ({ reel, size = 26, color }) => {
  const { width, height } = useVideoConfig();
  const { x, y } = reel.challenge.focus;
  return (
    <div
      style={{
        position: "absolute",
        left: x * width - size / 2,
        top: y * height - size / 2,
        width: size,
        height: size,
        borderRadius: "50%",
        background: color ?? "#ff2d55",
        boxShadow: `0 0 0 4px ${reel.palette.fg}, 0 0 24px rgba(0,0,0,0.45)`,
      }}
    />
  );
};
