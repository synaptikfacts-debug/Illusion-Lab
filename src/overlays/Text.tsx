import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { SAFE_ZONE } from "../../config/platforms";
import type { Reel } from "../core/schema";
import { resolveTime, type Timeline } from "../core/timing";
import { FONT } from "../fonts";

export function useSafeRect() {
  const { width, height } = useVideoConfig();
  const x = SAFE_ZONE.left * width;
  const y = SAFE_ZONE.top * height;
  return { x, y, w: width * (1 - SAFE_ZONE.left - SAFE_ZONE.right), h: height * (1 - SAFE_ZONE.top - SAFE_ZONE.bottom) };
}

const SHADOW = "0 6px 28px rgba(0,0,0,0.55), 0 2px 0 rgba(0,0,0,0.35)";

/** Text block anchored inside the safe zone. `anchor` = "top" | "bottom" of the safe rect, `offset` in px. */
const SafeText: React.FC<{
  anchor: "top" | "bottom";
  offset?: number;
  opacity?: number;
  scale?: number;
  children: React.ReactNode;
}> = ({ anchor, offset = 0, opacity = 1, scale = 1, children }) => {
  const s = useSafeRect();
  return (
    <div
      style={{
        position: "absolute",
        left: s.x,
        width: s.w,
        ...(anchor === "top" ? { top: s.y + offset } : { bottom: undefined, top: s.y + s.h - offset }),
        transform: `${anchor === "bottom" ? "translateY(-100%) " : ""}scale(${scale})`,
        transformOrigin: anchor === "top" ? "50% 0%" : "50% 100%",
        opacity,
        textAlign: "center",
        fontFamily: FONT,
        color: "#ffffff",
        textShadow: SHADOW,
        lineHeight: 1.05,
      }}
    >
      {children}
    </div>
  );
};

