import React from "react";
import { AbsoluteFill, interpolate, Sequence, useCurrentFrame } from "remotion";
import { theme } from "../theme";
import { StatCard } from "../components/StatCard";
import { Leaf } from "../components/Leaf";

const Fade: React.FC<{ from: number; durationInFrames: number; children: React.ReactNode }> = ({
  from,
  durationInFrames,
  children,
}) => {
  const frame = useCurrentFrame();
  const local = frame - from;
  const opacity = interpolate(local, [0, 15, durationInFrames - 15, durationInFrames], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return <div style={{ opacity, position: "absolute", inset: 0, padding: 90 }}>{children}</div>;
};

const Heading: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div
    style={{
      fontFamily: theme.font.chrome,
      fontSize: 24,
      color: theme.color.shamrock,
      letterSpacing: "0.06em",
      marginBottom: 30,
    }}
  >
    {children}
  </div>
);

export const ArmSpecifics: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: theme.color.phthalo }}>
      <div
        style={{
          position: "absolute",
          top: 40,
          right: 90,
          fontFamily: theme.font.chrome,
          fontSize: 20,
          color: theme.color.paper,
          letterSpacing: "0.04em",
        }}
      >
        ARM-SPECIFIC OPTIMIZATION, MEASURED, NOT ASSUMED
      </div>

      <Sequence from={0} durationInFrames={260}>
        <Fade from={0} durationInFrames={260}>
          <Heading>NATIVE REPACK BEATS ARM KLEIDIAI</Heading>
          <div style={{ display: "flex", gap: 40 }}>
            <StatCard value="+39.7" unit="%" label="PROMPT PROCESSING" accent={theme.color.shamrock} />
            <StatCard value="+14.3" unit="%" label="DECODE" accent={theme.color.jade} />
          </div>
          <div style={{ fontFamily: theme.font.prose, fontSize: 22, color: theme.color.paper, marginTop: 30, maxWidth: 1000 }}>
            Cortex-A76 has no i8mm/SVE, so KleidiAI never reaches its best kernels here: llama.cpp&apos;s own aarch64
            dotprod repack path wins on the production model. Verified live, not assumed.
          </div>
        </Fade>
      </Sequence>

      <Sequence from={260} durationInFrames={260}>
        <Fade from={0} durationInFrames={260}>
          <Heading>A REAL BUG, FOUND AND FIXED</Heading>
          <div style={{ display: "flex", gap: 40 }}>
            <StatCard value="10.6" unit="x" label="PROMPT PROCESSING, GPU HIDDEN VS VISIBLE" accent={theme.color.shamrock} />
          </div>
          <div style={{ fontFamily: theme.font.prose, fontSize: 22, color: theme.color.paper, marginTop: 30, maxWidth: 1000 }}>
            Any visible Vulkan device pins CPU weights in GPU write-combined memory, even at zero GPU layers. One
            environment variable fixes it: worth 10.6x, not the 22% an earlier pass measured on a smaller model.
          </div>
        </Fade>
      </Sequence>

      <Sequence from={520} durationInFrames={240}>
        <Fade from={0} durationInFrames={240}>
          <Heading>Q4_0 BEATS EVERY K-QUANT AND SPECULATIVE DECODING</Heading>
          <div style={{ display: "flex", gap: 40 }}>
            <StatCard value="+73.9" unit="%" label="Q4_0 VS. BEST K-QUANT (PROMPT)" accent={theme.color.shamrock} />
            <StatCard value="6.0" unit="% slower" label="SPECULATIVE DECODING, REJECTED" accent={theme.color.complementary} />
          </div>
        </Fade>
      </Sequence>

      <Sequence from={760} durationInFrames={440}>
        <Fade from={0} durationInFrames={440}>
          <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
              <Leaf size={80} color={theme.color.shamrock} />
              <span style={{ fontFamily: theme.font.computed, fontSize: 90, color: theme.color.paper }}>Bonbibi</span>
            </div>
            <div
              style={{
                fontFamily: theme.font.prose,
                fontSize: 26,
                color: theme.color.paper,
                marginTop: 30,
                textAlign: "center",
              }}
            >
              github.com/msradam/bonbibi: MIT licensed, fully reproducible
            </div>
            <div
              style={{
                fontFamily: theme.font.chrome,
                fontSize: 20,
                color: theme.color.shamrock,
                marginTop: 16,
                letterSpacing: "0.04em",
              }}
            >
              ARM AI OPTIMIZATION CHALLENGE 2026, PHYSICAL AI TRACK
            </div>
          </AbsoluteFill>
        </Fade>
      </Sequence>
    </AbsoluteFill>
  );
};
