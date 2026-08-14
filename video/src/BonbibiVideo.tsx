import React, { useEffect } from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { Fonts } from "./Fonts";
import { Problem } from "./segments/Problem";
import { LiveDemo } from "./segments/LiveDemo";
import { HowItWorks } from "./segments/HowItWorks";
import { ArmSpecifics } from "./segments/ArmSpecifics";

// 30fps, 5400 frames = 180s = exactly 3:00, the Devpost limit.
// 0:00-0:30 problem | 0:30-1:30 live demo | 1:30-2:20 how it works | 2:20-3:00 Arm specifics
// Matches the storyboard in HACKATHON.md "UX brief for the demo".
export const BonbibiVideo: React.FC = () => {
  useEffect(() => {
    document.title = "Bonbibi";
  }, []);

  return (
    <AbsoluteFill>
      <Fonts />
      <Sequence from={0} durationInFrames={900}>
        <Problem />
      </Sequence>
      <Sequence from={900} durationInFrames={1800}>
        <LiveDemo />
      </Sequence>
      <Sequence from={2700} durationInFrames={1500}>
        <HowItWorks />
      </Sequence>
      <Sequence from={4200} durationInFrames={1200}>
        <ArmSpecifics />
      </Sequence>
    </AbsoluteFill>
  );
};
