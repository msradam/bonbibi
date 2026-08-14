import React from "react";
import { AbsoluteFill, interpolate, Sequence, useCurrentFrame } from "remotion";
import { theme } from "../theme";
import { StatCard } from "../components/StatCard";

const sceneOpacity = (frame: number, durationInFrames: number) =>
  interpolate(frame, [0, 20, durationInFrames - 20, durationInFrames], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

const Kernel: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: theme.color.phthalo, padding: 90, opacity: sceneOpacity(frame, 560) }}>
      <div style={{ fontFamily: theme.font.chrome, fontSize: 26, color: theme.color.shamrock, letterSpacing: "0.06em", marginBottom: 20 }}>
        HOW IT WORKS
      </div>
      <div style={{ fontFamily: theme.font.prose, fontSize: 34, color: theme.color.paper, maxWidth: 1100, lineHeight: 1.4, marginBottom: 50 }}>
        One board, two engines, running at the same time: the GPU simulates the flood while four Arm cores route
        people and narrate the result.
      </div>
      <div style={{ display: "flex", gap: 40 }}>
        <StatCard value="1.59" unit="x" label="GPU KERNEL, LLM-OPTIMIZED, CORRECTNESS-GATED" accent={theme.color.shamrock} />
        <StatCard value="2.09" unit="x" label="THAT ADVANTAGE GROWS UNDER CONCURRENT LOAD" accent={theme.color.jade} />
      </div>
      <div style={{ fontFamily: theme.font.prose, fontSize: 24, color: theme.color.paper, maxWidth: 1000, marginTop: 30, lineHeight: 1.4 }}>
        A finite-state machine owns compile → verify → benchmark → keep/revert. A kernel that fails physics can never
        produce a benchmark number. It refuses to score a deliberately mass-violating variant.
      </div>
    </AbsoluteFill>
  );
};

const Concurrency: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: theme.color.phthalo, padding: 90, opacity: sceneOpacity(frame, 940) }}>
      <div style={{ fontFamily: theme.font.chrome, fontSize: 22, color: theme.color.shamrock, letterSpacing: "0.04em", marginBottom: 30 }}>
        THE CONCURRENCY COUNTERFACTUAL
      </div>
      <table style={{ fontFamily: theme.font.computed, fontSize: 26, color: theme.color.paper, borderCollapse: "collapse", width: "100%", maxWidth: 1100 }}>
        <thead>
          <tr style={{ borderBottom: `2px solid ${theme.color.paper}` }}>
            <th style={{ textAlign: "left", padding: "10px 20px", fontFamily: theme.font.chrome, fontWeight: 400 }}>CONDITION</th>
            <th style={{ textAlign: "right", padding: "10px 20px", fontFamily: theme.font.chrome, fontWeight: 400 }}>GPU STEPS/S</th>
            <th style={{ textAlign: "right", padding: "10px 20px", fontFamily: theme.font.chrome, fontWeight: 400 }}>CPU T/S</th>
          </tr>
        </thead>
        <tbody>
          <tr style={{ color: theme.color.shamrock }}>
            <td style={{ padding: "10px 20px" }}>DEPLOYMENT (GPU + CPU SPLIT)</td>
            <td style={{ textAlign: "right", padding: "10px 20px" }}>712</td>
            <td style={{ textAlign: "right", padding: "10px 20px" }}>10.3</td>
          </tr>
          <tr>
            <td style={{ padding: "10px 20px" }}>BEST CPU-ONLY ALTERNATIVE</td>
            <td style={{ textAlign: "right", padding: "10px 20px" }}>681</td>
            <td style={{ textAlign: "right", padding: "10px 20px" }}>8.4</td>
          </tr>
        </tbody>
      </table>
      <div style={{ fontFamily: theme.font.prose, fontSize: 22, color: theme.color.paper, marginTop: 20 }}>
        The split wins both axes at once, against partitioned, oversubscribed, and time-sliced CPU-only
        alternatives.
      </div>
    </AbsoluteFill>
  );
};

export const HowItWorks: React.FC = () => {
  return (
    <>
      <Sequence from={0} durationInFrames={560}>
        <Kernel />
      </Sequence>
      <Sequence from={560} durationInFrames={940}>
        <Concurrency />
      </Sequence>
    </>
  );
};