const fade = (f: number, a: number, b: number, len = 8) =>
  interpolate(f, [a, a + len, b - len, b], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

/** Hook: fully visible on frame 0 (no intro), leaves quickly when the challenge starts. */
export const HookText: React.FC<{ reel: Reel; tl: Timeline }> = ({ reel, tl }) => {
  const f = useCurrentFrame();
  if (f >= tl.hook.end + 10) return null;
  const out = interpolate(f, [tl.hook.end - 2, tl.hook.end + 10], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const pop = interpolate(f, [0, 10], [1, 1.04], { extrapolateRight: "clamp" });
  return (
    <SafeText anchor="top" offset={40} opacity={out} scale={pop}>
      <div style={{ fontSize: 118, fontWeight: 900, letterSpacing: -1, textTransform: "uppercase" }}>{reel.hook.text}</div>
      {reel.hook.sub && (
        <div style={{ fontSize: 54, fontWeight: 700, marginTop: 18, color: reel.palette.fg }}>{reel.hook.sub}</div>
      )}
    </SafeText>
  );
};

export const InstructionText: React.FC<{ reel: Reel; tl: Timeline }> = ({ reel, tl }) => {
  const f = useCurrentFrame();
  if (f < tl.challenge.start || f >= tl.challenge.end) return null;
  return (
    <SafeText anchor="top" offset={30} opacity={fade(f, tl.challenge.start + 4, tl.challenge.end)}>
      <div style={{ fontSize: 64, fontWeight: 900, textTransform: "uppercase" }}>{reel.challenge.instruction}</div>
    </SafeText>
  );
};

export const Countdown: React.FC<{ reel: Reel; tl: Timeline }> = ({ reel, tl }) => {
  const f = useCurrentFrame();
  const s = useSafeRect();
  if (!reel.challenge.countdown || f < tl.challenge.start || f >= tl.challenge.end) return null;
  const remaining = Math.ceil((tl.challenge.end - f) / tl.fps);
  const p = (f - tl.challenge.start) / tl.challenge.dur;
  const op = fade(f, tl.challenge.start, tl.challenge.end, 10);
  const barW = s.w * 0.6;
  return (
    <SafeText anchor="bottom" offset={30} opacity={op}>
      <div style={{ fontSize: 120, fontWeight: 900 }}>{remaining}</div>
      <div
        style={{
          margin: "14px auto 0",
          width: barW,
          height: 12,
          borderRadius: 6,
          background: "rgba(255,255,255,0.25)",
          overflow: "hidden",
        }}
      >
        <div style={{ width: barW * p, height: "100%", background: reel.palette.fg, borderRadius: 6 }} />
      </div>
    </SafeText>
  );
};

export const RevealText: React.FC<{ reel: Reel; tl: Timeline }> = ({ reel, tl }) => {
  const f = useCurrentFrame();
  if (!reel.reveal.text || f < tl.reveal.start || f >= tl.reveal.end) return null;
  return (
    <SafeText anchor="top" offset={30} opacity={fade(f, tl.reveal.start + 6, tl.reveal.end)}>
      <div style={{ fontSize: 76, fontWeight: 900, textTransform: "uppercase" }}>{reel.reveal.text}</div>
    </SafeText>
  );
};

export const EndText: React.FC<{ reel: Reel; tl: Timeline }> = ({ reel, tl }) => {
  const f = useCurrentFrame();
  const from = tl.transform.start + Math.round(tl.transform.dur * 0.35);
  if (!reel.endText || f < from || f >= tl.bridge.start) return null;
  return (
    <SafeText anchor="bottom" offset={60} opacity={fade(f, from, tl.bridge.start, 10)}>
      <div style={{ fontSize: 72, fontWeight: 900 }}>{reel.endText}</div>
    </SafeText>
  );
};

export const Captions: React.FC<{ reel: Reel; tl: Timeline }> = ({ reel, tl }) => {
  const f = useCurrentFrame();
  const active = reel.captions.find((c) => {
    const a = resolveTime(c.at, tl);
    return f >= a && f < a + Math.round(c.dur * tl.fps);
  });
  if (!active) return null;
  const a = resolveTime(active.at, tl);
  return (
    <SafeText anchor="bottom" offset={230} opacity={fade(f, a, a + Math.round(active.dur * tl.fps), 5)}>
      <div style={{ fontSize: 52, fontWeight: 700 }}>{active.text}</div>
    </SafeText>
  );
};

/** Brief notice before intense patterns. Visible on frame 0 so it is also there when the reel loops. */
export const IntensityNotice: React.FC<{ reel: Reel; tl: Timeline }> = ({ reel, tl }) => {
  const f = useCurrentFrame();
  const s = useSafeRect();
  const until = tl.challenge.start + 2 * tl.fps;
  if (!reel.intense || f >= until) return null;
  const op = interpolate(f, [until - 12, until], [1, 0], { extrapolateLeft: "clamp" });
  return (
    <div
      style={{
        position: "absolute",
        left: s.x,
        width: s.w,
        top: s.y + s.h - 270, // above the countdown block
        textAlign: "center",
        opacity: op,
        fontFamily: FONT,
        fontWeight: 700,
        fontSize: 34,
        color: "#ffffff",
        textShadow: SHADOW,
      }}
    >
      ⚠️ Intense visual pattern
    </div>
  );
};

/** Preview only (toggle `showSafeZone` in Studio): shades areas covered by platform UI. */
export const SafeZoneOverlay: React.FC = () => {
  const s = useSafeRect();
  const { width, height } = useVideoConfig();
  const shade = "rgba(255,0,80,0.28)";
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div style={{ position: "absolute", left: 0, top: 0, width, height: s.y, background: shade }} />
      <div style={{ position: "absolute", left: 0, top: s.y + s.h, width, height: height - s.y - s.h, background: shade }} />
      <div style={{ position: "absolute", left: 0, top: s.y, width: s.x, height: s.h, background: shade }} />
      <div style={{ position: "absolute", left: s.x + s.w, top: s.y, width: width - s.x - s.w, height: s.h, background: shade }} />
      <div style={{ position: "absolute", left: s.x, top: s.y, width: s.w, height: s.h, outline: "4px dashed #00ffd0" }} />
    </AbsoluteFill>
  );
};

/** Cover still: big title over the chosen frame. HUD overlays are hidden in cover mode. */
export const CoverOverlay: React.FC<{ reel: Reel }> = ({ reel }) => (
  <AbsoluteFill>
    <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0) 45%)" }} />
    <SafeText anchor="top" offset={20}>
      <div style={{ fontSize: 132, fontWeight: 900, textTransform: "uppercase", letterSpacing: -2 }}>{reel.cover.title}</div>
      {reel.cover.sub && <div style={{ fontSize: 60, fontWeight: 700, marginTop: 16, color: reel.palette.fg }}>{reel.cover.sub}</div>}
    </SafeText>
  </AbsoluteFill>
);
