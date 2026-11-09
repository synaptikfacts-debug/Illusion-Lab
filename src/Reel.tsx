import React, { useMemo } from "react";
import { AbsoluteFill, Freeze, interpolate, Sequence, useCurrentFrame } from "remotion";
import { Soundtrack } from "./audio/Soundtrack";
import { getEffect } from "./core/registry";
import type { CompositionProps, Reel as ReelT } from "./core/schema";
import { timeline, type Timeline } from "./core/timing";
import {
  Captions,
  Countdown,
  CoverOverlay,
  EndText,
  HookText,
  InstructionText,
  IntensityNotice,
  RevealText,
  SafeZoneOverlay,
} from "./overlays/Text";
import "./fonts";

function useEffectDef(kind: "illusion" | "transform", reel: ReelT) {
  const spec = kind === "illusion" ? reel.illusion : reel.transform;
  return useMemo(() => {
    const def = getEffect(kind, spec.type);
    return { Component: def.component, params: def.schema.parse(spec.props) };
  }, [kind, spec]);
}

/** What frame 0 looks like. Also used by the loop bridge, so the last frame flows back into the first. */
const Opening: React.FC<{ reel: ReelT; tl: Timeline; hud: boolean }> = ({ reel, tl, hud }) => {
  const { Component, params } = useEffectDef("illusion", reel);
  return (
    <AbsoluteFill>
      <Component params={params} reel={reel} tl={tl} />
      {hud && (
        <>
          <HookText reel={reel} tl={tl} />
          <IntensityNotice reel={reel} tl={tl} />
        </>
      )}
    </AbsoluteFill>
  );
};

const LoopBridge: React.FC<{ reel: ReelT; tl: Timeline }> = ({ reel, tl }) => {
  const f = useCurrentFrame(); // relative to bridge start
  const opacity = interpolate(f, [0, tl.bridge.dur - 1], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ opacity }}>
      <Freeze frame={0}>
        <Opening reel={reel} tl={tl} hud />
      </Freeze>
    </AbsoluteFill>
  );
};

export const Reel: React.FC<CompositionProps> = (props) => {
  const { showSafeZone, coverMode, withMusic, ...reel } = props;
  const tl = useMemo(() => timeline(reel), [reel.fps, reel.phases, reel.loopBridgeSec]);
  const transform = useEffectDef("transform", reel);
  return (
    <AbsoluteFill style={{ background: reel.palette.bg }}>
      <Sequence durationInFrames={tl.transform.start} name="Illusion">
        <Opening reel={reel} tl={tl} hud={false} />
      </Sequence>
      <Sequence from={tl.transform.start} durationInFrames={tl.transform.dur} name="Transformation">
        <transform.Component params={transform.params} reel={reel} tl={tl} />
      </Sequence>
      {!coverMode && (
        <>
          <HookText reel={reel} tl={tl} />
          <IntensityNotice reel={reel} tl={tl} />
          <InstructionText reel={reel} tl={tl} />
          <Countdown reel={reel} tl={tl} />
          <RevealText reel={reel} tl={tl} />
          <EndText reel={reel} tl={tl} />
          <Captions reel={reel} tl={tl} />
        </>
      )}
      {!coverMode && (
        <Sequence from={tl.bridge.start} durationInFrames={tl.bridge.dur} name="Loop bridge">
          <LoopBridge reel={reel} tl={tl} />
        </Sequence>
      )}
      <Soundtrack reel={reel} tl={tl} withMusic={withMusic} />
      {coverMode && <CoverOverlay reel={reel} />}
      {showSafeZone && <SafeZoneOverlay />}
    </AbsoluteFill>
  );
};
