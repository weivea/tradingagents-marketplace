import React from "react";
import { Composition } from "remotion";
import { ShortVideo } from "./ShortVideo";
import type { VideoProps } from "./types";

const FPS = 30;

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="ShortVideo"
      component={ShortVideo as unknown as React.FC<Record<string, unknown>>}
      durationInFrames={300} // placeholder, overridden by props
      fps={FPS}
      width={1080}
      height={1920}
      defaultProps={
        {
          sections: [],
          timestamps: [],
          audioPath: "",
          totalDuration: 10,
          seed: "default",
        } as Record<string, unknown>
      }
      calculateMetadata={({ props }) => {
        const vp = props as unknown as VideoProps;
        return {
          durationInFrames: Math.ceil(vp.totalDuration * FPS),
        };
      }}
    />
  );
};
