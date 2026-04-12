import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";

interface Props {
  progress: number;
  icon?: string;
  enterDelay?: number;
}

export const ProgressBar: React.FC<Props> = ({ progress, icon = "❶", enterDelay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const delayFrames = Math.round(enterDelay * fps);

  const fillProgress = interpolate(
    frame - delayFrames,
    [0, 20],
    [0, progress * 100],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  const opacity = interpolate(
    frame - delayFrames,
    [0, 10],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <div
      style={{
        position: "absolute",
        bottom: 120,
        left: 80,
        right: 80,
        display: "flex",
        alignItems: "center",
        gap: 16,
        opacity,
      }}
    >
      <span style={{ fontSize: 24, fontWeight: 700, color: "#8b5cf6", minWidth: 36 }}>
        {icon}
      </span>
      <div
        style={{
          flex: 1,
          height: 4,
          background: "rgba(255, 255, 255, 0.1)",
          borderRadius: 2,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${fillProgress}%`,
            background: "linear-gradient(90deg, #8b5cf6, #3b82f6)",
            borderRadius: 2,
          }}
        />
      </div>
    </div>
  );
};
