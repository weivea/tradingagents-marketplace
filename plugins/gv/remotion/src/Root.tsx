import { Composition } from "remotion";
import { ShortVideo } from "./ShortVideo";
import type { VideoProps } from "./types";

const FPS = 30;

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="ShortVideo"
      component={ShortVideo}
      durationInFrames={300} // placeholder, overridden by props
      fps={FPS}
      width={1080}
      height={1920}
      defaultProps={{
        sections: [],
        timestamps: [],
        audioPath: "",
        totalDuration: 10,
        seed: "default",
      }}
      calculateMetadata={({ props }) => {
        return {
          durationInFrames: Math.ceil(props.totalDuration * FPS),
        };
      }}
    />
  );
};
