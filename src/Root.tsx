import React from "react";
import { Composition } from "remotion";
import { CompositionSchema, ReelSchema } from "./core/schema";
import { timeline } from "./core/timing";
import { Reel } from "./Reel";

// Every reels/NNNN-name.ts (not starting with "_") becomes a composition. No core edits needed per reel.
const ctx = import.meta.webpackContext("../reels", { recursive: false, regExp: /^\.\/\d{4}-[\w-]+\.ts$/ });

const reels = ctx.keys().map((key) => {
  const reel = ReelSchema.parse(ctx(key).default);
  const file = key.replace(/^\.\//, "").replace(/\.ts$/, "");
  if (reel.id !== file) throw new Error(`reels/${file}.ts has id "${reel.id}" - it must match the file name`);
  return reel;
});

export const Root: React.FC = () => (
  <>
    {reels.map((reel) => (
      <Composition
        key={reel.id}
        id={reel.id}
        component={Reel}
        schema={CompositionSchema}
        defaultProps={{ ...reel, showSafeZone: false, coverMode: false, withMusic: true }}
        width={reel.width}
        height={reel.height}
        fps={reel.fps}
        durationInFrames={timeline(reel).total}
        calculateMetadata={({ props }) => ({
          durationInFrames: timeline(props).total,
          fps: props.fps,
          width: props.width,
          height: props.height,
        })}
      />
    ))}
  </>
);
