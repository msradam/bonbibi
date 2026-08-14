import { Composition } from "remotion";
import "./index.css";
import { BonbibiVideo } from "./BonbibiVideo";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Bonbibi"
      component={BonbibiVideo}
      durationInFrames={5400}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
