import React from "react";
import { Audio, interpolate, Sequence, staticFile } from "remotion";
import type { Reel } from "../core/schema";
import { resolveTime, type Timeline } from "../core/timing";

/** Music bed + optional voiceover + SFX cues. Paths are relative to assets/. Loudness is normalised after render. */
export const Soundtrack: React.FC<{ reel: Reel; tl: Timeline }> = ({ reel, tl }) => {
  const { music, musicVolume, vo, voVolume, sfx } = reel.audio;
  const fadeOut = Math.round(tl.fps * 0.5);
  return (
    <>
      {music && (
        <Audio
          src={staticFile(music)}
          volume={(f) =>
            musicVolume * interpolate(f, [tl.total - fadeOut, tl.total], [1, 0.4], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
          }
        />
      )}
      {vo && <Audio src={staticFile(vo)} volume={voVolume} />}
      {sfx.map((cue, i) => (
        <Sequence key={i} from={resolveTime(cue.at, tl)} layout="none">
          <Audio src={staticFile(cue.file)} volume={cue.volume} />
        </Sequence>
      ))}
    </>
  );
};
