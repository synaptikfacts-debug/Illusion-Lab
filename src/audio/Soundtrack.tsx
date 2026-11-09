import React from "react";
import { Audio, interpolate, Sequence, staticFile } from "remotion";
import type { Reel } from "../core/schema";
import { resolveTime, type Timeline } from "../core/timing";

/** Music bed + optional voiceover + SFX cues. Paths are relative to assets/. Loudness is normalised after render. */
export const Soundtrack: React.FC<{ reel: Reel; tl: Timeline; withMusic: boolean }> = ({ reel, tl, withMusic }) => {
  const { musicVolume, vo, voVolume, sfx } = reel.audio;
  // music only in the YouTube mix (owner rule); generated tracks are built to loop, so no fade
  const music = withMusic ? (reel.audio.musicGen ? `generated/${reel.id}-music.wav` : reel.audio.music) : null;
  const loops = !!reel.audio.musicGen;
  const fadeOut = Math.round(tl.fps * 0.5);
  return (
    <>
      {music && (
        <Audio
          src={staticFile(music)}
          volume={(f) =>
            musicVolume * (loops ? 1 : interpolate(f, [tl.total - fadeOut, tl.total], [1, 0.4], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }))
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
