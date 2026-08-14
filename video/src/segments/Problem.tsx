import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";
import { Leaf } from "../components/Leaf";

const Stat: React.FC<{
  from: string;
  to: string;
  caption: string;
  showAt: number;
}> = ({ from, to, caption, showAt }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const local = frame - showAt;
  const opacity = interpolate(local, [0, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const flip = spring({ frame: local, fps, config: { damping: 200 }, durationInFrames: 25 });

  return (
    <div style={{ opacity, display: "flex", alignItems: "baseline", gap: 20 }}>
      <span
        style={{
          fontFamily: theme.font.computed,
          fontSize: 64,
          color: theme.color.paper,
          opacity: 1 - flip,
          position: flip > 0.5 ? "absolute" : "static",
        }}
      >
        {from}
      </span>
      <span
        style={{
          fontFamily: theme.font.computed,
          fontSize: 64,
          color: theme.color.shamrock,
          opacity: flip,
        }}
      >
        {flip > 0.5 ? to : from}
      </span>
      <span style={{ fontFamily: theme.font.prose, fontSize: 26, color: theme.color.paper, maxWidth: 420 }}>
        {caption}
      </span>
    </div>
  );
};

export const Problem: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const titleOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const titleY = spring({ frame, fps, config: { damping: 200 } });
  const fadeOut = interpolate(frame, [860, 900], [1, 0], { extrapolateLeft: "clamp" });

  const taglineOpacity = interpolate(frame - 140, [0, 25], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const subcaptionOpacity = interpolate(frame - 220, [0, 25], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: theme.color.phthalo, opacity: fadeOut }}>
      <AbsoluteFill style={{ padding: 90, justifyContent: "flex-start" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 18,
            opacity: titleOpacity,
            transform: `translateY(${(1 - titleY) * -30}px)`,
          }}
        >
          <Leaf size={64} color={theme.color.shamrock} />
          <span style={{ fontFamily: theme.font.computed, fontSize: 72, color: theme.color.paper }}>
            Bonbibi
          </span>
        </div>

        <div
          style={{
            opacity: titleOpacity,
            marginTop: 10,
            fontFamily: theme.font.chrome,
            fontSize: 18,
            color: theme.color.shamrock,
            letterSpacing: "0.04em",
          }}
        >
          ADAM MUNAWAR RAHMAN, ARM CREATE: AI OPTIMIZATION CHALLENGE 2026, PHYSICAL AI TRACK
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 28, marginTop: 60 }}>
          <Stat from="26%" to="39%" caption="of disabled evacuees could leave immediately, with warning" showAt={35} />
          <Stat from="10%" to="6%" caption="could not evacuate at all, with warning" showAt={70} />
        </div>

        <div
          style={{
            opacity: taglineOpacity,
            marginTop: 60,
            fontFamily: theme.font.prose,
            fontSize: 30,
            color: theme.color.paper,
            maxWidth: 900,
            lineHeight: 1.4,
          }}
        >
          Warning works. <strong style={{ color: theme.color.shamrock }}>Routing is the missing half</strong>, and
          in the places that flood worst, connectivity fails first.
        </div>

        <div
          style={{
            opacity: subcaptionOpacity,
            marginTop: 40,
            fontFamily: theme.font.chrome,
            fontSize: 22,
            color: theme.color.paper,
            letterSpacing: "0.04em",
          }}
        >
          1.81 BILLION PEOPLE FACE SIGNIFICANT FLOOD RISK, 89% IN LOW- AND MIDDLE-INCOME COUNTRIES
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
