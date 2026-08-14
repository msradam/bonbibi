import React from "react";
import {
  AbsoluteFill,
  interpolate,
  OffthreadVideo,
  Sequence,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { theme } from "../theme";
import { Leaf } from "../components/Leaf";

const CaptureSlot: React.FC<{ src: string }> = ({ src }) => (
  <AbsoluteFill style={{ backgroundColor: theme.color.phthaloMid }}>
    <OffthreadVideo src={staticFile(`captures/${src}`)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
  </AbsoluteFill>
);

const LowerThird: React.FC<{ text: string; frame: number; from: number }> = ({ text, frame, from }) => {
  const local = frame - from;
  const opacity = interpolate(local, [0, 15, 45, 60], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        position: "absolute",
        bottom: 70,
        left: 70,
        opacity,
        background: theme.color.phthalo,
        border: `2px solid ${theme.color.shamrock}`,
        padding: "14px 24px",
        fontFamily: theme.font.chrome,
        fontSize: 24,
        color: theme.color.paper,
        letterSpacing: "0.03em",
      }}
    >
      {text}
    </div>
  );
};

// Title (0-90) + three ~19s capture slots filling the rest of the
// 1800-frame (60s) segment exactly, so nothing goes to a blank screen.
export const LiveDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const titleOpacity = interpolate(frame, [0, 20, 60, 90], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: theme.color.ink }}>
      <AbsoluteFill
        style={{
          alignItems: "center",
          justifyContent: "center",
          opacity: titleOpacity,
          zIndex: 2,
          backgroundColor: theme.color.phthalo,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <Leaf size={44} color={theme.color.shamrock} />
          <span style={{ fontFamily: theme.font.chrome, fontSize: 34, color: theme.color.paper, letterSpacing: "0.06em" }}>
            LIVE ON A RASPBERRY PI 5, NO INTERNET
          </span>
        </div>
      </AbsoluteFill>

      {/* panel: IDLE -> real self-test -> RUN FLOOD CHECK -> RUNNING */}
      <Sequence from={90} durationInFrames={570}>
        <CaptureSlot src="panel_idle_to_run.mp4" />
        <LowerThird text="THE PANEL ITSELF, REAL SELF-TEST, REAL FLOOD SIM" frame={frame} from={90} />
      </Sequence>

      {/* console: storm runs, hazard bands drape over the real basemap */}
      <Sequence from={660} durationInFrames={570}>
        <CaptureSlot src="console_storm_run.mp4" />
        <LowerThird text="GPU FLOOD SIMULATION, PHYSICS-VERIFIED EVERY FRAME" frame={frame} from={660} />
      </Sequence>

      {/* console: tap a location, routes diverge by mobility profile, guidance streams */}
      <Sequence from={1230} durationInFrames={570}>
        <CaptureSlot src="console_routes_diverge.mp4" />
        <LowerThird text="ONE VERDICT PER PROFILE, DETERMINISTIC, NEVER THE LLM" frame={frame} from={1230} />
      </Sequence>
    </AbsoluteFill>
  );
};
